package org.hisp.dhis.datageneration.generator.unit;

/*
 * Copyright (c) 2004-2019, University of Oslo
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 *
 * Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 * Neither the name of the HISP project nor the names of its contributors may
 * be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 * ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.base.Joiner;
import com.vividsolutions.jts.geom.Point;
import net.andreinc.mockneat.types.enums.StringType;
import net.andreinc.mockneat.unit.objects.From;
import net.andreinc.mockneat.unit.text.Strings;
import org.hisp.dhis.common.CodeGenerator;
import org.hisp.dhis.common.ValueType;
import org.hisp.dhis.datageneration.cache.EntityCache;
import org.hisp.dhis.datageneration.domain.*;
import org.hisp.dhis.datageneration.generator.DefaultGenerationOptions;
import org.hisp.dhis.datageneration.generator.IdCounter;
import org.hisp.dhis.datageneration.utils.CollectionSizer;
import org.hisp.dhis.datageneration.utils.RandomUtils;
import org.hisp.dhis.dxf2.events.event.DataValue;

import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static net.andreinc.mockneat.unit.text.SQLInserts.sqlInserts;
import static net.andreinc.mockneat.unit.time.LocalDates.localDates;
import static net.andreinc.mockneat.unit.types.Bools.bools;
import static net.andreinc.mockneat.unit.types.Doubles.doubles;
import static net.andreinc.mockneat.unit.types.Ints.ints;
import static org.hisp.dhis.datageneration.utils.PostgreSQL.TEXT_BACKSLASH;
import static org.hisp.dhis.datageneration.utils.PostgreSQL.TEXT_BACKSLASH_NO_ESCAPE;
import static org.hisp.dhis.datageneration.utils.RandomUtils.*;

/**
 * @author Luciano Fiandesio
 */
public class TeiUnit
    implements
    Unit
{
    private ObjectMapper mapper = new ObjectMapper();

    public List<String> get( DefaultGenerationOptions options, EntityCache entityCache, IdCounter idCounter )
    {
        long defaultAoc = entityCache.getDefaultAttributeOptionComboId();

        List<String> statements = new ArrayList<>();

        // Get a program that is type Tracker
        Program program = getRandomTrackerProgram( entityCache );

        long teiId = idCounter.getCounter( "TEI" );
        long piId = idCounter.getCounter( "PI" );

        // pick a random OU from the program
        long ouId = From.from( program.getOrgUnits() ).get().getId();

        statements.add( sqlInserts().tableName( "trackedentityinstance" )
            .column( "trackedentityinstanceid", Long.toString( teiId ) )
            .column( "organisationunitid", Long.toString( ouId ) )
            .column( "uid", CodeGenerator.generateUid(), TEXT_BACKSLASH )
            .column( "created", localDateTime(), TEXT_BACKSLASH )
            .column( "lastupdated", localDateTime(), TEXT_BACKSLASH )
            .column( "trackedentitytypeid", program.getTeiType().toString() )
            .column( "inactive", "false", TEXT_BACKSLASH )
            // .column("lastupdatedby", localDates().thisYear().display(BASIC_ISO_DATE))
            .column( "createdatclient", localDateTime(), TEXT_BACKSLASH )
            // .column("lastupdatedatclient",
            .column( "deleted", "false", TEXT_BACKSLASH )
            // .column("geometry", localDates().thisYear().display(BASIC_ISO_DATE))
            .column( "featuretype", "NONE", TEXT_BACKSLASH )
            // .column("coordinates", localDates().thisYear().display(BASIC_ISO_DATE))
            // .column("code", strings().size(5), TEXT_BACKSLASH)
            // .column("created", "2014-03-26 15:40:12", TEXT_BACKSLASH)
            .get().toString() );

        idCounter.increment("TEI");

        String created = localDateTime();
        String enrollmentDate = localDateTime();
        // Enrollment
        statements.add( sqlInserts().tableName( "programinstance" )
            .column( "programinstanceid", Long.toString( piId ) )
            .column( "enrollmentdate", enrollmentDate, TEXT_BACKSLASH )
            .column( "programid", program.getId().toString() )
            .column( "status", "COMPLETED", TEXT_BACKSLASH )
            .column( "uid", CodeGenerator.generateUid(), TEXT_BACKSLASH )
            .column( "created", created, TEXT_BACKSLASH )
            .column( "lastUpdated", created, TEXT_BACKSLASH )
            .column( "trackedentityinstanceid", Long.toString( teiId ) )
            .column( "organisationunitid", Long.toString( ouId ) )
            .column( "incidentdate", enrollmentDate, TEXT_BACKSLASH )
            .column( "createdatclient", localDateTime(), TEXT_BACKSLASH )
            .column( "deleted", "false", TEXT_BACKSLASH )
            .get().toString() );

        idCounter.increment( "PI" );

        int eventsSize = CollectionSizer.getCollectionSize( options.getTeiGenerationOptions().getEventsRange() );

        ProgramStage programStage = From.from( program.getStages() ).get();

        // Events
        statements.add( Joiner.on( "\n" ).join( IntStream.rangeClosed( 1, eventsSize ).mapToObj( ev -> {
            long eventId = idCounter.getCounter( "PSI" );
            String sql =  sqlInserts().tableName( "programstageinstance" )
                .column( "programstageinstanceid", Long.toString( eventId ) )
                .column( "programinstanceid", Long.toString( piId ) )
                .column( "programstageid", Long.toString( programStage.getId() ) )
                .column( "duedate", localDateTimeInFuture(), TEXT_BACKSLASH )
                // .column( "executiondate", rndFactory.dateTimesInFuture(), TEXT_BACKSLASH )
                // TODO ok to be null ?
                // .column( "completed", rndFactory.dateTimesInFuture(), TEXT_BACKSLASH ) TODO
                // ok to be null ?
                .column( "organisationunitid", Long.toString( ouId ) )
                .column( "status", "ACTIVE", TEXT_BACKSLASH )
                .column( "uid", CodeGenerator.generateUid(), TEXT_BACKSLASH )
                .column( "created", created, TEXT_BACKSLASH )
                .column( "lastupdated", created, TEXT_BACKSLASH )
                .column( "attributeoptioncomboid", Long.toString( defaultAoc ) )
                .column( "deleted", "false", TEXT_BACKSLASH )
                .column( "eventdatavalues",
                    createDataValuesAsJson( programStage, options.getTeiGenerationOptions().getDataValueRange() ),
                    TEXT_BACKSLASH_NO_ESCAPE )
                .get().toString();
            idCounter.increment( "PSI" );
            return sql;
        } ).collect( Collectors.toList() ) ) );
        
        // how many program attributes to create //
        int attributeSize = CollectionSizer.getCollectionSize( options.getTeiGenerationOptions().getEventsRange(),
            program.getAttributes().size() );
        
        statements.add( Joiner.on( "\n" ).join( randomizeSequence( attributeSize ).stream().map( ev -> {

            ProgramAttribute attribute =  program.getAttributes().get( ev );

            return sqlInserts().tableName( "trackedentityattributevalue" )
                .column( "trackedentityinstanceid", Long.toString( teiId ) )
                .column( "trackedentityattributeid", Long.toString( attribute.getId() ) )
                .column( "value", rndValueFrom( attribute.getValueType() ), TEXT_BACKSLASH )
                .column( "created", created, TEXT_BACKSLASH )
                .column( "lastupdated", created, TEXT_BACKSLASH ).get()
                .toString();
        } ).collect( Collectors.toList() ) ) );

        return statements;
    }

    private Program getRandomTrackerProgram( EntityCache entityCache )
    {
        return From
            .from(
                entityCache.getPrograms().stream().filter( p -> p.getTeiType() != 0 ).collect( Collectors.toList() ) )
            .get();
    }

    private String createDataValuesAsJson( ProgramStage programStage, String dataValueSizeRange )
    {
        List<Integer> indexes = randomizeSequence( programStage.getDataElements().size() );

        List<String> values = new ArrayList<>();

        for ( Integer index : indexes )
        {
            StringBuilder sb = new StringBuilder();

            DataElement de = programStage.getDataElements().get( index );

            DataValue dv = withRandomValue( de );
            sb.append( "\"" ).append( de.getUid() ).append( "\":" );
            try
            {
                sb.append( mapper.writeValueAsString( dv ) );
            }
            catch ( Exception e )
            {
                e.printStackTrace(); // TODO
            }
            values.add( sb.toString() );
        }
        return "{" + Joiner.on( "," ).join( values ) + "}";

    }

    private DataValue withRandomValue( DataElement dataElement )
    {
        DataValue dataValue = new DataValue();
        dataValue.setDataElement( dataElement.getUid() );
        dataValue.setProvidedElsewhere( false );
        String val;

        if ( dataElement.getOptionSet() != null && !dataElement.getOptionSet().isEmpty() )
        {
            val = dataElement.getOptionSet().get( ints().range( 0, dataElement.getOptionSet().size() - 1 ).get() );
        }
        else
        {
            val = rndValueFrom( dataElement.getValueType() );
        }
        dataValue.setValue( val );
        return dataValue;
    }

    private String rndValueFrom( ValueType valueType )
    {
        String val = null;

        if ( valueType.isBoolean() )
        {
            if ( valueType.equals( ValueType.BOOLEAN ) )
            {
                val = String.valueOf( bools().get() );
            }
            else
            {
                // TRUE_ONLY
                val = "true";
            }
        }

        else if ( valueType.isDate() )
        {
            val = localDates().display( DateTimeFormatter.ISO_LOCAL_DATE ).get();
        }

        else if ( valueType.isNumeric() )
        {
            val = String.valueOf( ints().range( 1, 10000 ).get() );
        }
        else if ( valueType.isDecimal() )
        {
            val = String.valueOf( doubles().range( 100.0, 1000.0 ).get() );
        }
        else if ( valueType.isText() )
        {
            val = Strings.strings().type( StringType.LETTERS ).get();
        }
        else if ( valueType.isOrganisationUnit() )
        {
            val = ""; // TODO
        }
        else if ( valueType.isGeo() )
        {
            Point p = createRandomPoint();
            val = p.getY() + ", " + p.getY();
        }
        return val;
    }
}

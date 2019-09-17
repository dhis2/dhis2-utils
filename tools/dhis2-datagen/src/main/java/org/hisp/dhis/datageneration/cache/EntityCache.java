package org.hisp.dhis.datageneration.cache;

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

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.hisp.dhis.common.ValueType;
import org.hisp.dhis.datageneration.domain.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.rowset.SqlRowSet;
import org.springframework.stereotype.Component;

import com.google.common.collect.Lists;

import lombok.Getter;
import lombok.extern.java.Log;

/**
 * @author Luciano Fiandesio
 */
@Log
@Component
public class EntityCache
{

    private JdbcTemplate jdbcTemplate;

    private Map<String, List<DataElement>> programStageDateElementMap;

    @Getter
    private boolean init = false;

    @Getter
    private List<Program> programs;

    @Getter
    private List<TeiType> teiTypes;

    @Getter
    private List<CategoryOptionCombo> categoryOptionCombos;

    @Getter
    private Long defaultAttributeOptionComboId;
    
    public EntityCache( JdbcTemplate jdbcTemplate )
    {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void init()
    {

        log.info( "init cache creation" );

        loadTeiTypes();

        loadCategoryOptionCombos();
        
        defaultAttributeOptionComboId = categoryOptionCombos.stream().filter( CategoryOptionCombo::isDefaultCoc )
            .findFirst().get().getId();
        
        loadDataElementsByProgramStage();

        loadPrograms();

        log.info( programs.size() + " programs loaded in cache" );

        init = true;
    }

    private void loadTeiTypes()
    {
        teiTypes = jdbcTemplate.query( "SELECT trackedentitytypeid, name FROM trackedentitytype", new Object[] {},
            ( resultSet, rowNum ) -> new TeiType( resultSet.getLong( "trackedentitytypeid" ),
                resultSet.getString( "name" ) ) );
    }

    private void loadCategoryOptionCombos()
    {
        categoryOptionCombos = jdbcTemplate.query( "SELECT categoryoptioncomboid, name FROM categoryoptioncombo",
            new Object[] {},
            ( resultSet, rowNum ) -> new CategoryOptionCombo( resultSet.getLong( "categoryoptioncomboid" ),
                resultSet.getString( "name" ), resultSet.getString( "name" ).equalsIgnoreCase( "default" ) ) );
    }

    private void loadDataElementsByProgramStage()
    {

        programStageDateElementMap = new HashMap<>();

        SqlRowSet srs = jdbcTemplate
            .queryForRowSet( "SELECT ps.uid as psuid, de.uid, de.valuetype\n" + "FROM dataelement de\n"
                + "         JOIN programstagedataelement p on de.dataelementid = p.dataelementid\n"
                + "         JOIN programstage ps on ps.programstageid = p.programstageid\n"
                + "group by ps.uid, de.uid, de.valuetype\n" + "order by ps.uid" );

        String key = null;
        while ( srs.next() )
        {

            String programStageUid = srs.getString( "psuid" );
            if ( programStageDateElementMap.containsKey( programStageUid ) )
            {
                programStageDateElementMap.get( programStageUid ).add( fromSqlRowSet( srs ) );
            }
            else
            {
                programStageDateElementMap.put( programStageUid, Lists.newArrayList( fromSqlRowSet( srs ) ) );
            }
        }
    }

    private DataElement fromSqlRowSet( SqlRowSet srs )
    {
        // TODO add option sets
        return new DataElement( srs.getString( "uid" ), ValueType.valueOf( srs.getString( "valuetype" ) ), null );
    }

    private void loadPrograms()
    {

        programs = jdbcTemplate.query( "SELECT programid, uid, type, trackedentitytypeid FROM PROGRAM", new Object[] {},
            ( rs, rowNum ) -> new Program( rs.getLong( "programid" ), rs.getString( "uid" ), rs.getString( "type" ),
                rs.getLong( "trackedentitytypeid" ), getOrgUnitByProgram( rs.getLong( "programid" ) ),
                getProgramStagesByProgram( rs.getString( "uid" ) ),
                getProgramAttibutesByProgram( rs.getLong( "programid" ) ) ) );

    }

    private List<ProgramAttribute> getProgramAttibutesByProgram(Long programId )
    {

        return jdbcTemplate.query(
            "select t.trackedentityattributeid, t.uid, t.valuetype, t.uniquefield from program_attributes pa "
                + "join trackedentityattribute t on pa.trackedentityattributeid = t.trackedentityattributeid "
                + "where pa.programid = ?;",
            new Object[] { programId },
            ( rs, rowNum ) -> new ProgramAttribute( rs.getLong( "trackedentityattributeid" ), rs.getString( "uid" ),
                ValueType.valueOf( rs.getString( "valuetype" ) ), rs.getBoolean( "uniquefield" ) ) );

    }

    private List<OrgUnit> getOrgUnitByProgram(Long programId )
    {

        return jdbcTemplate.query(
            "select o.organisationunitid, o.uid from program_organisationunits pou join organisationunit o on pou.organisationunitid = o.organisationunitid where pou.programid = ?",
            new Object[] { programId },
            ( rs, rowNum ) -> new OrgUnit( rs.getLong( "organisationunitid" ), rs.getString( "uid" ) ) );

    }

    private List<ProgramStage> getProgramStagesByProgram(String programUid )
    {

        return jdbcTemplate.query(
            "SELECT ps.programstageid, ps.uid from programstage ps join program p on ps.programid = p.programid where p.uid = ?",
            new Object[] { programUid }, ( rs, rowNum ) -> new ProgramStage(
                    rs.getLong( "programstageid" ),
                    rs.getString( "uid" ),
                programStageDateElementMap.get( rs.getString( "uid" ) ) ) );

    }
}

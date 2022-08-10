package org.hisp.dhis.datageneration.command;

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

import java.time.Duration;
import java.time.Instant;

import org.hisp.dhis.datageneration.cache.EntityCache;
import org.hisp.dhis.datageneration.generator.DefaultGenerationOptions;
import org.hisp.dhis.datageneration.generator.GeneratorFactory;
import org.hisp.dhis.datageneration.generator.GeneratorType;
import org.hisp.dhis.datageneration.generator.TeiGenerationOptions;
import org.hisp.dhis.datageneration.shell.ProgressBar;
import org.hisp.dhis.datageneration.shell.ShellHelper;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

/**
 * @author Luciano Fiandesio
 */
@ShellComponent
public class DataGenerationCommand
{

    private final EntityCache entityCache;

    private final GeneratorFactory factory;

    private final ShellHelper shellHelper;

    private ProgressBar progressBar;

    public DataGenerationCommand( EntityCache entityCache, GeneratorFactory factory, ShellHelper shellHelper, ProgressBar progressBar )
    {
        this.entityCache = entityCache;
        this.factory = factory;
        this.shellHelper = shellHelper;
        this.progressBar = progressBar;
    }

    @ShellMethod( "Generate SQL Insert script" )
    public String gen(
        @ShellOption( { "-S", "--size" } ) Long size,
        @ShellOption( value = { "-T", "--type" }, help = "available options: TEI" ) String type,
        @ShellOption( value = { "-F", "--file" }, help = "full path to destination file (e.g. /home/kirk/myfile.sql)" ) String pathToFile,
        @ShellOption( value = { "--events",  }, help = "range of events to generate (e.g. 1-10, will create 1 to 10 events)", defaultValue = "1-10") String eventsRange,
        @ShellOption( value = { "--attributes",  }, help = "range of attributes to generate (e.g. 1-10, will create 1 to 10 attributes)", defaultValue = "1-10") String attributesRange,
        @ShellOption( value = { "--dataValues",  }, help = "range of data values to generate (e.g. 1-10, will create 1 to 10 data values)", defaultValue = "1-10") String dataValuesRange)
    {
        Instant startGen = Instant.now();

        if ( !entityCache.isInit() )
        {
            Instant start = Instant.now();
            entityCache.init();
            Instant finish = Instant.now();
            shellHelper
                .printInfo( String.format( "Cache created in %d ms.", Duration.between( start, finish ).toMillis() ) );

        }

        this.factory.getGenerator( type ).generate( DefaultGenerationOptions.builder()
            .file( pathToFile ).quantity( size ).teiGenerationOptions( TeiGenerationOptions.builder()
                .eventsRange( eventsRange )
                .attributeRange( attributesRange )
                .dataValueRange( dataValuesRange ).build() )
            .build(), entityCache );

        return String.format( "Generation completed in %d ms.",
            Duration.between( startGen, Instant.now() ).toMillis() );

    }
}

package org.hisp.dhis.datageneration.generator;

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

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Observable;
import java.util.Observer;

import org.hisp.dhis.datageneration.cache.EntityCache;
import org.hisp.dhis.datageneration.domain.CategoryOptionCombo;
import org.hisp.dhis.datageneration.generator.unit.TeiUnit;
import org.hisp.dhis.datageneration.id.IdFactory;
import org.hisp.dhis.datageneration.observer.ProgressUpdateEvent;
import org.hisp.dhis.datageneration.writer.SqlStatementsWriter;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.java.Log;

/**
 * @author Luciano Fiandesio
 */
@Log
@Component
public class TeiGenerator
    extends
    Observable
    implements
    Generator
{

    private final IdFactory idFactory;

    private final EntityCache entityCache;

    private final SqlStatementsWriter writer;

    private final Observer observer;

    private ObjectMapper mapper;

    private final int CHUNCK_SIZE = 5000;

    public TeiGenerator(EntityCache entityCache, IdFactory idFactory, SqlStatementsWriter writer, Observer observer)
    {
        this.entityCache = entityCache;
        this.idFactory = idFactory;
        this.writer = writer;
        this.observer = observer;

        mapper =  new ObjectMapper();
    }

    public void generate( DefaultGenerationOptions options, EntityCache entityCache )
    {
        // TODO does it make sense to randomize this?
        long defaultaoc = entityCache.getCategoryOptionCombos().stream().filter( CategoryOptionCombo::isDefaultCoc )
            .findFirst().get().getId();



        long totalChunks = (options.getQuantity() < CHUNCK_SIZE ? 1 : options.getQuantity() / CHUNCK_SIZE);
        int currentChunkSize = 0;
        long processedChunks = 0;

        // fetch the first available IDS from target tables
        IdCounter counter = new IdCounter(
            "TEI", idFactory.getStartTeiId(),
            "PI", idFactory.getStartProgramInstanceId(),
            "PSI", idFactory.getStartProgramStageInstanceId());

        List<String> statements = new ArrayList<>();
        fireProgressEvent( processedChunks, totalChunks);
        for ( int i = 0; i < options.getQuantity(); i++ )
        {

            statements.addAll(new TeiUnit().get(options, entityCache, counter));

            currentChunkSize++;

            if ( currentChunkSize == CHUNCK_SIZE)
            {
                // flush to file the current chunk
                writer.write( new File( options.getFile() ), statements );
                // Reset StringBuilder
                statements = new ArrayList<>();
                //
                counter.updateAll( (long) CHUNCK_SIZE );
                // reset chunk count
                currentChunkSize = 0;
                // increment number of processed chunks so far
                processedChunks ++;
                // send event for progress bar in CLI
                fireProgressEvent( processedChunks, totalChunks);
            }
        }
        // flush remaining data
        writer.write( new File( options.getFile() ), statements );
    }
    
    private void fireProgressEvent( long processedChuncks, long totalChuncks )
    {
        if ( observer != null )
        {
            String message = "";
            if ( processedChuncks < totalChuncks )
            {
                message = ":: please WAIT ::";
            }
            observer.update( this, new ProgressUpdateEvent( processedChuncks, totalChuncks, message ) );
        }
    }

}

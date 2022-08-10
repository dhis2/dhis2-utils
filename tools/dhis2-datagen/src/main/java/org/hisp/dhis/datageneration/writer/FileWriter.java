package org.hisp.dhis.datageneration.writer;

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
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.Writer;
import java.nio.channels.Channels;
import java.util.List;

import org.springframework.stereotype.Component;

/**
 * @author Luciano Fiandesio
 */
@Component
public class FileWriter
    implements
    SqlStatementsWriter
{
    public void write( File file, StringBuilder sb )
    {
        if ( !file.exists() )
        {
            try
            {
                file.createNewFile();
            }
            catch ( IOException e )
            {
                e.printStackTrace();
            }
        }

        try (Writer writer = Channels.newWriter( new FileOutputStream( file.getAbsoluteFile(), true ).getChannel(),
            "UTF-8" ))
        {
            writer.append( sb );
        }
        catch ( IOException e )
        {
            e.printStackTrace();
        }
    }

    @Override
    public void write( File file, List<String> statements )
    {
        if ( !file.exists() )
        {
            try
            {
                file.createNewFile();

            }
            catch ( IOException e )
            {
                e.printStackTrace(); // TODO
            }
        }
        try
        {
            java.io.FileWriter writer = new java.io.FileWriter( file, true );
            write( statements, writer );
        }
        catch ( IOException e )
        {
            e.printStackTrace();
        }
    }

    private void write( List<String> records, Writer writer )
        throws IOException
    {
        // long start = System.currentTimeMillis();
        for ( String record : records )
        {
            writer.write( record + "\n" );
        }
        writer.flush();
        writer.close();
    }
}

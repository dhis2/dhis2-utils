package org.hisp.dhis.i18nresourceeditor.persistence;

/*
 * Copyright (c) 2004-2005, University of Oslo
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * * Redistributions of source code must retain the above copyright notice, this
 *   list of conditions and the following disclaimer.
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 * * Neither the name of the <ORGANIZATION> nor the names of its contributors may
 *   be used to endorse or promote products derived from this software without
 *   specific prior written permission.
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
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Hashtable;
import java.util.Locale;
import java.util.Properties;

import org.hisp.dhis.i18nresourceeditor.exception.I18nInvalidLocaleException;
import org.hisp.dhis.i18nresourceeditor.exception.I18nResourceException;

/**
 * @author Oyvind Brucker
 */
public class FileUtils
{
    public static Hashtable<String, String> loadResource( String path )
        throws I18nResourceException
    {
        File file = new File( path );

        Properties prop = new Properties();

        try
        {
            prop.load( new FileInputStream( file ) );
        }
        catch ( FileNotFoundException fnfe )
        {
            throw new I18nResourceException( "Error while loading resource, file not found", fnfe );
        }
        catch ( IOException ioe )
        {
            throw new I18nResourceException( "I/O Error while loading resource", ioe );
        }
        catch ( IllegalArgumentException iae )
        {
            throw new I18nResourceException( "Encoding related error while loading resource", iae );
        }
        
        Hashtable<String, String> hash = new Hashtable<String, String>();

        for ( Object key : prop.keySet() )
        {
            String k = (String) key;
            String v = prop.getProperty( k );
            hash.put( k, v );
        }

        return hash;
    }

    /**
     * @param content key/value pairs to save
     * @param path full path for the resource including complete filename with
     *        locale information
     * @throws I18nResourceException
     */
    public static void saveResource( Hashtable<?, ?> content, String path )
        throws I18nResourceException
    {
        File file = new File( path );

        Properties prop = new Properties();

        prop.putAll( content );

        try
        {
            clearFile( file );

            prop.store( new FileOutputStream( file, true ), null );
        }
        catch ( FileNotFoundException fnfe )
        {
            throw new I18nResourceException( "Error while saving resource, file not found", fnfe );
        }
        catch ( IOException ioe )
        {
            throw new I18nResourceException( "I/O Error while saving resource", ioe );
        }

    }

    /**
     * Converts a string from a filename convention (en_GB) to a locale object
     * Examples of valid input: "no", "no_NO", "no_NO_NY", "no_NO_B",
     * "no_NO_POSIX"
     * 
     * @param name String to convert
     * @return locale
     */
    public static Locale getLocaleFromFilename( String name )
        throws I18nInvalidLocaleException
    {

        if ( name.startsWith( "_" ) )
        {
            name = name.replaceFirst( "_", "" );
        }

        String[] tmp = name.split( "_" );

        if ( tmp.length == 1 )
        {
            if ( tmp[0].length() == 2 )
            {
                return new Locale( tmp[0] );
            }
        }
        else if ( tmp.length == 2 )
        {
            if ( tmp[0].length() == 2 && tmp[1].length() == 2 )
            {
                return new Locale( tmp[0], tmp[1] );
            }
        }
        else if ( tmp.length == 3 )
        {
            if ( tmp[0].length() == 2 && tmp[1].length() == 2 )
            {
                return new Locale( tmp[0], tmp[1], tmp[2] );
            }
        }

        throw new I18nInvalidLocaleException( "Unable to determine Locale for string: " + name );
    }

    /**
     * This method is used to clear/empty a specified file, if exists.
     * 
     * @param file the given file
     * @return void
     * @throws I18nResourceException
     */
    private static void clearFile( File file )
        throws I18nResourceException
    {
        try
        {
            FileOutputStream erasor = new FileOutputStream( file );
            erasor.write( (new String()).getBytes() );
            erasor.close();
        }
        catch ( FileNotFoundException fnfe )
        {
            throw new I18nResourceException( "Error while saving resource, file not found", fnfe );
        }
        catch ( IOException ioe )
        {
            throw new I18nResourceException( "I/O Error while clearing/emptying file's name" + file.getAbsolutePath(),
                ioe );
        }
    }
}

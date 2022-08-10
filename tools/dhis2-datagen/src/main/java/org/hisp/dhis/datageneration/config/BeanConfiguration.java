package org.hisp.dhis.datageneration.config;

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
import java.util.Optional;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.core.io.FileSystemResource;

/**
 * @author Luciano Fiandesio
 */
@Configuration
public class BeanConfiguration
{
    private static final String DEFAULT_ENV_VAR = "DHIS2_HOME";

    private static final String DEFAULT_SYS_PROP = "dhis2.home";

    private static final String DEFAULT_DHIS_HOME = "/opt/dhis2";

    @Bean
    public static PropertySourcesPlaceholderConfigurer propertySourcesPlaceholderConfigurer()
    {
        String externalDir;

        String path = getProperty( DEFAULT_SYS_PROP )
            .orElse( getEnvVariable( DEFAULT_ENV_VAR ).orElse( DEFAULT_DHIS_HOME ) );

        if ( new File( path ).exists() )
        {
            externalDir = path;
        } else {
            throw new IllegalArgumentException("Unable to find dhis2 configuration file");
        }

        PropertySourcesPlaceholderConfigurer properties = new PropertySourcesPlaceholderConfigurer();
        properties.setLocation( new FileSystemResource( externalDir + "/dhis.conf" ) );
        properties.setIgnoreResourceNotFound( false );

        return properties;
    }

    private static Optional<String> getProperty( String propertyName )
    {
        return Optional.ofNullable( System.getProperty( propertyName ) );
    }

    private static Optional<String> getEnvVariable( String variableName )
    {
        return Optional.ofNullable( System.getenv( variableName ) );
    }

}

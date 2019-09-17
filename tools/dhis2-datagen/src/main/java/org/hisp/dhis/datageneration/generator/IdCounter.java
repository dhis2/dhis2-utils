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

import java.util.HashMap;
import java.util.Map;

/**
 * @author Luciano Fiandesio
 */
public class IdCounter
{
    private Map<String, Long> counters;

    private IdCounter( Map<String, Long> map, long increase )
    {
        Map<String, Long> localMap = new HashMap<>();
        for ( String key : map.keySet() )
        {
            localMap.put( key, map.get( key ) + increase );
        }
        this.counters = localMap;
    }

    public IdCounter( String key1, Long counter1 )
    {
        counters = new HashMap<>();
        counters.put( key1, counter1 );
    }

    public IdCounter( String key1, Long counter1, String key2, Long counter2 )
    {
        this( key1, counter1 );
        counters.put( key2, counter2 );
    }

    public IdCounter( String key1, Long counter1, String key2, Long counter2, String key3, Long counter3 )
    {
        this( key1, counter1, key2, counter2 );
        counters.put( key3, counter3 );
    }

    public IdCounter( String key1, Long counter1, String key2, Long counter2, String key3, Long counter3, String key4,
                      Long counter4 )
    {
        this( key1, counter1, key2, counter2, key3, counter3 );
        counters.put( key4, counter4 );
    }

    public void updateAll( Long number )
    {
        for ( String key : counters.keySet() )
        {
            Long c = counters.get( key );
            counters.put( key, c + number );
        }

    }

    public Long getCounter( String counter )
    {
        return this.counters.get( counter );
    }
}

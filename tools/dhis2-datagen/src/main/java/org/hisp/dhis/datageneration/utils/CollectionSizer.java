package org.hisp.dhis.datageneration.utils;

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

import static net.andreinc.mockneat.unit.types.Ints.ints;

/**
 * @author Luciano Fiandesio
 */
public class CollectionSizer
{

    /**
     *
     * @param range
     * @param collectionSize
     * @return
     */
    public static int getCollectionSize( String range, int collectionSize )
    {
        int min = Integer.parseInt( range.split( "-" )[0] );
        int max = Integer.parseInt( range.split( "-" )[1] );
        if ( min == 0 && max == 0 )
        {
            return 0;
        }
        if ( min > collectionSize )
        {
            min = collectionSize;
        }
        if ( max > collectionSize )
        {
            max = collectionSize;
        }
        return ints().rangeClosed( min, max ).get() - 1;
    }

    public static int getCollectionSize( String range )
    {
        int min = Integer.parseInt( range.split( "-" )[0] );
        int max = Integer.parseInt( range.split( "-" )[1] );
        if ( min == 0 && max == 0 )
        {
            return 0;
        }
        return ints().rangeClosed( min, max ).get() - 1;
    }
}

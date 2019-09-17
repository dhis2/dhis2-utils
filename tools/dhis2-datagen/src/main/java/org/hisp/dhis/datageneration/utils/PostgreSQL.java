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
package org.hisp.dhis.datageneration.utils;

import static net.andreinc.mockneat.unit.text.sql.escapers.Generic.DOUBLE_APOSTROPHE;

import java.util.Arrays;
import java.util.function.Function;
import java.util.function.UnaryOperator;

import net.andreinc.mockneat.unit.text.sql.SQLEscaper;

/**
 * @author Luciano Fiandesio
 */
public class PostgreSQL
{

    private PostgreSQL()
    {
    }

    // Text escaper using the $ QUOTE strategy
    public static final Function<String, String> TEXT_$_QUOTED = DOUBLE_APOSTROPHE
        .andThen( input -> "$quot$" + input + "$quot$" );

    public static final UnaryOperator<String> TEXT_BACKSLASH = new SQLEscaper( Arrays.asList(
        new SQLEscaper.TextEscapeToken( "\u0000", "\\x00", "\\\\0" ), new SQLEscaper.TextEscapeToken( "'", "'", "''" ),
        new SQLEscaper.TextEscapeToken( "\"", "\"", "\\\\\"" ),
        new SQLEscaper.TextEscapeToken( "\b", "\\x08", "\\\\b" ),
        new SQLEscaper.TextEscapeToken( "\n", "\\n", "\\\\n" ), new SQLEscaper.TextEscapeToken( "\r", "\\r", "\\\\r" ),
        new SQLEscaper.TextEscapeToken( "\t", "\\t", "\\\\t" ),
        new SQLEscaper.TextEscapeToken( "\u001A", "\\x1A", "\\\\Z" ),
        new SQLEscaper.TextEscapeToken( "\\", "\\\\", "\\\\\\\\" ) ) )::escape;

    public static final UnaryOperator<String> TEXT_BACKSLASH_NO_ESCAPE = new SQLEscaper( Arrays.asList(
            new SQLEscaper.TextEscapeToken( "\u0000", "\\x00", "\\\\0" ), new SQLEscaper.TextEscapeToken( "'", "'", "''" ),
            new SQLEscaper.TextEscapeToken( "\b", "\\x08", "\\\\b" ),
            new SQLEscaper.TextEscapeToken( "\n", "\\n", "\\\\n" ), new SQLEscaper.TextEscapeToken( "\r", "\\r", "\\\\r" ),
            new SQLEscaper.TextEscapeToken( "\t", "\\t", "\\\\t" ),
            new SQLEscaper.TextEscapeToken( "\u001A", "\\x1A", "\\\\Z" ),
            new SQLEscaper.TextEscapeToken( "\\", "\\\\", "\\\\\\\\" ) ) )::escape;
}

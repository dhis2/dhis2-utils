package org.hisp.dhis.datageneration.shell;

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

import lombok.Getter;
import lombok.Setter;

/**
 * @author Luciano Fiandesio
 */
@Getter
@Setter
public class ProgressBar
{
    private static final String CUU = "\u001B[A";

    private static final String DL = "\u001B[1M";

    private String doneMarker = "=";

    private String remainsMarker = "-";

    private String leftDelimiter = "<";

    private String rightDelimiter = ">";

    ShellHelper shellHelper;

    private boolean started = false;

    public ProgressBar( ShellHelper shellHelper )
    {
        this.shellHelper = shellHelper;
    }

    public void display( int percentage )
    {
        display( percentage, null );
    }

    public void display( int percentage, String statusMessage )
    {
        if ( !started )
        {
            started = true;
            shellHelper.getTerminal().writer().println();
        }
        int x = (percentage / 5);
        int y = 20 - x;
        String message = ((statusMessage == null) ? "" : statusMessage);

        String done = shellHelper.getSuccessMessage( new String( new char[x] ).replace( "\0", doneMarker ) );
        String remains = new String( new char[y] ).replace( "\0", remainsMarker );

        String progressBar = String.format( "%s%s%s%s %d", leftDelimiter, done, remains, rightDelimiter, percentage );

        shellHelper.getTerminal().writer().println( CUU + "\r" + DL + progressBar + "% " + message );
        shellHelper.getTerminal().flush();
    }

    public void reset()
    {
        started = false;
    }
}

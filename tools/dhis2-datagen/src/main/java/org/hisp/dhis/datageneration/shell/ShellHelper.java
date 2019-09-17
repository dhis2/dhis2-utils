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


import org.jline.terminal.Terminal;
import org.jline.utils.AttributedStringBuilder;
import org.jline.utils.AttributedStyle;
import org.springframework.beans.factory.annotation.Value;

/**
 * @author Luciano Fiandesio
 */
public class ShellHelper {

    @Value("${shell.out.info}")
    public String infoColor;

    @Value("${shell.out.success}")
    public String successColor;

    @Value("${shell.out.warning}")
    public String warningColor;

    @Value("${shell.out.error}")
    public String errorColor;

    private Terminal terminal;

    public ShellHelper(Terminal terminal) {
        this.terminal = terminal;
    }

    /**
     * Construct colored message in the given color.
     *
     * @param message message to return
     * @param color   color to print
     * @return colored message
     */
    public String getColored(String message, PromptColor color) {
        return (new AttributedStringBuilder()).append(message, AttributedStyle.DEFAULT.foreground(color.toJlineAttributedStyle())).toAnsi();
    }

    public String getInfoMessage(String message) {
        return getColored(message, PromptColor.valueOf(infoColor));
    }

    public String getSuccessMessage(String message) {
        return getColored(message, PromptColor.valueOf(successColor));
    }

    public String getWarningMessage(String message) {
        return getColored(message, PromptColor.valueOf(warningColor));
    }

    public String getErrorMessage(String message) {
        return getColored(message, PromptColor.valueOf(errorColor));
    }

    //--- Print methods -------------------------------------------------------

    /**
     * Print message to the console in the default color.
     *
     * @param message message to print
     */
    public void print(String message) {
        print(message, null);
    }

    /**
     * Print message to the console in the success color.
     *
     * @param message message to print
     */
    public void printSuccess(String message) {
        print(message, PromptColor.valueOf(successColor));
    }

    /**
     * Print message to the console in the info color.
     *
     * @param message message to print
     */
    public void printInfo(String message) {
        print(message, PromptColor.valueOf(infoColor));
    }

    /**
     * Print message to the console in the warning color.
     *
     * @param message message to print
     */
    public void printWarning(String message) {
        print(message, PromptColor.valueOf(warningColor));
    }

    /**
     * Print message to the console in the error color.
     *
     * @param message message to print
     */
    public void printError(String message) {
        print(message, PromptColor.valueOf(errorColor));
    }

    /**
     * Generic Print to the console method.
     *
     * @param message message to print
     * @param color   (optional) prompt color
     */
    public void print(String message, PromptColor color) {
        String toPrint = message;
        if (color != null) {
            toPrint = getColored(message, color);
        }
        terminal.writer().println(toPrint);
        terminal.flush();
    }

    //--- set / get methods ---------------------------------------------------

    public Terminal getTerminal() {
        return terminal;
    }

    public void setTerminal(Terminal terminal) {
        this.terminal = terminal;
    }
}
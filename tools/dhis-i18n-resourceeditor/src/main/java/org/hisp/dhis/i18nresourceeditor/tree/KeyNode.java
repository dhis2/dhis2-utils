package org.hisp.dhis.i18nresourceeditor.tree;

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

import java.util.Locale;
import java.util.Collection;

/**
 * @author Oyvind Brucker 
 */
public class KeyNode implements ResourceNode {

    private String key;
    private ModuleNode parent;

    public KeyNode(String key, ModuleNode parent) {
        this.key = key;
        this.parent = parent;
    }

    public ModuleNode getParent() {
        return parent;
    }

    // -------------------------------------------------------------------------
    // Resource node implementation
    // -------------------------------------------------------------------------
    
    public int getType() {
        return KEY;
    }

    public void translate(Locale locale, String translation) {
        parent.translate(locale, key, translation);
    }

    public String getCaption() {
        return key;
    }

    public String getText(Locale locale) {
        return parent.getTranslation(locale, key);
    }

    public Collection<Locale> getAvailableLocales() {
        return parent.getAvailableLocales();
    }

    public ModuleNode getRoot() {
        return parent.getRoot();
    }

    // -------------------------------------------------------------------------
    // Comparable implementation
    // -------------------------------------------------------------------------
    
    public int compareTo(ResourceNode o) {
        if (o instanceof ModuleNode) {
            return -1;
        } else {
            return key.compareTo(o.toString());
        }
    }

    public boolean equals(Object object) {
        return this.toString().equals(object);
    }
    
    public int hashCode() {
        return this.toString().hashCode();
    }

    public String toString() {
        return getCaption();
    }
}
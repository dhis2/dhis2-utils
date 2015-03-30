package org.hisp.dhis.i18nresourceeditor.service;

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

import org.hisp.dhis.i18nresourceeditor.persistence.FileUtils;
import org.hisp.dhis.i18nresourceeditor.exception.I18nResourceException;
import org.hisp.dhis.i18nresourceeditor.exception.I18nInvalidLocaleException;

import java.util.Collection;
import java.util.ArrayList;
import java.util.Locale;
import java.util.Hashtable;

public class ConfigurationManager {

    private I18nLogging log;
    private Hashtable<String, String> config;
    private boolean usingDefaults = true;

    public ConfigurationManager(I18nLogging log) {
        this.log = log;

        try {
            config = FileUtils.loadResource("config.properties ");

            usingDefaults = false;
        } catch (I18nResourceException e) {
            config = getDefaults();
        }
    }

    public Collection<String> getResourceFilenames() {
        Collection<String> validFilenames = new ArrayList<String>();

        String filenames = config.get("DHIS2ResourceFiles");

        String[] tmp = filenames.split(",");

        for (int i = 0; i < tmp.length; i++) {
            validFilenames.add(tmp[i]);
        }

        return validFilenames;
    }

    public Locale getDefaultLocale() {
        String localeName = config.get("DefaultLocale");

        Locale locale = null;

        try {
            locale = FileUtils.getLocaleFromFilename(localeName);
        } catch (I18nInvalidLocaleException e) {
            try {
                localeName = getDefaults().get("DefaultLocale");
                locale = FileUtils.getLocaleFromFilename(localeName);
            } catch (I18nInvalidLocaleException ex) {
                locale = Locale.UK; // Should be unreachable
            }

            log.outWarning("Using default configuration, unable to determine default locale from string: " +
                    localeName + " now using: " + locale);
        }

        return locale;
    }

    /**
     * Method called if configuration file cant be read
     * @return Hashtable object containing 
     */
    public Hashtable<String, String> getDefaults() {
        Hashtable<String, String> defaultConfig = new Hashtable<String, String>();

        defaultConfig.put("DefaultLocale", "en_GB");
        defaultConfig.put("DHIS2ResourceFiles", "i18n_module,i18n_global");

        return defaultConfig;
    }

    public boolean isUsingDefaults() {
        return usingDefaults;
    }
}

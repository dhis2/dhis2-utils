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

import java.io.File;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Locale;

/**
 * @author Oyvind Brucker
 */
public class ModuleNode implements ResourceNode {

    private File path; // root path for module
    private File resourcePath;
    private String name;
    private String basename;
    private ModuleNode parent = null;
    private HashMap<Locale, Hashtable<String, String>> translationMap =
            new HashMap<Locale, Hashtable<String, String>>();
    private ArrayList<ResourceNode> children = new ArrayList<ResourceNode>();
    private ArrayList<ModuleNode> modules = new ArrayList<ModuleNode>();
    private Collection<Locale> modifiedLocales = new ArrayList<Locale>();

    public ModuleNode() {
    }

    // -------------------------------------------------------------------------
    // Resource node implementation
    // -------------------------------------------------------------------------
    public int getType() {
        return MODULE;
    }

    public void translate(Locale locale, String translation) {
    }

    public String getCaption() {
        return name;
    }

    public String getText(Locale locale) {
        if (parent == null && translationMap.isEmpty()) {
            return name + " parent project, contains " + modules.size() + " modules with i18n resources.";
        }

        String isModified = "no";

        if (!modifiedLocales.isEmpty()) {
            isModified = "yes";
        }

        String str = "Module: " + name + "\n";
        str += "Module path: " + path + "\n";
        str += "Module resource path: " + resourcePath + "\n";
        str += "Resource basename: " + basename + "\n";
        str += "The current resource will be saved as: " + resourcePath + File.separator + basename + "_" + locale +
                ".properties" + "\n";
        str += "Modified in this session: " + isModified + "\n";

        return str;
    }

    public Collection<Locale> getAvailableLocales() {
        // Aggregate from all submodules
        if (parent == null && !modules.isEmpty()) {
            Collection<Locale> locales = new ArrayList<Locale>();

            for (ModuleNode module : modules) {
                locales.addAll(module.getAvailableLocales());
            }

            return locales;
        } else {
            return translationMap.keySet();
        }
    }

    public ModuleNode getRoot() {
        if (parent == null) {
            return this;
        } else {
            return parent.getRoot();
        }
    }

    // -------------------------------------------------------------------------
    // Comparable implementation
    // -------------------------------------------------------------------------
    public int compareTo(ResourceNode o) {
        if (o instanceof KeyNode) {
            return 1;
        } else {
            return name.compareTo(o.toString());
        }
    }

    // -------------------------------------------------------------------------
    // TreeModel methods
    // -------------------------------------------------------------------------
    public void addChild(ResourceNode resourceNode) {
        children.add(resourceNode);
    }

    public int getChildCount() {
        return children.size();
    }

    public ResourceNode getChild(int i) {
        return children.get(i);
    }

    public int getIndexOfChild(ResourceNode child) {
        return children.indexOf(child);
    }

    // -------------------------------------------------------------------------
    // Module specific
    // -------------------------------------------------------------------------
    public void translate(Locale locale, String key, String translation) {
        Hashtable<String, String> translations = translationMap.get(locale);

        // In case this is the first translation for this locale
        if (translations == null) {
            translations = new Hashtable<String, String>();

            translationMap.put(locale, translations);
        }

        translations.put(key, translation);

        if (!modifiedLocales.contains(locale)) {
            modifiedLocales.add(locale);
        }
    }

    public String getTranslation(Locale locale, String key) {
        Hashtable<String, String> translations = translationMap.get(locale);

        String translation = "";

        if (translations != null) {
            translation = translations.get(key);
        }

        if (translation != null) {
            return translation;
        } else {
            return "";
        }
    }

    public void addDefaultTranslation(Locale locale, Hashtable<String, String> hash) {
        translationMap.put(locale, hash);

        for (String key : hash.keySet()) {
            KeyNode keyNode = new KeyNode(key, this);

            if (!children.contains(keyNode)) {
                children.add(keyNode);
            }
        }

        Collections.sort(children);
    }

    public void addTranslation(Locale locale, Hashtable<String, String> hash) {
        if (translationMap.keySet().contains(locale)) {
            translationMap.get(locale).putAll(hash);
        } else {
            translationMap.put(locale, hash);
        }
    }

    public HashMap<Locale, Hashtable<String, String>> getTranslationMap() {
        return translationMap;
    }

    public void addLocale(Locale locale) {
        if (!translationMap.containsKey(locale)) {
            Hashtable<String, String> translations = new Hashtable<String, String>();
            translationMap.put(locale, translations);
        }
    }

    public void addModule(ModuleNode module) {
        if (parent == null) {
            modules.add(module);

            children.add(module);

            Collections.sort(children);
        } else {
            parent.addModule(module);
        }
    }

    public void removeModule(ModuleNode module) {
        if (parent == null) {
            modules.remove(module);

            children.remove(module);

            Collections.sort(children);
        } else {
            parent.removeModule(module);
        }
    }

    public Collection<ModuleNode> getModules() {
        return modules;
    }

    public boolean isModified(Locale locale) {
        return modifiedLocales.contains(locale);
    }

    public File getPath() {
        return path;
    }

    public void setPath(File path) {
        this.path = path;
    }

    public File getResourcePath() {
        return resourcePath;
    }

    public void setResourcePath(File resourcePath) {
        this.resourcePath = resourcePath;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getBasename() {
        return basename;
    }

    public void setBasename(String basename) {
        this.basename = basename;
    }

    public ModuleNode getParent() {
        return parent;
    }

    public void setParent(ModuleNode parent) {
        this.parent = parent;
    }

    public String toString() {
        return getCaption();
    }
}

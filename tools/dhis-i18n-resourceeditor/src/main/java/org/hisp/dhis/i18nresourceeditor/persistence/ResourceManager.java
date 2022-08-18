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

import org.hisp.dhis.i18nresourceeditor.service.ConfigurationManager;
import org.hisp.dhis.i18nresourceeditor.service.I18nLogging;
import org.hisp.dhis.i18nresourceeditor.tree.ModuleNode;
import org.hisp.dhis.i18nresourceeditor.exception.I18nResourceException;
import org.hisp.dhis.i18nresourceeditor.exception.I18nInvalidLocaleException;

import java.io.File;
import java.util.Collection;
import java.util.Locale;
import java.util.Hashtable;
import java.util.Map;
import java.util.ArrayList;

public class ResourceManager {

    private I18nLogging log;

    public ResourceManager(I18nLogging log) {
        this.log = log;
    }
    // -------------------------------------------------------------------------
    // Dependencies
    // -------------------------------------------------------------------------
    private ConfigurationManager configurationManager = new ConfigurationManager(log);

    // -------------------------------------------------------------------------
    // Public
    // -------------------------------------------------------------------------
    /**
     * Returns one single resource
     *
     * @param path Path to resource
     * @return ModuleNode containing resources (if any exist)
     * @throws org.hisp.dhis.i18nresourceeditor.exception.I18nResourceException
     *
     */
    public ModuleNode getResource(String path)
            throws I18nResourceException {
        ModuleNode node = new ModuleNode();

        File file = new File(path);

        if (!file.exists() && !file.isFile()) {
            throw new I18nResourceException("Tried to get resource from an nonexistent path");
        }

        node.setPath(file.getParentFile());

        /**
         * Any properties file input ending in .properties is supported, this means that we may have to strip the
         * locale off the file to get the basename, which again means that we need to verify potential locales
         * to make sure that they are not part of the basename. 
         */
        String resourceFilename = file.getName();

        String localeName = "";
        String basename = "";

        if (!resourceFilename.endsWith(".properties")) {
            throw new I18nResourceException("Please select a properties file");
        }

        resourceFilename = resourceFilename.replaceFirst(".properties", "");

        String[] fn = resourceFilename.split("_");

        Collection<String> validParts = new ArrayList<String>();

        for (int i = 0; i < fn.length; i++) {
            if (validParts.size() == 1 && fn[i].length() > 2) {
                validParts.clear(); // Variant not accepted unless country is specified
            } else if (validParts.size() < 2 && fn[i].length() == 2) {
                validParts.add(fn[i]); // Add country
            } else if (validParts.size() == 2 && i != (fn.length - 1)) {
                validParts.clear(); // Can at most have one valid part after country (variant)
            } else if (validParts.size() == 2 && i == (fn.length - 1) && fn[i].length() > 0) {
                validParts.add(fn[i]); // Add variant (little restrictions on character space)
            }
        }

        if (validParts.size() == 0) {
            basename = resourceFilename; // Then the default properties file was selected
        } else {
            for (String part : validParts) {
                localeName += "_" + part;
            }

            basename += resourceFilename.substring(0, resourceFilename.indexOf(localeName));
        }

        node.setResourcePath(file.getParentFile());

        node.setBasename(basename);

        node.setName(basename + " *.properties");

        loadResource(node);

        return node;
    }

    /**
     * Searches a given path for resources and builds a hierarchy of modules,
     * Only one level for now, works best with the current GUI
     *
     * @param path path to search
     * @throws org.hisp.dhis.i18nresourceeditor.exception.I18nResourceException
     *
     */
    public ModuleNode getModules(String path)
            throws I18nResourceException {
        File file = new File(path);

        if (!file.exists() && !file.isDirectory()) {
            throw new I18nResourceException("Tried to search for modules in an nonexistent path");
        }

        if (!verifyProjectRoot(file)) {
            throw new I18nResourceException("Unable to verify project root");
        }

        // Create and configure the root node

        ModuleNode rootNode = new ModuleNode();

        rootNode.setPath(file);

        rootNode.setName(file.getName());

        // Populate with resources and remove modules without any resources

        findProjects(rootNode, file);

        ArrayList<ModuleNode> toRemove = new ArrayList<ModuleNode>();

        for (ModuleNode module : rootNode.getModules()) {
            loadModule(module);

            if (module.getChildCount() == 0) {
                toRemove.add(module);
            }
        }

        for (ModuleNode module : toRemove) {
            rootNode.removeModule(module);
        }

        return rootNode;
    }

    public void saveModule(ModuleNode module)
            throws I18nResourceException {
        for (ModuleNode submodule : module.getModules()) {
            saveModule(submodule);
        }

        Map<Locale, Hashtable<String, String>> translationMap = module.getTranslationMap();

        for (Locale locale : translationMap.keySet()) {
            if (module.isModified(locale)) {
                String completeResourcePath = module.getResourcePath().getAbsolutePath() + File.separator +
                        module.getBasename() + "_" + locale + ".properties";
                
                FileUtils.saveResource(translationMap.get(locale), completeResourcePath);

                log.outInfo("Saved resource: " + completeResourcePath);
            }
        }
    }

    // -------------------------------------------------------------------------
    // Private - General
    // -------------------------------------------------------------------------
    /**
     * @param projectPath Path to project
     * @return Project name
     */
    private String getProjectname(File projectPath) {
        String projectName = projectPath.getParentFile().getName();

        if (projectName == null) {
            projectName = "(unnamed project)";
        }

        // Should have alternatives

        return projectName;
    }

    /**
     * Loads a single resource, assuming that the resource path is known
     *
     * @param node The node that will get populated with resources
     */
    private void loadResource(ModuleNode node) {
        File resourcePath = node.getResourcePath();

        String basename = node.getBasename();

        for (File file : resourcePath.listFiles()) {
            String filename = file.getName();

            if (file.isFile() && filename.startsWith(basename) && filename.endsWith(".properties")) {
                filename = filename.replaceFirst(basename, "");
                filename = filename.replaceFirst(".properties", "");

                /**
                 * The string will be empty if its the default properties file
                 */
                if (filename.equals("")) {
                    Locale locale = configurationManager.getDefaultLocale();

                    try {
                        Hashtable<String, String> resource = FileUtils.loadResource(file.getAbsolutePath());

                        node.addDefaultTranslation(locale, resource);

                        log.outInfo(
                                "Loaded properties for default locale (" + locale + ") from: " + file.getAbsolutePath());
                    } catch (I18nResourceException e) {
                        log.outWarning("Failed to load resources from default properties file at: " +
                                file.getAbsolutePath() + " (ignored)");
                    }
                } else {
                    Locale locale;

                    try {
                        locale = FileUtils.getLocaleFromFilename(filename);
                    } catch (I18nInvalidLocaleException e) {
                        log.outWarning("Invalid locale for resource: " + file.getAbsolutePath() + " (file ignored)");

                        continue;
                    }

                    try {
                        Hashtable<String, String> resource = FileUtils.loadResource(file.getAbsolutePath());

                        node.addTranslation(locale, resource);

                        log.outInfo("Loaded properties for locale " + locale.getDisplayName() + " from: " +
                                file.getAbsolutePath());

                    } catch (I18nResourceException e) {
                        log.outWarning(
                                "Failed to load resources from properties file at: " + file.getAbsolutePath() + ", message: " + e.getMessage());
                    }

                }
            }
        }
    }

    // -------------------------------------------------------------------------
    // Private - Multi project
    // -------------------------------------------------------------------------
    /**
     * Loads all resources for a specific Module
     *
     * @param node The node that will get populated with resources
     */
    private void loadModule(ModuleNode node) {
        getModuleResourcePath(node, node.getPath());

        if (node.getResourcePath() != null) {
            loadResource(node);
        }
    }

    private void getModuleResourcePath(ModuleNode node, File path) {
        Collection<String> resourceFilenames = configurationManager.getResourceFilenames();

        File[] files = path.listFiles();

        for (int i = 0; i < files.length; i++) {
            if (files[i].isDirectory() && !files[i].getName().startsWith(".") &&
                    !files[i].getName().equals("target") && !files[i].getName().startsWith("dhis-")) {
                getModuleResourcePath(node, files[i]);
            } else if (node.getBasename() == null) {
                for (String filename : resourceFilenames) {
                    if (files[i].getName().startsWith(filename) && files[i].getName().endsWith(".properties") &&
                            files[i].isFile()) {
                        node.setBasename(filename);

                        node.setResourcePath(files[i].getParentFile().getAbsoluteFile());

                        return;
                    }
                }
            }
        }
    }

    private boolean verifyProjectRoot(File file) {
        File[] files = file.listFiles();

        for (int i = 0; i < files.length; i++) {
            if (files[i].getName().equals("dhis-support")) {
                return true;
            }
        }
        return false;
    }

    private void findProjects(ModuleNode node, File path) {
        File[] files = path.listFiles();

        for (int i = 0; i < files.length; i++) {
            if (files[i].isDirectory() && !files[i].getName().startsWith(".") &&
                    !files[i].getName().equals("target")) {
                findProjects(node, files[i]);
            } else if (files[i].getName().equals("pom.xml")) {
                ModuleNode newNode = new ModuleNode();
                newNode.setPath(files[i].getParentFile());
                newNode.setName(getProjectname(files[i]));
                node.addModule(newNode);
                log.outInfo(("Found module at: " + newNode.getPath()));
            }
        }
    }
}
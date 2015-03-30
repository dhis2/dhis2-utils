package org.hisp.dhis.i18nresourceeditor.gui;

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

import org.hisp.dhis.i18nresourceeditor.tree.ModuleNode;
import org.hisp.dhis.i18nresourceeditor.tree.KeyNode;
import org.hisp.dhis.i18nresourceeditor.tree.ResourceNode;

import javax.swing.event.TreeModelListener;
import javax.swing.tree.TreeModel;
import javax.swing.tree.TreePath;

/**
 * @author Oyvind Brucker
 */
public class ResourceTreeSelectionModel implements TreeModel {

    private ModuleNode rootModule;

    public ResourceTreeSelectionModel(ModuleNode rootModule) {
        this.rootModule = rootModule;
    }

    public void setRoot(ModuleNode rootModule) {
        this.rootModule = rootModule;
    }

    /**
     * Treemodel implementation
     */
    public Object getRoot() {
        return rootModule;
    }

    public Object getChild(Object object, int i) {
        if (object instanceof KeyNode) {
            return null;
        }

        ModuleNode module = (ModuleNode) object;

        return module.getChild(i);
    }

    public int getChildCount(Object object) {
        if (object instanceof KeyNode) {
            return 0;
        }

        ModuleNode module = (ModuleNode) object;

        return module.getChildCount();
    }

    public boolean isLeaf(Object object) {
        if (object instanceof KeyNode) {
            return true;
        }

        ModuleNode module = (ModuleNode) object;

        if (module.getChildCount() == 0) {
            return true;
        }

        return false;
    }

    public int getIndexOfChild(Object parent, Object child) {
        if (parent instanceof KeyNode | child instanceof ResourceNode) {
            return -1;
        }

        ModuleNode module = (ModuleNode) parent;

        ResourceNode resource = (ResourceNode) child;

        return module.getIndexOfChild(resource);
    }

    public void valueForPathChanged(TreePath treePath, Object object) {
        // Not used, static tree from creation
    }

    public void addTreeModelListener(TreeModelListener treeModelListener) {
        // Not used
    }

    public void removeTreeModelListener(TreeModelListener treeModelListener) {
        // Not used
    }
}
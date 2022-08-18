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

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.GridLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;

import javax.swing.DefaultComboBoxModel;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JDialog;
import javax.swing.JEditorPane;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.JToolBar;
import javax.swing.JTree;
import javax.swing.SwingConstants;
import javax.swing.ToolTipManager;
import javax.swing.UIManager;
import javax.swing.WindowConstants;
import javax.swing.border.TitledBorder;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;
import javax.swing.tree.DefaultTreeCellRenderer;
import javax.swing.tree.TreePath;

import org.hisp.dhis.i18nresourceeditor.exception.I18nResourceException;
import org.hisp.dhis.i18nresourceeditor.persistence.ResourceManager;
import org.hisp.dhis.i18nresourceeditor.tree.ModuleNode;
import org.hisp.dhis.i18nresourceeditor.tree.ResourceNode;

/**
 * @author Oyvind Brucker
 * @author Saptarshi Purkayastha
 */
public class I18nResourceEditorGUI extends JFrame {

    static final String dhisName = "DHIS 2";
    static final String programName = dhisName + " i18n Resource Editor";
    static final String programVersion = "0.3";
    static final Font headerFont = new Font(null, Font.BOLD, 15); // Used as standard header
    static final Font headerFont2 = new Font(null, Font.BOLD, 14); // Used as standard sub-header
    static final String strAdvancedWarning = "(advanced)";
    static final int PROJECT_MODE = 1;
    static final int SINGLE_MODE = 2;
    // -------------------------------------------------------------------------
    // Dependencies
    // -------------------------------------------------------------------------
    private I18nLoggingSwing log = new I18nLoggingSwing();
    private ResourceManager resourceManager = new ResourceManager(log);
    // Root module used by the tree
    private ModuleNode rootModule = new ModuleNode();
    // -------------------------------------------------------------------------
    // GUI Components
    // -------------------------------------------------------------------------
    // General components
    private JTextArea txtDebug = log.getTextArea();
    private JToolBar toolbar = new JToolBar(); // Top toolbar
    private JTabbedPane tabpane = new JTabbedPane();
    private JButton cmdSave = new JButton("Save");
    private JButton cmdSetLocale = new JButton("Select locale");
    private JButton cmdLocaleInfo = new JButton("Locale information");
    private JLabel lblHeaderTop = new JLabel();
    private JPanel panelMain = new JPanel(); // The main JPanel component in the center
    private JSplitPane splitMain = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
    private JLabel lblStatus = new JLabel("Status:");
    // Main tab
    private JTree resourceTree = new JTree();
    private ResourceTreeSelectionModel treeModel = new ResourceTreeSelectionModel(rootModule);
    private JPanel panelMainCenter = new JPanel(); // The center of panelMain
    private JPanel panelMainTop = new JPanel();
    private JPanel panelMainBottom = new JPanel();
    TitledBorder panelMainTopBorder = new TitledBorder(new TitledBorder(""), "Translations", 0, 0, headerFont);
    private JTextArea txtLocale = new JTextArea();

    private JLabel lblMainTop = new JLabel(); // Top label on the main component
    // Main tab - reference
    TitledBorder panelMainBottomBorder = new TitledBorder(new TitledBorder(""), "Reference", 0, 0, headerFont);
    private JLabel lblReferenceTop = new JLabel("Select reference locale:");
    private JPanel panelMainReferencesTop = new JPanel();
    private JTextArea txtRefLocale = new JTextArea();
    private String[] dummyData = {"<select locale to work on first>"};
    private JComboBox cmbRefLocaleSelect = new JComboBox(dummyData);
    private HashMap<String, Locale> mapLocales =
            new HashMap<String, Locale>(); // Maps a String representation of the locales to the actual locales
    private HashMap<String, Locale> mapReflocales = new HashMap<String, Locale>();
    // Settings tab
    private JPanel panelSettings = new JPanel();
    private JLabel lblSettingsDHIS2dirHeader =
            new JLabel("Change the basedirectory for where to search for resources");
    private JPanel panelSettingsDHIS2dir = new JPanel();
    private JTextField txtSettingsDHIS2dir = new JTextField();
    private JButton cmdSettingsDHIS2dir = new JButton("Apply");
    private JButton cmdSettingsBrowse = new JButton("Browse");
    private JFileChooser fcDHIS2dir = new JFileChooser();
    private JFileChooser fcDHIS2resource = new JFileChooser();
    // Help tab
    private JEditorPane txtHelp = new JEditorPane();
    private JFrame parent = this;
    private JPanel panelHelp = new JPanel();
    private JButton cmdHelp = new JButton("Basic help");
    private JButton cmdHelpAdvanced = new JButton("More help ");
    private JButton cmdHelpGenerateISO = new JButton("Generate ISO-639 and ISO-3199 tables");
    private HelpSelection helpSelection = new HelpSelection();
    // Debug tab
    private JPanel panelDebug = new JPanel();
    private JPanel panelDebugTop = new JPanel();
    private JLabel lblDebugTop = new JLabel("Debug information (DEV)");
    private JButton cmdDebugClose = new JButton("Close this tab");
    private ActionListener debugListener = new DebugListener();
    // Start Dialog - Selecting DHIS2 directory or simple mode
    private JDialog dialogStart = new JDialog(parent, programName + " startup..");
    private JLabel lblDialogStartHeader = new JLabel("Select how to translate " + dhisName + " resources");
    private JPanel panelDialogStartTabs = new JPanel();
    private JPanel panelDialogStartDHIS2 = new JPanel();
    private JPanel panelDialogStartSimple = new JPanel();
    private JTabbedPane tabDialogStart = new JTabbedPane();
    private JTextArea txtDialogStartBody = new JTextArea("Please select the " + dhisName +
            " source code root directory, ie. the \"dhis-2\" directory inside the repository checkout. " +
            "The directory tree will be searched for i18n resources.\n\n" +
            "You can later reset the directory under Settings.\n\n" +
            "See Help for more information about this program.\n");
    private JTextArea txtDialogStartBodyS = new JTextArea("Please select a " + dhisName +
            " compatible resource bundle, " + "you can then simply edit this resource for all locales.\n\n");
    private JPanel panelDialogStartBottom = new JPanel();
    private JPanel panelDialogStartBottomS = new JPanel();
    private JLabel lblDialogStartDHIS2dir = new JLabel();
    private JButton cmdDialogStartBrowse = new JButton("Browse");
    private JButton cmdDialogStartOk = new JButton("OK");
    private JButton cmdDialogStartBrowseS = new JButton("Browse");
    private JButton cmdDialogStartOkS = new JButton("OK");
    private JLabel lblDialogStartDHIS2resource = new JLabel();
    // The select locale dialog
    private JDialog dialog = new JDialog(parent);
    private JList lstDialog = new JList();
    private JTabbedPane tabpaneDialog = new JTabbedPane();
    private JPanel panelDialogSimple = new JPanel(); // For simple selection from a list
    private JPanel panelDialogAdvanced = new JPanel(); // For compliation of a locale manually
    private JPanel panelDialogBottom = new JPanel();
    private JButton cmdDialogCancel = new JButton("Cancel"); // One for each tab to look like the same button
    private JButton cmdDialogCancel2 = new JButton("Cancel");
    private JLabel lblDialogHeader = new JLabel("Please select a locale");
    private JButton cmdDialogSimpleSelect = new JButton("Select");
    private JPanel panelDialogAdvancedInput = new JPanel(); // Panel holding the input help in advanced tab
    private JLabel lblDialogAdvancedHeader = new JLabel("For list of supported and translated ISO codes see help");
    private JTextField txtDialogAdvancedLanguage = new JTextField();
    private JTextField txtDialogAdvancedCountry = new JTextField();
    private JTextField txtDialogAdvancedVariant = new JTextField();
    private JLabel lblDialogAdvancedLanguage = new JLabel("Language (ISO-639) lower case: ");
    private JLabel lblDialogAdvancedCountry = new JLabel("Country (ISO-3166) upper case: ");
    private JLabel lblDialogAdvancedVariant = new JLabel("Variant: ");
    private JPanel panelDialogAdvancedLookup = new JPanel();
    private JButton cmdDialogAdvancedSelect = new JButton("Select");
    private JLabel lblDialogAdvancedLookupLanguage = new JLabel("Language: ");
    private JLabel lblDialogAdvancedLookupCountry = new JLabel("Country: ");
    private JLabel lblDialogAdvancedLookupVariant = new JLabel("Variant: ");
    private JLabel lblDialogAdvancedLookupLanguageR = new JLabel(""); // Response from java api lookup of language
    private JLabel lblDialogAdvancedLookupCountryR = new JLabel("");
    private JLabel lblDialogAdvancedLookupVariantR = new JLabel("");
    private JLabel lblDialogAdvancedLookupValid = new JLabel("Valid " + dhisName + " Resource Bundle:");
    private JLabel lblDialogAdvancedLookupValidR = new JLabel("");
    private String strNotFound = "(not found)"; // To display when a lookup is not found in the java api
    // Locale info dialog
    private JDialog dialogLocaleInfo = new JDialog(parent);
    private JLabel lblDialogLocaleInfoHeader = new JLabel("Locale info");
    private JLabel lblDialogLocaleInfoLanguage = new JLabel("");
    private JLabel lblDialogLocaleInfoLanguageISO = new JLabel("");
    private JLabel lblDialogLocaleInfoCountry = new JLabel("");
    private JLabel lblDialogLocaleInfoCountryISO = new JLabel("");
    private JLabel lblDialogLocaleInfoCountryISO3 = new JLabel("");
    private JLabel lblDialogLocaleInfoVariantS = new JLabel("");
    private JLabel lblDialogLocaleInfoVariantL = new JLabel("");
    private JButton cmdDialogLocaleInfoInfoOk = new JButton("Close");
    private JPanel panelMainInfo = new JPanel();
    private JPanel panelBottomInfo = new JPanel();
    // -------------------------------------------------------------------------
    // Misc components
    // -------------------------------------------------------------------------
    private Locale currentLocale = Locale.UK; //configurationManager.getDefaultLocale();
    private Locale currentRefLocale = Locale.UK; //configurationManager.getDefaultLocale();
    private int translatorMode = SINGLE_MODE;
    private boolean debugMode = true;
    // These arrays will during startup be converted to HTML
    final static String[][] FAQ = {{"How do I use the translator?", "(quick guide)"},
        {"What is the reference locale for?", "To see the translations available for existing resources"}, {
            "Why isnt the reference language editable?",
            "To prevent user errors and to enhance clearity of the task at hand"},};
    final static String[][] FAQadvanced = {{
            "Can I use language and variant without a country when creating a custom locale?",
            "No, to use variant country is needed"},};
    String strHelpHTML = "";
    String strHelpHTMLAdvanced = "";
    String strISOTablesHTML = "";

    public I18nResourceEditorGUI() {

        // -------------------------------------------------------------------------
        // Set properties
        // -------------------------------------------------------------------------
        txtLocale.setFont(new Font("Arial Unicode MS", Font.PLAIN, 16));
        setTitle(programName + " " + programVersion);
        cmdSetLocale.addActionListener(new SelectLocaleListener());
        cmbRefLocaleSelect.addActionListener(new SelectReflocaleListener());
        cmdSave.addActionListener(new SaveResourcesListener());
        toolbar.setFloatable(false);
        toolbar.setBorderPainted(true);
        toolbar.setRollover(true);
        lblHeaderTop.setFont(headerFont2);
        panelMainTop.setBorder(panelMainTopBorder);
        panelMainBottom.setLayout(new BorderLayout());
        panelMainBottom.setBorder(panelMainBottomBorder);
        panelMainTop.setLayout(new BorderLayout());
        cmdSetLocale.setToolTipText("Select the locale that you want to work on");
        panelMain.setLayout(new BorderLayout());
        resourceTree.setCellRenderer(new KeyTreeCellRenderer());
        resourceTree.setToggleClickCount(1);
        resourceTree.setModel(treeModel);
        panelMainCenter.setLayout(new GridLayout(2, 1));
        txtLocale.setBorder(new TitledBorder("Select a key and enter text here"));
        txtLocale.getDocument().addDocumentListener(new TranslationListener());
        txtRefLocale.setBorder(new TitledBorder("The reference is displayed here:"));
        txtRefLocale.setEditable(false);
        panelMainReferencesTop.setPreferredSize(new Dimension(400, 50));
        cmbRefLocaleSelect.setPreferredSize(new Dimension(200, 20));
        cmbRefLocaleSelect.setEnabled(false);
        FlowLayout refFlowLayout = new FlowLayout();
        refFlowLayout.setAlignment(FlowLayout.LEFT);
        panelMainReferencesTop.setLayout(refFlowLayout);
        lblReferenceTop.setAlignmentX(SwingConstants.LEFT);
        lblMainTop.setPreferredSize(new Dimension(50, 50));
        lblMainTop.setText("No data is saved until you hit the save button on the toolbar (top menu)");
        lblMainTop.setAlignmentX(Component.CENTER_ALIGNMENT);
        cmdSave.setIcon(getIcon("save.gif"));
        cmdSetLocale.setIcon(getIcon("locale.gif"));

        // Info
        cmdLocaleInfo.setIcon(getIcon("info.gif"));
        cmdLocaleInfo.addActionListener(new LocaleInfoDisplay());
        dialogLocaleInfo.setLayout(new BorderLayout());
        dialogLocaleInfo.setBounds(200, 200, 400, 400);
        dialogLocaleInfo.setResizable(false);
        dialogLocaleInfo.setTitle("Locale information");
        panelMainInfo.setLayout(new GridLayout(7, 2));
        panelMainInfo.setBorder(new TitledBorder("General information"));
        lblDialogLocaleInfoHeader.setIcon(getIcon("info.gif"));
        lblDialogLocaleInfoHeader.setFont(headerFont);
        lblDialogLocaleInfoHeader.setPreferredSize(new Dimension(50, 50));

        // Settings
        panelSettingsDHIS2dir.setBorder(new TitledBorder("Change the " + dhisName + " directory"));
        panelSettingsDHIS2dir.setPreferredSize(new Dimension(500, 100));
        txtSettingsDHIS2dir.setPreferredSize(new Dimension(300, 20));
        fcDHIS2dir.setFileFilter(new DirFileFilter());
        fcDHIS2dir.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
        cmdSettingsDHIS2dir.addActionListener(new UpdateDHIS2dirListener());
        ToolTipManager.sharedInstance().registerComponent(resourceTree);

        // Start dialog
        dialogStart.setBounds(200, 200, 400, 400);
        dialogStart.setLayout(new BorderLayout());
        panelDialogStartDHIS2.setLayout(new BorderLayout());
        panelDialogStartSimple.setLayout(new BorderLayout());
        panelDialogStartTabs.setLayout(new BorderLayout());
        lblDialogStartHeader.setIcon(getIcon("help.gif"));
        lblDialogStartHeader.setFont(headerFont);
        lblDialogStartHeader.setPreferredSize(new Dimension(50, 50));
        txtDialogStartBody.setEditable(false);
        txtDialogStartBody.setLineWrap(true);
        txtDialogStartBody.setWrapStyleWord(true);
        txtDialogStartBodyS.setEditable(false);
        txtDialogStartBodyS.setLineWrap(true);
        txtDialogStartBodyS.setWrapStyleWord(true);
        panelDialogStartBottom.setPreferredSize(new Dimension(300, 150));
        panelDialogStartBottom.setLayout(new BorderLayout());
        panelDialogStartBottomS.setPreferredSize(new Dimension(300, 150));
        panelDialogStartBottomS.setLayout(new BorderLayout());
        lblDialogStartDHIS2dir.setPreferredSize(new Dimension(280, 60));
        lblDialogStartDHIS2dir.setBorder(new TitledBorder(dhisName + " repository directory"));
        cmdDialogStartBrowse.setEnabled(true); //

        lblDialogStartDHIS2resource.setPreferredSize(new Dimension(280, 60));
        lblDialogStartDHIS2resource.setBorder(new TitledBorder(dhisName + " resource file"));
        dialogStart.setResizable(false);
        cmdDialogStartOk.setEnabled(false); // Must enter something to continue
        cmdDialogStartOkS.setEnabled(false);
        cmdDialogStartOk.addActionListener(new UpdateDHIS2dirListener());
        cmdDialogStartOkS.addActionListener(new UpdateDHIS2dirListener());
        dialogStart.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);

        // Help
        txtHelp.setContentType("text/html");
        txtHelp.setEditable(false);
        panelHelp.setLayout(new BorderLayout());
        cmdHelp.addActionListener(helpSelection);
        cmdHelpAdvanced.addActionListener(helpSelection);
        cmdHelpGenerateISO.addActionListener(helpSelection);

        // Debug tab
        cmdDebugClose.addActionListener(debugListener);
        lblDebugTop.setFont(headerFont2);
        panelDebug.setLayout(new BorderLayout());
        panelDebugTop.add(lblDebugTop);
        panelDebugTop.add(cmdDebugClose);
        panelDebug.add(panelDebugTop, BorderLayout.NORTH);
        panelDebug.add(new JScrollPane(txtDebug), BorderLayout.CENTER);
        txtDebug.setEditable(false);
        txtDebug.setLineWrap(true);
        txtDebug.setWrapStyleWord(true);

        // The set locale dialog
        dialog.setLayout(new BorderLayout());
        dialog.setBounds(200, 200, 400, 400);
        dialog.setResizable(false);
        dialog.setTitle("Locale selection");
        lblDialogHeader.setIcon(getIcon("locale.gif"));
        lblDialogHeader.setFont(headerFont);
        lblDialogHeader.setPreferredSize(new Dimension(50, 50));
        panelDialogSimple.setLayout(new BorderLayout());
        lstDialog.setSize(300, 300);
        lstDialog.addMouseListener(new LocaleListMouseAdapter());
        panelDialogAdvanced.setLayout(new BorderLayout());
        panelDialogAdvancedInput.setLayout(new GridLayout(3, 2));
        panelDialogAdvancedInput.setBorder(new TitledBorder("Type codes manually here:"));
        panelDialogAdvancedLookup.setLayout(new GridLayout(4, 2));
        panelDialogAdvancedLookup.setBorder(new TitledBorder("Automatically updated lookups from the Java API:"));
        lblDialogAdvancedHeader.setFont(headerFont2);
        lblDialogAdvancedHeader.setPreferredSize(new Dimension(40, 40));
        lblDialogAdvancedHeader.setHorizontalAlignment(SwingConstants.CENTER);
        cmdDialogAdvancedSelect.setEnabled(false);

        // Global
        setSize(new Dimension(1024, 768));
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        getContentPane().setLayout(new BorderLayout());

        // -------------------------------------------------------------------------
        // Add components
        // -------------------------------------------------------------------------

        JPanel helpHeader = new JPanel();
        helpHeader.setLayout(new BorderLayout());
        JPanel helpButtons = new JPanel();
        helpButtons.add(cmdHelp);
        helpButtons.add(cmdHelpAdvanced);
        helpButtons.add(cmdHelpGenerateISO);
        helpHeader.add(helpButtons, BorderLayout.CENTER);
        panelHelp.add(helpHeader, BorderLayout.NORTH);
        panelHelp.add(new JScrollPane(txtHelp));
        toolbar.add(cmdSave);
        toolbar.add(cmdSetLocale);
        toolbar.add(cmdLocaleInfo);
        toolbar.add(lblHeaderTop);
        getContentPane().add(toolbar, BorderLayout.NORTH);
        getContentPane().add(tabpane, BorderLayout.CENTER);
        getContentPane().add(lblStatus, BorderLayout.SOUTH);

        // Main
        panelMainTop.add(lblMainTop, BorderLayout.NORTH);
        panelMainTop.add(new JScrollPane(txtLocale), BorderLayout.CENTER);
        panelMainCenter.add(panelMainTop);
        panelMainCenter.add(panelMainBottom);
        resourceTree.addMouseListener(new TreeMouseAdapter());

        // Main - reference
        panelMainReferencesTop.add(lblReferenceTop);
        panelMainReferencesTop.add(cmbRefLocaleSelect);
        panelMainBottom.add(panelMainReferencesTop, BorderLayout.NORTH);
        panelMainBottom.add(txtRefLocale, BorderLayout.CENTER);
        panelMainBottom.add(new JScrollPane(txtRefLocale));
        splitMain.setLeftComponent(new JScrollPane(resourceTree));
        splitMain.setRightComponent(panelMainCenter);
        panelMain.add(splitMain);

        // Settings
        panelSettingsDHIS2dir.add(lblSettingsDHIS2dirHeader);
        panelSettingsDHIS2dir.add(txtSettingsDHIS2dir);
        panelSettingsDHIS2dir.add(cmdSettingsBrowse);
        panelSettingsDHIS2dir.add(cmdSettingsDHIS2dir);
        panelSettings.add(panelSettingsDHIS2dir);

        // Start dialog
        dialogStart.add(lblDialogStartHeader, BorderLayout.NORTH);
        panelDialogStartBottom.add(lblDialogStartDHIS2dir, BorderLayout.CENTER);
        panelDialogStartBottomS.add(lblDialogStartDHIS2resource, BorderLayout.CENTER);
        JPanel panelDialogStartDummy = new JPanel();
        panelDialogStartDummy.add(cmdDialogStartBrowse);
        panelDialogStartDummy.add(cmdDialogStartOk);
        panelDialogStartBottom.add(panelDialogStartDummy, BorderLayout.SOUTH);
        JPanel panelDialogStartDummy2 = new JPanel();
        panelDialogStartDummy2.add(cmdDialogStartBrowseS);
        panelDialogStartDummy2.add(cmdDialogStartOkS);
        panelDialogStartBottomS.add(panelDialogStartDummy2, BorderLayout.SOUTH);
        cmdDialogStartBrowseS.addActionListener(new SelectResourceListener());
        cmdDialogStartBrowse.addActionListener(new SelectProjectDirListener());
        panelDialogStartDHIS2.add(new JScrollPane(txtDialogStartBody), BorderLayout.CENTER);
        panelDialogStartSimple.add(new JScrollPane(txtDialogStartBodyS), BorderLayout.CENTER);
        panelDialogStartDHIS2.add(panelDialogStartBottom, BorderLayout.SOUTH);
        panelDialogStartSimple.add(panelDialogStartBottomS, BorderLayout.SOUTH);
        tabDialogStart.add(panelDialogStartDHIS2, "DHIS2 repository ");
        tabDialogStart.add(panelDialogStartSimple, "Single resource");
        panelDialogStartDHIS2.setEnabled(false);
        dialogStart.add(tabDialogStart);

        // Select locale dialog
        panelDialogSimple.add(new JScrollPane(lstDialog), BorderLayout.CENTER);
        cmdDialogSimpleSelect.addActionListener(new SelectLocaleSimpleListener());
        cmdDialogAdvancedSelect.addActionListener(new SelectLocaleAdvancedListener());
        cmdDialogCancel.addActionListener(new CancelSelectLocaleDialog());
        cmdDialogCancel2.addActionListener(new CancelSelectLocaleDialog());
        JPanel panelCollectSimpleButton = new JPanel();
        panelCollectSimpleButton.add(cmdDialogSimpleSelect);
        panelCollectSimpleButton.add(cmdDialogCancel);
        panelDialogSimple.add(panelCollectSimpleButton, BorderLayout.SOUTH);
        tabpaneDialog.add(panelDialogSimple, "Simple");
        tabpaneDialog.add(panelDialogAdvanced, "Manual " + strAdvancedWarning);
        dialog.add(lblDialogHeader, BorderLayout.NORTH);
        dialog.add(tabpaneDialog, BorderLayout.CENTER);
        dialog.add(panelDialogBottom, BorderLayout.SOUTH);
        panelDialogAdvanced.add(lblDialogAdvancedHeader, BorderLayout.NORTH); // The advanced tab starts here..
        panelDialogAdvancedInput.add(lblDialogAdvancedLanguage);
        panelDialogAdvancedInput.add(txtDialogAdvancedLanguage);
        panelDialogAdvancedInput.add(lblDialogAdvancedCountry);
        panelDialogAdvancedInput.add(txtDialogAdvancedCountry);
        panelDialogAdvancedInput.add(lblDialogAdvancedVariant);
        panelDialogAdvancedInput.add(txtDialogAdvancedVariant);
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupLanguage); // lookup frame
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupLanguageR);
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupCountry);
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupCountryR);
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupVariant);
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupVariantR);
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupValid);
        panelDialogAdvancedLookup.add(lblDialogAdvancedLookupValidR);
        JPanel panelCollect = new JPanel(); // A panel that collects the two panels in the middle of the layout
        panelCollect.setLayout(new GridLayout(2, 1));
        panelCollect.add(panelDialogAdvancedInput);
        panelCollect.add(panelDialogAdvancedLookup);
        panelDialogAdvanced.add(panelCollect, BorderLayout.CENTER);
        JPanel panelCollectButton = new JPanel();
        panelCollectButton.add(cmdDialogAdvancedSelect);
        panelCollectButton.add(cmdDialogCancel2);
        panelDialogAdvanced.add(panelCollectButton, BorderLayout.SOUTH);
        JavaApiLookupListener javaApiLookupListener = new JavaApiLookupListener();
        txtDialogAdvancedLanguage.getDocument().addDocumentListener(javaApiLookupListener);
        txtDialogAdvancedCountry.getDocument().addDocumentListener(javaApiLookupListener);
        txtDialogAdvancedVariant.getDocument().addDocumentListener(javaApiLookupListener);

        // Info dialog
        dialogLocaleInfo.add(lblDialogLocaleInfoHeader, BorderLayout.NORTH);
        panelMainInfo.add(new JLabel("Language: "));
        panelMainInfo.add(lblDialogLocaleInfoLanguage);
        panelMainInfo.add(new JLabel("Language (ISO-639): "));
        panelMainInfo.add(lblDialogLocaleInfoLanguageISO);
        panelMainInfo.add(new JLabel("Country: "));
        panelMainInfo.add(lblDialogLocaleInfoCountry);
        panelMainInfo.add(new JLabel("Country (ISO-3166) 2 letter:"));
        panelMainInfo.add(lblDialogLocaleInfoCountryISO);
        panelMainInfo.add(new JLabel("Country (ISO-3166) 3 letter:"));
        panelMainInfo.add(lblDialogLocaleInfoCountryISO3);
        panelMainInfo.add(new JLabel("Variant (short): "));
        panelMainInfo.add(lblDialogLocaleInfoVariantS);
        panelMainInfo.add(new JLabel("Variant (long): "));
        panelMainInfo.add(lblDialogLocaleInfoVariantL);
        panelBottomInfo.add(cmdDialogLocaleInfoInfoOk);
        dialogLocaleInfo.add(panelMainInfo, BorderLayout.CENTER);
        dialogLocaleInfo.add(panelBottomInfo, BorderLayout.SOUTH);
        cmdDialogLocaleInfoInfoOk.addActionListener(new LocaleInfoDisplayClose());

        // Add to the main tabpane
        tabpane.add(panelMain, "Translations");
        tabpane.add(panelHelp, "Help");
        tabpane.add(panelSettings, "Settings " + strAdvancedWarning);

        if (debugMode) {
            tabpane.add(panelDebug, "Debug " + strAdvancedWarning);
        }

        // -------------------------------------------------------------------------
        // Other pre processing
        // -------------------------------------------------------------------------

        // Create the HTML page based on the Strings from FAQ
        strHelpHTML = "<html><head></head><body>" + "<ul>";
        for (int i = 0; i < FAQ.length; i++) {
            strHelpHTML += "<li><b>" + FAQ[i][0] + "</b><br>" + "<div>" + FAQ[i][1] + "</div></li>";
        }
        strHelpHTML += "</ul>" + "</body></html>";

        // The advanced help..
        strHelpHTMLAdvanced = "<html><head></head><body>" + "<ul>";
        for (int i = 0; i < FAQadvanced.length; i++) {
            strHelpHTMLAdvanced +=
                    "<li><b>" + FAQadvanced[i][0] + "</b><br>" + "<div>" + FAQadvanced[i][1] + "</div></li>";

        }
        strHelpHTMLAdvanced += "</ul>" + "</body></html>";

        // Display basic help as default
        txtHelp.setText(strHelpHTML);

        refreshLocaleCaptions();

        checkIfValidResourceBundle();

        // Start by displaying the selection GUI dialog
        dialogStart.setVisible(true);
    }

    /**
     * Some utility methods
     */
    public void refreshLocaleCaptions() {
        /**
         * Sets all captions after a change of locale and at startup
         * Also enables the infobutton if no locale is selected
         */
        String headerPrefix = "    Currently working on: ";
        String headerSuffix = "    ";
        if (currentLocale != null) {
            lblHeaderTop.setText(headerPrefix + getLocaleInfoline(currentLocale) + headerSuffix);
            cmdLocaleInfo.setEnabled(true);
        } else {
            lblHeaderTop.setText(headerPrefix + "(none selected)" + headerSuffix);
            cmdLocaleInfo.setEnabled(false);
        }
    }

    public static Icon getIcon(String iconName) {
        return new ImageIcon(I18nResourceEditorGUI.class.getResource("/icons/" + iconName));
    }

    public void setStatus(String message) {
        lblStatus.setText("Status: " + message);
    }

    public String getLocaleInfoline(Locale locale) {
        String localeInfo = "";

        if (locale == null) {
            return "";
        }
        if (locale.getDisplayLanguage() != null && !locale.getDisplayLanguage().equals("")) {
            localeInfo += locale.getDisplayLanguage() + " - ";
        }
        if (locale.getDisplayCountry() != null && !locale.getDisplayCountry().equals("")) {
            localeInfo += locale.getDisplayCountry() + " ";
        }
        if (locale.getDisplayVariant() != null && !locale.getDisplayVariant().equals("")) {
            localeInfo += "(" + locale.getDisplayVariant() + ") ";
        }

        localeInfo += "[" + locale.toString() + "] ";

        return localeInfo;
    }

    public ResourceNode getSelectedResource() {
        ResourceNode resource = null;

        try {
            resource = (ResourceNode) resourceTree.getSelectionPath().getLastPathComponent();
        } catch (NullPointerException e) {
            // Will be thrown if nothing is selected in the tree yet
        }

        return resource;
    }

    public void generateISOTablesHTML() {
        // Not pretty
        strISOTablesHTML = "";
        strISOTablesHTML += "<h1>ISO tables</h1>";
        strISOTablesHTML += "<p>These tables are generated based on information from the Java API installed" +
                ". They will hence show what is currently supported by this computer in the sense that this is the" +
                " resources that can be managed (the select locale dialog uses this to validate locales).</p>";
        strISOTablesHTML += "<p><b>ISO-639:</b> Lower-case two letter language codes.</p>";
        strISOTablesHTML += "<p><b>ISO-3166:</b> Upper-case two letter country codes.</p>";
        strISOTablesHTML += "<table valign=top><tr><td>"; // Outer table
        strISOTablesHTML += "<h2><center>ISO-639</center></h2>";
        strISOTablesHTML += "<table border=1>";

        String[] languages = Locale.getISOLanguages();

        for (int i = 0; i < languages.length; i++) {
            Locale tmpLocale = new Locale(languages[i]);
            strISOTablesHTML += "<tr><td>" + languages[i] + "</td><td>" + tmpLocale.getDisplayLanguage() + "</td></tr>";
        }

        strISOTablesHTML += "</table></td><td>";

        String[] countries = Locale.getISOCountries();

        strISOTablesHTML += "<h2><center>ISO-3166</center></h2>";
        strISOTablesHTML += "<table border=1>";

        for (int i = 0; i < countries.length; i++) {
            Locale tmpLocale = new Locale("en", countries[i]);
            strISOTablesHTML += "<tr><td>" + countries[i] + "</td><td>" + tmpLocale.getDisplayCountry() + "</td></tr>";
        }

        strISOTablesHTML += "</table></td></tr></table>";
    }

    public void checkIfValidResourceBundle() {
        /**
         * Looks in the java api for the correct names typed in the custom locale selection
         * Language code and country code needs to be
         */
        // It should at least contain a language, which is the first parameter needed to create a locale
        boolean valid = false;

        Locale tmpLocale = new Locale(txtDialogAdvancedLanguage.getText());

        // Only accept valid ISO languages

        String[] languages = Locale.getISOLanguages();

        for (int i = 0; i < languages.length; i++) {
            if (languages[i].equals(txtDialogAdvancedLanguage.getText().toLowerCase())) {
                valid = true;
            }
        }

        if (!tmpLocale.getDisplayLanguage().equals("") && txtDialogAdvancedLanguage.getText().length() == 2 &&
                valid) {
            lblDialogAdvancedLookupLanguageR.setText(tmpLocale.getDisplayLanguage());
            lblDialogAdvancedLookupValidR.setForeground(Color.GREEN);
            lblDialogAdvancedLookupValidR.setText("Yes");
            cmdDialogAdvancedSelect.setEnabled(true);
            valid = true;
        } else {
            lblDialogAdvancedLookupLanguageR.setText(strNotFound);
            lblDialogAdvancedLookupValidR.setForeground(Color.RED);
            lblDialogAdvancedLookupValidR.setText("No");
            cmdDialogAdvancedSelect.setEnabled(false);
            valid = false;
        }

        // Test country, recommended for a locale
        // Only accept valid ISO languages
        String[] countries = Locale.getISOCountries();
        boolean validCountry = false;
        for (int i = 0; i < countries.length; i++) {
            if (countries[i].equals(txtDialogAdvancedCountry.getText().toUpperCase())) {
                validCountry = true;
            }
        }
        tmpLocale = new Locale("en", txtDialogAdvancedCountry.getText());
        if (!tmpLocale.getDisplayCountry().equals("") && txtDialogAdvancedCountry.getText().length() == 2 &&
                validCountry) {
            lblDialogAdvancedLookupCountryR.setText(
                    tmpLocale.getDisplayCountry() + " (" + txtDialogAdvancedCountry.getText().toUpperCase() + ")");
        } else {
            lblDialogAdvancedLookupCountryR.setText(strNotFound);
            if (valid) {
                lblDialogAdvancedLookupValidR.setForeground(Color.DARK_GRAY);
                lblDialogAdvancedLookupValidR.setText("Yes (country recommended)");
            }
        }
        // Variant, optional and rarely used
        tmpLocale = new Locale("en", "UK", txtDialogAdvancedVariant.getText());
        if (!tmpLocale.getDisplayVariant().equals("")) {
            lblDialogAdvancedLookupVariantR.setText(tmpLocale.getDisplayVariant());
        } else {
            lblDialogAdvancedLookupVariantR.setText(strNotFound);
        }
        // Remove strNotFound when empty
        if (txtDialogAdvancedLanguage.getText().length() == 0) {
            lblDialogAdvancedLookupLanguageR.setText("");
        }
        if (txtDialogAdvancedCountry.getText().length() == 0) {
            lblDialogAdvancedLookupCountryR.setText("");
        }
        if (txtDialogAdvancedVariant.getText().length() == 0) {
            lblDialogAdvancedLookupVariantR.setText("");
        }
    }

    public void updateResources() {
        /**
         * Updates resources after basedir to work on has changed
         */
        try {
            if (translatorMode == SINGLE_MODE) {
                rootModule = resourceManager.getResource(txtSettingsDHIS2dir.getText().trim());
            } else {
                rootModule = resourceManager.getModules(txtSettingsDHIS2dir.getText().trim());
            }

            treeModel.setRoot(rootModule);
        } catch (I18nResourceException i18ne) {
            JOptionPane.showMessageDialog(parent, i18ne.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
        }

        // Compile the list to display in the simple select locale dialog
        Locale[] locales = Locale.getAvailableLocales();

        for (int i = 0; i < locales.length; i++) {
            // They must contain both language and country,
            if (!locales[i].getDisplayLanguage().equals("") && locales[i].getDisplayLanguage() != null &&
                    !locales[i].getDisplayCountry().equals("") && locales[i].getDisplayCountry() != null) {
                mapLocales.put(getLocaleInfoline(locales[i]), locales[i]);
            }
        }

        Collection<Locale> dhis2Locales = rootModule.getAvailableLocales();

        // Include a message to inform of existing translations
        for (Locale locale : dhis2Locales) {
            // Remove duplicates
            if (mapLocales.containsValue(locale)) {
                mapLocales.remove(getLocaleInfoline(locale));
            }
            mapLocales.put(getLocaleInfoline(locale) + " (Resources for this locale exist)", locale);
        }

        List<String> list = new ArrayList<String>(mapLocales.keySet());

        Collections.sort(list);

        lstDialog.setListData(list.toArray());

        setReferenceLocales();

        resourceTree.updateUI();
    }

    public void setReferenceLocales() {
        Collection<Locale> dhis2Locales = rootModule.getAvailableLocales();

        if (dhis2Locales.size() > 1 && currentLocale != null) {
            mapReflocales.clear();
            for (Locale locale : dhis2Locales) {
                // Don't display the locale were working on
                if (locale != currentLocale) {
                    mapReflocales.put(getLocaleInfoline(locale), locale);
                }
            }

            // Sort the reference locales
            ArrayList<String> sortedList = new ArrayList<String>(mapReflocales.keySet());

            Collections.sort(sortedList);

            cmbRefLocaleSelect.setModel(new DefaultComboBoxModel(sortedList.toArray()));

            cmbRefLocaleSelect.setEnabled(true);

            cmbRefLocaleSelect.setSelectedIndex(0);
        } else {
            cmbRefLocaleSelect.setEnabled(false);

            String[] msg = {"<no references available>"};

            cmbRefLocaleSelect.setModel(new DefaultComboBoxModel(msg));
        }
    }

    private void updateReferenceText(ResourceNode resource) {
        if (currentRefLocale != null) {
            if (resource.getType() == ResourceNode.MODULE) {
                txtRefLocale.setBorder(new TitledBorder("The reference is displayed here:"));
                txtRefLocale.setText("");
            } else if (resource.getText(currentRefLocale) == null || resource.getText(currentRefLocale).equals("")) {
                txtRefLocale.setBorder(new TitledBorder("No translation exist for this locale for this key"));
                txtRefLocale.setText("");
            } else {
                txtRefLocale.setBorder(new TitledBorder("The reference is displayed here:"));
                txtRefLocale.setText(resource.getText(currentRefLocale));
            }
        }
    }

    /**
     * Updates translation for a key when something is entered in txtLocale
     */
    public void updateTranslation() {
        ResourceNode resource = getSelectedResource();

        resource.translate(currentLocale, txtLocale.getText());
    }

    /**
     * Listeners as private classes
     */
    private class SelectProjectDirListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            int returnVal = fcDHIS2dir.showOpenDialog(parent);

            if (returnVal == JFileChooser.APPROVE_OPTION) {
                txtSettingsDHIS2dir.setText(fcDHIS2dir.getSelectedFile().getPath());
                lblDialogStartDHIS2dir.setText(fcDHIS2dir.getSelectedFile().getPath());

                cmdDialogStartOk.setEnabled(true);

                translatorMode = PROJECT_MODE;

                if (cmdSettingsBrowse.getActionListeners().length == 0) {
                    cmdSettingsBrowse.addActionListener(new SelectProjectDirListener());
                }
            } else {
                // Do nothing
            }
        }
    }

    private class SelectResourceListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            int returnVal = fcDHIS2resource.showOpenDialog(parent);

            if (returnVal == JFileChooser.APPROVE_OPTION) {
                panelSettingsDHIS2dir.setBorder(new TitledBorder("DHIS2 resource"));
                lblSettingsDHIS2dirHeader.setText("Change the resource file to work on here");
                txtSettingsDHIS2dir.setText(fcDHIS2resource.getSelectedFile().getPath());
                lblDialogStartDHIS2resource.setText(fcDHIS2resource.getSelectedFile().getPath());
                if (cmdSettingsBrowse.getActionListeners().length == 0) {
                    cmdSettingsBrowse.addActionListener(new SelectResourceListener());
                }
                translatorMode = SINGLE_MODE;
                cmdDialogStartOkS.setEnabled(true);
            } else {
                // Do nothing
            }
        }
    }

    private class UpdateDHIS2dirListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            dialogStart.setVisible(false);
            setVisible(true);
            updateResources();
        }
    }

    private class SelectLocaleListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            // Set the path back to root to avoid saving after txtLocale.setText()
            resourceTree.setSelectionPath(new TreePath(rootModule));

            txtLocale.setBorder(new TitledBorder("Select a key and enter text here"));
            txtRefLocale.setBorder(new TitledBorder("The reference is displayed here:"));

            dialog.setVisible(true);
        }
    }

    private class SelectLocaleSimpleListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            /**
             * Selects a locale in the dialog created by the SelectLocaleListener
             */
            try {
                // Set the path back to root to avoid saving after txtLocale.setText()
                resourceTree.setSelectionPath(new TreePath(rootModule));

                txtLocale.setBorder(new TitledBorder("Select a key and enter text here"));
                txtRefLocale.setBorder(new TitledBorder("The reference is displayed here:"));

                Locale locale = mapLocales.get(lstDialog.getSelectedValue());

                setCurrentLocale(locale);

                dialog.setVisible(false); // Hide the dialog again after selecting
            } catch (Exception ex) {
                // Do nothing
            }
        }
    }

    private class SelectLocaleAdvancedListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            /**
             * Selects a locale in the dialog created by the SelectLocaleListener
             */
            // See if country should be included, language should be validated at this point
            Locale currentLocaleTmp;
            if (!lblDialogAdvancedLookupCountryR.equals("") &&
                    !lblDialogAdvancedLookupCountryR.equals(strNotFound)) {
                // Check if variant, hence only allowed with country specified
                if (txtDialogAdvancedVariant.getText().equals("") || txtDialogAdvancedVariant.getText() == null) {
                    currentLocaleTmp =
                            new Locale(txtDialogAdvancedLanguage.getText(), txtDialogAdvancedCountry.getText());
                } else {
                    currentLocaleTmp = new Locale(txtDialogAdvancedLanguage.getText(),
                            txtDialogAdvancedCountry.getText(),
                            txtDialogAdvancedVariant.getText());
                }
            } else {
                currentLocaleTmp = new Locale(txtDialogAdvancedLanguage.getText());
            }
            setCurrentLocale(currentLocaleTmp);
            dialog.setVisible(false); // Hide the dialog again after selecting

        }
    }

    public void setCurrentLocale(Locale locale) {
        /**
         * Changes the current locale and resets everything
         */
        currentLocale = locale;
        // Need to add this to the resources, need to be aware of all locales for the reference list
        rootModule.addLocale(currentLocale);
        resourceTree.updateUI();
        refreshLocaleCaptions();
        setReferenceLocales();
    }

    private class CancelSelectLocaleDialog implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            /**
             * Just hides the dialog
             */
            dialog.setVisible(false);
        }
    }

    private class LocaleInfoDisplay implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            // Set the correct labels
            lblDialogLocaleInfoHeader.setText("Locale information for " + getLocaleInfoline(currentLocale));
            lblDialogLocaleInfoLanguage.setText(currentLocale.getDisplayLanguage());
            lblDialogLocaleInfoLanguageISO.setText(currentLocale.getLanguage());
            lblDialogLocaleInfoCountry.setText(currentLocale.getDisplayCountry());
            lblDialogLocaleInfoCountryISO.setText(currentLocale.getCountry());
            lblDialogLocaleInfoCountryISO3.setText(currentLocale.getISO3Country());
            lblDialogLocaleInfoVariantS.setText(currentLocale.getVariant());
            lblDialogLocaleInfoVariantL.setText(currentLocale.getDisplayVariant());
            dialogLocaleInfo.setVisible(true);
        }
    }

    private class LocaleInfoDisplayClose implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            dialogLocaleInfo.setVisible(false);
        }
    }

    public class SelectReflocaleListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            if (currentLocale != null) {
                // Then we should see what the list contains
                String localestr = (String) cmbRefLocaleSelect.getModel().getSelectedItem();
                currentRefLocale = mapReflocales.get(localestr); // The string points to a locale in the map
                // Update the translation
                try {
                    ResourceNode resource = getSelectedResource();
                    updateReferenceText(resource);
                } catch (Exception ex) {
                    //log.outWarning( "SelectReflocaleListener: Exception thrown, " + ex );
                }
            }
        }
    }

    private class SaveResourcesListener implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            try {
                resourceManager.saveModule(rootModule);
            } catch (I18nResourceException ex) {
                JOptionPane.showMessageDialog(parent, ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    private class HelpSelection implements ActionListener {

        public void actionPerformed(ActionEvent e) {
            /**
             * Sets the help text
             */
            if (e.getSource() == cmdHelp) {
                txtHelp.setText(strHelpHTML);
            } else if (e.getSource() == cmdHelpAdvanced) {
                txtHelp.setText(strHelpHTMLAdvanced);
            } else if (e.getSource() == cmdHelpGenerateISO) {
                if (strISOTablesHTML == "") {
                    generateISOTablesHTML();
                    txtHelp.setText(strISOTablesHTML);
                    cmdHelpGenerateISO.setText("View ISO-639 and ISO-3199 tables");
                } else {
                    txtHelp.setText(strISOTablesHTML);
                }

            }

        }
    }

    private class JavaApiLookupListener implements DocumentListener {

        public void changedUpdate(DocumentEvent e) {
            checkIfValidResourceBundle(); // Recheck changes
        }

        public void insertUpdate(DocumentEvent e) {
            checkIfValidResourceBundle(); // Recheck changes
        }

        public void removeUpdate(DocumentEvent e) {
            checkIfValidResourceBundle(); // Recheck changes
        }
    }

    private class TranslationListener implements DocumentListener {

        public void changedUpdate(DocumentEvent e) {
        }

        public void insertUpdate(DocumentEvent e) {
            updateTranslation();
        }

        public void removeUpdate(DocumentEvent e) {
            if (e.getOffset() != 0 | e.getDocument().getLength() == 0) {
                updateTranslation();
            }
        }
    }

    public class TreeMouseAdapter extends MouseAdapter {

        public void mouseClicked(MouseEvent e) {
            ResourceNode resource = null;

            try {
                resource = getSelectedResource();

                if (resource.getType() == ResourceNode.MODULE) {
                    txtLocale.setBorder(new TitledBorder("Module: " + resource.getCaption()));
                    txtLocale.setEnabled(false);
                    txtLocale.setBackground(toolbar.getBackground());

                    txtRefLocale.setBorder(new TitledBorder("The reference is displayed here:"));
                    txtRefLocale.setText("");
                } else {
                    txtLocale.setEnabled(true);
                    txtLocale.setBackground(txtRefLocale.getBackground());
                    txtLocale.setBorder(
                            new TitledBorder("Enter text for key \"" + resource.getCaption() + "\" here"));
                }

                txtLocale.setText(resource.getText(currentLocale));

                updateReferenceText(resource);
            } catch (NullPointerException npe) {
                log.outWarning("TreeMouseAdapter: NullPointerException");
            }
        }
    }

    public class LocaleListMouseAdapter extends MouseAdapter {
        // Make the select locale list double-clickable

        public void mousePressed(MouseEvent e) {
            if (e.getClickCount() == 2) {
                cmdDialogSimpleSelect.doClick();
            }
        }
    }

    public class KeyTreeCellRenderer extends DefaultTreeCellRenderer {

        final Font fontListed = new Font(null, Font.PLAIN, 12);
        final Font fontModule = new Font(null, Font.BOLD, 12);
        final Font fontHidden = new Font(null, Font.ITALIC, 12);

        public Component getTreeCellRendererComponent(JTree tree, Object value, boolean selected, boolean expanded,
                boolean leaf, int row, boolean hasFocus) {
            super.getTreeCellRendererComponent(tree, value, selected, expanded, leaf, row, hasFocus);

            ResourceNode resource;

            try {
                resource = (ResourceNode) value;
            } catch (ClassCastException cce) {
                return this; // Unreachable
            }

            setText(resource.getCaption());

            if (resource.getType() == ResourceNode.MODULE) {
                if (selected) {
                    setFont(fontModule);
                    setForeground(new JList().getSelectionForeground());
                    setBackground(new JList().getSelectionBackground());
                } else {
                    setFont(fontModule);
                    setForeground(tree.getForeground());
                    setBackground(tree.getBackground());
                }
            } else {
                if (resource.getText(currentLocale).equals("")) {
                    setFont(fontListed);
                    setIcon(I18nResourceEditorGUI.getIcon("not_translated.gif"));
                } else {
                    // Hide formatting keys
                    setFont(fontListed);
                    setIcon(I18nResourceEditorGUI.getIcon("translated.gif"));
                }
                // Show formatting stuff in italic
                if (resource.getCaption().startsWith("format.")) {
                    setFont(fontHidden);
                }
            }
            return this;
        }
    }

    private class DebugListener implements ActionListener {

        /**
         * Closes debug window or switches debug mode on and off (Depending on caller)
         */
        public void actionPerformed(ActionEvent e) {
            JButton cmdSource = (JButton) e.getSource();
            if (cmdSource == cmdDebugClose) {
                tabpane.remove(panelDebug);
            } else {
                // Switch on and off, not in use yet
                if (debugMode) {
                    debugMode = false;
                } else {
                    debugMode = true;
                }
            }
        }
    }

    public static void main(String[] args) {
        // Try to set the look and feel first, if it doesnt work default is used.
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
        }

        try {
            new I18nResourceEditorGUI();
        } catch (Exception e) {
            JOptionPane.showMessageDialog(new JFrame(),
                    "Error during startup: " + e + " thrown. Message: " + e.getMessage(),
                    "i18n Resource Editor - error", JOptionPane.ERROR_MESSAGE);
            e.printStackTrace();
            System.exit(1);
        }
    }
}
# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView

from eddy.core.commands.iri import CommandIRIRemoveAnnotation, CommandCommmonSubstringIRIsRefactor
from eddy.core.commands.project import CommandProjectAddPrefix, CommandProjectRemovePrefix, \
    CommandProjectModifyPrefixResolution, CommandProjectModifyNamespacePrefix, CommandProjectAddAnnotationProperty, \
    CommandProjectRemoveAnnotationProperty, CommandProjectSetOntologyIRIAndVersion, \
    CommandProjectSetProjectLabelFromSimpleNameAndLanguage
from eddy.core.owl import IllegalPrefixError, IllegalNamespaceError, AnnotationAssertion

from eddy import ORGANIZATION, APPNAME
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.ui.annotation_assertion import AnnotationAssertionBuilderDialog
from eddy.ui.fields import StringField, ComboBox, CheckBox
from eddy.ui.message_box import MessageBoxFactory, MsgBoxType

LOGGER = getLogger()


class OntologyManagerDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'Ontology Manager' dialog.
    """

    noPrefixString = ''
    emptyString = ''

    def __init__(self, session):
        """
        Initialize the Ontology Manager dialog.
        :type session: Session
        """
        super().__init__(session)

        self.addingNewPrefix = False
        self.prefixIndexMap = {}
        self.project = session.project


        #############################################
        # GENERAL TAB
        #################################

        ## ONTOLOGY PROPERTIES GROUP

        iriLabel = QtWidgets.QLabel(self, objectName='ontology_iri_label')
        iriLabel.setFont(Font('Roboto', 13))
        iriLabel.setText('Ontology IRI')
        self.addWidget(iriLabel)

        iriField = StringField(self, objectName='ontology_iri_field')
        connect(iriField.textEdited, self.onOntologyIriOrVersionEdited)
        iriField.setFont(Font('Roboto', 13))
        iriField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(iriField)

        versionLabel = QtWidgets.QLabel(self, objectName='ontology_version_label')
        versionLabel.setFont(Font('Roboto', 13))
        versionLabel.setText('Ontology Version IRI')
        self.addWidget(versionLabel)

        versionField = StringField(self, objectName='ontology_version_field')
        connect(versionField.textEdited,self.onOntologyIriOrVersionEdited)
        versionField.setFont(Font('Roboto', 13))
        versionField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/1.0')
        self.addWidget(versionField)

        saveBtn = QtWidgets.QPushButton('Save', objectName='save_ont_iri_version_button')
        saveBtn.setEnabled(False)
        connect(saveBtn.clicked, self.saveOntologyIRIAndVersion)
        self.addWidget(saveBtn)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('ontology_iri_label'), self.widget('ontology_iri_field'))
        formlayout.addRow(self.widget('ontology_version_label'), self.widget('ontology_version_field'))

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('save_ont_iri_version_button'))

        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(formlayout)
        outerFormLayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Ontology IRI', self, objectName='ontology_iri_widget')
        groupbox.setLayout(outerFormLayout)
        self.addWidget(groupbox)

        ## ONTOLOGY IMPORTS GROUP

        table = QtWidgets.QTableWidget(0, 2, self, objectName='ontology_imports_table_widget')
        table.setHorizontalHeaderLabels(['Name', 'Ontology IRI'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(130)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='ontology_imports_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='ontology_imports_delete_button')
        connect(addBtn.clicked, self.addOntologyImport)
        connect(delBtn.clicked, self.removeOntologyImport)
        self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('ontology_imports_add_button'))
        boxlayout.addWidget(self.widget('ontology_imports_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('ontology_imports_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Imported Ontologies', self, objectName='ontology_imports_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## ONTOLOGY ANNOTATIONS GROUP

        table = QtWidgets.QTableWidget(0, 2, self, objectName='annotations_table_widget')
        table.clear()
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(170)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='ontology_annotations_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='ontology_annotations_delete_button')
        editBtn = QtWidgets.QPushButton('Edit', objectName='ontology_annotations_edit_button')
        connect(addBtn.clicked, self.addOntologyAnnotation)
        connect(delBtn.clicked, self.removeOntologyAnnotation)
        connect(editBtn.clicked, self.editOntologyAnnotation)
        self.addWidget(addBtn)
        self.addWidget(delBtn)
        self.addWidget(editBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('ontology_annotations_add_button'))
        boxlayout.addWidget(self.widget('ontology_annotations_delete_button'))
        boxlayout.addWidget(self.widget('ontology_annotations_edit_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('annotations_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Ontology Annotations', self, objectName='ontology_annotations_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## GENERAL TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_iri_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_imports_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_annotations_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('general_widget')
        self.addWidget(widget)

        #############################################
        # PREFIXES TAB
        #################################

        ## PREFIXES GROUP
        table = QtWidgets.QTableWidget(1, 2, self, objectName='prefixes_table_widget')
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))

        self.addWidget(table)


        delBtn = QtWidgets.QPushButton('Remove', objectName='prefixes_delete_button')
        #connect(addBtn.clicked, self.addPrefix)
        connect(delBtn.clicked, self.removePrefix)
        #self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        #boxlayout.addWidget(self.widget('prefixes_add_button'))
        boxlayout.addWidget(self.widget('prefixes_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('prefixes_table_widget'))
        formlayout.addRow(boxlayout)

        definedPrefixesGroupbox = QtWidgets.QGroupBox('Defined Prefixes', self, objectName='defined_prefixes_group_widget')
        definedPrefixesGroupbox.setLayout(formlayout)
        self.addWidget(definedPrefixesGroupbox)


        prefixLabel = QtWidgets.QLabel(self, objectName='prefix_input_label')
        prefixLabel.setFont(Font('Roboto', 13))
        prefixLabel.setText('Prefix')
        self.addWidget(prefixLabel)

        prefixField = StringField(self, objectName='prefix_input_field')
        prefixField.setFont(Font('Roboto', 13))
        #prefixField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(prefixField)

        nsLabel = QtWidgets.QLabel(self, objectName='ns_input_label')
        nsLabel.setFont(Font('Roboto', 13))
        nsLabel.setText('Namespace')
        self.addWidget(nsLabel)

        nsField = StringField(self, objectName='ns_input_field')
        nsField.setFont(Font('Roboto', 13))
        #nsField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/1.0')
        self.addWidget(nsField)
        inputPrefixLayout = QtWidgets.QFormLayout()
        inputPrefixLayout.addRow(self.widget('prefix_input_label'), self.widget('prefix_input_field'))
        inputPrefixLayout.addRow(self.widget('ns_input_label'), self.widget('ns_input_field'))

        addBtn = QtWidgets.QPushButton('Add', objectName='prefixes_add_button')
        connect(addBtn.clicked, self.addPrefix)
        self.addWidget(addBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('prefixes_add_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(inputPrefixLayout)
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Define new prefix', self, objectName='add_prefix_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## PREFIXES TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('defined_prefixes_group_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('add_prefix_group_widget'), 1, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('prefixes_widget')
        self.addWidget(widget)

        #############################################
        # ANNOTATIONS TAB
        #################################

        ## ANNOTATIONS GROUP

        table = QtWidgets.QTableWidget(0, 2, self, objectName='annotation_properties_table_widget')
        table.setHorizontalHeaderLabels(['IRI', 'Comment'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        self.addWidget(table)

        #addBtn = QtWidgets.QPushButton('Add', objectName='annotation_properties_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='annotation_properties_delete_button')
        #connect(addBtn.clicked, self.addAnnotationProperty)
        connect(delBtn.clicked, self.removeAnnotationProperty)
        #self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        #boxlayout.addWidget(self.widget('annotation_properties_add_button'))
        boxlayout.addWidget(self.widget('annotation_properties_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('annotation_properties_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Annotation Properties', self, objectName='annotation_properties_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ########ADDED

        comboBoxLabel = QtWidgets.QLabel(self, objectName='iri_prefix_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Prefix')
        self.addWidget(comboBoxLabel)

        combobox = ComboBox(objectName='iri_prefix_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItem(self.noPrefixString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        combobox.setCurrentText(self.noPrefixString)
        self.addWidget(combobox)

        inputLabel = QtWidgets.QLabel(self, objectName='input_field_label')
        inputLabel.setFont(Font('Roboto', 12))
        inputLabel.setText('Input')
        self.addWidget(inputLabel)

        inputField = StringField(self, objectName='iri_input_field')
        # inputField.setFixedWidth(300)
        inputField.setFont(Font('Roboto', 12))
        inputField.setValue('')
        self.addWidget(inputField)

        fullIriLabel = QtWidgets.QLabel(self, objectName='full_iri_label')
        fullIriLabel.setFont(Font('Roboto', 12))
        fullIriLabel.setText('Full IRI')
        self.addWidget(fullIriLabel)
        fullIriField = StringField(self, objectName='full_iri_field')
        # fullIriField.setFixedWidth(300)
        fullIriField.setFont(Font('Roboto', 12))
        fullIriField.setReadOnly(True)
        self.addWidget(fullIriField)

        addBtn = QtWidgets.QPushButton('Add', objectName='annotation_add_button')
        connect(addBtn.clicked, self.addAnnotationProperty)
        self.addWidget(addBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('annotation_add_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('iri_prefix_combobox_label'), self.widget('iri_prefix_switch'))
        formlayout.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))
        formlayout.addRow(boxlayout)

        groupbox = QtWidgets.QGroupBox('Define new annotation property', self, objectName='add_annotation_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        connect(self.widget('iri_prefix_switch').currentIndexChanged, self.onAnnotationPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onAnnotationInputChanged)

        ## ANNOTATIONS TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('annotation_properties_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('add_annotation_group_widget'), 1, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('annotations_widget')
        self.addWidget(widget)

        #TODO
        #############################################
        # Global IRI
        #################################
        checkBoxLabel = QtWidgets.QLabel(self, objectName='checkBox_label')
        checkBoxLabel.setFont(Font('Roboto', 12))
        checkBoxLabel.setText('Derive rdfs:label from simple name')
        self.addWidget(checkBoxLabel)
        checked = self.project.addLabelFromSimpleName
        checkBox = CheckBox('',self,enabled=True,checked=checked,clicked=self.onLabelcheckBoxClicked, objectName='label_checkbox')
        self.addWidget(checkBox)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Default rdfs:label language')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.project.defaultLanguage:
            combobox.setCurrentText(self.project.defaultLanguage)
        else:
            combobox.setCurrentText(self.emptyString)
        if checkBox.isChecked():
            combobox.setStyleSheet("background:#FFFFFF");
            combobox.setEnabled(True)
        else:
            combobox.setStyleSheet("background:#808080");
            combobox.setEnabled(False)
        connect(combobox.currentIndexChanged, self.onLanguageSwitched)


        self.addWidget(combobox)
        iriLabelLayout = QtWidgets.QFormLayout()
        iriLabelLayout.addRow(self.widget('checkBox_label'), self.widget('label_checkbox'))
        iriLabelLayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))

        applyBtn = QtWidgets.QPushButton('Apply', objectName='iri_label_button')
        applyBtn.setEnabled(False)
        connect(applyBtn.clicked, self.doApplyIriLabel)
        self.addWidget(applyBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('iri_label_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(iriLabelLayout)
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('IRI Definition', self, objectName='iri_definition_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)


        #REFACTOR
        preLabel = QtWidgets.QLabel(self, objectName='pre_input_label')
        preLabel.setFont(Font('Roboto', 13))
        preLabel.setText('Pre ')
        self.addWidget(preLabel)

        preField = StringField(self, objectName='pre_input_field')
        preField.setFont(Font('Roboto', 13))
        # prefixField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(preField)

        postLabel = QtWidgets.QLabel(self, objectName='post_input_label')
        postLabel.setFont(Font('Roboto', 13))
        postLabel.setText('Post ')
        self.addWidget(postLabel)

        postField = StringField(self, objectName='post_input_field')
        postField.setFont(Font('Roboto', 13))
        # prefixField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(postField)

        iriRefactorLayout = QtWidgets.QFormLayout()
        iriRefactorLayout.addRow(self.widget('pre_input_label'), self.widget('pre_input_field'))
        iriRefactorLayout.addRow(self.widget('post_input_label'), self.widget('post_input_field'))

        refactorBtn = QtWidgets.QPushButton('Refactor', objectName='iri_refactor_button')
        connect(refactorBtn.clicked, self.doIriRefactor)
        self.addWidget(refactorBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('iri_refactor_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(iriRefactorLayout)
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('IRI Refactor', self, objectName='iri_refactor_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('iri_definition_group_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('iri_refactor_group_widget'), 1, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('iri_widget')
        self.addWidget(widget)


        # TODO END

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        #confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        #confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('general_widget'), 'General')
        widget.addTab(self.widget('prefixes_widget'), 'Prefixes')
        widget.addTab(self.widget('annotations_widget'), 'Annotations')
        widget.addTab(self.widget('iri_widget'), 'Global IRIs')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 520)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Ontology Manager')
        self.redraw()

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        table = self.widget('prefixes_table_widget')
        connect(table.cellChanged, self.managePrefixTableEntryModification)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PreferencesDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        ##
        ## TODO: complete validation and settings save
        ##
        #############################################
        # GENERAL TAB
        #################################

        #############################################
        # PREFIXES TAB
        #################################

        #############################################
        # ANNOTATIONS TAB
        #################################

        #############################################
        # SAVE & EXIT
        #################################

        super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        """
        Executed when the dialog is accepted.
        """
        ##
        ## TODO: complete validation and settings save
        ##
        #############################################
        # GENERAL TAB
        #################################

        #############################################
        # PREFIXES TAB
        #################################

        #############################################
        # ANNOTATIONS TAB
        #################################

        #############################################
        # SAVE & EXIT
        #################################

        super().reject()

    @QtCore.pyqtSlot()
    def redraw(self):
        """
        Redraw the dialog components, reloading their contents.
        """
        #############################################
        # GENERAL TAB
        #################################
        iriField = self.widget('ontology_iri_field')
        if self.project.ontologyIRI:
            iriField.setText(str(self.project.ontologyIRI))

        versionField = self.widget('ontology_version_field')
        if self.project.version and self.project.version != 'NULL':
            versionField.setText(self.project.version)

        self.widget('save_ont_iri_version_button').setEnabled(False)

        table = self.widget('annotations_table_widget')
        ontAnnAss = self.project.ontologyIRI.annotationAssertions
        table.clear()
        table.setRowCount(len(ontAnnAss))
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        rowcount = 0
        for assertion in ontAnnAss:
            propertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
            propertyItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
            propertyItem.setData(Qt.UserRole, assertion)
            table.setItem(rowcount, 0, propertyItem)
            valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
            valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(valueItem))
            rowcount += 1
        table.resizeColumnToContents(0)

        # TODO: reload imports when they are implemented

        #############################################
        # PREFIXES TAB
        #################################

        # Reload prefixes table contents
        prefixDictItems = self.project.prefixDictItems()
        table = self.widget('prefixes_table_widget')
        table.clear()
        table.setRowCount(len(prefixDictItems))
        table.setHorizontalHeaderLabels(['Prefix', 'Namespace'])

        rowcount = 0
        for prefix, namespace in prefixDictItems:
            table.setItem(rowcount, 0, QtWidgets.QTableWidgetItem(prefix))
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(namespace))
            rowcount += 1
        self.buildPrefixIndexMap()
        table.resizeColumnsToContents()

        #############################################
        # ANNOTATIONS TAB
        #################################
        annotationProperties = self.project.getAnnotationPropertyIRIs()
        table = self.widget('annotation_properties_table_widget')
        table.clear()
        table.setHorizontalHeaderLabels(['IRI', 'Comment'])
        table.setRowCount(len(annotationProperties))
        rowcount = 0
        for annIRI in annotationProperties:
            propertyItem = QtWidgets.QTableWidgetItem(str(annIRI))
            propertyItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
            table.setItem(rowcount,0,propertyItem)
            rowcount += 1
        table.resizeColumnsToContents()

        #############################################
        # Global IRI
        #################################
        checked = self.project.addLabelFromSimpleName
        checkBox = self.widget('label_checkbox')
        checkBox.setChecked(checked)

        combobox = self.widget('lang_switch')
        if self.project.defaultLanguage:
            combobox.setCurrentText(self.project.defaultLanguage)
        else:
            combobox.setCurrentText(self.emptyString)
        if checkBox.isChecked():
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF");
            self.widget('lang_switch').setEnabled(True)
        else:
            self.widget('lang_switch').setStyleSheet("background:#808080");
            self.widget('lang_switch').setEnabled(False)

        # REFACTOR
        self.widget('iri_label_button').setEnabled(False)
        preField = self.widget('pre_input_field')
        postField = self.widget('post_input_field')


        #############################################
        # SAVE & EXIT
        #################################


    #############################################
    # GENERAL TAB
    #################################
    @QtCore.pyqtSlot(str)
    def onOntologyIriOrVersionEdited(self, textValue):
        self.widget('save_ont_iri_version_button').setEnabled(True)

    @QtCore.pyqtSlot(bool)
    def saveOntologyIRIAndVersion(self, _):
        """
        Adds an ontology import to the current project.
        :type _: bool
        """
        try:
            oldIri = ''
            if self.project.ontologyIRI:
                oldIri = str(self.project.ontologyIRI)
            oldVersion = ''
            if self.project.version:
                oldVersion = self.project.version

            iriField = self.widget('ontology_iri_field')
            ontIriString = iriField.value()
            versionField = self.widget('ontology_version_field')
            version = versionField.value()

            self.project.isValidIdentifier(ontIriString)

            command = CommandProjectSetOntologyIRIAndVersion(self.project, ontIriString, version, oldIri, oldVersion)
            self.session.undostack.beginMacro('Set ontology IRI')
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()
            self.widget('save_ont_iri_version_button').setEnabled(False)

        except IllegalNamespaceError as e:
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal identifier',
                                                     'IRI definition issue', MsgBoxType.WARNING.value,
                                                     informativeText='The string "{}" is not a legal identifier'.format(
                                                         ontIriString),
                                                     detailedText=str(e))
            msgBox.exec_()

    @QtCore.pyqtSlot(bool)
    def addOntologyImport(self, _):
        """
        Adds an ontology import to the current project.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("addOntologyImport called")

    @QtCore.pyqtSlot(bool)
    def removeOntologyImport(self, _):
        """
        Removes an ontology import from the current project.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("removeOntologyImport called")

    @QtCore.pyqtSlot(bool)
    def addOntologyAnnotation(self, _):
        """
        Adds an annotation to the current ontology.
        :type _: bool
        """
        LOGGER.debug("addOntologyAnnotation called")
        assertionBuilder = self.session.doOpenAnnotationAssertionBuilder(self.project.ontologyIRI) #AnnotationAssertionBuilderDialog(self.project.ontologyIRI,self.session)
        connect(assertionBuilder.sgnAnnotationAssertionAccepted, self.onOntologyAnnotationAssertionAccepted)
        assertionBuilder.exec_()

    #@QtCore.pyqtSlot(AnnotationAssertion)
    def onOntologyAnnotationAssertionAccepted(self,assertion):
        '''
        :type assertion:AnnotationAssertion
        '''
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        table.setRowCount(rowcount + 1)
        propertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
        propertyItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        propertyItem.setData(Qt.UserRole,assertion)
        table.setItem(rowcount, 0, propertyItem)
        valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
        valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(valueItem))
        table.scrollToItem(table.item(rowcount, 0))
        table.resizeColumnToContents(0)


    @QtCore.pyqtSlot(bool)
    def removeOntologyAnnotation(self, _):
        """
        Removes an annotation from the current ontology.
        :type _: bool
        """
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                assertion = removedItem.data(Qt.UserRole)
                command = CommandIRIRemoveAnnotation(self.project, self.project.ontologyIRI, assertion)
                commands.append(command)
        self.session.undostack.beginMacro('Remove annotations >>')
        for command in commands:
            if command:
                self.session.undostack.push(command)
        self.session.undostack.endMacro()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))

    @QtCore.pyqtSlot(bool)
    def editOntologyAnnotation(self, _):
        table = self.widget('annotations_table_widget')
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                editItem = table.item(row, 0)
                assertion = editItem.data(Qt.UserRole)
                #editItem.setData(None)
                assertionBuilder = self.session.doOpenAnnotationAssertionBuilder(self.project.ontologyIRI,assertion)
                connect(assertionBuilder.sgnAnnotationAssertionCorrectlyModified,self.onOntologyAnnotationAssertionModified)
                assertionBuilder.exec_()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onOntologyAnnotationAssertionModified(self,assertion):
        '''
        :type assertion:AnnotationAssertion
        '''
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        for row in range(0,rowcount):
            propItem = table.item(row, 0)
            itemAssertion = propItem.data(Qt.UserRole)
            if itemAssertion is assertion:
                newPropertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
                newPropertyItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                newPropertyItem.setData(Qt.UserRole, assertion)
                table.setItem(row, 0, newPropertyItem)
                valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
                valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                table.setItem(row, 1, QtWidgets.QTableWidgetItem(valueItem))
                break

    #############################################
    # PREFIXES TAB
    #################################
    @QtCore.pyqtSlot(int,int)
    def managePrefixTableEntryModification(self, row, column):
        if not self.addingNewPrefix:
            if column==0:
                self.managePrefixModification(row,column)
            else:
                self.manageNamespaceModification(row,column)
        else:
            self.addingNewPrefix = False

    def managePrefixModification(self, row, column):
        table = self.widget('prefixes_table_widget')
        modifiedItem = table.item(row, column)
        itemText = modifiedItem.text()
        text = str(itemText)
        for index,prefix in self.prefixIndexMap.items():
            if not index==row:
                if prefix==text:
                    print('prefisso già definito')
                    table.setItem(row, 0, QtWidgets.QTableWidgetItem(self.prefixIndexMap[row]))
                    msgBox = MessageBoxFactory.getMessageBox(self,'Already defined prefix',
                                                             'Prefix definition issue',MsgBoxType.WARNING.value,
                                                             informativeText='The prefix "{}" is already used'.format(text))
                    msgBox.exec_()
                    return
        corrNSItem = table.item(row, 1)
        nsItemText = corrNSItem.text()
        nsText = str(nsItemText)
        try:
            self.project.isValidPrefixEntry(text,nsText)

            oldPrefix = None
            for pr,ns in self.project.prefixDictItems():
                if ns==nsText:
                    oldPrefix = pr
                    break

            command = CommandProjectModifyNamespacePrefix(self.project,nsText,text,oldPrefix)
            self.session.undostack.beginMacro('Replace prefix {0} '.format(oldPrefix))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()

            #aggiorno mappa
            self.prefixIndexMap[row]=text
        except IllegalPrefixError as e:
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(self.prefixIndexMap[row]))
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal prefix',
                                                     'Prefix definition issue', MsgBoxType.WARNING.value,
                                                     informativeText='The string "{}" is not a legal prefix'.format(text),
                                                     detailedText=str(e))
            msgBox.exec_()

    def manageNamespaceModification(self, row, column):
        table = self.widget('prefixes_table_widget')
        modifiedItem = table.item(row, column)
        itemText = modifiedItem.text()
        text = str(itemText)
        corrPrefixItem = table.item(row, 0)
        prefixItemText = corrPrefixItem.text()
        prefixText = str(prefixItemText)
        try:
            self.project.isValidPrefixEntry(prefixText, text)
            namespace = self.project.getPrefixResolution(prefixText)
            command = CommandProjectModifyPrefixResolution(self.project,prefixText,text,namespace)
            self.session.undostack.beginMacro('Modify prefix {0} '.format(text))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()

        except IllegalNamespaceError as e:
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal namespace',
                                                     'Prefix definition issue', MsgBoxType.WARNING.value,
                                                     informativeText='The string "{}" is not a legal namespace'.format(text),
                                                     detailedText=str(e))
            msgBox.exec_()

    def buildPrefixIndexMap(self):
        self.prefixIndexMap = {}
        table = self.widget('prefixes_table_widget')
        rowcount = table.rowCount()
        for row in range(0,rowcount):
            item = table.item(row, 0)
            itemText = item.text()
            text = str(itemText)
            self.prefixIndexMap[row]=text

    @QtCore.pyqtSlot(bool)
    def addPrefix(self, _):
        """
        Add a new prefix entry to the list of ontology prefixes.
        :type _: bool
        """
        try:
            prefixField = self.widget('prefix_input_field')
            prefixValue = prefixField.value()
            currentPrefixes = self.project.getManagedPrefixes()
            if prefixValue in currentPrefixes:
                print('prefisso già definito, modificalo dalla tabella')
                msgBox = MessageBoxFactory.getMessageBox(self, 'Already defined prefix',
                                                         'Prefix definition issue', MsgBoxType.WARNING.value,
                                                         informativeText='The prefix "{}" is already used'.format(prefixValue))
                msgBox.setWindowModality(Qt.ApplicationModal)
                msgBox.exec_()
                return
            nsField = self.widget('ns_input_field')
            nsValue = nsField.value()

            self.project.isValidPrefixEntry(prefixValue, nsValue)

            command = CommandProjectAddPrefix(self.project,prefixValue,nsValue)
            self.session.undostack.beginMacro('Add prefix {0} '.format(prefixValue))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()

            self.addingNewPrefix = True
            table = self.widget('prefixes_table_widget')
            rowcount = table.rowCount()
            table.setRowCount(rowcount + 1)
            table.setItem(rowcount, 0, QtWidgets.QTableWidgetItem(prefixValue))
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(nsValue))
            self.buildPrefixIndexMap()
            table.scrollToItem(table.item(rowcount, 0))
            prefixField.setValue('')
            nsField.setValue('')
        except IllegalPrefixError as e:
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal prefix',
                                                     'Prefix definition issue', MsgBoxType.WARNING.value,
                                                     informativeText='The string "{}" is not a legal prefix'.format(prefixValue),
                                                     detailedText=str(e))
            msgBox.exec_()
        except IllegalNamespaceError as e:
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal namespace',
                                                     'Prefix definition issue', MsgBoxType.WARNING.value,
                                                     informativeText='The string "{}" is not a legal namespace'.format(nsValue),
                                                     detailedText=str(e))
            msgBox.exec_()

    @QtCore.pyqtSlot(bool)
    def removePrefix(self, _):
        """
        Removes a set of prefix entries from the list of ontology prefixes.
        :type _: bool
        """
        table = self.widget('prefixes_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                itemText = removedItem.text()
                text = str(itemText)
                namespace = self.project.getPrefixResolution(text)
                command = CommandProjectRemovePrefix(self.project, text, namespace)
                self.session.undostack.beginMacro('Remove prefix {0} '.format(text))
                if command:
                    self.session.undostack.push(command)
                self.session.undostack.endMacro()

        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))
        self.buildPrefixIndexMap()

    #############################################
    # ANNOTATIONS TAB
    #################################
    @QtCore.pyqtSlot(bool)
    def addAnnotationProperty(self, _):
        """
        Adds an annotation property to the ontology alphabet.
        :type _: bool
        """
        try:
            annIRI = self.widget('full_iri_field').value()
            if not self.project.existAnnotationProperty(annIRI):
                self.project.isValidIdentifier(annIRI)

                command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                self.session.undostack.beginMacro('Add annotation property {0} '.format(annIRI))
                if command:
                    self.session.undostack.push(command)
                self.session.undostack.endMacro()

                table = self.widget('annotation_properties_table_widget')
                rowcount = table.rowCount()
                table.setRowCount(rowcount + 1)
                propertyItem = QtWidgets.QTableWidgetItem(str(annIRI))
                propertyItem.setFlags(QtCore.Qt.ItemIsEnabled)
                table.setItem(rowcount, 0, propertyItem)
                table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(''))
                table.scrollToItem(table.item(rowcount, 0))
            self.widget('iri_prefix_switch').setCurrentText(self.noPrefixString)
            self.widget('iri_input_field').setText('')
        except IllegalNamespaceError as e:
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal namespace',
                                                     'Entity definition', MsgBoxType.WARNING.value,
                                                     informativeText='The string "{}" is not a legal IRI'.format(annIRI),
                                                     detailedText=str(e))
            msgBox.exec_()

    @QtCore.pyqtSlot(bool)
    def removeAnnotationProperty(self, _):
        """
        Removes an annotation property from the ontology alphabet.
        :type _: bool
        """
        table = self.widget('annotation_properties_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                itemText = removedItem.text()
                text = str(itemText)
                commands.append(CommandProjectRemoveAnnotationProperty(self.project,text))
        self.session.undostack.beginMacro('remove annotation properties >>')
        for command in commands:
            if command:
                self.session.undostack.push(command)
        self.session.undostack.endMacro()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))

    @QtCore.pyqtSlot(int)
    def onAnnotationPrefixChanged(self, val):
        self.onAnnotationInputChanged('')

    @QtCore.pyqtSlot('QString')
    def onAnnotationInputChanged(self, val):
        prefix = self.widget('iri_prefix_switch').currentText()
        input = self.widget('iri_input_field').value()
        resolvedPrefix = self.resolvePrefix(prefix)
        fullIri = '{}{}'.format(resolvedPrefix, input)
        self.widget('full_iri_field').setValue(fullIri)

    def resolvePrefix(self, prefixStr):
        prefixLimit = prefixStr.find(':')
        if prefixLimit < 0:
            return ''
        else:
            prefixStr = prefixStr[0:prefixLimit]
            return self.project.getPrefixResolution(prefixStr)
            # return self.project.getPrefixResolution(prefixStr[:-1])

    @QtCore.pyqtSlot(bool)
    def doIriRefactor(self, _):
        """
        Add a new prefix entry to the list of ontology prefixes.
        :type _: bool
        """
        try:
            preField = self.widget('pre_input_field')
            preValue = preField.value()
            if not preValue:
                raise RuntimeError('Please insert a non-empty pre string')
            postField = self.widget('post_input_field')
            postValue = postField.value()
            if postValue:
                self.project.isValidIdentifier(postValue)
            if preValue == postValue:
                return
            matchingIRIS = self.project.getAllIriStartingWith(preValue)
            commandDict = dict()
            for iri in matchingIRIS:
                preIriStr = str(iri)
                postIriStr = str(iri).replace(preValue,postValue,1)
                try:
                    self.project.isValidIdentifier(postIriStr)
                    commandDict[preIriStr] = postIriStr
                except IllegalNamespaceError as e:
                    LOGGER.warning("doIriRefactor(pre='{}' post='{}'): {} excluded from refactoring [{}]".format(preValue,postValue,preIriStr,str(e)))
            command = CommandCommmonSubstringIRIsRefactor(self.project,preValue,commandDict)
            self.session.undostack.beginMacro("IRIs starting with '{}' refactor".format(preValue))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()
            msgBox = MessageBoxFactory.getMessageBox(self, 'IRI refactor',
                                                     'IRI refactor', MsgBoxType.INFO.value,
                                                     informativeText="{} IRIs starting with'{}' have been modified".format(len(commandDict), preValue))
            msgBox.exec_()
            preField.setValue('')
            postField.setValue('')
        except IllegalNamespaceError as e:
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal Post value',
                                                     'IRI refactor issue', MsgBoxType.WARNING.value,
                                                     informativeText='The string "{}" is not a legal namespace'.format(
                                                         postValue),
                                                     detailedText=str(e))
            msgBox.exec_()
        except RuntimeError as e:
            msgBox = MessageBoxFactory.getMessageBox(self, 'Illegal Pre value',
                                                     'IRI refactor issue', MsgBoxType.WARNING.value,
                                                     informativeText='Empty string is not allowed as Pre value',
                                                     detailedText=str(e))
            msgBox.exec_()


    #############################################
    # Global IRI
    #################################
    @QtCore.pyqtSlot()
    def onLabelcheckBoxClicked(self):
        checkBox = self.widget('label_checkbox')
        if checkBox.isChecked():
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF");
            self.widget('lang_switch').setEnabled(True)
        else:
            self.widget('lang_switch').setStyleSheet("background:#808080");
            self.widget('lang_switch').setEnabled(False)
        self.widget('iri_label_button').setEnabled(True)

    @QtCore.pyqtSlot(int)
    def onLanguageSwitched(self,index):
        self.widget('iri_label_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def doApplyIriLabel(self):
        checkBox = self.widget('label_checkbox')
        undoLanguage = self.project.defaultLanguage
        redoLanguage = str(self.widget('lang_switch').currentText())
        command = CommandProjectSetProjectLabelFromSimpleNameAndLanguage(self.project, checkBox.isChecked(), redoLanguage, not checkBox.isChecked(), undoLanguage)
        self.session.undostack.beginMacro('Set automatic rdf:label management')
        if command:
            self.session.undostack.push(command)
        self.session.undostack.endMacro()

        self.widget('iri_label_button').setEnabled(False)
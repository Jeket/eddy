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


from PyQt5 import QtWidgets
from PyQt5 import QtCore
from eddy.core.functions.signals import connect, disconnect
from eddy.core.datatypes.graphol import Item

#############################################
#   Ontology IRI
#################################
from eddy.core.owl import IllegalNamespaceError

class CommandProjectSetProjectLabelFromSimpleNameAndLanguage(QtWidgets.QUndoCommand):
    """
    This command is used to set the IRI identifying the ontology.
    """
    def __init__(self, project, labelFromSimpleNameRedo, languageRedo, labelFromSimpleNameUndo, languageUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type labelFromSimpleNameRedo: bool
        :type languageRedo: str
        :type labelFromSimpleNameUndo: bool
        :type languageUndo: str
        :type name: str
        """
        super().__init__(name or 'Set automatic rdf:label management')
        self._project = project
        self._labelFromSimpleNameRedo = labelFromSimpleNameRedo
        self._languageRedo = languageRedo
        self._labelFromSimpleNameUndo = labelFromSimpleNameUndo
        self._languageUndo = languageUndo

    def redo(self):
        """redo the command"""
        self._project.addLabelFromSimpleName = self._labelFromSimpleNameRedo
        self._project.defaultLanguage = self._languageRedo

    def undo(self):
        """undo the command"""
        self._project.addLabelFromSimpleName = self._labelFromSimpleNameUndo
        self._project.defaultLanguage = self._languageUndo

class CommandProjectSetOntologyIRIAndVersion(QtWidgets.QUndoCommand):
    """
    This command is used to set the IRI identifying the ontology.
    """
    def __init__(self, project, iriRedo, versionRedo, iriUndo, versionUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type iriRedo: str
        :type versionRedo: str
        :type iriUndo: str
        :type versionUndo: str
        :type name: str
        """
        super().__init__(name or 'Set ontology IRI')
        self._project = project
        self._iriRedo = iriRedo
        self._versionRedo = versionRedo
        self._iriUndo = iriUndo
        self._versionUndo = versionUndo

    def redo(self):
        """redo the command"""
        try:
            self._project.setOntologyIRI(self._iriRedo)
            self._project.version = self._versionRedo
        except IllegalNamespaceError:
            errorDialog = QtWidgets.QErrorMessage(parent=self)
            errorDialog.showMessage('The input string is not a valid IRI')
            errorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
            errorDialog.show()
            errorDialog.raise_()
            errorDialog.activateWindow()

    def undo(self):
        """undo the command"""
        self._project.setOntologyIRI(self._iriUndo)
        self._project.version = self._versionUndo


#############################################
#   PREFIXES
#################################
class CommandProjectAddPrefix(QtWidgets.QUndoCommand):
    """
    This command is used to add a prefix entry.
    """
    def __init__(self, project, prefix, namespace, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type name: str
        """
        super().__init__(name or 'Add prefix {0} '.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace

    def redo(self):
        """redo the command"""
        self._project.setPrefix(self._prefix,self._namespace)

    def undo(self):
        """undo the command"""
        self._project.removePrefix(self._prefix)

class CommandProjectRemovePrefix(QtWidgets.QUndoCommand):
    """
    This command is used to remove a prefix entry.
    """
    def __init__(self, project, prefix, namespace, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type name: str
        """
        super().__init__(name or 'Remove prefix {0} '.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace

    def redo(self):
        """redo the command"""
        self._project.removePrefix(self._prefix)

    def undo(self):
        """undo the command"""
        self._project.setPrefix(self._prefix,self._namespace)

class CommandProjectModifyPrefixResolution(QtWidgets.QUndoCommand):
    """
    This command is used to modify the namespace associated to a prefix.
    """
    def __init__(self, project, prefix, namespace, oldNamespace, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type oldNamespace: str
        :type name: str
        """
        super().__init__(name or 'Modify prefix {0}'.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace
        self._oldNamespace = oldNamespace

    def redo(self):
        """redo the command"""
        self._project.setPrefix(self._prefix,self._namespace)

    def undo(self):
        """undo the command"""
        self._project.setPrefix(self._prefix,self._oldNamespace)

class CommandProjectModifyNamespacePrefix(QtWidgets.QUndoCommand):
    """
    This command is used to modify the prefix associated to a namespace.
    """
    def __init__(self, project, namespace, prefix, oldPrefix, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type oldNamespace: str
        :type name: str
        """
        super().__init__(name or 'Modify prefix {0}'.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace
        self._oldPrefix = oldPrefix

    def redo(self):
        """redo the command"""
        self._project.setPrefix(self._prefix,self._namespace)

    def undo(self):
        """undo the command"""
        self._project.setPrefix(self._oldPrefix,self._namespace)

#############################################
#   ANNOTATION PROPERTIES
#################################
class CommandProjectAddAnnotationProperty(QtWidgets.QUndoCommand):
    """
    This command is used to add an annotation property entry.
    """
    def __init__(self, project, propIriStr, name=None):
        """
        Initialize the command.
        :type project: Project
        :type propIriStr: str
        :type name: str
        """
        super().__init__(name or 'Add annotation property {0} '.format(propIriStr))
        self._propIriStr = propIriStr
        self._project = project

    def redo(self):
        """redo the command"""
        self._project.addAnnotationProperty(self._propIriStr)

    def undo(self):
        """undo the command"""
        self._project.removeAnnotationProperty(self._propIriStr)

class CommandProjectRemoveAnnotationProperty(QtWidgets.QUndoCommand):
    """
    This command is used to remove an annotation property entry.
    """
    def __init__(self, project, propIriStr, name=None):
        """
        Initialize the command.
        :type project: Project
        :type propIriStr: str
        :type name: str
        """
        super().__init__(name or 'Remove annotation property {0} '.format(propIriStr))
        self._propIriStr = propIriStr
        self._project = project

    def redo(self):
        """redo the command"""
        self._project.removeAnnotationProperty(self._propIriStr)

    def undo(self):
        """undo the command"""
        self._project.addAnnotationProperty(self._propIriStr)

#TODO A REGIME METODI SOTTO CANCELLATI (TUTTI??)



class CommandProjectSetProfile(QtWidgets.QUndoCommand):
    """
    This command is used to set the profile of a project.
    """
    def __init__(self, project, undo, redo):
        """
        Initialize the command.
        :type project: Project
        :type undo: OWLProfile
        :type redo: OWLProfile
        """
        super().__init__("set project profile to '{0}'".format(redo))
        self.project = project
        self.data = {'undo': undo, 'redo': redo}

    def redo(self):
        """redo the command"""
        self.project.profile = self.project.session.createProfile(self.data['redo'], self.project)

        # Reshape all the Role and Attribute nodes to show/hide functionality and inverse functionality.
        for node in self.project.nodes():
            if node.type() in {Item.RoleNode, Item.AttributeNode}:
                node.updateNode(selected=node.isSelected())

        # Emit updated signals.
        self.project.session.sgnUpdateState.emit()
        self.project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.project.profile = self.project.session.createProfile(self.data['undo'], self.project)

        # Reshape all the Role and Attribute nodes to show/hide functionality and inverse functionality.
        for node in self.project.nodes():
            if node.type() in {Item.RoleNode, Item.AttributeNode}:
                node.updateNode(selected=node.isSelected())
                # Emit updated signals.

        # Emit updated signals.
        self.project.session.sgnUpdateState.emit()
        self.project.sgnUpdated.emit()




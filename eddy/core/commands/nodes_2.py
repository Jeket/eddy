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
from eddy.core.commands.labels import CommandLabelChange, GenerateNewLabel


class CommandProjetSetIRIPrefixesNodesDict(QtWidgets.QUndoCommand):

    def __init__(self, project, dict_old_val, dict_new_val):

        print('>>>      CommandProjetSetIRIPrefixesNodesDict  __init__')

        super().__init__('update dictionary')

        self.project = project
        self.dict_old_val = dict_old_val
        self.dict_new_val = dict_new_val

    def redo(self):
        print('>>>      CommandProjetSetIRIPrefixesNodesDict  (redo)')

        self.project.IRI_prefixes_nodes_dict.clear()
        self.project.IRI_prefixes_nodes_dict = self.project.copy_IRI_prefixes_nodes_dictionaries(self.dict_new_val,dict())
        self.project.sgnIRIPrefixNodeDictionaryUpdated.emit()

        print('>>>      CommandProjetSetIRIPrefixesNodesDict  (redo) END')

    def undo(self):
        print('>>>      CommandProjetSetIRIPrefixesNodesDict  (undo)')

        self.project.IRI_prefixes_nodes_dict.clear()
        self.project.IRI_prefixes_nodes_dict = self.project.copy_IRI_prefixes_nodes_dictionaries(self.dict_old_val,dict())
        self.project.sgnIRIPrefixNodeDictionaryUpdated.emit()

        print('>>>      CommandProjetSetIRIPrefixesNodesDict  (undo) END')


class CommandNodeSetRemainingCharacters(QtWidgets.QUndoCommand):
    def __init__(self, rc_undo, rc_redo, node, project):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        """
        super().__init__('add {0}'.format(node.name))
        self.rc_undo = rc_undo
        self.rc_redo = rc_redo
        self.node = node
        self.project = project

    def redo(self):
        """redo the command"""
        self.node.remaining_characters = self.rc_redo
        old_text = self.node.text()
        new_text = GenerateNewLabel(self.project, self.node).return_label()
        CommandLabelChange(self.node.diagram, self.node, old_text, new_text).redo()

    def undo(self):
        """undo the command"""
        self.node.remaining_characters = self.rc_undo
        new_text = self.node.text()
        old_text = GenerateNewLabel(self.project, self.node).return_label()
        CommandLabelChange(self.node.diagram, self.node, old_text, new_text).undo()
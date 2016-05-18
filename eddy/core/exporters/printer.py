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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QStandardItemModel
from PyQt5.QtWidgets import QTableView

from eddy.core.datatypes.graphol import Item
from eddy.core.exporters.pdf import PdfExporter

from eddy.lang import gettext as _


class PrinterExporter(PdfExporter):
    """
    This class can be used to print graphol projects.
    """
    def __init__(self, project, printer):
        """
        Initialize the Pdf Exporter.
        :type project: Project
        :type printer: QPrinter
        """
        super().__init__(project)
        self.printer = printer

    #############################################
    #   ELEMENTS EXPORT
    #################################

    def exportDiagrams(self):
        """
        Export all the diagrams in the current project.
        """
        for diagram in sorted(self.project.diagrams(), key=lambda x: x.name.lower()):
            if not diagram.isEmpty():
                source = diagram.visibleRect(margin=20)
                if self.newPage:
                    self.printer.newPage()
                diagram.render(self.painter, source=source)
                self.newPage = True

    def exportMetaData(self):
        """
        Export elements metadata.
        """
        metas = sorted(self.project.metas(Item.AttributeNode, Item.RoleNode), key=lambda x: x[1].lower())

        self.metamodel = QStandardItemModel()
        self.metamodel.setHorizontalHeaderLabels([
            _('META_HEADER_PREDICATE'),
            _('META_HEADER_TYPE'),
            _('META_HEADER_FUNCTIONAL'),
            _('META_HEADER_INVERSE_FUNCTIONAL'),
            _('META_HEADER_ASYMMETRIC'),
            _('META_HEADER_IRREFLEXIVE'),
            _('META_HEADER_REFLEXIVE'),
            _('META_HEADER_SYMMETRIC'),
            _('META_HEADER_TRANSITIVE')])

        # GENERATE DATA
        for entry in metas:
            meta = self.project.meta(entry[0], entry[1])
            func = self.exportFuncForItem[meta.item]
            data = func(meta)
            self.metamodel.appendRow(data)

        self.metaview = QTableView()
        self.metaview.setStyleSheet("""
        QTableView {
        border: 0;
        }
        QHeaderView {
        background: #D3D3D3;
        }""")

        self.metaview.setModel(self.metamodel)
        self.metaview.resizeColumnsToContents()
        self.metaview.resizeRowsToContents()
        self.metaview.setFixedWidth(sum(self.metaview.columnWidth(i) for i in range(self.metamodel.columnCount())))
        self.metaview.setFixedHeight(sum(self.metaview.rowHeight(i) for i in range(self.metamodel.rowCount())))
        self.metaview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.metaview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.metaview.verticalHeader().setVisible(False)

        if self.newPage:
            self.printer.newPage()

        xscale = self.printer.pageRect().width() / self.metaview.width()
        yscale = self.printer.pageRect().height() / self.metaview.height()
        self.painter.scale(min(xscale, yscale), min(xscale, yscale))
        self.metaview.render(self.painter)

    #############################################
    #   DOCUMENT GENERATION
    #################################

    def run(self):
        """
        Perform document generation.
        """
        self.painter = QPainter()
        self.painter.begin(self.printer)
        self.setCachingOff()
        self.exportDiagrams()
        self.exportMetaData()
        self.setCachingOn()
        self.painter.end()
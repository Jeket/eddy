# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


from textwrap import dedent

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout

from eddy import APPNAME, AUTHOR, VERSION, LICENSE, PROJECT_HOME
from eddy.core.datatypes.qt import Font


class AboutDialog(QDialog):
    """
    This class is used to display the 'About' dialog.
    """
    def __init__(self, parent=None):
        """
        Initialize the dialog.
        :type parent: QWidget
        """
        super().__init__(parent)

        message = dedent("""{TITLE}<br/>
        Version: {VERSION}<br/>
        Author: {AUTHOR}<br/>
        Copyright: © 2015 {AUTHOR}<br/>
        License: {LICENSE}<br/>
        Homepage: <a href="{HOMEPAGE}">{HOMEPAGE}</a>""" \
            .format(TITLE=APPNAME, VERSION=VERSION,
                    AUTHOR=AUTHOR, LICENSE=LICENSE,
                    HOMEPAGE=PROJECT_HOME))

        self.icon = QLabel(self)
        self.icon.setPixmap(QPixmap(':/images/eddy-smile'))

        self.text = QLabel(message, self)
        self.text.setWordWrap(True)
        self.text.setOpenExternalLinks(True)
        self.text.setAlignment(Qt.AlignLeft)
        self.text.setFixedWidth(340)
        self.text.setFont(Font('Arial', 13))

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.icon)
        leftLayout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        leftLayout.setContentsMargins(0, 0, 0, 0)

        rightLayout = QVBoxLayout()
        rightLayout.addWidget(self.text)
        rightLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        rightLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.addLayout(leftLayout)
        self.mainLayout.addLayout(rightLayout)

        self.setFixedWidth(520)
        self.setFixedHeight(self.sizeHint().height())
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('About {0}'.format(APPNAME))
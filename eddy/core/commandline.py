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


import textwrap

from PyQt5 import QtCore

from eddy import APPNAME


class CommandLineParser(QtCore.QCommandLineParser):
    """
    Extension of QtCore.QCommandLineParser that can parse command line options for the application.
    """
    NO_SPLASH = 'no-splash'
    OPEN = 'open'

    def __init__(self):
        """
        Initialize the CommandLineParser.
        """
        super().__init__()
        self.addHelpOption()
        self.addVersionOption()
        self.addOptions([
            QtCore.QCommandLineOption(
                [CommandLineParser.NO_SPLASH],
                'Do not show the application splash screen.'
            ),
            QtCore.QCommandLineOption(
                [CommandLineParser.OPEN],
                'Look for a project in the workspace with the given name and open it.',
                valueName=CommandLineParser.OPEN
            ),
        ])
        self.addPositionalArgument('project', 'Path to a project file to open.', '[project]')
        self.setApplicationDescription(textwrap.dedent("""
        {0}, a graphical editor for the specification and visualization of Graphol ontologies.
        """).format(APPNAME))

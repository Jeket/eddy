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


import os
import platform
import sys
import pkg_resources
import pytest

from PyQt5 import QtCore, QtWidgets

import eddy
from eddy import APPNAME, ORGANIZATION
from eddy.core.application import Eddy
from eddy.core.datatypes.system import File
from eddy.core.jvm import findJavaHome, addJVMClasspath, addJVMOptions
from eddy.core.output import getLogger


#############################################
# APPLICATION FIXTURES
#################################

@pytest.fixture(scope="session")
def qapp_args():
    """
    Overrides pytest-qt default qapp_args fixture to
    provide custom arguments for Eddy.
    """
    return [APPNAME, '--no-splash']


@pytest.yield_fixture(scope="session")
def qapp(qapp_args, tmpdir_factory):
    """
    Overrides pytest-qt default qapp fixture to provide
    an instance of Eddy.

    You can use the ``qapp`` fixture in tests which require a ``QApplication``
    to run, but where you don't need full ``qtbot`` functionality.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        global _qapp_instance
        os.environ['JAVA_HOME'] = findJavaHome() or ''

        if sys.platform.startswith('win'):
            path = os.getenv('PATH', '')
            path = path.split(os.pathsep)
            path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin'))
            if platform.architecture()[0] == '32bit':
                path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin', 'client'))
            else:
                path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin', 'server'))
            os.environ['PATH'] = os.pathsep.join(path)

        for path in pkg_resources.resource_listdir(eddy.core.jvm.__name__, 'lib'):
            if File.forPath(path) is File.Jar:
                addJVMClasspath(pkg_resources.resource_filename(eddy.core.jvm.__name__, os.path.join('lib', path)))
        # noinspection PyTypeChecker
        addJVMOptions('-ea', '-Xmx512m')

        workspace_tmpdir = tmpdir_factory.mktemp('settings')
        QtCore.QSettings.setPath(QtCore.QSettings.NativeFormat,
                                 QtCore.QSettings.UserScope,
                                 str(workspace_tmpdir))
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('workspace/home', str(workspace_tmpdir))
        settings.setValue('update/check_on_startup', False)

        _qapp_instance = Eddy(qapp_args)
        _qapp_instance.configure()
        yield _qapp_instance
    else:
        yield app


# holds a global QApplication instance created in the qapp fixture; keeping
# this reference alive avoids it being garbage collected too early
_qapp_instance = None


#############################################
# LOGGING FIXTURES
#################################

class LoggingDisabled(object):
    """
    Context manager that temporarily disable logging.

    USAGE:

    >>> with LoggingDisabled():
    >>>     # do stuff
    """
    DISABLED = False

    def __init__(self):
        self.nested = LoggingDisabled.DISABLED

    def __enter__(self):
        if not self.nested:
            Logger = getLogger()
            Logger.disabled = True
            LoggingDisabled.DISABLED = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.nested:
            Logger = getLogger()
            Logger.disabled = False
            LoggingDisabled.DISABLED = False


@pytest.fixture(scope='session')
def logging_disabled():
    """
    Fixture used to get an instance of the LoggingDisabled context manager.
    """
    yield LoggingDisabled()


#############################################
# AUTO-USE FIXTURES
#################################

@pytest.fixture(autouse=True)
def no_save_dialog(monkeypatch):
    """
    Automatically patch Session objects to override the default
    closeEvent handler, preventing it to show the save dialog.
    """
    monkeypatch.delattr('eddy.ui.session.Session.closeEvent')


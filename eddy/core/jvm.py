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

"""This module is a thin wrapper around JNI libraries and is intended to abstract the API related to the JVM support"""

import os
import sys
from enum import unique

from eddy.core.datatypes.common import Enum_
from eddy.core.functions.path import expandPath

_LINUX = sys.platform.startswith('linux')
_MACOS = sys.platform.startswith('darwin')
_WIN32 = sys.platform.startswith('win32')

_jvmLibraries = []
_jvmClasspath = []
_jvmOptions = []


@unique
class JVMJNILib(Enum_):
    JNIUS = 'jnius'
    JPYPE = 'jpype'


def isJVMAvailable():
    """
    Returns True if there is at least one avaiable JNI wrapper library.

    :rtype: bool
    """
    return len(_jvmLibraries) > 0


def getAvailableJVMLibraries():
    """
    Returns a list of available JNI wrapper libraries

    :rtype: list
    """
    return _jvmLibraries


def getJVMClasspath():
    """
    Returns the current JVM classpath
    :rtype: list
    """
    return _jvmClasspath


def addJVMClasspath(*paths):
    """
    Add the given list of paths to the JVM classpath.

    :type paths: list
    """
    _jvmClasspath.extend(paths)


def getJVMOptions():
    """
    Returns the current JVM options
    :rtype: list
    """
    return _jvmOptions


def addJVMOptions(*opts):
    """
    Add the given list of options to the JVM options.
    :type opts: list
    """
    _jvmOptions.extend(opts)


def getJavaVM(jnilib=JVMJNILib.JNIUS):
    """
    Returns a reference to a JavaVM instance based on the specified library.

    :type jnilib: JVMJNILib
    :rtype: JavaVM
    """
    try:
        if jnilib == JVMJNILib.JNIUS:
            vm = JniusJavaVM()
        elif jnilib == JVMJNILib.JPYPE:
            vm = JPypeJavaVM()
        else:
            vm = JavaVM()

        if not vm.isRunning():
            vm.addClasspath(*getJVMClasspath())
            vm.addOptions(*getJVMOptions())

        return vm
    except NameError:
        raise JVMError('No such JNI library \'{0}\''.format(jnilib))


def findJavaHome():
    """
    Locate and return the path to a valid JRE installation,
    or None if no such path can be found.

    :rtype: str
    """
    # LOOK FOR BUNDLED JRE FIRST
    if os.path.isdir(expandPath('@resources/java/')):
        return expandPath('@resources/java/')
    # TODO: BETTER ATTEMPT TO LOCATE JRE HOME
    return os.getenv('JAVA_HOME')


class JavaVM(object):
    """
    Abstract class representing the interface with the Java Virtual Machine.
    """
    _instance = None

    def __init__(self):
        """
        Creates a new JavaVM instance.
        """
        self.classpath = getattr(self, 'classpath', [])
        self.options = getattr(self, 'options', [])

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    #############################################
    #   INTERFACE
    #################################

    def initialize(self):
        """
        Initializes the JVM instance.
        """
        pass

    def getJavaClass(self, cname: str) -> object:
        """
        Returns a wrapper object representing the Java class identified by the canonical name `cname`.
        Raises an error if called before initializing the JVM.

        :type cname: str
        :rtype: object
        """
        pass

    def cast(self, destclass: object, obj: object) -> object:
        """
        Returns the given Java object `obj` casted to class `destclass`.

        :type destclass: object
        :type obj: object
        :rtype: object
        """
        pass

    def isRunning(self):
        """
        Returns `True` if a JVM instance is already running.

        :rtype: bool
        """
        pass

    def addOptions(self, *opts):
        """
        Append options to the list of JVM start-up options

        :type opts: list
        """
        self.options.extend(opts)

    def getOptions(self):
        """
        Returns the list of options used by the JVM.

        :rtype: list
        """
        return self.options

    def addClasspath(self, *paths):
        """
        Appends items to the classpath for the JVM to use.
        Replaces any existing classpath, overriding the CLASSPATH environment variable.

        :type paths: list
        """
        self.classpath.extend(paths)

    def setClasspath(self, *paths):
        """
        Sets the classpath for the JVM to use. Replaces any existing classpath,
        overriding the CLASSPATH environment variable.

        :type paths: list
        """
        self.classpath = list(paths)

    def getClasspath(self):
        """
        Retrieves the classpath the JVM will use.

        :rtype: list
        """
        return self.classpath

    def isThreadAttachedToJVM(self):
        """
        Returns True if the current python thread is attached to the JVM thread, and False otherwise.

        :rtype: bool
        """
        pass

    def attachThreadToJVM(self):
        """
        Attaches the current thread to the one running the JVM.

        Each time you create a native Python thread that uses the Java API
        you need to call this method explicitly before executing any call
        to the Java library.
        """
        pass

    def detachThreadFromJVM(self):
        """
        Detaches the current thread from the one running the JVM.

        Each time you create a native Python thread that uses the Java API
        you need to call this method explicitly before the thread terminates.
        """
        pass

    def getImplementation(self):
        """
        Returns a reference to the library implementing this API.
        """
        pass

    #############################################
    #   CONTEXT MANAGER
    #################################

    def __enter__(self):
        if not self.isRunning():
            self.initialize()
        self.attachThreadToJVM()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.isRunning():
            self.detachThreadFromJVM()


try:
    # noinspection PyUnresolvedReferences
    import jnius_config

    if hasattr(sys, 'frozen'):
        def get_classpath():
            """
            Retrieves the classpath the JVM will use.

            This function is intended to patch the default jnius_config (>1.1.0) implementation
            that makes use of pkg_resources.resource_filename to retrieve the path
            for additional Java classes inside the jnius module, which cannot be
            used when the application is frozen.
            """
            # add a path to java classes packaged with jnius
            return_classpath = [expandPath('@resources/lib/')]

            if jnius_config.classpath is not None:
                return_classpath = jnius_config.classpath + return_classpath
            elif 'CLASSPATH' in os.environ:
                return_classpath = os.environ['CLASSPATH'].split(jnius_config.split_char) + return_classpath
            else:
                return_classpath = [os.path.realpath('.')] + return_classpath
            return return_classpath

        # PATCH jnius_config IMPLEMENTATION
        jnius_config.get_classpath = get_classpath


    class JniusJavaVM(JavaVM):
        """
        Implementation of a JavaVM using pyjnius as the backend wrapper.
        """
        _instance = None

        def __init__(self):
            super().__init__()
            self.jnius = getattr(self, 'jnius', None)
            self.initialized = getattr(self, 'initialized', False)

            # If some other module has imported jnius prior
            # to the object creation, then the vm is already initialized
            # i.e. classpath and options cannot be set anymore
            if not self.initialized and jnius_config.vm_running:
                import jnius
                self.initialized = True
                self.jnius = jnius

        @classmethod
        def __new__(cls, *args, **kwargs):
            if not cls._instance:
                cls._instance = object.__new__(cls)
            return cls._instance

        #############################################
        #   INTERFACE
        #################################

        def initialize(self):
            """
            Initializes the JVM instance.
            """
            if self.initialized:
                return

            try:
                # IMPORT JNIUS TO TRIGGER CREATION OF JNIENV
                import jnius
                self.jnius = jnius
                self.initialized = True
            except BaseException as e:
                raise JVMError('Error initializing JVM instance: {0}'.format(e))

        def getJavaClass(self, cname: str) -> object:
            """
            Returns a wrapper object representing the Java class identified by the canonical name `cname`.
            Raises an error if called before initializing the JVM.

            :type cname: str
            :rtype: object
            """
            if not self.isRunning():
                raise JVMError('JVM has not been initialized yet')
            try:
                return self.jnius.autoclass(cname)
            except Exception as e:
                raise JVMClassNotFoundError('No such class {0}: {1}'.format(cname, e))

        def cast(self, destclass: object, obj: object) -> object:
            """
            Returns the given Java object `obj` casted to class `destclass`.

            :type destclass: object
            :type obj: object
            :rtype: object
            """
            return self.jnius.cast(destclass, obj)

        def addOptions(self, *opts):
            """
            Append options to the list of JVM start-up options

            :type opts: list
            """
            super().addOptions(*opts)
            try:
                jnius_config.add_options(*opts)
            except ValueError as e:
                raise JVMError(e)

        def getOptions(self):
            """
            Returns the list of options used by the JVM.

            :rtype: list
            """
            return jnius_config.get_options()

        def addClasspath(self, *paths):
            """
            Appends items to the classpath for the JVM to use.
            Replaces any existing classpath, overriding the CLASSPATH environment variable.

            :type paths: list
            """
            super().addClasspath(*paths)
            try:
                for path in paths:
                    jnius_config.add_classpath(path)
            except ValueError as e:
                raise JVMError(e)

        def setClasspath(self, *paths):
            """
            Sets the classpath for the JVM to use. Replaces any existing classpath,
            overriding the CLASSPATH environment variable.

            :type paths: list
            """
            super().setClasspath(*paths)
            try:
                jnius_config.set_classpath(*paths)
            except ValueError as e:
                raise JVMError(e)

        def getClasspath(self):
            """
            Retrieves the classpath the JVM will use.

            :rtype: list
            """
            return jnius_config.get_classpath()

        def isRunning(self):
            """
            Returns `True` if a JVM instance is already running.

            :rtype: bool
            """
            return jnius_config.vm_running

        def isThreadAttachedToJVM(self):
            """
            Returns True if the current python thread is attached to the JVM thread, and False otherwise.

            :rtype: bool
            """
            return self.isRunning()

        def detachThreadFromJVM(self):
            """
            Detaches the current thread from the one running the JVM.

            Each time you create a native Python thread that uses the Java API
            you need to call this method explicitly before the thread terminates.
            """
            if self.isRunning():
                self.jnius.detach()

        def getImplementation(self):
            """
            Returns a reference to the library implementing this API.
            """
            return self.jnius

    # ADD JNIUS TO THE AVAILABLE WRAPPERS
    _jvmLibraries.append(JVMJNILib.JNIUS)

except ImportError:
    pass

try:
    # noinspection PyUnresolvedReferences
    import jpype

    class JPypeJavaVM(JavaVM):
        """
        Implementation of a JavaVM that uses jpype as the backend wrapper.
        """
        _instance = None

        def __init__(self):
            super().__init__()
            self.jpype = getattr(self, 'jpype', jpype)
            self.initialized = getattr(self, 'initialized', False)

        def __new__(cls, *args, **kwargs):
            if not cls._instance:
                cls._instance = object.__new__(cls)
            return cls._instance

        #############################################
        #   INTERFACE
        #################################

        def initialize(self):
            """
            Initializes the JVM instance.
            """
            if self.initialized:
                return
            try:
                sep = ';' if _WIN32 else ':'
                classpath = sep.join([p for p in self.classpath])
                jpype.startJVM(jpype.getDefaultJVMPath(), '-Djava.class.path={0}'.format(classpath), *self.options)
                self.jpype = jpype
                self.initialized = True
            except RuntimeError as e:
                raise JVMError('Error initializing JVM: {0}'.format(e))

        def isRunning(self):
            """
            Returns `True` if a JVM instance is already running.

            :rtype: bool
            """
            return self.initialized and self.jpype.isJVMStarted()

        def getJavaClass(self, cname: str):
            """
            Returns a wrapper object representing the Java class identified by the canonical name `cname`.
            Raises an error if the JVM if called before initializing the JVM.

            :type cname: str
            :rtype: object
            """
            if not self.initialized:
                raise JVMError('JVM has not been initialized yet')
            try:
                splits = cname.split('.')
                ret = self.jpype.JPackage(splits[0])
                for pkg in splits[1:]:
                    ret = getattr(ret, pkg)
                return ret
            except Exception as e:
                raise JVMClassNotFoundError('No such class {0}: {1}'.format(cname, e))

        def cast(self, destclass, obj):
            """
            Returns the given Java object `obj` casted to class `destclass`.

            :type destclass: object
            :type obj: object
            :rtype: object
            """
            return obj

        def isThreadAttachedToJVM(self):
            """
            Returns True if the current python thread is attached to the JVM thread, and False otherwise.

            :rtype: bool
            """
            return self.isRunning() and self.jpype.isThreadAttachedToJVM()

        def attachThreadToJVM(self):
            """
            Attaches the current thread to the one running the JVM.

            Each time you create a native Python thread that uses the Java API
            you need to call this method explicitly before executing any call
            to the Java library.
            """
            self.jpype.attachThreadToJVM()

        def detachThreadFromJVM(self):
            """
            Detaches the current thread from the one running the JVM.

            Each time you create a native Python thread that uses the Java API
            you need to call this method explicitly before the thread terminates.
            """
            if self.jpype.isThreadAttachedToJVM():
                self.jpype.detachThreadFromJVM()
                pass

        def getImplementation(self):
            """
            Returns a reference to the library implementing this API.
            """
            return self.jpype

    # ADD JPYPE TO THE AVAILABLE WRAPPERS
    _jvmLibraries.append(JVMJNILib.JPYPE)

except ImportError:
    pass


class JVMError(RuntimeError):
    """
    Raised whenever there is an error with the JVM instance.
    """
    pass


class JVMClassNotFoundError(JVMError):
    """
    Raised whenever there a requested Java class is not found in the classpath.
    """
    pass

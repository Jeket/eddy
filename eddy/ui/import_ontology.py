import os
from urllib.parse import urlparse

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QRadioButton, QButtonGroup, QAbstractButton

from eddy.core.common import HasWidgetSystem, HasThreadingSystem
from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import first
from eddy.core.functions.signals import connect
from eddy.core.loaders.owl2 import OwlOntologyImportChecker
from eddy.core.owl import ImportedOntology
from eddy.ui.fields import StringField


class ImportOntologyDialog(QtWidgets.QDialog, HasWidgetSystem, HasThreadingSystem):
    sgnOntologyImportAccepted = QtCore.pyqtSignal(ImportedOntology)
    sgnOntologyImportCorrectlyModified = QtCore.pyqtSignal(ImportedOntology)
    sgnOntologyImportRejected = QtCore.pyqtSignal()

    VERIFICATION_THREAD_NAME = 'OWL2ImportVerification'

    def __init__(self, session, importedOntology=None):
        """
        Initialize the OWL ontology import dialog.
        :type session: Session
        :type importedOntology: ImportedOntology
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.importedOntology = importedOntology



        self.step = 0

        self.stacked = QtWidgets.QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)

        self.widgetImportType = ImportTypeWidget(self.session, self.stacked)
        self.widgetLocalImport = LocalFileWidget(self.session, self.stacked)
        connect(self.widgetLocalImport.sgnValidPath,self.onValidFilePath)
        connect(self.widgetLocalImport.sgnNotValidPath, self.onNonValidFilePath)
        self.widgetRemoteImport = WebFileWidget(self.session, self.stacked)
        connect(self.widgetRemoteImport.sgnValidURI, self.onValidURI)
        connect(self.widgetRemoteImport.sgnNotValidURI, self.onNonValidURI)
        self.widgetVerify = VerifyWidget(self.session, self.stacked)
        self.widgetConfirm = ConfirmWidget(self.session, parent=self.stacked)
        self.widgetError = ErrorWidget(self.session, parent=self.stacked)

        self.stacked.addWidget(self.widgetImportType)
        self.stacked.addWidget(self.widgetLocalImport)
        self.stacked.addWidget(self.widgetRemoteImport)
        self.stacked.addWidget(self.widgetVerify)
        self.stacked.addWidget(self.widgetConfirm)
        self.stacked.addWidget(self.widgetError)

        self.stacked.setCurrentWidget(self.widgetImportType)

        #############################################
        # CONFIRMATION AND NAVIGATION BOX
        #################################
        backBtn = QtWidgets.QPushButton('Back', objectName='back_button')
        connect(backBtn.clicked, self.onBackClicked)
        backBtn.setEnabled(False)
        self.addWidget(backBtn)
        continueBtn = QtWidgets.QPushButton('Continue', objectName='continue_button')
        connect(continueBtn.clicked, self.onContinueClicked)
        self.addWidget(continueBtn)
        saveBtn = QtWidgets.QPushButton('Save', objectName='save_button')
        saveBtn.setEnabled(False)
        self.addWidget(saveBtn)
        cancelBtn = QtWidgets.QPushButton('Cancel', objectName='cancel_button')
        self.addWidget(cancelBtn)
        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(backBtn, QtWidgets.QDialogButtonBox.ActionRole)
        confirmation.addButton(continueBtn, QtWidgets.QDialogButtonBox.ActionRole)
        confirmation.addButton(saveBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.addButton(cancelBtn, QtWidgets.QDialogButtonBox.RejectRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.stacked)
        formlayout.addRow(self.widget('confirmation_widget'))

        self.setLayout(formlayout)

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Import ontology')
        self.redraw()

    def redraw(self):
        """
        Redraw the dialog components, reloading their contents.
        """
        if self.step==0:
            self.stacked.setCurrentWidget(self.widgetImportType)
        elif self.step==1:
            if self.widgetImportType.getSelectedRadioId()==0:
                self.stacked.setCurrentWidget(self.widgetLocalImport)
            elif self.widgetImportType.getSelectedRadioId()==1:
                self.stacked.setCurrentWidget(self.widgetRemoteImport)
        elif self.step==2:
            self.stacked.setCurrentWidget(self.widgetVerify)
        elif self.step==3:
            self.stacked.setCurrentWidget(self.widgetConfirm)
        elif self.step==4:
            self.stacked.setCurrentWidget(self.widgetError)

        self.widget('back_button').setEnabled(self.isBackButtonEnabled())
        self.widget('continue_button').setEnabled(self.isContinueButtonEnabled())
        self.widget('save_button').setEnabled(self.isSaveButtonEnabled())
        self.widget('cancel_button').setEnabled(self.isCancelButtonEnabled())

    def isBackButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return not (widget is self.widgetImportType or widget is self.widgetVerify)

    def isContinueButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return widget is self.widgetImportType or (widget is self.widgetLocalImport and widget.isValidPath) or (widget is self.widgetRemoteImport and widget.isValidUri)

    def isSaveButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return widget is self.widgetConfirm

    def isCancelButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return not widget is self.widgetVerify

    def startImportVerification(self):
        checker = None
        current = self.stacked.currentWidget()
        if current is self.widgetLocalImport:
            checker = OwlOntologyImportChecker(current.pathField.value())
        elif current is self.widgetRemoteImport:
            checker = OwlOntologyImportChecker(current.uriField.value(), isLocalImport=False)
        connect(checker.sgnCompleted, self.onVerificationCompleted)
        connect(checker.sgnErrored, self.onVerificationError)
        self.redraw()
        self.startThread(self.VERIFICATION_THREAD_NAME, checker)

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        """
        Executed when the dialog is accepted.
        """
        super().reject()

    @QtCore.pyqtSlot(bool)
    def onBackClicked(self, _):
        """
        Back button pressed
        :type _: bool
        """
        if self.step==3:
            self.step -= 2
        elif self.step==4:
            self.step -=3
        else:
            self.step -= 1
        self.redraw()

    @QtCore.pyqtSlot(bool)
    def onContinueClicked(self, _):
        """
        Back button pressed
        :type _: bool
        """
        if self.step==0:
            self.step += 1
            self.redraw()
        elif self.step==1:
            self.step += 1
            self.startImportVerification()
        else:
            self.step += 1
            self.redraw()

    @QtCore.pyqtSlot()
    def onValidFilePath(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetLocalImport:
            self.widget('continue_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def onNonValidFilePath(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetLocalImport:
            self.widget('continue_button').setEnabled(False)

    @QtCore.pyqtSlot()
    def onValidURI(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetRemoteImport:
            self.widget('continue_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def onNonValidURI(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetRemoteImport:
            self.widget('continue_button').setEnabled(True)

    @QtCore.pyqtSlot(str,str,str)
    def onVerificationCompleted(self,location, ontologyIri, versionIri):
        self.widgetVerify.progressStep(0)
        self.widgetConfirm.locationText.setValue('{}'.format(location))
        self.widgetConfirm.iriText.setValue('{}'.format(ontologyIri))
        self.widgetConfirm.versionText.setValue('{}'.format(versionIri))
        self.stopThread(self.VERIFICATION_THREAD_NAME)
        self.step += 1
        self.redraw()

    @QtCore.pyqtSlot(str, Exception)
    def onVerificationError(self,location, exc):
        self.widgetVerify.progressStep(0)
        self.widgetError.locationText.setText('{}'.format(location))
        self.widgetError.problemTextArea.setPlainText('{}'.format(str(exc)))
        self.stopThread(self.VERIFICATION_THREAD_NAME)
        self.step += 2
        self.redraw()


class ImportTypeWidget(QtWidgets.QWidget):

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        self.fileSystemRadioButton = QRadioButton('Import an ontology from a local document',self)
        self.fileSystemRadioButton.setChecked(True)
        self.checkedId = 0
        self.webRadioButton = QRadioButton('Import an ontology from a document on the web',self)

        self.buttonGroup = QButtonGroup(self)
        self.buttonGroup.addButton(self.fileSystemRadioButton,id=0)
        self.buttonGroup.addButton(self.webRadioButton, id=1)
        self.buttonGroup.setExclusive(True)
        connect(self.buttonGroup.buttonClicked, self.onButtonClicked)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.fileSystemRadioButton)
        formlayout.addRow(self.webRadioButton)

        groupbox = QtWidgets.QGroupBox('Import type', self)
        groupbox.setLayout(formlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)


    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(QAbstractButton)
    def onButtonClicked(self, button):
        """
        Executed when a radio button is clicked
        """
        self.checkedId = self.buttonGroup.checkedId()

    def getSelectedRadioId(self):
        return self.buttonGroup.checkedId()

class LocalFileWidget(QtWidgets.QWidget):
    sgnValidPath = QtCore.pyqtSignal()
    sgnNotValidPath = QtCore.pyqtSignal()

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session
        self.isValidPath = False
        pathLabel = QtWidgets.QLabel(self, objectName='path_label')
        pathLabel.setText('Path')
        self.pathField = StringField(self, objectName='path_field')
        connect(self.pathField.textChanged, self.onPathFieldChanged)
        self.browseBtn = QtWidgets.QPushButton('Browse')
        self.browseBtn.setEnabled(True)
        connect(self.browseBtn.clicked, self.onBrowseClicked)
        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(pathLabel, self.pathField)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.browseBtn)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(formlayout)
        outerFormLayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Import from local document', self)
        groupbox.setLayout(outerFormLayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(str)
    def onPathFieldChanged(self, path):
        if os.path.isfile(path):
            self.isValidPath = True
            self.sgnValidPath.emit()
            self.pathField.setStyleSheet("color: black;")
        else:
            self.isValidPath = False
            self.sgnNotValidPath.emit()
            self.pathField.setStyleSheet("color: red;")

    @QtCore.pyqtSlot(bool)
    def onBrowseClicked(self,  _):
        """
        Back button pressed
        :type _: bool
        """
        self.browseBtn.setDown(False)
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setNameFilter("OWL files (*.owl)")
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            path = first(dialog.selectedFiles())
            if path:
                self.pathField.setText(path)

class WebFileWidget(QtWidgets.QWidget):
    sgnValidURI = QtCore.pyqtSignal()
    sgnNotValidURI = QtCore.pyqtSignal()

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session
        self.isValidUri = False
        uriLabel = QtWidgets.QLabel(self, objectName='uri_label')
        uriLabel.setText('URI')
        self.uriField = StringField(self, objectName='uri_field')
        connect(self.uriField.textChanged, self.onUriFieldChanged)
        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(uriLabel, self.uriField)
        groupbox = QtWidgets.QGroupBox('Import from remote document', self)
        groupbox.setLayout(formlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)


    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(str)
    def onUriFieldChanged(self, uri):
        if urlparse(uri):
            self.isValidUri = True
            self.sgnValidURI.emit()
            self.uriField.setStyleSheet("color: black;")
        else:
            self.isValidUri = False
            self.sgnNotValidURI.emit()
            self.uriField.setStyleSheet("color: red;")

class VerifyWidget(QtWidgets.QWidget):

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        # PROGRESS BAR
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        msgLabel = QtWidgets.QLabel(self)
        msgLabel.setText('Verifying ontology import....')

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(msgLabel)
        boxlayout.addWidget(self.progressBar)

        groupbox = QtWidgets.QGroupBox('Import verification', self)
        groupbox.setLayout(boxlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)

    @QtCore.pyqtSlot(int)
    def progressStep(self, step):
        self.progressBar.setValue(step)

class ConfirmWidget(QtWidgets.QWidget):

    def __init__(self, session, location='', ontIri='', versionIri='', parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        msgLabel = QtWidgets.QLabel(self)
        msgLabel.setText('The following ontology will be imported:')

        self.locationLabel = QtWidgets.QLabel(self)
        self.locationLabel.setText('Location: '.format(location))
        self.locationText = StringField(self)
        self.locationText.setValue('{}'.format(location))
        self.locationText.setReadOnly(True)

        self.iriLabel = QtWidgets.QLabel(self)
        self.iriLabel.setText('Ontology IRI: ')
        self.iriText = StringField(self)
        self.iriText.setValue('{}'.format(ontIri))
        self.iriText.setReadOnly(True)

        self.versionLabel = QtWidgets.QLabel(self)
        self.versionLabel.setText('Version IRI: ')
        self.versionText = StringField(self)
        self.versionText.setValue('{}'.format(versionIri))
        self.versionText.setReadOnly(True)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.locationLabel,self.locationText)
        formlayout.addRow(self.iriLabel,self.iriText)
        formlayout.addRow(self.versionLabel,self.versionText)
        groupbox = QtWidgets.QGroupBox(parent=self)
        groupbox.setLayout(formlayout)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(msgLabel)
        boxlayout.addWidget(groupbox)

        groupbox = QtWidgets.QGroupBox('Finalize import', self)
        groupbox.setLayout(boxlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)

class ErrorWidget(QtWidgets.QWidget):

    def __init__(self, session, location='', problemDescription='', parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        msgLabel = QtWidgets.QLabel(self)
        msgLabel.setText('Problems encountered while verifying import:')

        self.locationLabel = QtWidgets.QLabel(self)
        self.locationLabel.setText('Location: ')
        self.locationText = StringField(self)
        self.locationText.setValue('{}'.format(location))
        self.locationText.setReadOnly(True)

        self.problemLabel = QtWidgets.QLabel(self)
        self.problemLabel.setText('Problem: ')
        self.problemTextArea = QtWidgets.QPlainTextEdit(self)
        self.problemTextArea.setPlainText('{}'.format(problemDescription))
        self.problemTextArea.setReadOnly(True)
        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.locationLabel,self.locationText)
        formlayout.addRow(self.problemLabel,self.problemTextArea)
        groupbox = QtWidgets.QGroupBox(parent=self)
        groupbox.setLayout(formlayout)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(msgLabel)
        boxlayout.addWidget(groupbox)

        groupbox = QtWidgets.QGroupBox('Revision needed', self)
        groupbox.setLayout(boxlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)
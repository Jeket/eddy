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

import math
import sys

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.graphol import Special
from eddy.core.datatypes.owl import OWLAxiom, OWLSyntax
from eddy.core.datatypes.qt import Font
from eddy.core.exporters.owl2 import OWLOntologyFetcher
from eddy.core.functions.signals import connect
from eddy.core.jvm import getJavaVM
from eddy.core.output import getLogger
from eddy.core.worker import AbstractWorker

LOGGER = getLogger()


class OntologyConsistencyCheckDialog(QtWidgets.QDialog, HasThreadingSystem):
    """
    Extends QtWidgets.QDialog with facilities to perform Ontology Consistency check
    """
    sgnWork = QtCore.pyqtSignal()

    def __init__(self, project, session):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        self.project = project
        self.workerThread = None
        self.worker = None

        self.msgbox_busy = QtWidgets.QMessageBox(self, objectName='msgbox_busy')
        self.msgbox_busy.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_busy.setWindowTitle('Please Wait!')
        self.msgbox_busy.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.msgbox_busy.setText('Running reasoner  (Please Wait!)')
        self.msgbox_busy.setTextFormat(QtCore.Qt.RichText)

        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setMinimumWidth(350)
        ####################################################

        self.messageBoxLayout = QtWidgets.QVBoxLayout()
        self.messageBoxLayout.setContentsMargins(0, 6, 0, 0)
        self.messageBoxLayout.setAlignment(QtCore.Qt.AlignCenter)

        self.messageBoxLayout.addWidget(self.msgbox_busy)
        self.messageBoxLayout.addWidget(self.status_bar)

        self.messageBoxArea = QtWidgets.QWidget()
        self.messageBoxArea.setLayout(self.messageBoxLayout)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self.messageBoxArea)

        self.setLayout(self.mainLayout)

        if sys.platform.startswith('linux'):
            desktopsize = QtWidgets.QDesktopWidget().screenGeometry()
            top = (desktopsize.height() / 2) - (self.height() / 2)
            left = (desktopsize.width() / 2) - (self.width() / 2)
            self.move(left, top)

        self.setFont(Font('Roboto', 12))
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Please Wait!')
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint)
        self.hide()
        self.setWindowModality(QtCore.Qt.NonModal)
        self.show()

        ######################################################
        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)

        connect(self.sgnWork, self.doWork)
        self.sgnWork.emit()

        #self.session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Unsatisfiable_Entity_Explorer')
        #self.session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Explanation_explorer')
        self.session.BackgrounddeColourNodesAndEdges(call_updateNode=True,call_ClearInconsistentEntitiesAndDiagItemsData=True)

        connect(self.project.sgnItemAdded, self.project.reset_changes_made_after_reasoning_task)
        connect(self.project.sgnItemRemoved, self.project.reset_changes_made_after_reasoning_task)

    #############################################
    #   INTERFACE
    #################################

    def dispose(self):
        """
        Gracefully quits working thread.
        """
        if self.workerThread:
            self.workerThread.quit()
            if not self.workerThread.wait(2000):
                self.workerThread.terminate()
                self.workerThread.wait()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for SyntaxValidationDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent):
        """
        Executed when the dialog is closed.
        :type closeEvent: QCloseEvent
        """
        self.dispose()

    def showEvent(self, showEvent):
        """
        Executed whenever the dialog is shown.
        :type showEvent: QShowEvent
        """
        self.sgnWork.emit()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doWork(self):
        """
        Perform on or more advancements step in the validation procedure.
        """
        worker = OntologyConsistencyCheckWorker(self.status_bar,self.project,self.session)
        connect(worker.sgnBusy, self.displaybusydialog)
        connect(worker.sgnError, self.onErrorInExec)
        connect(worker.sgnAllOK, self.onPerfectOntology)
        connect(worker.sgnOntologyInconsistency, self.onOntologicalInconsistency)
        connect(worker.sgnUnsatisfiableEntities, self.onUnsatisfiableEntities)
        self.startThread('OntologyConsistencyCheck', worker)

    @QtCore.pyqtSlot(bool)
    def displaybusydialog(self, activate):
        if activate is True:
            pass
            #self.msgbox_busy.exec_()
            #self.close() giuliuo
        if activate is False:
            pass
            #self.msgbox_busy.close()
            #self.msgbox_busy.close() giulio

    @QtCore.pyqtSlot()
    def onErrorInExec(self):

        self.msgbox_error = QtWidgets.QMessageBox(self)
        self.msgbox_error.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_error.setWindowTitle('Error!')
        self.msgbox_error.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_error.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_error.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        self.msgbox_error.setText('An error occured, please see the LOGGER')

        if sys.platform.startswith('linux'):
            size = self.msgbox_error.size()
            desktopsize = QtWidgets.QDesktopWidget().screenGeometry()
            top = (desktopsize.height() / 2) - (size.height() / 2)
            left = (desktopsize.width() / 2) - (size.width() / 2)
            self.msgbox_error.move(left, top)

        self.close()

        self.msgbox_error.exec_()

    @QtCore.pyqtSlot()
    def onPerfectOntology(self):
        """
        Executed when ontology is perfect
        :type message: str
        """
        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        self.msgbox_done.setText('Ontology is consistent and  all classes are satisfiable')

        if sys.platform.startswith('linux'):

            size = self.msgbox_done.size()
            desktopsize = QtWidgets.QDesktopWidget().screenGeometry()
            top = (desktopsize.height()/2) - (size.height()/2)
            left = (desktopsize.width() / 2) - (size.width() / 2)
            self.msgbox_done.move(left,top)

        self.close()
        self.msgbox_done.exec_()

    @QtCore.pyqtSlot()
    def onOntologicalInconsistency(self):

        self.hide()

        dialog_2 = InconsistentOntologyDialog(self.project,None,self.session)
        dialog_2.exec_()

        self.close()

    @QtCore.pyqtSlot()
    def onUnsatisfiableEntities(self):
        """
        Executed when there is atleast 1 unsatisfiable class
        :type message: str
        """
        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        self.msgbox_done.setText('Ontology is consistent however some class(es) are unsatisfiable.\n'
                                 'See Unsatisfiable Entity Explorer for details.\n'
                                 'To reset the background colouring of the nodes in the diagram, '
                                 'press the Reset button in the toolbar')

        if sys.platform.startswith('linux'):

            size = self.msgbox_done.size()
            desktopsize = QtWidgets.QDesktopWidget().screenGeometry()
            top = (desktopsize.height()/2) - (size.height()/2)
            left = (desktopsize.width() / 2) - (size.width() / 2)
            self.msgbox_done.move(left,top)

        self.close()
        self.msgbox_done.exec_()
        #self.session.pmanager.create_add_and_start_plugin('unsatisfiable_entity_explorer')


class OntologyConsistencyCheckWorker(AbstractWorker):
    """
    Extends QtCore.QObject providing a worker thread that will perform the project Ontology Consistency check
    """
    sgnBusy = QtCore.pyqtSignal(bool)
    sgnAllOK = QtCore.pyqtSignal()
    sgnOntologyInconsistency = QtCore.pyqtSignal()
    sgnUnsatisfiableEntities = QtCore.pyqtSignal()
    sgnError = QtCore.pyqtSignal()

    def __init__(self, status_bar, project, session):
        """
        Initialize the syntax validation worker.
        :type current: int
        :type items: list
        :type project: Project
        """
        super().__init__()
        self.project = project
        self.session = session
        self.status_bar = status_bar
        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()
        self.Iterator = self.vm.getJavaClass('java.util.Iterator')
        self.String = self.vm.getJavaClass('java.lang.String')
        self.Object = self.vm.getJavaClass('java.lang.Object')
        self.Configuration = self.vm.getJavaClass('org.semanticweb.HermiT.Configuration')
        self.Reasoner = self.vm.getJavaClass('org.semanticweb.HermiT.Reasoner')
        self.ReasonerFactory = self.vm.getJavaClass('org.semanticweb.HermiT.ReasonerFactory')
        self.Explanation = self.vm.getJavaClass('org.semanticweb.owl.explanation.api.Explanation')
        self.ExplanationGenerator = self.vm.getJavaClass('org.semanticweb.owl.explanation.api.ExplanationGenerator')
        self.InconsistentOntologyExplanationGeneratorFactory = self.vm.getJavaClass('org.semanticweb.owl.explanation.impl.blackbox.checker.InconsistentOntologyExplanationGeneratorFactory')
        # self.BlackBoxExplanation = self.vm.getJavaClass('com.clarkparsia.owlapi.explanation.BlackBoxExplanation')
        self.SilentExplanationProgressMonitor = self.vm.getJavaClass('com.clarkparsia.owlapi.explanation.util.SilentExplanationProgressMonitor')
        #self.ExplanationProgressMonitor = self.vm.getJavaClass('com.clarkparsia.owlapi.explanation.util.*')
        self.DefaultExplanationGenerator = self.vm.getJavaClass('com.clarkparsia.owlapi.explanation.DefaultExplanationGenerator')
        self.OWLFunctionalSyntaxFactory = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLFunctionalSyntaxFactory')
        self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.IRI = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLAxiom')
        self.OWLClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClass')
        self.OWLClassExpression = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClassExpression')
        self.OWLDataProperty = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLDataProperty')
        self.OWLDatatype = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLDatatype')
        self.OWLEntity = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLEntity')
        self.OWLNamedIndividual = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLNamedIndividual')
        self.OWLObjectProperty = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectProperty')
        self.OWLObjectPropertyExpression = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectPropertyExpression')
        self.OWLOntology = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLOntology')
        self.OWLOntologyCreationException = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLOntologyCreationException')
        self.OWLOntologyManager = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLOntologyManager')
        #self.OWLSubClassOfAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLSubClassOfAxiom')
        self.InconsistentOntologyException = self.vm.getJavaClass('org.semanticweb.owlapi.reasoner.InconsistentOntologyException')
        self.Node = self.vm.getJavaClass('org.semanticweb.owlapi.reasoner.Node')
        self.InconsistentOntologyException_string = 'JVM exception occurred: Inconsistent ontology'

    def axioms(self):
        """
        Returns the set of axioms that needs to be exported.
        :rtype: set
        """
        return {axiom for axiom in OWLAxiom}

    @QtCore.pyqtSlot()
    def onCompleted(self):

        self.accept()

    def fetch_axioms_and_set_variables(self,bottom_entity_node,java_class):

        self.status_bar.showMessage('Ontology is inconsistent; Fetching explanations for the same')

        if java_class == self.OWLClass:
            self.status_bar.showMessage('Fetching explanations for unsatisfiable class(es)')
        elif java_class == self.OWLDataProperty:
            self.status_bar.showMessage('Fetching explanations for unsatisfiable attribute(s)')
        elif java_class == self.OWLObjectPropertyExpression:
            self.status_bar.showMessage('Fetching explanations for unsatisfiable role(s)')
        else:
            self.status_bar.showMessage('')

        entities_of_bottom_entity_node = bottom_entity_node.getEntities()
        entities_of_bottom_entity_node_itr = entities_of_bottom_entity_node.iterator()

        unsatisfiable_entities_string = []
        explanations_for_all_unsatisfiable_entities = []

        while entities_of_bottom_entity_node_itr.hasNext():
            unsatisfiable_entity = entities_of_bottom_entity_node_itr.next()

            if unsatisfiable_entity.toString() in Special.BottomEntities.value.values():
                continue

            unsatisfiable_entities_string.append(unsatisfiable_entity.toString())

            explanations_for_unsatisfiable_entity = []
            axioms_of_explanations = []

            if java_class == self.OWLClass:
                axiom_err = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(unsatisfiable_entity, self.OWLFunctionalSyntaxFactory.OWLNothing());
            elif java_class == self.OWLDataProperty:
                exists_for_some_values = self.OWLFunctionalSyntaxFactory.DataSomeValuesFrom(unsatisfiable_entity, self.OWLFunctionalSyntaxFactory.TopDatatype());
                axiom_err = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(exists_for_some_values, self.OWLFunctionalSyntaxFactory.OWLNothing());
            elif java_class == self.OWLObjectPropertyExpression:
                exists_for_some_objects = self.OWLFunctionalSyntaxFactory.ObjectSomeValuesFrom(unsatisfiable_entity, self.OWLFunctionalSyntaxFactory.OWLThing());
                axiom_err = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(exists_for_some_objects, self.OWLFunctionalSyntaxFactory.OWLNothing());
            else:
                raise RuntimeError('Invalid unsatisfiable entity {0}'.format(java_class))

            axiom_err_sc = axiom_err.getSubClass()
            explanations_raw = self.generator_unsatisfiable_entities.getExplanations(axiom_err_sc)
            explanations_raw_itr = explanations_raw.iterator()

            while (explanations_raw_itr.hasNext()):
                expl_raw = explanations_raw_itr.next()
                explanations_for_unsatisfiable_entity.append(expl_raw)
                axioms_of_expl = []
                axioms_itr = expl_raw.iterator()

                # get axioms for the explanation
                while axioms_itr.hasNext():
                    axiom_raw = axioms_itr.next()
                    axioms_of_expl.append(axiom_raw.toString())
                axioms_of_explanations.append(axioms_of_expl)
            explanations_for_all_unsatisfiable_entities.append(explanations_for_unsatisfiable_entity)

        if java_class == self.OWLClass:
            self.project.unsatisfiable_classes = unsatisfiable_entities_string
            self.project.explanations_for_unsatisfiable_classes = explanations_for_all_unsatisfiable_entities
        elif java_class == self.OWLDataProperty:
            self.project.unsatisfiable_attributes = unsatisfiable_entities_string
            self.project.explanations_for_unsatisfiable_attributes = explanations_for_all_unsatisfiable_entities
        elif java_class == self.OWLObjectPropertyExpression:
            self.project.unsatisfiable_roles = unsatisfiable_entities_string
            self.project.explanations_for_unsatisfiable_roles = explanations_for_all_unsatisfiable_entities
        else:
            raise RuntimeError('invalid unsatisfiable entity {0}'.format(java_class))

    def reason_over_ontology(self):
        self.status_bar.showMessage('Fetching ontology')

        worker = OWLOntologyFetcher(self.project, axioms=self.axioms(), normalize=False, syntax=OWLSyntax.Functional)
        worker.run()

        self.vm.attachThreadToJVM()
        errored_message = worker.errored_message
        if errored_message is not None:
            self.status_bar.showMessage(errored_message)
            self.project.inconsistent_ontology = None
            LOGGER.error(errored_message)
            return

        dict = worker.refined_axiom_to_node_or_edge
        ontology = worker.ontology

        if ontology is None:
            LOGGER.warning('ontology is None')
        else:
            LOGGER.info('ontology is not None')

        self.project.axioms_to_nodes_edges_mapping = dict
        self.project.ontology_OWL = ontology

        self.manager = self.OWLManager.createOWLOntologyManager()
        configuration = self.Configuration();
        try:
            hermit = self.Reasoner(configuration, ontology);
        except Exception as e0:
            self.project.inconsistent_ontology = None
            LOGGER.error(str(e0))
            return

        progressMonitor = self.SilentExplanationProgressMonitor()

        self.status_bar.showMessage('Running reasoner over ontology')

        try:
            hermit.precomputeInferences()

            if hermit.isConsistent() is True:
                self.project.inconsistent_ontology = False
            else:
                raise RuntimeError('ontology is inconsistent however exception was not thrown')

            factory = self.ReasonerFactory()

            self.generator_unsatisfiable_entities = self.DefaultExplanationGenerator(self.manager, factory, ontology, hermit, progressMonitor)

            #BottomClass
            bottom_class_node = hermit.getBottomClassNode();
            bottom_data_property_node = hermit.getBottomDataPropertyNode();
            bottom_object_property_node = hermit.getBottomObjectPropertyNode();
            self.fetch_axioms_and_set_variables(bottom_class_node,self.OWLClass)
            self.fetch_axioms_and_set_variables(bottom_data_property_node, self.OWLDataProperty)
            self.fetch_axioms_and_set_variables(bottom_object_property_node, self.OWLObjectPropertyExpression)
            hermit.flush();
            hermit.dispose();

        except Exception as e:
            hermit.flush();
            hermit.dispose();

            if str(e) == self.InconsistentOntologyException_string:
                self.status_bar.showMessage('Ontology is inconsistent; Fetching explanations for the same')
                self.project.inconsistent_ontology = True
                factory = self.ReasonerFactory()
                ecf = self.InconsistentOntologyExplanationGeneratorFactory(factory, 0)
                generator = ecf.createExplanationGenerator(ontology)
                axiom = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(self.OWLFunctionalSyntaxFactory.OWLThing(), self.OWLFunctionalSyntaxFactory.OWLNothing())

                try:
                    explanations = generator.getExplanations(axiom)
                    explanations_itr = explanations.iterator()

                    while explanations_itr.hasNext():
                        explanation = explanations_itr.next()
                        self.project.explanations_for_inconsistent_ontology.append(explanation)

                except Exception as ex:
                    ex.printStackTrace()
            else:
                self.project.inconsistent_ontology = None
                LOGGER.error(str(e))

    @QtCore.pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        self.reason_over_ontology()

        if self.project.inconsistent_ontology is not None:
            if self.project.inconsistent_ontology is True:
                self.sgnOntologyInconsistency.emit()
            else:
                if len(self.project.unsatisfiable_classes) or len(self.project.unsatisfiable_attributes) or len(self.project.unsatisfiable_roles):
                    self.sgnUnsatisfiableEntities.emit()
                else:
                    self.sgnAllOK.emit()

            self.finished.emit()
        else:
            self.sgnError.emit()


class InconsistentOntologyDialog(QtWidgets.QDialog, HasThreadingSystem):
    sgnWork = QtCore.pyqtSignal()

    def __init__(self, project, path, session):
        super().__init__(session)
        self.msgbox_done = QtWidgets.QMessageBox(self, objectName='msgbox_done')
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_done.setText('Ontology is inconsistent.\n The link(s) for the explanation(s) are displayed below.\n' \
                                 'You may choose to display one explanation at a time in the Explanation Explorer ' \
                                 'in the bottom-right portion of the screen.\n' \
                                 'To reset the background colouring of the nodes in the diagram, press the Reset button in the toolbar')
        self.messageBoxLayout = QtWidgets.QHBoxLayout()
        self.messageBoxLayout.setContentsMargins(0, 6, 0, 0)
        self.messageBoxLayout.setAlignment(QtCore.Qt.AlignCenter)
        #self.messageBoxLayout.addWidget(self.widget('msgbox_done'))
        self.messageBoxLayout.addWidget(self.msgbox_done)

        self.messageBoxArea = QtWidgets.QWidget()
        self.messageBoxArea.setLayout(self.messageBoxLayout)

        self.confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmation.addButton(QtWidgets.QDialogButtonBox.Close)
        self.confirmation.setFont(Font('Roboto', 12))
        self.confirmation.setObjectName('confirmation')

        connect(self.confirmation.rejected, self.close)

        #self.addWidget(self.confirmation)

        self.confirmationLayout = QtWidgets.QHBoxLayout()
        self.confirmationLayout.setContentsMargins(0, 0, 0, 0)
        #self.confirmationLayout.addWidget(self.widget('confirmation'), 0, QtCore.Qt.AlignCenter)
        self.confirmationLayout.addWidget(self.confirmation)

        self.confirmationArea = QtWidgets.QWidget()
        self.confirmationArea.setLayout(self.confirmationLayout)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self.messageBoxArea)
        self.mainLayout.addWidget(self.confirmationArea)

        self.setLayout(self.mainLayout)
        self.setFont(Font('Roboto', 12))
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Ontology consistency check complete')

        #self.setWindowFlags(QtCore.Qt.Window) no full screen option

        if sys.platform.startswith('linux'):
            size = self.size()
            desktopsize = QtWidgets.QDesktopWidget().screenGeometry()
            top = (desktopsize.height()/2) - (size.height()/2)
            left = (desktopsize.width() / 2) - (size.width() / 2)
            self.move(left,top)

        self.hide()
        self.setWindowModality(QtCore.Qt.NonModal)
        self.show()

        self.project = project
        self.session = session
        self.setLayout(self.mainLayout)
        #self.session.pmanager.create_add_and_start_plugin('explanation_explorer')
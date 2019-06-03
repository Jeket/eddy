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
import pytest

from eddy.core.datatypes.owl import OWLSyntax, OWLAxiom
from eddy.core.exporters.graphml import GraphMLDiagramExporter
from eddy.core.exporters.owl2 import OWLOntologyExporterWorker
from eddy.core.exporters.pdf import PdfDiagramExporter
from eddy.core.functions.fsystem import fread
from eddy.core.functions.path import expandPath
from eddy.ui.session import Session


@pytest.fixture
def session(qapp, qtbot, logging_disabled):
    """
    Provide an initialized Session instance.
    """
    with logging_disabled:
        session = Session(qapp, expandPath('@tests/test_project_1'))
        session.show()
    qtbot.addWidget(session)
    qtbot.waitExposed(session, timeout=3000)
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(session.project.diagram('diagram'))
    yield session


#############################################
#   GRAPHML EXPORT
#################################

def test_export_diagram_to_graphml(session, qtbot, tmpdir):
    # GIVEN
    graphml = tmpdir.join('diagram.graphml')
    project = session.project
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(project.diagram('diagram'))
    # WHEN
    worker = GraphMLDiagramExporter(session.mdi.activeDiagram(), session)
    worker.run(str(graphml))
    # THEN
    assert os.path.isfile(str(graphml))


#############################################
#   PDF EXPORT
#################################

def test_export_diagram_to_pdf(session, qtbot, tmpdir):
    # GIVEN
    pdffile = tmpdir.join('diagram.pdf')
    project = session.project
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(project.diagram('diagram'))
    # WHEN
    worker = PdfDiagramExporter(session.mdi.activeDiagram(), session,
                                diagrams=[session.mdi.activeDiagram()])
    worker.run(str(pdffile))
    # THEN
    assert os.path.isfile(str(pdffile))


#############################################
#   OWL EXPORT
#################################

def test_export_project_to_owl_without_normalization(session, tmpdir):
    # WHEN
    owlfile = tmpdir.join('test_project_1.owl')
    project = session.project
    worker = OWLOntologyExporterWorker(project, str(owlfile),
                                       axioms={x for x in OWLAxiom},
                                       normalize=False,
                                       syntax=OWLSyntax.Functional)
    worker.run()
    # THEN
    assert os.path.isfile(str(owlfile))
    # WHEN
    content = list(filter(None, fread(str(owlfile)).split('\n')))
    # THEN
    assert 'Prefix(owl:=<http://www.w3.org/2002/07/owl#>)' in content
    assert 'Prefix(rdf:=<http://www.w3.org/1999/02/22-rdf-syntax-ns#>)' in content
    assert 'Prefix(xml:=<http://www.w3.org/XML/1998/namespace>)' in content
    assert 'Prefix(xsd:=<http://www.w3.org/2001/XMLSchema#>)' in content
    assert 'Prefix(rdfs:=<http://www.w3.org/2000/01/rdf-schema#>)' in content
    assert 'Prefix(test:=<http://www.dis.uniroma1.it/~graphol/test_project#>)' in content
    assert 'Ontology(<http://www.dis.uniroma1.it/~graphol/test_project>' in content
    assert 'Declaration(Class(test:Vegetable))' in content
    assert 'Declaration(Class(test:Person))' in content
    assert 'Declaration(Class(test:Male))' in content
    assert 'Declaration(Class(test:Female))' in content
    assert 'Declaration(Class(test:Mother))' in content
    assert 'Declaration(Class(test:Father))' in content
    assert 'Declaration(Class(test:Underage))' in content
    assert 'Declaration(Class(test:Adult))' in content
    assert 'Declaration(Class(test:Vehicle))' in content
    assert 'Declaration(Class(test:Less_than_50_cc))' in content
    assert 'Declaration(Class(test:Over_50_cc))' in content
    assert 'Declaration(NamedIndividual(test:Bob))' in content
    assert 'Declaration(NamedIndividual(test:Alice))' in content
    assert 'Declaration(NamedIndividual(test:Trudy))' in content
    assert 'Declaration(ObjectProperty(test:hasAncestor))' in content
    assert 'Declaration(ObjectProperty(test:hasParent))' in content
    assert 'Declaration(ObjectProperty(test:hasFather))' in content
    assert 'Declaration(ObjectProperty(test:hasMother))' in content
    assert 'Declaration(ObjectProperty(test:isAncestorOf))' in content
    assert 'Declaration(ObjectProperty(test:drives))' in content
    assert 'Declaration(DataProperty(test:name))' in content
    assert 'Declaration(Datatype(xsd:string))' in content
    assert 'AnnotationAssertion(rdfs:comment test:Person "A human being"^^xsd:string)' in content
    assert 'SubClassOf(test:Person ObjectSomeValuesFrom(test:hasAncestor owl:Thing))' in content
    assert 'SubClassOf(test:Father test:Male)' in content
    assert 'SubClassOf(test:Mother test:Female)' in content
    assert 'SubClassOf(test:Underage ObjectAllValuesFrom(test:drives test:Less_than_50_cc))' in content
    assert 'SubObjectPropertyOf(test:hasParent test:hasAncestor)' in content
    assert 'SubObjectPropertyOf(test:hasFather test:hasParent)' in content
    assert 'SubObjectPropertyOf(test:hasMother test:hasParent)' in content
    assert 'FunctionalObjectProperty(test:hasFather)' in content
    assert 'FunctionalObjectProperty(test:hasMother)' in content
    assert 'DataPropertyRange(test:name xsd:string)' in content
    assert 'DataPropertyDomain(test:name test:Person)' in content
    assert 'InverseObjectProperties(test:hasAncestor test:isAncestorOf)' in content
    assert 'ObjectPropertyAssertion(test:isAncestorOf test:Bob test:Alice)' in content
    assert 'ObjectPropertyRange(test:hasAncestor test:Person)' in content
    assert 'ObjectPropertyRange(test:hasFather test:Father)' in content
    assert 'ObjectPropertyRange(test:hasMother test:Mother)' in content
    assert 'ObjectPropertyRange(test:drives test:Vehicle)' in content
    assert 'NegativeObjectPropertyAssertion(test:isAncestorOf test:Bob test:Trudy)' in content
    assert ')' in content
    # AND
    assert 'SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasAncestor) owl:Thing) test:Person)' not in content
    assert 'SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasMother) owl:Thing) test:Mother)' not in content
    assert 'SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasFather) owl:Thing) test:Father)' not in content
    # AND
    assert any([line in content for line in
                ['EquivalentClasses(test:Person ObjectUnionOf(test:Underage test:Adult))',
                 'EquivalentClasses(test:Person ObjectUnionOf(test:Adult test:Underage))',
                 'EquivalentClasses(ObjectUnionOf(test:Underage test:Adult) test:Person)',
                 'EquivalentClasses(ObjectUnionOf(test:Adult test:Person) test:Person)']])
    assert any([line in content for line in
                ['EquivalentClasses(test:Person DataSomeValuesFrom(test:name rdfs:Literal))',
                 'EquivalentClasses(DataSomeValuesFrom(test:name rdfs:Literal) test:Person)']])
    assert any([line in content for line in
                ['EquivalentClasses(test:Person ObjectUnionOf(test:Female test:Male))',
                 'EquivalentClasses(test:Person ObjectUnionOf(test:Male test:Female))',
                 'EquivalentClasses(ObjectUnionOf(test:Female test:Male) test:Person)',
                 'EquivalentClasses(ObjectUnionOf(test:Male test:Female) test:Person)']])
    assert any([line in content for line in
                ['EquivalentClasses(test:Vehicle ObjectUnionOf(test:Less_than_50_cc test:Over_50_cc))',
                 'EquivalentClasses(test:Vehicle ObjectUnionOf(test:Over_50_cc test:Less_than_50_cc))',
                 'EquivalentClasses(ObjectUnionOf(test:Less_than_50_cc test:Over_50_cc) test:Vehicle)',
                 'EquivalentClasses(ObjectUnionOf(test:Over_50_cc test:Less_than_50_cc) test:Vehicle)']])
    assert any([line in content for line in
                ['EquivalentClasses(test:Person ObjectAllValuesFrom(test:drives owl:Thing))',
                 'EquivalentClasses(ObjectAllValuesFrom(test:drives owl:Thing) test:Person)',]])
    assert any([line in content for line in
                ['DisjointClasses(test:Female test:Male)',
                 'DisjointClasses(test:Male test:Female)']])
    assert any([line in content for line in
                ['DisjointClasses(test:Person test:Vegetable)',
                 'DisjointClasses(test:Vegetable test:Person)']])
    assert any([line in content for line in
                ['DisjointClasses(test:Underage test:Adult)',
                 'DisjointClasses(test:Adult test:Underage)']])
    assert any([line in content for line in
                ['DisjointClasses(test:Less_than_50_cc test:Over_50_cc)',
                 'DisjointClasses(test:Over_50_cc test:Less_than_50_cc)']])
    # AND
    assert len(content) == 59


def test_export_project_to_owl_with_normalization(session, tmpdir):
    # WHEN
    owlfile = tmpdir.join('test_project_1.owl')
    project = session.project
    worker = OWLOntologyExporterWorker(project, str(owlfile),
                                       axioms={x for x in OWLAxiom},
                                       normalize=True,
                                       syntax=OWLSyntax.Functional)
    worker.run()
    # THEN
    assert os.path.isfile(str(owlfile))
    # WHEN
    content = list(filter(None, fread(str(owlfile)).split('\n')))
    # THEN
    assert 'Prefix(owl:=<http://www.w3.org/2002/07/owl#>)' in content
    assert 'Prefix(rdf:=<http://www.w3.org/1999/02/22-rdf-syntax-ns#>)' in content
    assert 'Prefix(xml:=<http://www.w3.org/XML/1998/namespace>)' in content
    assert 'Prefix(xsd:=<http://www.w3.org/2001/XMLSchema#>)' in content
    assert 'Prefix(rdfs:=<http://www.w3.org/2000/01/rdf-schema#>)' in content
    assert 'Prefix(test:=<http://www.dis.uniroma1.it/~graphol/test_project#>)' in content
    assert 'Ontology(<http://www.dis.uniroma1.it/~graphol/test_project>' in content
    assert 'Declaration(Class(test:Vegetable))' in content
    assert 'Declaration(Class(test:Person))' in content
    assert 'Declaration(Class(test:Male))' in content
    assert 'Declaration(Class(test:Female))' in content
    assert 'Declaration(Class(test:Mother))' in content
    assert 'Declaration(Class(test:Father))' in content
    assert 'Declaration(Class(test:Underage))' in content
    assert 'Declaration(Class(test:Adult))' in content
    assert 'Declaration(Class(test:Vehicle))' in content
    assert 'Declaration(Class(test:Less_than_50_cc))' in content
    assert 'Declaration(Class(test:Over_50_cc))' in content
    assert 'Declaration(NamedIndividual(test:Bob))' in content
    assert 'Declaration(NamedIndividual(test:Alice))' in content
    assert 'Declaration(NamedIndividual(test:Trudy))' in content
    assert 'Declaration(ObjectProperty(test:hasAncestor))' in content
    assert 'Declaration(ObjectProperty(test:hasParent))' in content
    assert 'Declaration(ObjectProperty(test:hasFather))' in content
    assert 'Declaration(ObjectProperty(test:hasMother))' in content
    assert 'Declaration(ObjectProperty(test:isAncestorOf))' in content
    assert 'Declaration(ObjectProperty(test:drives))' in content
    assert 'Declaration(DataProperty(test:name))' in content
    assert 'Declaration(Datatype(xsd:string))' in content
    assert 'AnnotationAssertion(rdfs:comment test:Person "A human being"^^xsd:string)' in content
    assert 'SubClassOf(test:Person ObjectSomeValuesFrom(test:hasAncestor owl:Thing))' in content
    assert 'SubClassOf(test:Father test:Male)' in content
    assert 'SubClassOf(test:Mother test:Female)' in content
    assert 'SubClassOf(test:Person DataSomeValuesFrom(test:name rdfs:Literal))' in content
    assert 'SubClassOf(test:Female test:Person)' in content
    assert 'SubClassOf(test:Male test:Person)' in content
    assert 'SubClassOf(test:Underage test:Person)' in content
    assert 'SubClassOf(test:Adult test:Person)' in content
    assert 'SubClassOf(test:Less_than_50_cc test:Vehicle)' in content
    assert 'SubClassOf(test:Over_50_cc test:Vehicle)' in content
    assert 'SubClassOf(test:Underage ObjectAllValuesFrom(test:drives test:Less_than_50_cc))' in content
    assert 'SubClassOf(test:Person ObjectAllValuesFrom(test:drives owl:Thing))' in content
    assert 'SubClassOf(ObjectAllValuesFrom(test:drives owl:Thing) test:Person)' in content
    assert 'SubObjectPropertyOf(test:hasParent test:hasAncestor)' in content
    assert 'SubObjectPropertyOf(test:hasFather test:hasParent)' in content
    assert 'SubObjectPropertyOf(test:hasMother test:hasParent)' in content
    assert 'FunctionalObjectProperty(test:hasFather)' in content
    assert 'FunctionalObjectProperty(test:hasMother)' in content
    assert 'DataPropertyRange(test:name xsd:string)' in content
    assert 'DataPropertyDomain(test:name test:Person)' in content
    assert 'InverseObjectProperties(test:hasAncestor test:isAncestorOf)' in content
    assert 'ObjectPropertyAssertion(test:isAncestorOf test:Bob test:Alice)' in content
    assert 'ObjectPropertyRange(test:hasAncestor test:Person)' in content
    assert 'ObjectPropertyRange(test:hasFather test:Father)' in content
    assert 'ObjectPropertyRange(test:hasMother test:Mother)' in content
    assert 'ObjectPropertyRange(test:drives test:Vehicle)' in content
    assert 'NegativeObjectPropertyAssertion(test:isAncestorOf test:Bob test:Trudy)' in content
    assert ')' in content
    # AND
    assert 'SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasAncestor) owl:Thing) test:Person)' not in content
    assert 'SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasMother) owl:Thing) test:Mother)' not in content
    assert 'SubClassOf(ObjectSomeValuesFrom(ObjectInverseOf(test:hasFather) owl:Thing) test:Father)' not in content
    assert 'SubClassOf(DataSomeValuesFrom(test:name rdfs:Literal) test:Person)' not in content
    # AND
    assert any([line in content for line in
                ['SubClassOf(test:Person ObjectUnionOf(test:Underage test:Adult))',
                 'SubClassOf(test:Person ObjectUnionOf(test:Adult test:Underage))']])
    assert any([line in content for line in
                ['SubClassOf(test:Person ObjectUnionOf(test:Female test:Male))',
                 'SubClassOf(ObjectUnionOf(test:Female test:Male) test:Person)']])
    assert any([line in content for line in
                ['SubClassOf(test:Vehicle ObjectUnionOf(test:Less_than_50_cc test:Over_50_cc))',
                 'SubClassOf(test:Vehicle ObjectUnionOf(test:Over_50_cc test:Less_than_50_cc))']])
    assert any([line in content for line in
                ['DisjointClasses(test:Female test:Male)',
                 'DisjointClasses(test:Male test:Female)']])
    assert any([line in content for line in
                ['DisjointClasses(test:Person test:Vegetable)',
                 'DisjointClasses(test:Vegetable test:Person)']])
    assert any([line in content for line in
                ['DisjointClasses(test:Underage test:Adult)',
                 'DisjointClasses(test:Adult test:Underage)']])
    assert any([line in content for line in
                ['DisjointClasses(test:Less_than_50_cc test:Over_50_cc)',
                 'DisjointClasses(test:Over_50_cc test:Less_than_50_cc)']])
    # AND
    assert len(content) == 66
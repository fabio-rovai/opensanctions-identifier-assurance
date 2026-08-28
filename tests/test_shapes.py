import rdflib, pathlib
from pyshacl import validate
R = pathlib.Path(__file__).resolve().parent.parent
def test_shapes_fire_on_collisions_silent_on_clean():
    data = rdflib.Graph()
    for f in ['ontology/resolution-assurance.ttl','skos/schemes.ttl','shapes/instances.ttl']:
        data.parse(R/f, format='turtle')
    sh = rdflib.Graph(); sh.parse(R/'shapes/resolution-shapes.ttl', format='turtle')
    conforms, rg, _ = validate(data, shacl_graph=sh, advanced=True)
    SH=rdflib.Namespace('http://www.w3.org/ns/shacl#')
    results=list(rg.subjects(rdflib.RDF.type, SH.ValidationResult))
    assert not conforms
    assert len(results)==11
    assert not any('clean' in str(rg.value(r,SH.focusNode) or '') for r in results)

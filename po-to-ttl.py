import polib
import pyewts
from opencc import OpenCC
import glob
from rdflib import URIRef, Literal, BNode, Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD
from operator import itemgetter, attrgetter

EWTSCONV = pyewts.pyewts()
CCT2S = OpenCC('t2s')

PREFIXMAP = {
    "http://purl.bdrc.io/resource/": "bdr",
    "http://purl.bdrc.io/ontology/core/": "bdo",
    "http://purl.bdrc.io/admindata/": "bda",
    "http://purl.bdrc.io/ontology/admin/": "adm",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.w3.org/2004/02/skos/core#": "skos"
}

BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")
BDA = Namespace("http://purl.bdrc.io/admindata/")
ADM = Namespace("http://purl.bdrc.io/ontology/admin/")

NSM = NamespaceManager(Graph())
NSM.bind("bdr", BDR)
NSM.bind("bdo", BDO)
NSM.bind("bda", BDA)
NSM.bind("adm", ADM)
NSM.bind("skos", SKOS)
NSM.bind("rdfs", RDFS)

OVERWRITE = False

def botoewts(unistr):
    res = EWTSCONV.toWylie(unistr)
    #if warns:
    #    print("warnings in the EWTS to Unicode transformation:")
    #    print("transforming: %s" % ewtsstr)
    #    print(warns)
    return res

def get_pofile_from_file(path):
    print("get data from %s" % path)
    return polib.pofile(path, check_for_duplicates=True)
    
def qname_to_res(qname):
    for longuri, prefix in PREFIXMAP.items():
        if qname.startswith(prefix+":"):
            return URIRef(longuri+qname[len(prefix)+1:])
    return None

def add_translation(g, msgid, msgstr):
    if msgstr == "":
        return
    parts = msgid.split("::")
    if (len(parts) < 2):
        print("error: cannot split "+msgid)
        return
    s = qname_to_res(parts[0])
    p = qname_to_res(parts[1])
    o = Literal(botoewts(msgstr), lang="bo-x-ewts")
    g.add((s,p,o))

def get_graph_from_file(path):
    g = Graph()
    g.namespace_manager = NSM
    pofile = get_pofile_from_file(path)
    for e in pofile:
        add_translation(g, e.msgid, e.msgstr)
    return g

if __name__ == "__main__":
    coreg = get_graph_from_file("transifex-output/core_bo.po")
    admg =  get_graph_from_file("transifex-output/adm_bo.po")
    coreg.serialize("transifex-output/core_bo.ttl", format="turtle")
    admg.serialize("transifex-output/adm_bo.ttl", format="turtle")
import polib
import pyewts
from opencc import OpenCC
import glob
from rdflib import URIRef, Literal, BNode, Graph
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD

EWTSCONV = pyewts.pyewts()
CCT2S = OpenCC('t2s')

PO_NAME_TO_TTL_PATH = {
    "core": ["core/bdo.ttl", "core/unknown-entities.ttl", "roles/creators.ttl", "types/*.ttl"],
    "adm": ["adm/admin.ttl", "adm/content_providers.ttl", "adm/legal_entities.ttl", "adm/types/access_types.ttl", "adm/types/license_types.ttl", "adm/types/status_types.ttl"]
}

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

def ewtstobo(ewtsstr):
    warns = []
    res = EWTSCONV.toUnicode(ewtsstr, warns)
    #if warns:
    #    print("warnings in the EWTS to Unicode transformation:")
    #    print("transforming: %s" % ewtsstr)
    #    print(warns)
    return res

def hanttohans(hantstr):
    return CCT2S.convert(hantstr)

LANGS = ["bo", "en", "zhhans"]

LT_TO_FILESUFFIX = {
    "bo": {"suffix": "bo"},
    "en": {"suffix": "en"},
    "zh-hans": {"suffix": "zhhans"},
    "bo-x-ewts": {"suffix": "bo", "fun": lambda x: ewtstobo(x)},
    "zh-hant": {"suffix": "zhhans", "fun": lambda x: hanttohans(x)},
}

def update_all():
    for poname, ttlpathlist in PO_NAME_TO_TTL_PATH.items():
        ttlfiles = get_all_files_from_globlist(ttlpathlist)
        polist = {}
        for l in LANGS:
            popath = "po/%s_%s.po"  % (poname, l)
            podata = get_podata_from_file(popath)
            polist[l] = podata
        for ttlpath in ttlfiles:
            m = get_model_from_file(ttlpath)
            if not m:
                print("error: cannot get model from %s" % ttlpath)
                continue
            add_model_to_polist(m, ttlpath, polist)
        for l, podata in polist.items():
            popath = "po/%s_%s.po"  % (poname, l)
            save_po(podata["pofile"], popath)

def get_all_files_from_globlist(globlist):
    res = []
    for g in globlist:
        res += glob.glob('owl-schema/'+g)
    return res

def get_podata_from_file(path):
    pofile = polib.pofile(path)
    entrymap = {}
    for e in pofile:
        entrymap[e.msgid] = e
    return {"pofile": pofile, "entrymap": entrymap}

def get_model_from_file(path):
    g = Graph()
    g.parse(path, format="ttl")
    return g

def add_model_to_polist(model, ttlpath, polist):
    resources = set()
    for s,p,o in model.triples( (None,  SKOS.prefLabel, None) ):
        resources.add(s)
    for s,p,o in model.triples( (None,  RDFS.label, None) ):
        resources.add(s)
    for res in resources:
        add_res_to_polist(res, model, ttlpath, polist)

def shorten_uri(uri):
    for longuri, prefix in PREFIXMAP.items():
        if uri.startswith(longuri):
            return prefix+':'+uri[len(longuri):]
    return None
    

def add_res_to_polist(res, model, ttlpath, polist):
    resshort = shorten_uri(res)
    # don't consider resources outside the common namespaces
    if not resshort:
        return
    comment = ""
    # no ontology labels
    for s,p,o in model.triples( (res, RDF.type , OWL.Ontology) ):
        return
    # no deprecated resources
    for s,p,o in model.triples( (res, OWL.deprecated , None) ):
        return
    for s,p,o in model.triples( (res, ADM.translationPriority , None) ):
        return
    for s,p,o in model.triples( (res, OWL.equivalentClass , None) ):
        return
    for s,p,o in model.triples( (res, RDFS.comment , None) ):
        if not o.language or o.language != "en":
            continue
        val = o.value.strip()
        # we only want single line comments
        if val.count('\n') > 0:
            continue
        comment = val
        break
    for s,p,o in model.triples( (res, RDFS.seeAlso , None) ):
        if comment:
            comment += "\n"
        comment += "see also: %s" % o
    triplesmap = {"skos:prefLabel": [], "rdfs:label": []}
    for s,p,o in model.triples( (res, SKOS.prefLabel , None) ):
        triplesmap["skos:prefLabel"].append(o)
    for s,p,o in model.triples( (res, RDFS.label , None) ):
        triplesmap["rdfs:label"].append(o)
    for shortp, olist in triplesmap.items():
        for o in olist:
            lang = o.language
            if not lang:
                continue
            lang = lang.lower()
            if lang not in LT_TO_FILESUFFIX:
                continue
            msgid = resshort + '_' + shortp
            value = o.value
            posuffix = LT_TO_FILESUFFIX[lang]["suffix"]
            if "fun" in LT_TO_FILESUFFIX[lang]:
                value = LT_TO_FILESUFFIX[lang]["fun"](value)
            podata = polist[posuffix]
            poentry = None
            poentryalreadypresent = False
            if msgid in podata["entrymap"]:
                poentry = podata["entrymap"][msgid]
                poentryalreadypresent = True
            else:
                poentry = polib.POEntry(msgid=msgid)
            if comment:
                poentry.comment = comment
            poentry.msgctxt = res
            # removing "owl-schema/"
            poentry.occurrences = [(ttlpath[11:], "")]
            if not poentryalreadypresent or not OVERWRITE:
                poentry.msgstr = value
            if msgid not in podata["entrymap"]:
                podata["entrymap"][msgid] = poentry
                podata["pofile"].append(poentry)

def save_po(po, path):
    po.save(path)

if __name__ == "__main__":
    update_all()
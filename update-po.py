import polib
import pyewts
from opencc import OpenCC
import glob
from rdflib import URIRef, Literal, BNode, Graph
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD
from operator import itemgetter, attrgetter

EWTSCONV = pyewts.pyewts()
CCT2S = OpenCC('t2s')

PO_NAME_TO_TTL_PATH = {
    "core": ["core/bdo.ttl", "roles/creators.ttl", "types/*.ttl"],
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

SUFFIXES = ["_bo", "_en", "_zhhans", ""]

LT_TO_FILESUFFIX = {
    "bo": {"suffix": "_bo"},
    "en": {"suffix": "_en"},
    "zh-hans": {"suffix": "_zhhans"},
    "bo-x-ewts": {"suffix": "_bo", "fun": lambda x: ewtstobo(x)},
    "zh-hant": {"suffix": "_zhhans", "fun": lambda x: hanttohans(x)},
}

def update_all():
    for poname, ttlpathlist in PO_NAME_TO_TTL_PATH.items():
        ttlfiles = get_all_files_from_globlist(ttlpathlist)
        polist = {}
        for s in SUFFIXES:
            popath = "po/%s.pot" % poname
            if s:
                popath = "po/%s%s.po"  % (poname, s)
            podata = get_podata_from_file(popath)
            polist[s] = podata
        for ttlpath in ttlfiles:
            m = get_model_from_file(ttlpath)
            if not m:
                print("error: cannot get model from %s" % ttlpath)
                continue
            add_model_to_polist(m, ttlpath, polist)
        for s, podata in polist.items():
            popath = "po/%s.pot" % poname
            if s:
                popath = "po/%s%s.po"  % (poname, s)
            save_po(podata, popath)

def get_all_files_from_globlist(globlist):
    res = []
    for g in globlist:
        res += glob.glob('owl-schema/'+g)
    return res

def get_podata_from_file(path):
    print("get data from %s" % path)
    pofile = polib.pofile(path, check_for_duplicates=True)
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

def addlabeltolabelmap(prop, o, labelsmap):
    lang = o.language.lower()
    suffix = LT_TO_FILESUFFIX[lang]["suffix"]
    if "fun" in LT_TO_FILESUFFIX[lang]:
        value = LT_TO_FILESUFFIX[lang]["fun"](o.value)
        labelsmap[prop][suffix].append(value)
    else:
        labelsmap[prop][suffix].append(o)


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
    comments = []
    for s,p,o in model.triples( (res, RDFS.comment , None) ):
        if not o.language or o.language != "en":
            continue
        val = o.value.strip()
        # we only want single line comments (do we?)
        if val.count('\n') > 0:
            continue
        comments.append(val)
    for s,p,o in model.triples( (res, ADM.userTooltip , None) ):
        if not o.language or o.language != "en":
            continue
        val = o.value.strip()
        # we only want single line comments (do we?)
        if val.count('\n') > 0:
            continue
        comments.append(val)
    comments = sorted(comments)
    for c in comments:
        if comment:
            comment += "\n"
        comment += c
    seealsos = []
    for s,p,o in model.triples( (res, RDFS.seeAlso , None) ):
        seealsos.append(o)
    seealsos = sorted(seealsos)
    for seealso in seealsos:
        if comment:
            comment += "\n"
        comment += "see also: %s" % seealso
    labelsmap = {"skos:prefLabel": {}, "rdfs:label": {}, "adm:userTooltip": {}}
    # initialize with a table containing all the interesting SUFFIXES:
    for s in SUFFIXES:
        for p, v in labelsmap.items():
            v[s] = []
    otherlabels = []
    for s,p,o in model.triples( (res, SKOS.prefLabel , None) ):
        if not o.language or o.language not in LT_TO_FILESUFFIX:
            otherlabels.append(o.value)
            continue
        addlabeltolabelmap("skos:prefLabel", o, labelsmap)
    for s,p,o in model.triples( (res, RDFS.label , None) ):
        otherlabels.append(o.value)
        if not o.language or o.language not in LT_TO_FILESUFFIX:
            continue
        addlabeltolabelmap("rdfs:label", o, labelsmap)
    for s,p,o in model.triples( (res, ADM.userTooltip , None) ):
        otherlabels.append(o.value)
        if not o.language or o.language not in LT_TO_FILESUFFIX:
            continue
        addlabeltolabelmap("adm:userTooltip", o, labelsmap)
    for s,p,o in model.triples( (res, SKOS.altLabel , None) ):
        otherlabels.append(o.value)
    for shortp, suffixtolabel in labelsmap.items():
        # if all the suffixes are empty for the property, let's ignore it:
        hasData = False
        for suffix, labels in suffixtolabel.items():
            if len(labels) > 0:
                hasData = True
                break
        if not hasData:
            continue
        msgid = resshort + '::' + shortp
        value = o.value
        for suffix, labels in suffixtolabel.items():    
            podata = polist[suffix]
            poentryalreadypresent = False
            if len(labels) == 0 and suffix:
                # no untranslated strings in .po files
                continue
            if msgid in podata["entrymap"]:
                poentry = podata["entrymap"][msgid]
                poentryalreadypresent = True
            else:
                poentry = polib.POEntry(msgid=msgid)
                podata["pofile"].append(poentry)
                podata["entrymap"][msgid] = poentry
            if not suffix:
                if comment:
                    poentry.comment = comment
                poentry.msgctxt = res
                # removing "owl-schema/"
                poentry.occurrences = [(ttlpath[11:], "")]
                poentry.msgstr = ""
            else:
                if len(labels) > 0:
                    if not poentryalreadypresent or not OVERWRITE or not poentry.msgstr:
                        poentry.msgstr = labels[0]
                    if comment:
                        poentry.comment = comment
                if len(labels) > 1:
                    print("abnormal number of labels in %s for %s (%s)" % (suffix, resshort, shortp))

def save_po(podata, path):
    #print(path)
    #print(podata["entrymap"])
    sortedentries = list(podata["entrymap"].values())
    sortedentries = sorted(sortedentries, key=attrgetter('msgid'))
    pofile = podata["pofile"]
    pofile.entries = sortedentries
    print("saving %d strings in %s" % (len(podata["entrymap"]), path))
    pofile.save(path)

if __name__ == "__main__":
    update_all()
# Localization of the Buddhist Digital Ontology

## Installation

```
pip3 install -r requirements.txt
```

If the above gives an error you may need to:
```
pip3 install -U setuptools
```

On the first git clone it may be necesary to:
```
git submodule update --init
```
When there is a change in the owl-schema, after the initial config above, the following may be used to sync to the head of the owl-schema repo:
```
git submodule update --recursive --remote
```
## Usage

The `.po` files produced by `update-po.py` are expected to be used with a service such as [Transifex](https://www.transifex.com/).

```
curl -X PUT -H Content-Type:text/turtle -T transifex-output/core_bo.ttl -G http://buda1.bdrc.io:13180/fuseki/corerw/data --data-urlencode 'graph=http://purl.bdrc.io/graph/trans_core_bo'
curl -X PUT -H Content-Type:text/turtle -T transifex-output/adm_bo.ttl -G http://buda1.bdrc.io:13180/fuseki/corerw/data --data-urlencode 'graph=http://purl.bdrc.io/graph/trans_adm_bo'
```

## Copyright

The Python code is:

Copyright (C) 2019 Buddhist Digital Resource Center and is under the [Apache License v2.0](LICENSE).

The translations in the .po files are under the same license as the [Buddhist Digital Ontology](https://github.com/buda-base/owl-schema): 

Copyright (C) 2019 Buddhist Digital Resource Center, distributed under the [CC0 1.0 Universal (CC0 1.0) Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/deed).

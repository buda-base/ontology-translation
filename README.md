# Localization of the Buddhist Digital Ontology

## Installation

```
pip3 install -r requirements.txt
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

## Copyright

The Python code is:

Copyright (C) 2019 Buddhist Digital Resource Center and is under the [Apache License v2.0](LICENSE).

The translations in the .po files are under the same license as the [Buddhist Digital Ontology](https://github.com/buda-base/owl-schema): 

Copyright (C) 2019 Buddhist Digital Resource Center, distributed under the [CC0 1.0 Universal (CC0 1.0) Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/deed).

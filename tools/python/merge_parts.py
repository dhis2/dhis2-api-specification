#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

@author: philld
"""

import requests
import json

endpointsfile="./../docs/input/endpoints_via_doclet.json"
schemafile="../../docs/input/schemas_api.json"
endpointslist="../../docs/input/endpoints_combo.txt"
specbase="../../docs/spec/openapi_base.json"
specfile="../../docs/spec/openapi.json"
pathsfile="../../docs/input/paths.json"
tagsfile="../../docs/input/tags.json"

#
ofile=open(specbase,'r')
openapi = json.load(ofile)
ofile.close()

pfile=open(pathsfile,'r')
paths = json.load(pfile)
pfile.close()
tfile=open(tagsfile,'r')
tags = json.load(tfile)
tfile.close()

sfile=open(schemafile,'r')
schemas = json.load(sfile)
sfile.close()


apifile= open(specfile,'w')
openapi["components"]["schemas"].update(schemas)
openapi["paths"].update(paths)
openapi["tags"] =tags
apifile.write(json.dumps(openapi , sort_keys=True, indent=2, separators=(',', ': ')))
apifile.close()





#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

@author: philld
"""

import requests
import json
import copy
from dhis2api.explorer import specsorter

# specfile="schema_out.json"
# outfile="schema_out.json"


specfile="../../docs/spec/src/metadata_paths_openapi.json"
outfile="../../docs/spec/src/assertible_paths_openapi.json"


ofile=open(specfile,'r')

openapi = json.load(ofile)
ofile.close()



def recurseList(l,p):
    #print(p)
    for v in l:
        if isinstance(v, dict):
            if "x-name" in v:
                nP = p + "_n-" + v["x-name"]
                recurseDict(v,nP)
            else:
                if "name" in v:
                    nP = p + "_n-" + v["name"]
                    recurseDict(v,nP)
        else:
            if isinstance(v, list):
                nP = p + "_"+v
                recurseList(v,nP)

def recurseDict(d,p):
    # print("__", p)

    myItems = copy.deepcopy(d)
    for k, v in myItems.items():
        if isinstance(v, dict):
            nP = p+"_"+k
            if k in ["post", "put", "delete"]:
                print(p,k)
                try:
                    del d[k]
                except KeyError:
                    pass
            else:
                recurseDict(d[k],nP)
        else:
            if isinstance(v, list):
                nP = p+ "_"+k
                recurseList(d[k],nP)


recurseDict(openapi,"ROOT")

ss = specsorter(openapi)
openapi_sorted = ss.sortspec()

apifile= open(outfile,'w')
apifile.write(json.dumps(openapi_sorted , sort_keys=True, indent=2, separators=(',', ': ')))
apifile.close()

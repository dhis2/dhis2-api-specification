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


specfile="../../docs/spec/src/components_openapi.json"
outfile="../../docs/spec/src/components_c_openapi.json"


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
    #print(p)
    for k, v in d.items():
        if isinstance(v, dict):
            if k in ["favorite", "favorites"]:
                # print(p,"dict__",k,v)
                if k == "favorite":
                    d[k] = {"type": "boolean"}
                if k == "favorites":
                    d[k]["items"] = {'$ref': '#/components/schemas/favorite'}
            else:
                nP = p+"_"+k
                recurseDict(v,nP)
        else:
            if isinstance(v, list):
                if k in ["favorite", "favorites"]:
                    print("list__",k,v)
                nP = p+ "_"+k
                recurseList(v,nP)
            else:
                if k in ["favorite", "favorites"]:
                    print("none__",k,v)



recurseDict(openapi,"ROOT")

ss = specsorter(openapi)
openapi_sorted = ss.sortspec()

apifile= open(outfile,'w')
apifile.write(json.dumps(openapi_sorted , sort_keys=True, indent=2, separators=(',', ': ')))
apifile.close()

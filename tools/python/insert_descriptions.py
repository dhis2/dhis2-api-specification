#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

@author: philld
"""

import requests
import json

specfile="../../docs/spec/newbase_openapi.json"
#docsfile="../../docs/input/web_api.cm"

docsfile="/home/philld/reps/dhis2-markdown-docs/src/commonmark/en/content/developer/web-api.md"


ofile=open(specfile,'r')

openapi = json.load(ofile)
ofile.close()

docfile = open(docsfile, "r") 
docs = docfile.read() 
docfile.close()

def between(value, a, b):
    # Find and validate before-part.
    pos_a = value.find(a)
    if pos_a == -1: return ""
    # Find and validate after part.
    pos_b = value.rfind(b)
    if pos_b == -1: return ""
    # Return middle part.
    adjusted_pos_a = pos_a + len(a)
    if adjusted_pos_a >= pos_b: return ""
    return value[adjusted_pos_a:pos_b]

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
            nP = p+"_"+k
            recurseDict(v,nP)
        else:
            if isinstance(v, list):
                nP = p+ "_"+k
                recurseList(v,nP)
            else:
                if k == "description":
                    tagS= "<!-- API+"+p+" -->"
                    tagE= "<!-- API-"+p+" -->"
                    text = between(docs,tagS,tagE)
                    if text != "":
                        text = "<!-- auto-inserted: do not edit here -->"+text
                        d.update({"description":text})



recurseDict(openapi,"DESC")

apifile= open(specfile,'w')
apifile.write(json.dumps(openapi , sort_keys=False, indent=2, separators=(',', ': ')))
apifile.close()




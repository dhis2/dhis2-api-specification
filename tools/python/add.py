#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

@author: philld
"""

import requests
import json

specfile="../../docs/spec/openapi.json"
pathsfile="../../docs/input/paths.json"
tagsfile="../../docs/input/tags.json"

types = {   "BOOLEAN" : [{ "type": "boolean", "format": "boolean"},"",""],
            "COLLECTION" : [{ "type": "array", "items": "<FILLIN>"},"minItems","maxItems"],
            "COLOR" : [{ "type": "string", "format": "COLOR"},"",""],
            "COMPLEX" : [{ "type": "object", "format": "<FILLIN>"},"",""],
            "CONSTANT" : [{ "type": "string"},"",""],
            "DATE" : [{ "type": "string", "format": "date"},"minLength","maxLength"],
            "EMAIL" : [{ "type": "string", "format": "boolean"},"minLength","maxLength"],
            "GEOLOCATION" : [{ "type": "string", "format": "geolication"},"minLength","maxLength"],
            "IDENTIFIER" : [{ "type": "string", "format": "uid"},"minLength","maxLength"],
            "INTEGER" : [{ "type": "string", "format": "integer"},"minimum","maximum"],
            "NUMBER" : [{ "type": "string", "format": "double"},"minimum","maximum"],
            "PASSWORD" : [{ "type": "string", "format": "password"},"minLength","maxLength"],
            "PHONENUMBER" : [{ "type": "string", "format": "phone number"},"minLength","maxLength"],
            "REFERENCE" : [{ "type": "string", "format": "uid"},"minLength","maxLength"],
            "TEXT" : [{ "type": "string"},"minLength","maxLength"],
            "URL" : [{ "type": "string", "format": "url"},"minLength","maxLength"]
        }


ofile=open(specfile,'r')
openapi = json.load(ofile)
ofile.close()

pfile=open(pathsfile,'r')
paths = json.load(pfile)
pfile.close()
tfile=open(tagsfile,'r')
tags = json.load(tfile)
tfile.close()

for h in openapi:
    print(h)
    for i in openapi[h]:
        try:
            for s in openapi[h][i]:
                openapi[h][i][s].update({"x-status-dhis2": "template"})
        except:
            print("BANG!")




apifile= open(specfile,'w')
apifile.write(json.dumps(openapi , sort_keys=True, indent=2, separators=(',', ': ')))
apifile.close()





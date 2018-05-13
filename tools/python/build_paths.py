#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

@author: philld
"""

import requests
import json



# r_schemas = requests.get("https://play.dhis2.org/dev/api/schemas.json",auth=('system','System123'))
# ofile=open("/home/philld/api/examples/redoc/openapi.json",'r')
# openapi = json.load(ofile)
# ofile.close()
pfile=open("/home/philld/api/doclets/spring-mvc-api-doclet/fullIndex3.json",'r')
pathapi = json.load(pfile)
pfile.close()

pp = []
for p in pathapi:
    pp += [p]

countmatched = 0
countmissed = 0

sfile=open("/home/philld/api/examples/redoc/schemas_api.json",'r')
schemas = json.load(sfile)
sfile.close()

ss = {}
for s in schemas:
    ss.update({s.lower():  s})

print(ss)

paths = {}
tags = []

allfile=open("/home/philld/dhis2/api/endpoints/endpoints_combo.txt",'r')
for line in allfile:
    endp = line.rstrip()
    tag = endp.replace("{","").split("/")[1]
    tagentry = '{"description":"","name":"' + tag + '","x-status":"draft"}'
    if tagentry not in tags:
        tags.append(tagentry)

    path = {}

    if endp in pp:
        for m in pathapi[endp]:
            method = m["method"].lower()
            requestBody = {}
            if method == "get" and endp == ("/" + tag):
                thisSchema = tag.title().rstrip('s').lower()
                print(thisSchema)
                if thisSchema in ss:
                    ref = {"$ref": ("#/components/schemas/" + ss[thisSchema])}
                    requestBody = {"required":True,"content":{"application/json":{"schema":{"allOf":[ref]}}}}
                else:
                    requestBody = {"required":True,"content":{"application/json":{"schema":{}}}}
            mbody = {"description":m["description"],"tags":[tag],"requestBody": requestBody}
            params = []
            if len(m["pathVariables"]) > 0:
                for v in m["pathVariables"]:
                    params.append({"name":v,"in":"path"})
            mbody.update({"parameters":(params + m["requestParams"])})

            path.update({method:mbody})
    else:
        method = "get"
        requestBody = {}
        if endp == ("/" + tag):
            thisSchema = tag.title().rstrip('s').lower()
            if thisSchema in ss:
                ref = {"$ref": ("#/components/schemas/" + ss[thisSchema])}
                requestBody = {"required":True,"content":{"application/json":{"schema":{"allOf":[ref]}}}}
            else:
                requestBody = {"required":True,"content":{"application/json":{"schema":{}}}}
        mbody = {"description":m["description"],"tags":[tag],"requestBody": requestBody}
        params = []
        mbody.update({"parameters":(params)})

        path.update({method:mbody})

    paths.update({endp:path})  

allfile.close()


pathsfile= open("/home/philld/api/examples/redoc/paths2.json",'w')
pathsfile.write(json.dumps(paths , sort_keys=True, indent=2, separators=(',', ': ')))
pathsfile.close()


tagsfile= open("/home/philld/api/examples/redoc/tags2.json",'w')
tagsfile.write("[")
sep= ""
for t in sorted(tags):
    tagsfile.write(sep+t)
    sep = ","
tagsfile.write("]")
tagsfile.close()
    
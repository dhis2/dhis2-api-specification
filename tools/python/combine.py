#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

@author: philld
"""

import requests
import json

base="../../docs/spec/"
src="../../docs/spec/src/"

specs=[
    {"base":"metadata_base_openapi.json", "output":"metadata_openapi.json"},
    {"base":"assertible_base_openapi.json", "output":"assertible_openapi.json"},
]

for spec in specs:
    specfile=src+spec["base"]
    combifile=base+spec["output"]

    def replaceRefs(spec):
        for p in spec:
            if "$ref" in spec[p]:
                ref=(spec[p]["$ref"]).strip('./').split('#/')
                f=ref[0]
                part=ref[1]
                tfile=open(src+f)
                spec[p] = json.load(tfile)[part]
                tfile.close()
            elif isinstance(spec[p], dict):
                replaceRefs(spec[p])

    ofile=open(specfile,'r')
    openapi = json.load(ofile)
    ofile.close()

    replaceRefs(openapi)

    jout=json.dumps(openapi , sort_keys=True, indent=2, separators=(',', ': '))
    # jout=jout.replace("#/parameters","#/components/parameters")
    # jout=jout.replace("#/schemas","#/components/schemas")
    jout=jout.replace("./components_openapi.json#","#")

    apifile= open(combifile,'w')
    apifile.write(jout)
    apifile.close()

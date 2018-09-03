#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

@author: philld
"""

import requests
import json
import copy

endpointsfile="./../docs/input/endpoints_via_doclet.json"
schemabase="../../docs/input/schemas.json"
schemafile="../../docs/input/schemas_api.json"
endpointslist="../../docs/input/endpoints_combo.txt"
specbase="../../docs/spec/openapi_base.json"
specfile="../../docs/spec/openapi.json"
pathsfile="../../docs/input/paths.json"
tagsfile="../../docs/input/tags.json"

def f(x):
    return {
        "BOOLEAN" : [{ "type": "boolean", "format": "boolean"},"minLength","maxLength"],
        "COLLECTION" : [{ "type": "array"},"minItems","maxItems"],
        "COLOR" : [{ "type": "string", "format": "COLOR"},"",""],
        "COMPLEX" : [{ "type": "object", "format": "<FILLIN>"},"minLength","maxLength"],
        "CONSTANT" : [{ "type": "string"},"","maxLength"],
        "DATE" : [{ "type": "string", "format": "date-time"},"minLength","maxLength"],
        "EMAIL" : [{ "type": "string", "format": "boolean"},"minLength","maxLength"],
        "GEOLOCATION" : [{ "type": "string", "format": "geolocation"},"minLength","maxLength"],
        "IDENTIFIER" : [{ "type": "string", "format": "uid"},"minLength","maxLength"],
        "INTEGER" : [{ "type": "string", "format": "integer"},"minimum","maximum"],
        "NUMBER" : [{ "type": "string", "format": "double"},"minimum","maximum"],
        "PASSWORD" : [{ "type": "string", "format": "password"},"minLength","maxLength"],
        "PHONENUMBER" : [{ "type": "string", "format": "phone number"},"minLength","maxLength"],
        "REFERENCE" : [{ "type": "string", "format": "uid"},"minLength","maxLength"],
        "TEXT" : [{ "type": "string"},"minLength","maxLength"],
        "URL" : [{ "type": "string", "format": "url"},"minLength","maxLength"]
    }[x]


r_schemas = requests.get("https://play.dhis2.org/dev/api/schemas.json",auth=('system','System123'))

sfile=open(schemafile,'r')
r_schemas = json.load(sfile)
sfile.close()

schemas = {}

for s in r_schemas.json()["schemas"]:
    n = s["name"]
    line = 0
    #if hasattr(s,"apiEndpoint"):
    try:
        #print("Endpoint:     ",s["apiEndpoint"].replace("https://play.dhis2.org/dev/api/",""))
        schemas.update({n : {"properties":{},"required":[],"x-status-dhis2":"template"}})

        for p in s["properties"]:
            props = {}
            propertyType = p["propertyType"]
            props = f(propertyType)
            endName = p["name"]
            endMin = props[1]
            endMax = props[2]
            print("========================= ",n,":",endName)
            print(-1, p["propertyType"], props[0])

            print(p["propertyType"])
            if p["readable"] == True:
                schemas[n]["properties"].update({endName:props[0]})

                print(0, p["propertyType"], props[0])

                line = 1
                if "itemPropertyType" in p:
                    print(1, p["itemPropertyType"], props[0])
                    if p["itemPropertyType"] == "COMPLEX":
                        iprops = {}
                        for s in r_schemas.json()["schemas"]:
                            if s["name"].lower() == endName.lower() or s["name"].lower() == endName.rstrip('s').lower():
                                iprops = {"schema": {"$ref":"#/components/schemas/"+s["name"]}}
                    else:    
                        itemPropertyType = p["itemPropertyType"]
                        iprops = f(itemPropertyType)

                line = 1.5
                if p["propertyType"] == "COLLECTION":
                    print(2, p["itemPropertyType"], props[0])
                    schemas[n]["properties"][endName].update({"items": iprops })

                line = 2
                if "min" in p:
                    schemas[n]["properties"][endName].update({endMin: p["min"]})
                line = 3
                if "max" in p:
                    schemas[n]["properties"][endName].update({endMax: p["max"]})
                line = 4
                if "length" in p:
                    schemas[n]["properties"][endName].update({endMax: p["length"]})
                line = 5
                if "constants" in p:
                    schemas[n]["properties"][endName].update({"enum": p["constants"]})
                #print(p["required"])
                line = 6
                if p["required"] == True:
                    schemas[n]["required"].append(endName)

                line = 7
                if p["writable"] == True:
                    schemas[n]["properties"][endName].update({"readOnly": False})
                else:
                    schemas[n]["properties"][endName].update({"readOnly": True})

       
        #print("href: ",s["href"],"\n")
    except KeyError:
        print("keyerror:",line)
        #print("href: ",s["href"],"\n")
    
#print(json.dumps(schemas , sort_keys=True, indent=2, separators=(',', ': ')))

apifile= open("/home/philld/api/examples/redoc/schemas_api.json",'w')
apifile.write(json.dumps(schemas , sort_keys=True, indent=2, separators=(',', ': ')))
apifile.close()





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


specfile="../../docs/spec/output_openapi.json"
outfile="../../docs/spec/output_c_openapi.json"


ofile=open(specfile,'r')

openapi = json.load(ofile)
ofile.close()


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



def chooseObjects(a,b,interactive=False):
    ret = 0
    retcodes = ["a","b","s","w", "r"]
    while ret not in retcodes:
        aKeys = list(a.keys())
        bKeys = list(b.keys())
        combKeys = aKeys+bKeys
        sCombkeys = list(set(combKeys))
        sCombkeys.sort()
        cnt = 0
        selector = '{:>20} {:>20} {:>20}   {}\n'.format("key", "a", "b", "row")
        for k in sCombkeys:
            av = ""
            bv = ""
            cnt+=1
            if k in aKeys:
                av = a[k]
            if k in bKeys:
                bv = b[k]
            try:
                selector+= '{:>20} {:>20} {:>20}   [{}]\n'.format(k, av, bv, cnt)
            except TypeError:
                return "s"
        selector += '\na - use a | b - use b | r - replace a with b | s - skip | w - write file (save) | [1-{}] - swap rows\n : '.format(cnt)
        if interactive:
            ret = input(selector)
        else:
            ret = "b"
        if ret not in retcodes:
            swapKey = sCombkeys[int(ret)-1]
            print("swapping",swapKey)
            ao = a.pop(swapKey,None)
            bo = b.pop(swapKey,None)
            if ao != None:
                b[swapKey] = ao
            if bo != None:
                a[swapKey] = bo
    return ret


def makeRef(d,props,kp,k):
    #bob += " "+ kp + ":" + myProps[kp]["type"]
    if "$ref" not in props[kp].keys():
        if  props[kp]["type"] not in ["object","array"]:

            # check if the property is already described in a schema
            if kp in d["components"]["schemas"]:
                # there is a schema for someting with that name. Check if properties are the same
                if d["components"]["schemas"][kp] == props[kp]:
                    # It matches both the schema and the properties - use it as the ref
                    props[kp] = {"$ref":"#/components/schemas/"+kp}
                else:
                    # The name exists but properties don't match
                    # Determine whether to use the old, new, or modified
                    print('\n______________________ {} [{}]'.format(kp, k))
                    choice = "s"
                    choice = chooseObjects(d["components"]["schemas"][kp],props[kp])
                    if choice == "a":
                        # use the original
                        props[kp] = {"$ref":"#/components/schemas/"+kp}
                    if choice == "r":
                        # make a new one
                        d["components"]["schemas"][kp] = copy.deepcopy(props[kp])
                        props[kp] = {"$ref":"#/components/schemas/"+kp}
                    if choice == "b":
                        # make a new one
                        d["components"]["schemas"][kp+"_"+k] = props[kp]
                        props[kp] = {"$ref":"#/components/schemas/"+kp+"_"+k}
                    if choice == "w":
                        # write to the output file (save)
                        apifile= open(outfile,'w')
                        apifile.write(json.dumps(d , sort_keys=False, indent=2, separators=(',', ': ')))
                        apifile.close()

            else:
                # there is no existing schema, so add it
                d["components"]["schemas"][kp] = props[kp]



def recurseDict(d):
    myItems = copy.deepcopy(d["components"]["schemas"])
    for k in myItems.keys():
        #bob = ""
        try:
            myProps = d["components"]["schemas"][k]["properties"]
            for kp in myProps.keys():
                makeRef( d, myProps, kp,k)
        except KeyError:
            pass

        # write to the output file (save)
        apifile= open(outfile,'w')
        apifile.write(json.dumps(d , sort_keys=True, indent=2, separators=(',', ': ')))
        apifile.close()



recurseDict(openapi)

ss = specsorter(openapi)
openapi_sorted = ss.sortspec()

apifile= open(outfile,'w')
apifile.write(json.dumps(openapi_sorted , sort_keys=True, indent=2, separators=(',', ': ')))
apifile.close()

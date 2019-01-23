#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 15:34:25 2018

Copyright (c) 2018, University of Oslo
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of the HISP project nor the names of its contributors may
  be used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

@author: philld
"""

import requests
import json
import sys, re
import logging
import random
from pprint import pprint
from datetime import datetime
import copy


class component:
    """
    This is a model for the endpoint item.
    It is initialised from a schema.
    """

    def __init__(self, schema, reference, rnd_seed=None):
        self.schema = schema
        self.reference = reference
        self.mode = ""
        self.uid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.name_chars = "abcdefghijklmnopqrstuvwxyz       ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.users = ["GOLswS44mh8","xE7jOejl9FI"]

        self.functions = {
            "array": self.array_component ,
            "object": self.object_component ,
            "integer": self.integer_component ,
            "boolean": self.boolean_component,
            "number": self.number_component,
            "string": self.string_component
        }
        self.location=[]
        self.payload={}
        self.required={}
        self.readonly={}
        self.random_gen=random.Random()
        self.random_gen2=random.Random()
        self.reseed(rnd_seed)
        self.setcounter = {}
        # print("init schema")
        # pprint(schema['items']['properties']['lastUpdatedBy'])
        # pprint(reference['components']['schemas']['attribute']['properties']['lastUpdatedBy'])


    def reseed(self,rnd_seed):
        self.random_gen.seed(rnd_seed)
        self.random_gen2.seed(datetime.now().microsecond)

    def set_attributes(self,alist,attribute, val="true"):
        """
        we need to map the attribute list, with items in the form
         "<level1>:<level2>:..." (with one or more levels/names)
        to the structure like
         schema['items']['properties'][<level1>]['items']['properties'][<level2>]...
        The last "level" is the item we want to apply the attribute to
        """
        # create a "moving" reference to the schema
        schema_part = self.schema['items']

        # print("set_attributes:",alist,attribute,val)
        # pprint(schema_part)

        # loop over the list of items
        for a_item in alist:
            # Keep track of how many times we've been asked to set this value.
            # If we hit 10 times, set the value to readOnly
            try:
                self.setcounter[a_item] = self.setcounter[a_item] + 1
            except KeyError:
                self.setcounter[a_item] = 1
            if self.setcounter[a_item] > 9:
                attribute = "readOnly"
                val = True
                

            u_exists = True
            # drill down through the "levels" (separated by ":")
            for level in a_item.split(':'):
                schema_parent = schema_part
                try:
                    int(level)
                except ValueError:
                    try:
                        schema_part2 = schema_part['properties']
                    except KeyError:
                        schema_part2 = schema_part['items']['properties']

                try:
                    schema_part = schema_part2[level]
                except KeyError:
                    u_exists = False

            # print("update IN")
            # pprint(schema_part)

            if attribute == "required":
                try:
                    if a_item not in schema_parent["required"]:
                        schema_parent["required"].append(a_item)
                except KeyError:
                    schema_parent["required"] = [a_item]
                    #pprint(schema_parent)
                self.add_requirement(attribute)
            # If the attribute is "unique" we can rule out that the object is an enum
            elif attribute == "unique" and u_exists:
                try:
                    if schema_part["format"] == "enum":
                        # change it to general
                        schema_part["format"] = "general"
                        del schema_part["enum"]
                    schema_part.update({attribute: val})
                except KeyError:
                    pass

            elif attribute == "invalid":
                print("<<<<<<<<<<<<delete "+level)
                #pprint(schema_part2)
                del schema_part2[level]
                #pprint(schema_part2)


            else:
                schema_part.update({attribute: val})


            # print("update OUT")
            # pprint(schema_part)

            # reset the schema
            schema_part = self.schema['items']
            # print("update OUT")
            # pprint(schema_part)

        #pprint(self.schema)

    def clear_required(self,schema=None):
        if schema == None:
            schema = self.schema
        self._clearRDict(schema)

    def _clearRList(self,a):
        #print(p)
        cnt=0
        for v in a:
            try:
                if isinstance(v, dict):
                    self._clearRDict(a[cnt])
                elif isinstance(v, list):
                        self._clearRList(a[cnt])
            except (KeyError, IndexError):
                pass
            cnt+=1


    def _clearRDict(self,a):
        for k, v in a.items():
            if k == "required":
                a[k].clear()
            else:
                try:
                    if isinstance(v, dict):
                        self._clearRDict(a[k])
                    elif isinstance(v, list):
                        self._clearRList(a[k])
                except KeyError:
                    pass

    def get_required(self):
        return self.required

    def print_schema(self):
        #print((json.dumps(self.schema , sort_keys=True, indent=2, separators=(',', ': '))))
        pprint(self.schema)

    def get_schema(self):
        return self.schema

    def set_schema(self,schema):
        self.schema = schema
        #print("set_schema")
        #pprint(schema['properties']["lastUpdatedBy"])
        #pprint(schema)

    def add_requirement(self,name):
        self.required[name] = "REQUIRED"
        #print(name,"required")

    def remove_requirement(self,name):
        self.required[name] = "NOT_REQUIRED"

    def get_payload(self):
        return self.payload

    def create_payload(self,mode):
        # generate an example payload
        # compatible with the model schema
        self.mode=mode

        #loop over the schema
        func = self.functions[self.schema['type']]
        # print("in")
        # pprint(self.schema)
        payload=func(self.schema,"",self.random_gen)
        #print("out")
        self.payload = payload
        #return payload

    def consolidate_minmax(self,schema,minName,maxName):
        max = (2**31)-1
        min = 0
        s = copy.deepcopy(schema)
        for m in s:
            if not s[m]:
                s[m] = 0
            if m in ["min","minimum","minLength","minItems","minProperties"]:
                # print(m,s[m],min)
                if s[m] > min:
                    min = s[m]
                del schema[m]
            if m in ["max","maximum","maxLength","maxItems","maxProperties","maxDefault"]:
                # print(m,s[m],max)
                if float(s[m]) < float(max):
                    max = s[m]
                del schema[m]

        schema[minName] = min
        schema[maxName] = max


    def array_component(self,schema,name,rnd_gen):
        self.location.append(name)
        # print('/'.join(self.location))
        self.consolidate_minmax(schema,"minItems","maxItems")

        ret = []
        array_schema = False

        if len(schema) > 1:
            try:
                # print("PALD 01")
                # print("items_type:", schema['items']['type'])
                func = self.functions[schema['items']['type']]
            except KeyError:
                func = self.functions["object"]
                # print("PALD 02")
                pass
            except TypeError:
                func = self.functions["array"]
                pass

            try:
                if schema['x-association'] == "true":
                    # print("array ASSOCIATION:",name)
                    # pprint(schema)
                    # pass the association tag to the children
                    schema['items']['x-association'] = "true"
            except KeyError:
                pass

            try:
                for _ in range(1):
                    # print("PALD 03")
                    ret.append(func(schema['items'],"items",self.random_gen))
                    # print("PALD 04")
            except KeyError:
                # print("error creating payload!")
                pass



        self.location.pop()
        return ret

    def object_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        self.consolidate_minmax(schema,"minProperties","maxProperties")

        # dereference any ref objects
        # print("here 1")
        try:
            # pprint(schema)
            for s in schema["schema"]:
                schema[s] = copy.deepcopy(schema["schema"][s])
            del schema["schema"]
        except KeyError:
            pass
        try:
            # print("here 2")
            # pprint(schema)
            ref_schema = self.reference
            for r in schema["$ref"].split('/')[1:]:

                # print("here 3",r)
                ref = ref_schema[r]
                ref_schema = copy.deepcopy(ref)
            for r in ref_schema:

                # print("here 4",r)
                schema[r] = ref_schema[r]
            del schema["$ref"]
        except KeyError:
            pass



        ret = {}
            #print("-REMOVE REQUIRED: ",schema['required'])
        try:
            for p in schema['properties']:
                # print("  |",self.location, p)

                # as a workaround for "anyOf" just take the last option
                try:
                    if 'anyOf' in schema['properties'][p]:
                        print("FOUND ANYOF - assuming last one")
                        schema['properties'][p] = schema['properties'][p]['anyOf'][-1]
                        # pprint(schema['properties'][p])
                except:
                    print("keyerror FOUND ANYOF")
                    pass

                if self.mode == "full":
                    try:
                        func = self.functions[schema['properties'][p]['type']]
                        ret.update({p:func(schema['properties'][p],p,self.random_gen)})
                    except KeyError:
                        # print("full mode key error")
                        pass
                #is it required according to the schema?
                if self.mode == "required":
                    try:
                        for r in schema['required']:
                            if r == p:
                                func = self.functions[schema['properties'][p]['type']]
                                ret.update({p:func(schema['properties'][p],p,self.random_gen)})
                    except KeyError:
                        # print("required key error")
                        pass
                if self.mode == "minimal":
                    try:
                        if p in schema['required']:
                            # print(p,"is required!!")
                            func = self.functions[schema['properties'][p]['type']]
                            ret.update({p:func(schema['properties'][p],p,self.random_gen)})
                    except KeyError:
                        print("Key error while trying to get required attribute",p)
                        pass
                if self.mode == "writable":
                    writable=True
                    try:
                        if schema['properties'][p]['readOnly'] == True:
                            #print(p,"readonly")
                            writable=False
                    except KeyError:
                        # print("writable key error")
                        pass
                    if writable:
                        try:
                            func = self.functions[schema['properties'][p]['type']]
                            try:
                                if schema['properties'][p]['x-unique'] == "true":
                                    #print("- unique")
                                    ret.update({p:func(schema['properties'][p],p,self.random_gen2)})
                            except KeyError:
                                ret.update({p:func(schema['properties'][p],p,self.random_gen)})
                        except KeyError:
                            # print("if writable key error")
                            pass
        except KeyError:
            print("object "+name+" with no properties")
            schema["properties"] = {}
            #pprint(schema)
            #no properties - could be an empty object - PALD: NEED TO DEAL WITH THIS
            pass

        #if self.mode == "minimal":
            #print("=REMOVE REQUIRED: ",schema['required'])
        if len(self.location):
            self.location.pop()
        return ret

    def integer_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        self.consolidate_minmax(schema,"minimum","maximum")
        val = "integer"
        val = schema['maximum']
        self.location.pop()
        return val

    def boolean_component(self,schema,name,rnd_gen):
        self.location.append(name)
        for att in ["min","max","minLength","maxLength","format","example"]:
            try:
                del schema[att]
            except KeyError:
                pass
        #print('/'.join(self.location))
        val = False
        if self.mode in ["full","minimal","writable"]:
            val = True
        self.location.pop()
        return val

    def number_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        self.consolidate_minmax(schema,"minimum","maximum")
        val = "number"
        val = schema['maximum']

        self.location.pop()
        return val

    def string_component(self,schema,name,rnd_gen):
        self.location.append(name)
        # print('/'.join(self.location))

        # Set format to general if none exists
        try:
            if schema['format'] == None:
                schema['format'] = "general"
        except KeyError:
            schema['format'] = "general"

        # set a maximum of 255 (for now)
        schema["maxDefault"] = 255
        self.consolidate_minmax(schema,"minLength","maxLength")
        if schema['format'] not in ["uid","date-time"]:
            schema["minLength"] = 1

        val = "string"
        if schema['format'] == "enum":
            del schema["minLength"]
            del schema["maxLength"]
            val = "ENUMTEST"
            try:
                selection = list(schema['enum'])
                val = selection[rnd_gen.randint(0,len(selection)-1)]
            except KeyError:
                pass
        if schema['format'] == "date-time":
            schema["maxLength"] = 23
            val = "2014-03-02T03:07:54.855"
        if schema['format'] == "coordinates":
            val = "[[-12.439,8.2729],[-12.4362,8.2706]]"
        if schema['format'] == "double":
            val = rnd_gen.uniform(schema["minLength"],schema["maxLength"])
        if schema['format'] == "integer":
            val = rnd_gen.randint(schema["minLength"],schema["maxLength"])
        if schema['format'] == "access":
            schema["minLength"] = 8
            schema["maxLength"] = 8
            val = "rw------"
        if schema['format'] == "uid":
            schema["minLength"] = 11
            schema["maxLength"] = 11
            val = ""
            for _ in range(11):
                val += self.uid_chars[rnd_gen.randint(0,len(self.uid_chars)-1)]
        if schema['format'] == "url":
            val = "http://www.example.com"
        if schema['format'] == "email":
            val = "example@dhis2.org"
        if schema['format'] == "general":
            val = ""
            for _ in range(int(schema['maxLength'])):
                val += self.name_chars[rnd_gen.randint(0,len(self.name_chars)-1)]

        try:
            if schema['x-association'] == "true":
                print("string ASSOCIATION:",name)
                # pprint(schema)
                # use example as the input
                try:
                    val = schema['example']
                except KeyError:
                    if name in ["user","lastUpdatedBy","id"]:
                        val = self.users[rnd_gen.randint(0,len(self.users)-1)]
                    pass
                print("val:",val)
                #logger.info("example: "+val)
        except KeyError:
            pass

        self.location.pop()
        return val

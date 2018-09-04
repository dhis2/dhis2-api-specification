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

# create logger with 'spam_application'
logger = logging.getLogger('dhis2api')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('api_explorer.log')
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

def payloadHash(s):
    return abs(hash(s)) % (10 ** 8)


class apicall:

    def __init__(self, call):
        # define the host alternatives
        self.host="https://play.dhis2.org/dev_qa1"
        self.r = {}
        # the call that is passed in may or may not have query parameters
        self.api_call=re.sub(r'/api/[0-9]{2}/',r'/api/',call[call.find("/api/"):])
        self.parts = self.api_call.rstrip('\n').split('?')
        self.endpoint=self.parts[0].rstrip('\n')
        ep = ""
        epDelim = ""
        for epp in self.endpoint.split('/')[1:]:
            if len(epp) == 11:
                print("uid?:",epp)
                epp = "@UID@"
            ep += epDelim + epp
            epDelim = "__"

        self.endpoint_ = ep
        self.response = ""
        self.content = ""
        self.method = ""
        self.payload = ""

        # split any query parameters up into a list of key,value pairs
        self.query_params = []
        if len(self.parts) > 1:
            self.append_queries(self.parts[1])

        self.functions = {
            "get": requests.get ,
            "post": requests.post ,
            "patch": requests.patch ,
            "options": requests.options ,
            "put": requests.put ,
            "delete": requests.delete
        }

    def send_request(self,method, queries=True):
        self.method=method
        self.response=""
        self.content = ""
        try:
            try:
                func = self.functions[method]
            except KeyError:
                logger.info("Invalid method passed to send_request; using GET.")
                func = self.functions["get"]
            try:    
                self.r = func(self.full_call(),auth=('system','System123'), json=self.payload)
            except TypeError:
                logger.error("Check that the target server is running")
            #print(self.r.headers)
            if 'Content-Type' in self.r.headers:
                if self.r.headers['Content-Type'].find("json") != -1:
                    self.response= json.loads(self.r.text)
                else:
                    self.response=self.r.text
                if method == "get":
                    self.content=self.r.headers['Content-Type']
        except json.JSONDecodeError:
            self.content=self.r.headers['Content-Type']
        except:
            logger.debug("Unexpected error: "+ sys.exc_info())

    def append_queries(self, queryString):

        for query in queryString.split('&'):
            keyval = query.split('=')
            if len(keyval) > 1:
                self.query_params.append({keyval[0]:keyval[1]})
            else:
                queryParam = keyval[0]
                self.query_params.append(queryParam)


    def has_q_params(self):
        if self.query_params:
            return True
        else:
            return False
    
    def set_host(self, host):
        self.host = host

    def set_payload(self, log):
        try:
            if log.find('payload="') != -1:
                self.payload = log[log.find('payload="')+9:-2].encode('utf8').decode('unicode_escape')
                if self.payload == "{}":
                    self.payload = ""
        except AttributeError:
            self.payload = log
    
    def has_payload(self):
        if self.payload == "":
            return False
        return True

    def full_call(self):
        query_part = ""
        delim = '?'
        for q in self.query_params:
            #print(q)
            
            if isinstance(q,dict):
                for k,v in q.items():
                    query_part += delim + '='.join([k,v])
                    delim = '&'
            else:
                query_part += delim + q
            delim = '&'
            
        return self.host + self.endpoint + query_part

    def query_json(self, sort=True):
        return json.dumps(self.query_params , sort_keys=sort, indent=2, separators=(',', ': '))

    def payload_json(self, sort=True):
        return json.dumps(self.payload , sort_keys=sort, indent=2, separators=(',', ': '))

    def response_json(self, sort=False):
        return json.dumps(self.response , sort_keys=sort, indent=2, separators=(',', ': '),)

    def getSchema(self,eps):
        try:
            if eps[self.endpoint][self.method]["responses"][self.r.status_code]["content"][self.content.split(';')[0]]["schema"]:
                return eps[self.endpoint][self.method]["responses"][self.r.status_code]["content"] [self.content.split(';')[0]]["schema"]
        except:
            logger.debug("new SchemaBuilder needed")
        return ''


class ep_model:
    """
    This is a model for the endpoint item.
    It is initialised from a schema.
    """

    def __init__(self, schema, rnd_seed=None):
        self.schema = schema
        self.mode = ""
        self.uid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.name_chars = "abcdefghijklmnopqrstuvwxyz       ABCDEFGHIJKLMNOPQRSTUVWXYZ"

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
        
    def reseed(self,rnd_seed):
        self.random_gen.seed(rnd_seed)
        self.random_gen2.seed(self.random_gen.randint(0,999999))
        
    def reseed_unique(self,rnd_seed):
        self.random_gen2.seed(rnd_seed)
    
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

        # loop over the list of items
        for a_item in alist:
            # drill down through the "levels" (separated by ":")
            for level in a_item.split(':'):
                try:
                    int(level) 
                except ValueError:
                    try:
                        schema_part2 = schema_part['properties']
                    except KeyError:
                        schema_part2 = schema_part['items']['properties']
                    schema_part = schema_part2[level]
            schema_part[attribute] = "true"
            schema_part = self.schema['items']
    

    def get_required(self):
        return self.required

    def print_schema(self):
        print((json.dumps(self.schema , sort_keys=True, indent=2, separators=(',', ': '))))

    def get_schema(self):
        return self.schema

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
        #print(self.schema['type'])
        func = self.functions[self.schema['type']]
        payload=func(self.schema,"",self.random_gen)
        self.payload = payload
        #return payload

    def array_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        ret = []
        try:
            func = self.functions[schema['items']['type']]
            for _ in range(1):
                ret.append(func(schema['items'],"items",self.random_gen))
        except KeyError:
            pass
        self.location.pop()
        return ret

    def object_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        ret = {}
        if self.mode == "minimal":
            #print("+REMOVE REQUIRED: ",schema['required'])
            schema['required'][:] = []
            #print("-REMOVE REQUIRED: ",schema['required'])
        for p in schema['properties']:
            #print("  |",p)
            #is it required according to the schema?
            if self.mode == "full":
                func = self.functions[schema['properties'][p]['type']]
                ret.update({p:func(schema['properties'][p],p,self.random_gen)})
            if self.mode == "required":
                for r in schema['required']:
                    if r == p:
                        func = self.functions[schema['properties'][p]['type']]
                        ret.update({p:func(schema['properties'][p],p,self.random_gen)})
            if self.mode == "minimal":
                try:
                    if self.required[p] == "REQUIRED":
                        #print("MINIMAL--required:",p)
                        schema['required'].append(p)
                        func = self.functions[schema['properties'][p]['type']]
                        ret.update({p:func(schema['properties'][p],p,self.random_gen)})
                except KeyError:
                    pass
            if self.mode == "writable":
                writable=True
                try:
                    if schema['properties'][p]['readOnly'] == "true":
                        #print(p,"readonly")
                        writable=False
                except KeyError:
                    pass
                if writable:
                    #print(p,"\n- writable")
                    func = self.functions[schema['properties'][p]['type']]
                    try:
                        if schema['properties'][p]['unique'] == "true":
                            #print("- unique")
                            ret.update({p:func(schema['properties'][p],p,self.random_gen2)})
                    except KeyError:
                        ret.update({p:func(schema['properties'][p],p,self.random_gen)})
        
        #if self.mode == "minimal":
            #print("=REMOVE REQUIRED: ",schema['required'])
        self.location.pop()
        return ret

    def integer_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        val = "integer"
        val = schema['max']
        self.location.pop()
        return val

    def boolean_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        val = False
        if self.mode in ["full","minimal","writable"]:
            val = True
        self.location.pop()
        return val

    def number_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        val = "number"
        val = schema['max']
        self.location.pop()
        return val

    def string_component(self,schema,name,rnd_gen):
        self.location.append(name)
        #print('/'.join(self.location))
        val = "string"
        if schema['format'] == "enum":
            val = "ENUMTEST"
            selection = schema['enum']
            val = selection[rnd_gen.randint(0,len(selection)-1)]
        if schema['format'] == "date-time":
            val = "2014-03-02T03:07:54.855"
        if schema['format'] == "access":
            val = "rw------"
        if schema['format'] == "uid":
            val = ""
            for _ in range(11):
                val += self.uid_chars[rnd_gen.randint(0,len(self.uid_chars)-1)]
        if schema['format'] == "url":
            val = "http://play.dhis2.org/api/example"
        if schema['format'] == "general":
            val = ""
            for _ in range(schema['max']):
                val += self.name_chars[rnd_gen.randint(0,len(self.name_chars)-1)]
        
        try:
            if schema['association'] == "true":
                # use example as the input
                val = schema['example']
                print("example:",val)
        except KeyError:
            pass
        self.location.pop()
        return val




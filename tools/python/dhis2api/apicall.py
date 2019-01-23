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
from datetime import datetime

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
                #print("uid?:",epp)
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
                if self.payload == "":
                    self.r = func(self.full_call(),auth=('system','System123'))
                else:
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

    def replace_query(self, key, value):
        for q in self.query_params:
            try:
                if q[key]:
                    q[key] = value
            except KeyError:
                pass


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

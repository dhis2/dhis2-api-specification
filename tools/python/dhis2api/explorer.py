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

from dhis2api.genson import SchemaBuilder
from dhis2api.apicall import apicall
from dhis2api.component import component
#import psycopg2
#from jsonschema import Draft4Validator
import json, jsonref, re
from datetime import datetime
from pprint import pprint, pformat
import copy
import sys
from os import read
from ast import literal_eval
from operator import itemgetter

metatada_get_template = {
                        "pager": {
                          "$ref": "#/components/schemas/pagination"
                        }
                      }

ep_template = {
                  "items": {
                    "$ref": "<metadata_schema>"
                  },
                  "maxItems": 2147483647,
                  "minItems": 0,
                  "readOnly": False,
                  "type": "array"
                }

class specsorter:

    def __init__(self, d):
        self.myDict = d

    def sortList(self,l):
        for v in l:
            if isinstance(v, dict):
                self.sortDict(v)

            else:
                if isinstance(v, list):
                    self.sortList(v)
                else:
                    l.sort()


    def sortDict(self,d):
        for k, v in d.items():
            if k == "tags" and not v == []:
                if isinstance(v[0], dict):
                    # tags are not nested and should be sorted by name
                    d[k] = sorted(v, key=itemgetter('name'))
            elif isinstance(v, dict):
                self.sortDict(v)
            else:
                if isinstance(v, list):
                    self.sortList(v)

    def sortspec(self):
        self.sortDict(self.myDict)
        return self.myDict


class diff_checker:
    '''
    Initialised with two json payloads
    '''

    def __init__(self,a,b):
        self.a = a
        self.b = b
        self.path = []
        self.diffs = []

    def _get_difflist(self):
        return self.diffs

    def _diffList(self,a,b):
        #print(p)
        cnt=0
        # print("+++++++++++_diffList a b")
        # pprint(a)
        # pprint(b)
        for v in a:
            self.path.append(str(cnt))
            try:
                if isinstance(v, dict):
                    self._diffDict(v,b[cnt])
                else:
                    if isinstance(v, list):
                        self._diffList(v,b[cnt])
                    else:
                        try:
                            if v != b[cnt]:
                                #print("dict[",':'.join(self.path),"]","value:",str(v),"!=",str(b[k]),"READONLY")
                                self.diffs.append(':'.join(self.path))
                        except TypeError:
                            self.diffs.append(':'.join(self.path))
                            pass
            except (KeyError, IndexError):
                #print("[",':'.join(self.path),"]","removed")
                self.diffs.append(':'.join(self.path))
            cnt+=1
            self.path.pop()
        # print("-----------_diffList a b")


    def _diffDict(self,a,b):
        # print("+++++++++++_diffDict a b")
        # pprint(a)
        # pprint(b)
        for k, v in a.items():
            self.path.append(k)
            try:
                if isinstance(v, dict):
                    self._diffDict(v,b[k])
                else:
                    if isinstance(v, list):
                        self._diffList(v,b[k])
                    else:
                        try:
                            if v != b[k]:
                                #print("dict[",':'.join(self.path),"]","value:",str(v),"!=",str(b[k]),"READONLY")
                                self.diffs.append(':'.join(self.path))
                        except TypeError:
                            self.diffs.append(':'.join(self.path))
                            pass
            except KeyError:
                #print("[",':'.join(self.path),"]","removed")
                self.diffs.append(':'.join(self.path))
            self.path.pop()
        # print("-----------_diffDict a b")

    def report_diffs(self):
        if isinstance(self.a, dict):
            self._diffDict(self.a,self.b)
        if isinstance(self.a,list):
            self._diffList(self.a,self.b)
        return self._get_difflist()


class endpoint_explorer():

    def __init__(self,dhis2instance,ep,fullspec,prelim):
        self.fullspec = fullspec
        self.fullcopy = copy.deepcopy(fullspec)
        self.dhis2instance = dhis2instance
        self.endpoint = ep
        self.mode = "ENG"
        self.component_model = None
        self.single = ep.rstrip('s')
        if self.single[-2:] == 'ie':
            self.single = self.single[:-2]+'y'
        self.here = "init"
        self.print_progress(1,"Initialising explorer for "+ep+" ("+self.single+")")
        self.schema = None
        self.builder = SchemaBuilder(False)
        self.prelim = prelim
        if prelim:
           #pprint(prelim)
           self.builder.add_schema({"items":prelim})
        try:
            deref = jsonref.loads(json.dumps(fullspec))
            #print("PALD deref")
            #pprint(deref["paths"]["/"+self.endpoint]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"][self.endpoint])
            if deref["paths"]["/"+self.endpoint]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"][self.endpoint]:
                component_schema = deref["paths"]["/"+self.endpoint]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"][self.endpoint]

                ins = pformat(component_schema)
                dins = literal_eval(ins)

                # print("before add")
                # pprint(dins)
                self.builder.add_schema(component_schema)
                # print("after add")
                # pprint(self.builder.to_schema())
                #print("before toschema")
                self.sync_builder2schema()
        except KeyError:
            pass
        notag = True
        for t in self.fullspec["tags"]:
            #print("TAG:",t["name"])
            if t["name"] == self.endpoint:
                notag = False
        if notag:
            newtag = {"name":self.endpoint,"description":""}
            self.fullspec["tags"].append(newtag)
        self.created = [] # keep a list of entries we create, so that we can clean up
        self.verbose = False
        self.array_based = True # some EPs return arrays of items, others are single objects
        self.api_request = None # re-usable apicall member
        self.api_responsej = ""
        self.api_response = None
        self.invalid_methods = []
        self.errors = set()
        self.organisationUnits = {}
        self.error_codes = {
            "E4000": {"type":"required","identifier":"errorProperty"},
            "E4001": {"type":"maximum","identifier":"errorProperty"},
            "E4003": {"type":"email","identifier":"errorProperty"},
            "E4004": {"type":"url","identifier":"none"},
            "E5000": {"type":"unique","identifier":"ID"},
            "E5002": {"type":"dependency","identifier":"message"},
            "E5003": {"type":"unique","identifier":"errorProperty"}
        }
        self.earlyExit = False
        self.responses = {}
        for m in ["get","post"]:
            self.responses[m] = {}


    def merge_dicts(self, dict1, dict2):
        """ Recursively merges dict2 into dict1 """
        if not isinstance(dict1, dict) or not isinstance(dict2, dict):
            return dict1
        for k in dict2:
            if k == "500":
                if k in dict1:
                    dict1[k] = self.merge_dicts(dict1[k], dict2[k])
                else:
                    dict1[k] = dict2[k]
        return dict1

    def merge_schemas(self, a, b, path=None, update=True):
        """
        http://stackoverflow.com/questions/7204805/python-dictionaries-of-dictionaries-merge
        merges b into a
        """
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge_schemas(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                elif isinstance(a[key], list) and isinstance(b[key], list):
                    for idx, val in enumerate(b[key]):
                        a[key][idx] = self.merge_schemas(a[key][idx], b[key][idx], path + [str(key), str(idx)], update=update)
                elif update:
                    a[key] = b[key]
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a


    def set_instance(self,dhis2instance):
        self.dhis2instance = dhis2instance

    def get_schema(self):
        if self.earlyExit:
            return self.fullcopy
        else:
            return self.fullspec

    def print_progress(self,level,title):
        indent = ""
        for i in range(0,level):
            indent = "   " + indent
        print('{:>24}:{} {}{:<100}'.format(self.endpoint,self.here,indent,title))

    def explore_get(self):
        try:
            # maybe GET isn't supported
            self.get_to_schema()
            # if self.component_model:
                # maybe POST isn't supported
                # if self.valid_method("POST"):
                #     self.post_max()
                # if self.valid_method("POST"):
                #     self.post_min()
                # if self.valid_method("POST"):
                #     self.check_uniqueness()
        except KeyError:
            print(self.endpoint,"DID NOT COMPLETE!")
            self.earlyExit = True
            exit(0)
            pass


    def explore(self):
        try:
            # maybe GET isn't supported
            self.get_to_schema()
            if self.component_model:
                # maybe POST isn't supported
                if self.valid_method("POST"):
                    self.post_max()
                if self.valid_method("POST"):
                    self.post_min()
                if self.valid_method("POST"):
                    self.check_uniqueness()
        except KeyError:
            print(self.endpoint,"DID NOT COMPLETE!")
            self.earlyExit = True
            exit(0)
            pass

        self.remove_invalid_methods()

    def remove_invalid_methods(self):
        for m in ["GET","POST"]:
            if not self.valid_method(m):
                try:
                    ep_name = "/"+self.endpoint
                    method = m.lower()
                    del self.fullspec["paths"][ep_name][method]
                except KeyError:
                    pass

    def initiate_call(self,all_fields=True):
        self.api_request=apicall("/api/"+self.endpoint)
        self.api_request.set_host(self.dhis2instance)
        if all_fields:
            # add a fields=:all if not already
            self.api_request.append_queries("fields=:all")

    def initiate_with_ep(self,ep,all_fields=True):
        self.api_request=apicall("/api/"+ep)
        self.api_request.set_host(self.dhis2instance)
        if all_fields:
            # add a fields=:all if not already
            self.api_request.append_queries("fields=:all")

    def set_payload(self,payload):
        if payload:
            if self.array_based:
                try:
                    self.api_request.set_payload(payload[0])
                except KeyError:
                    self.api_request.set_payload(payload)
            else:
                self.api_request.set_payload(payload)

    def save_uid(self,uid,level=2):
        message = uid+" created"
        self.print_progress(level,message)
        self.created.append(uid)

    def valid_method(self,method):
        ret = False
        if method not in self.invalid_methods:
            ret = True
        return ret

    def delete_all(self):
        # print("NO DELETE")
        while len(self.created) > 0:
            self.initiate_with_ep(self.endpoint+"/"+self.created.pop(0),False)
            self.do_call("delete")
            # could check the correct uid is reported back here
            # could also check that we cannot GET the item from the ep any more


    def handle_errors(self,method):
        """
        Manages all the error handling in one place.

        The reaction to an error depends on the mode:
            (ENG) Engineering mode: update the model
            (TEST) Testing mode: Raise a warning
        """
        update_model = False
        #print(self.api_responsej)
        self.print_progress(3,"checking response...")
        if method == "post":
            try:
                if self.api_response["status"] == "ERROR":
                    self.print_progress(3,"Error...")
                    # print(self.api_request.full_call())
                    # print(self.api_request.payload_json())
                    # print(self.api_responsej)

                    if self.api_response["httpStatusCode"] == 405:
                        error = "ERROR:"+str(self.api_response["httpStatusCode"])+" "+self.api_response["message"]
                        self.print_progress(4,error)
                        self.invalid_methods.append("POST")
                        return


                    if self.api_response["httpStatusCode"] >= 500:
                        handled = False
                        try:
                            # Look for a pattern that indicates maximum length
                            found = re.search('Unrecognized field "(.+?)" \(class', self.api_response["message"]).group(1)
                        except AttributeError:
                            # error message does not match the pattern
                            found = '' # apply error handling
                        if found != '':
                            handled = True
                            if self.mode == "ENG":
                                self.component_model.set_attributes([found],"invalid")
                                update_model = True
                                self.print_progress(4,found+" is not a valid attribute. Updating model.")

                        try:
                            # Look for a pattern that indicates invalid enum
                            found = re.search('value not one of declared Enum instance names: \[(.+?)\]', self.api_response["message"]).group(1)
                        except AttributeError:
                            # error message does not match the pattern
                            found = '' # apply error handling
                        if found != '':
                            handled = True
                            if self.mode == "ENG":
                                enums = found.split(', ')
                                it = ""
                                delim = ''
                                chained = re.search('through reference chain: (.+?)\)', self.api_response["message"]).group(1)
                                print("chained",chained)
                                chain = chained.replace('\"','').split('->')
                                print("chain",chain)
                                for c in chain:
                                    a = re.search('.*\[(.+?)\]',c).group(1)
                                    if a != 0:
                                        it += delim + a
                                        delim = ':'


                                self.print_progress(4,"Enum must be one of "+found+". Updating model.")
                                self.component_model.set_attributes([it],"enum",enums)
                                update_model = True

                        try:
                            # Look for a pattern that indicates reference    through reference chain: org.hisp.dhis.category.Category[\"user\"])
                            found = re.search('through reference chain.*\[\\"(.+?)\\"\]', self.api_response["message"]).group(1)
                        except AttributeError:
                            # error message does not match the pattern
                            found = '' # apply error handling
                        if found != '':
                            handled = True
                            if self.mode == "ENG":
                                self.print_progress(4,"- using example ID for "+found+" and repeating")
                                self.component_model.set_attributes([found],"x-association")
                                update_model = True

                        if not handled:
                            print("unhandled POST error [",self.api_response["httpStatusCode"],"]")
                            # print(self.api_request.full_call())
                            # print(self.api_request.payload_json())
                            # print(self.api_responsej)
                            # pprint(self.schema)
                            return
                    else:
                        error = "ERROR:"+str(self.api_response["httpStatusCode"])+" "+self.api_response["message"]
                        self.print_progress(4,error)

                        # if self.api_response["httpStatusCode"] == 409:
                            # print(self.api_request.payload_json())
                            # print(self.api_responsej)

                        if self.api_response["response"]["responseType"] == "ObjectReport":
                            for i in self.api_response["response"]["errorReports"]:
                                error_message = i["message"]
                                self.print_progress(5,error_message)
                                # try:
                                mapped_code = self.error_codes[i["errorCode"]]
                                # except KeyError:
                                #     pprint(self.api_response)
                                #     exit(0)
                                type = mapped_code["type"]
                                self.errors.add(type)

                                if type == "email":
                                    #print(self.api_responsej)
                                    identifier = mapped_code["identifier"]
                                    if self.mode == "ENG":
                                        self.print_progress(4,i[identifier]+" must be of format 'email'. Updating model.")
                                        self.component_model.set_attributes([i[identifier]],"format","email")
                                        update_model = True

                                if type == "url":
                                    #print(self.api_responsej)
                                    try:
                                        # Look for a pattern that indicates dependency on an existing attribute
                                        # If so, use an existing attribute (one of the example values)
                                        found = re.search('Property `(.+?)` requires a valid URL', error_message).group(1)
                                    except AttributeError:
                                        # error message does not match the pattern
                                        found = '' # apply error handling
                                    if found != '':

                                        if self.mode == "ENG":
                                            self.print_progress(4,found+" must be of format 'url'. Updating model.")
                                            self.component_model.set_attributes([found],"format","url")
                                            update_model = True

                                if type == "unique":
                                    #print(self.api_responsej)
                                    identifier = mapped_code["identifier"]
                                    if identifier == "ID":
                                        unique_attribute = ["id","code"] # id and code are assumed to always be unique
                                    else:
                                        unique_attribute = [i[identifier]]
                                    if self.mode == "ENG":
                                        #print("unique_attribute:",unique_attribute)
                                        uniq = unique_attribute
                                        for u in uniq:
                                            self.print_progress(4,"- "+u+" must be unique!")
                                            #print(self.api_request.payload_json())
                                            #print(self.api_responsej)
                                            self.print_progress(4,"- updating value of "+u+" in payload")
                                        self.component_model.set_attributes(uniq,"x-unique")
                                        update_model = True

                                elif type == "required":

                                    # pprint(self.api_response)
                                    identifier = mapped_code["identifier"]

                                    #self.component_model.add_requirement(i[identifier])
                                    try:
                                        req_prop = i[identifier]
                                    except KeyError:
                                        try:
                                            # Look for a pattern that indicates maximum length
                                            req_prop = re.search('Missing required property `(.+?)`', error_message).group(1)
                                        except AttributeError:
                                            # error message does not match the pattern
                                            req_prop = '' # apply error handling

                                    if req_prop:
                                        self.print_progress(4,req_prop+" is a required property. Updating model.")
                                        self.component_model.set_attributes([req_prop],"required")
                                        update_model = True

                                elif type == "maximum":
                                    identifier = mapped_code["identifier"]
                                    try:
                                        # Look for a pattern that indicates maximum length
                                        found = re.search('is (.+?), but given length was', error_message).group(1)
                                    except AttributeError:
                                        # error message does not match the pattern
                                        found = '' # apply error handling
                                    if found != '':
                                        if self.mode == "ENG":
                                            self.print_progress(4,i[identifier]+" has maximum value "+found+". Updating model.")
                                            self.component_model.set_attributes([i[identifier]],"maximum",found)
                                            update_model = True
                                elif type == "dependency":
                                    if re.match(r"^Invalid reference ", error_message):
                                        try:
                                            # Look for a pattern that indicates dependency on an existing attribute
                                            # If so, use an existing attribute (one of the example values)
                                            found = re.search(' for association `(.+?)`\.', error_message).group(1)
                                        except AttributeError:
                                            # error message does not match the pattern
                                            found = '' # apply error handling
                                        if found != '':
                                            if self.mode == "ENG":
                                                self.component_model.set_attributes([found+":id"],"x-association")
                                                update_model = True
                                                self.print_progress(4,"- using example ID for "+found+" and repeating")
                                else:
                                    print("OTHER ERROR NOT HANDLED YET!")

                        elif self.api_response["response"]["responseType"] == "ImportSummary":
                            for i in self.api_response["response"]["ImportSummaries"]:
                                error_message = i["status"]+" conflicts:"+ i["conflicts"]["object"]+"<->"+ i["conflicts"]["value"]
                                self.print_progress(5,error_message)
                                try:
                                    # Look for a pattern that indicates dependency on an existing attribute
                                    # If so, use an existing attribute (one of the example values)
                                    found = re.search(self.single+'\.(.+?)', i["conflicts"]["object"]).group(1)
                                except AttributeError:
                                    # error message does not match the pattern
                                    found = '' # apply error handling
                                if found != '':
                                    if self.mode == "ENG":
                                        self.print_progress(4,"- using example ID for "+found+" and repeating")
                                        self.component_model.set_attributes([found],"x-association")
                                        update_model = True




                elif 200 <= self.api_response["httpStatusCode"] <= 201:
                    # save the created id
                    try:
                        uid = self.api_response["response"]["uid"]
                        self.save_uid(uid,level=3)
                    except KeyError:
                        self.print_progress(3,"200 with no uid")
                        print(self.api_responsej)
                else:
                    self.print_progress(3,"Unhandled")
                    print(self.api_responsej)

            except TypeError:
                pass
                # self.print_progress(3,"KeyError - response:")
                # # was probably a successful GET call
                # pprint(self.api_response)
                # pass

        elif method == "delete":
            if self.api_response["httpStatus"] == "OK":
                # save the created id
                if method == "delete":
                    uid = self.api_response["response"]["uid"]
                    self.print_progress(3,uid+" deleted successfully")

        elif method == "get":
            # print("get call")
            sc = self.api_request.r.status_code


            if 200 <= self.api_request.r.status_code <= 202:
                self.print_progress(3,"retrieved")
                update_model = True

            elif 300 <= sc < 400:
                try:
                    self.responses[method][sc].add_object(self.api_response)
                except KeyError:
                    builder = SchemaBuilder(False)
                    builder.add_object(self.api_response,"root")
                    self.responses[method] += {sc:builder.to_schema()}

            elif self.api_request.r.status_code == 405:
                self.print_progress(3,"invalid method [405]")
                self.invalid_methods.append("GET")

            elif 400 <= self.api_request.r.status_code <= 406:
                # 400 bad request - may be missing a required parameter
                # 404 invalid path
                self.print_progress(3,"bad request ["+str(self.api_request.r.status_code)+"]")

            else:
                #pprint(self.api_response)
                try:
                    if self.api_response["status"] == "ERROR":
                        self.print_progress(3,"Error...")
                        if self.api_response["httpStatusCode"] == 409:
                            if self.api_response["message"].find("At least one organisation unit") != -1:
                                # we need to add ou to the query
                                self.api_request.append_queries("ou=vWbkYPRmKyS")

                        else:
                            print("not 409")
                            print(self.api_request.full_call())
                            print(self.api_request.payload_json())
                            print(self.api_responsej)
                            exit()
                except:
                    print("exception on error handling")
                    print(self.api_request.full_call())
                    print(self.api_request.payload_json())
                    print(self.api_responsej)
                    exit()

        if self.component_model and update_model:
            # print("PALD CM=======",sys._getframe().f_lineno)
            # self.component_model.print_schema()
            self.sync_model2builder()
            # print("PALD CM=======",sys._getframe().f_lineno)
            # self.component_model.print_schema()
            self.sync_builder2schema()
            # print("PALD CM=======",sys._getframe().f_lineno)
            # self.component_model.print_schema()


    def do_call(self,method):
        self.api_response = None
        self.api_responsej = ""
        self.print_progress(2,method.upper()+": "+self.api_request.full_call())
        self.api_request.send_request(method,False)
        self.api_responsej = self.api_request.response_json()
        self.api_response = json.loads(self.api_responsej)
        if self.verbose:
            print(self.api_responsej)
        self.handle_errors(method)

    def response_to_schema(self):
        self.sync_model2builder()
        # print(">>>>RESPONSE")
        # pprint(self.api_request.response)
        # print("<<<<RESPONSE:")
        # pprint(self.builder.to_schema())
        try:
            self.builder.add_object(self.api_request.response[self.endpoint],"root")
        except KeyError:
            self.builder.add_object(self.api_request.response,"root")
            self.array_based=False
        except TypeError:
            self.builder.add_object(self.api_request.response,"root")
            self.array_based=True

        #print('\n=== schema ===\n')
        self.sync_builder2schema()

        # this_schema = self.fullspec["components"]["schemas"][self.single]
        # for p in this_schema["properties"]:
        #     if p in self.fullspec["components"]["schemas"]:
        #         self.merge_schemas(self.fullspec["components"]["schemas"][p],copy.deepcopy(this_schema["properties"][p]))

    def sync_builder2schema(self):
        # print("sync_builder2schema object")
        # pprint(self.builder.to_schema())
        # print("sync_builder2schema IN")
        # pprint(self.builder.to_schema())
        try:
            #print("PALD ",sys._getframe().f_lineno)
            self.schema = self.builder.to_schema()["$schema"]
            sch = self.builder.to_schema()["$schema"]
        except KeyError:
            #print("PALD ",sys._getframe().f_lineno)
            self.schema = self.builder.to_schema()
            sch = self.builder.to_schema()


        # print("PALD schema",sys._getframe().f_lineno)
        # pprint(self.schema)
        if self.component_model:
            #print("PALD",sys._getframe().f_lineno)
            self.component_model.set_schema(self.schema)
        else:
            #print("PALD",sys._getframe().f_lineno)
            self.component_model = component(self.schema, self.fullspec)

        # print("PALD CM=======",sys._getframe().f_lineno)
        # self.component_model.print_schema()
        #sch = self.builder.to_schema()
        #print("______")

        # Update the components section

        try:
            new_schema = sch["items"]
        except KeyError:
            new_schema = sch

        update = self.slash_to_hierarchy__(self.single.split('/'), new_schema)

        # if self.prelim:
        #     prelim = {self.single:copy.deepcopy(self.prelim)}
        #     print("prelim MERGE")
        #     pprint(update)
        #     print("__________________________________________________________________________")
        #     pprint(prelim)
        #     print("__________________________________________________________________________")
        #     self.merge_dicts(update,prelim)
        #     pprint(update)
        #     print("__________________________________________________________________________")
        #     self.prelim = None
        #self.merge_dicts(self.fullspec["components"]["schemas"],update)
        self.fullspec["components"]["schemas"].update(update)
        # print("2=======")
        # print("---sync_builder2schema---")
        # pprint(self.schema)


    def slash_to_hierarchy__(self, name, child):

        if len(name) > 1:
            return {name[0]:self.slash_to_hierarchy__(name[1:],child)}
        else:
            return {name[0]:child}


    def sync_model2builder(self):
        if self.component_model:
            self.builder = SchemaBuilder(False)
            self.builder.add_schema(self.component_model.get_schema())
            # print("---model2builder---")
            # pprint(self.component_model.get_schema())


    def get_template(self):
        ep_name = "/"+self.endpoint
        properties = copy.deepcopy(metatada_get_template)
        props_schema = copy.deepcopy(ep_template)
        #print("properties:",self.single)
        props_schema["items"]["$ref"] = "#/components/schemas/"+ self.single
        #pprint(props_schema)
        properties[self.endpoint] = props_schema
        summary = "list "+ self.endpoint
        pathspec = {
                  ep_name: {
                    "get": {
                    "parameters": [
                        {"$ref": "#/components/parameters/paging"},
                        {"$ref": "#/components/parameters/page"},
                        {"$ref": "#/components/parameters/pageSize"},
                        {"$ref": "#/components/parameters/order"},
                        {"$ref": "#/components/parameters/filter"},
                        {"$ref": "#/components/parameters/field"}
                    ],
                      "responses": {
                        "200": {
                          "content": {
                            "application/json": {
                              #"x-dhis2-examples": { "full": { "$ref": ref_path } },
                              "schema": { "properties": properties }
                            }
                          }
                        }
                      },
                      "summary": summary,
                      "tags":[self.endpoint.split('/')[0]]
                    }
                  }
                }
        return pathspec

    def response_template(self,method,status_code):
        ep_name = "/"+self.endpoint
        #print("properties:",self.single)
        #props_schema["items"]["$ref"] = "#/components/schemas/"+ self.single
        #pprint(props_schema)
        #properties[self.endpoint] = props_schema
        #summary = "list "+ self.endpoint
        pathspec = {
                  ep_name: {
                    method: {
                      "responses": {
                        status_code: {
                          "content": {
                            "application/json": {
                              #"x-dhis2-examples": { "full": { "$ref": ref_path } },
                              "schema": {
                                    "$ref": "#/components/schemas/webmessage"
                                },
                                "example": self.api_responsej
                            }
                          }
                        }
                      }
                    }
                  }
                }
        return pathspec

    def post_template(self):
        ep_name = "/"+self.endpoint
        # properties = copy.deepcopy(metatada_get_template)
        # props_schema = copy.deepcopy(ep_template)
        # #print("properties:",self.single)
        # props_schema["items"]["$ref"] = "#/components/schemas/"+ self.single
        # #pprint(props_schema)
        summary = "create a new "+ self.single
        properties = "#/components/schemas/"+ self.single
        pathspec = {
                  ep_name: {
                    "post": {
                    "requestBody": {
                      "content": {
                        "application/json": {
                          #"x-dhis2-examples": { "full": { "$ref": ref_path } },
                          "schema": { "$ref": properties }
                        }
                      }
                    },
                      "summary": summary,
                      "tags":[self.endpoint.split('/')[0]]
                    }
                  }
                }
        return pathspec


    def delete_template(self):
        ep_name = "/"+self.endpoint+"/{id}"
        # properties = copy.deepcopy(metatada_get_template)
        # props_schema = copy.deepcopy(ep_template)
        # #print("properties:",self.single)
        # props_schema["items"]["$ref"] = "#/components/schemas/"+ self.single
        # #pprint(props_schema)
        summary = "delete a batch of "+ self.endpoint +" by id"
        pathspec = {
                  ep_name: {
                    "delete": {
                    "requestBody": {
                      "content": {
                        "application/json": {
                          #"x-dhis2-examples": { "full": { "$ref": ref_path } },
                          "properties": {
                            "type": "array",
                            "schema": { "$ref": "#/components/schemas/id" }
                          }
                        }
                      }
                    },
                      "summary": summary,
                      "tags":[self.endpoint.split('/')[0]]
                    }
                  }
                }
        return pathspec


    def delete_id_template(self):
        ep_name = "/"+self.endpoint+"/{id}"
        # properties = copy.deepcopy(metatada_get_template)
        # props_schema = copy.deepcopy(ep_template)
        # #print("properties:",self.single)
        # props_schema["items"]["$ref"] = "#/components/schemas/"+ self.single
        # #pprint(props_schema)
        summary = "delete a "+ self.single +" by id"
        pathspec = {
                  ep_name: {
                    "delete": {
                    "parameters": [
                        {"$ref": "#/components/parameters/id"}
                    ],
                      "summary": summary,
                      "tags":[self.endpoint.split('/')[0]]
                    }
                  }
                }
        return pathspec


    def get_to_schema(self):
        """
        Perform a full get request to populate an initial schema for the EP
        """
        self.here = "get_to_schema"
        self.print_progress(1,"Calling endpoint with all fields")
        self.initiate_call() # reset the caller
        self.api_request.append_queries("paging=false")
        ou_loop = []
        try:
            ep_name = "/"+self.endpoint
            if self.fullspec["paths"][ep_name]["get"]:
                for p in self.fullspec["paths"][ep_name]["get"]["parameters"]:
                    try:
                        if p["required"]:
                            if p["name"] == 'ou':
                                # this is a special case - we can check all
                                # organisation units
                                ou_path = "../../docs/spec/examples/organisationUnits_get_responses_200_content_json_full.json"
                                oufile=open(ou_path,'r')
                                ou_example = json.load(oufile)
                                oufile.close()

                                for ou in ou_example["organisationUnits"]:
                                    ou_loop.append(ou["id"])

                                next_ou = ou_loop.pop()
                                self.api_request.append_queries("ou="+next_ou)

                    except KeyError:
                        pass
        except KeyError:
            pass

        # run the call and record the schema - re-use existing defs where possible
        status="NotRun"
        safety=0

        ep_name = "/"+self.endpoint.replace('/','__')
        example_path = "../../docs/spec/examples"+ep_name+"_get_responses_200_content_json_full.json"
        #ref_path = "file:./examples"+ep_name+"_get_responses_200_content_json_full.json"
        pathspec = self.get_template()

        onegood = False
        #bad = False
        while status != "SUCCESS" or ou_loop and not onegood:
            #print("try",safety)

            safety += 1
            if safety > 5000:
                print("I LOOPED OUT get_to_schema")
                break
            self.do_call("get")
            sc = self.api_request.r.status_code
            if 200 <= sc <= 202:
                status = "SUCCESS"

                if self.api_responsej != {}:
                    exfile= open(example_path,'w')
                    exfile.write(json.dumps(self.api_response , sort_keys=True, indent=2, separators=(',', ': ')))
                    exfile.close()
                    # for p in self.fullspec["paths"]:
                    #    print(p)
                    #pprint(pathspec)
                    self.merge_dicts(self.fullspec["paths"],pathspec)
                    #pprint(self.fullspec["paths"]['/attributes'])
                    safety += 500  # just to prevent very long loop! will this better!

                self.print_progress(1,"Generating schema from response")
                self.response_to_schema()

                if ou_loop:
                    if status == "SUCCESS":
                        onegood = True
                    next_ou = ou_loop.pop()
                    print("next-ou:"+next_ou)
                    self.api_request.replace_query("ou",next_ou)

            if 400 <= sc <= 406:
                if sc == 405:
                    self.invalid_methods.append("GET")
                break

            if sc >= 300:
                response_spec = self.response_template("get",sc)
                self.merge_dicts(self.fullspec["paths"],response_spec)

        # OUTPUT THE SCHEMA?

    def post_max(self):
        """
        POST as much as possible to the EP, capture errors for readOnly and Unique values
        """
        self.here = "post_max"
        self.print_progress(1,"Generating POST (create) request from schema")
        self.initiate_call(False) # reset the caller
        status="NotRun"
        safety=0
        while status != "Created":
            safety += 1
            if safety > 50:
                print("I LOOPED OUT post_max")
                break
            self.component_model.create_payload(mode="writable")
            model_pl=self.component_model.get_payload()
            # pprint(model_pl)

            #print("payloadMAX")
            #pprint(model_pl)

            self.initiate_call(False)  # reset the call without the fields=:all query
            """ need to print this??
            myPayload=json.dumps(model_pl, sort_keys=True, indent=2, separators=(',', ': '))
            if print_response:
                print(myPayload)
            """

            self.print_progress(2,"Sending POST request")
            self.set_payload(model_pl)
            self.do_call("post")

            # catch readOnly errors and correct them
            # try:
            status = self.api_response["httpStatus"]
            # except TypeError:
            #     print(self.api_request.full_call())
            #     print(self.api_request.payload_json())
            #     pprint(self.api_response)
            #     exit(0)


            if self.api_response["httpStatusCode"] == 405:
                self.invalid_methods.append("POST")
                break
            else:
                pathspec = self.post_template()
                self.merge_dicts(self.fullspec["paths"],pathspec)
                response_spec = self.response_template("post",self.api_request.r.status_code)
                self.merge_dicts(self.fullspec["paths"],response_spec)


        # Hopefully we filled any dependencies above
        if self.api_response["httpStatus"] == "Created":

            # ep_name = "/"+self.endpoint
            # example_path = "../../docs/spec/examples"+ep_name+"_post_responses_200_content_json_full.json"
            # ref_path = "file:./examples"+ep_name+"_post_responses_200_content_json_full.json"
            # pathspec = self.post_template()

            # the created id
            uid = self.api_response["response"]["uid"]

            # retreive the created version and compare with the POST to work our readonly attributes
            self.print_progress(2,"Retrieving newly created item with GET")
            self.initiate_with_ep(self.endpoint+"/"+uid)
            self.do_call("get")

            self.print_progress(2,"Comparing POST payload with GET response")
            if self.array_based:
                dc=diff_checker(model_pl[0],self.api_response)
            else:
                dc=diff_checker(model_pl,self.api_response)
            dl=dc.report_diffs()
            #print("ReadOnly items:",dl)
            self.component_model.set_attributes(dl,"readOnly")
        else:
            # We didn't manage to get a working POST in the above loop
            error = "MAX POST FAILED: "+str(self.api_response["httpStatusCode"])+" "+self.api_response["httpStatus"]
            self.print_progress(2,error)

        # delete the created items
        self.delete_all()

    def post_min(self):
        """
        Create a minimal POST to the EP to figure out mandatory attributes
        """
        self.here = "post_min"
        self.print_progress(1,"Generating POST (create) request with minimal payload")
        self.initiate_call(False) # reset the caller
        status="NotRun"
        safety=0
        self.component_model.clear_required() # change all attributes to not-required
        while status != "Created":
            safety += 1
            if safety > 50:
                print("I LOOPED OUT post_min")
                break
            self.component_model.create_payload(mode="minimal")
            model_pl=self.component_model.get_payload()
            """
            myPayload=json.dumps(model_pl, sort_keys=True, indent=2, separators=(',', ': '))
            if print_response:
                print(myPayload)
            """
            # print("payloadMIN")
            # pprint(model_pl)
            self.set_payload(model_pl)
            self.do_call("post")
            status = self.api_response["httpStatus"]

            if self.api_response["httpStatusCode"] == 405:
                self.invalid_methods.append("POST")
                break
            else:
                pathspec = self.post_template()
                self.merge_dicts(self.fullspec["paths"],pathspec)
                response_spec = self.response_template("post",self.api_request.r.status_code)
                self.merge_dicts(self.fullspec["paths"],response_spec)

            if self.api_response["status"] == "ERROR": # NEED TO HANDLE OTHER ERRORS TOO!
                if self.api_response["httpStatusCode"] == 405:
                    self.invalid_methods.append("POST")
                    break

        self.print_progress(2,"Required items: "+str(self.component_model.get_required()))
        self.schema = self.component_model.get_schema()

        # delete the created items
        self.delete_all()

    def check_uniqueness(self):
        """
        Create a POST to the EP with all writable atributes and repeat to figure out unique attributes

        - First we send a POST with all writable attributes
        - Then we try to POST the same again
        - We look for errors about unique values, change those values, and repeat until we are successful
        """
        self.here = "check_uniqueness"
        self.print_progress(1,"Generating POST (create) request with payload of all writable attributes")
        self.initiate_call(False) # reset the caller
        sameseed=datetime.now().microsecond
        self.component_model.reseed(sameseed)
        self.component_model.create_payload(mode="writable")
        model_pl=self.component_model.get_payload()

        # print(json.dumps(model_pl , sort_keys=True, indent=2, separators=(',', ': ')))
        self.set_payload(model_pl)
        self.do_call("post")

        status = self.api_response["httpStatus"]
        if self.api_response["httpStatus"] == "Created":


            # now send again and test for conflicts
            status="NotRun"
            safety=0
            while status != "Created":
                safety += 1
                if safety > 10:
                    print("I LOOPED OUT check_uniqueness")
                    break

                self.do_call("post")
                status = self.api_response["httpStatus"]
                #uniq=[]
                if self.api_response["status"] == "ERROR":
                    self.component_model.reseed(sameseed)
                    self.component_model.create_payload(mode="writable")
                    model_pl=self.component_model.get_payload()
                    #print(json.dumps(model_pl , sort_keys=True, indent=2, separators=(',', ': ')))

                    self.set_payload(model_pl)

        else:
            # handle the error
            print("NEED TO HANDLE SOME ERRORS HERE!")
            print(self.api_request.full_call())
            print(self.api_request.payload_json())
            print(self.api_responsej)

        # delete the created items
        self.delete_all()

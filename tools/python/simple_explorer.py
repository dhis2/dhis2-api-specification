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

from dhisapi import apicall,ep_model
from genson import SchemaBuilder
import psycopg2
from jsonschema import Draft4Validator
import json, re


class diff_checker:

    def __init__(self,a,b):
        self.a = a
        self.b = b
        self.path = []
        self.diffs = []

    def get_difflist(self):
        return self.diffs

    def diffList(self,a,b):
        #print(p)
        cnt=0
        for v in a:
            self.path.append(str(cnt))
            try:
                if isinstance(v, dict):
                    self.diffDict(v,b[cnt])
                else:
                    if isinstance(v, list):
                        self.diffList(v,b[cnt])
                    else:
                        if v != b[cnt]:
                            #print("list[",':'.join(self.path),"]","!=",b[cnt],"READONLY")
                            self.diffs.append(':'.join(self.path))
            except (KeyError, IndexError):
                #print("[",':'.join(self.path),"]","removed")
                self.diffs.append(':'.join(self.path))
            cnt+=1
            self.path.pop()
            

    def diffDict(self,a,b):
        for k, v in a.items():
            self.path.append(k)
            try:
                if isinstance(v, dict):
                    
                    self.diffDict(v,b[k])
                else:
                    if isinstance(v, list):
                        self.diffList(v,b[k])
                    else:
                        if v != b[k]:
                            #print("dict[",':'.join(self.path),"]","value:",str(v),"!=",str(b[k]),"READONLY")
                            self.diffs.append(':'.join(self.path))
            except KeyError:
                #print("[",':'.join(self.path),"]","removed")
                self.diffs.append(':'.join(self.path))
            self.path.pop()

    def report_diffs(self):
        if isinstance(self.a, dict):
            self.diffDict(self.a,self.b)
        if isinstance(self.a,list):
            self.diffList(self.a,self.b)

def print_progress(ep,level,title):
    indent = " "
    for i in range(0,level):
        indent += " "
    print('[{:>30}]{}{:<100}'.format(ep,indent,title))




def explore_paths(dhis2instance,ep):

    print_response= False

    # make sure the instance is running and accessible

    # for each endpoint
    #ep = "dashboards"
    created=[]
        # find a successful (get) example


            # add a fields=:all if not already
    myCall=apicall("/api/"+ep)    
    myCall.set_host(dhis2instance)
    myCall.append_queries("fields=:all")
            # run the call and record the schema - re-use exinsting defs where possible

    #print(myCall.full_call())
    #print(myCall.query_json())

    print("\n\n 1. Calling endpoint",ep,"with all fields.\n_________________________")
    #print_progress(ep,1,"1 Calling endpoint with all fields")
    myCall.send_request("get",False)
    if print_response:
        print(myCall.response_json())

    print("\n\n 2. Generating schema from response.\n_________________________")
    builder =  SchemaBuilder(False)
    builder.add_object(myCall.response[ep])
    #print('\n=== schema ===\n')
    mySchema = builder.to_schema() 
    #mySchema = retSchema["properties"][ep]
    outfile= open("/home/philld/dhis2/api/server_logs/bigdata/se.json",'w')
    outfile.write(json.dumps(mySchema , sort_keys=True, indent=2, separators=(',', ': ')))
    outfile.close()
    if print_response:
        print(json.dumps(mySchema , sort_keys=True, indent=2, separators=(',', ': ')))

    # If valid for the endpoint, construct a POST from the full schema
    print("\n\n 3. Generating POST (create) request from schema.\n_________________________")
    myEP = ep_model(mySchema)
    status="NotRun"
    safety=0
    while status != "Created":
        safety += 1
        if safety > 20:
            break
        myEP.create_payload(mode="full")
        exam=myEP.get_payload()
        myPOST=apicall("/api/"+ep)
        myPOST.set_host(dhis2instance)
        myPayload=json.dumps(exam, sort_keys=True, indent=2, separators=(',', ': '))
        if print_response:
            print(myPayload)

        print("\n\n 4. Sending POST request.\n_________________________")

        myPOST.set_payload(exam[0])
        myPOST.send_request("post",False)
        #print(myPOST.response_json())
        # catch readOnly errors and correct them
        response = json.loads(myPOST.response_json())
        status = response["httpStatus"]
        if response["status"] == "ERROR":
                for i in response["response"]["errorReports"]:
                    mess = i["message"]
                    print(mess)
                    if re.match(r"^Invalid reference ", mess): 
                        try:
                            found = re.search(' for association `(.+?)`\.', mess).group(1)

                        except AttributeError:
                            # AAA, ZZZ not found in the original string
                            found = '' # apply your error handling
                        if found != '':
                            myEP.set_attributes([found+":id"],"association")
                            print("\n\n  - using example ID for",found,"and repeating.\n_________________________")

        if response["httpStatus"] == "Created":
            # save the created id
            uid = response["response"]["uid"]
            print(uid, "created")
            created.append(uid)
            print("\n\n 5. Retrieving newly created item with GET.\n_________________________")
            # retreive the created version and compare with the POST to work our readonly attributes
            myGETcheck= apicall("/api/"+ep+"/"+uid)
            myGETcheck.set_host("http://localhost:8080")
            myGETcheck.append_queries("fields=:all")
            myGETcheck.send_request("get",False)
            #print("_______________________PL")
            #print(myPayload)
            #print("_______________________RESP")
            resp = myGETcheck.response
            if print_response:
                print(myGETcheck.response_json())

            print("\n\n 6. Comparing POST payload with GET response.\n_________________________")
            dc=diff_checker(exam[0],resp)
            dc.report_diffs()
            dl=dc.get_difflist()
            print("ReadOnly items:",dl)
            myEP.set_attributes(dl,"readOnly") 







    # loop round this while there is a required param
    print("\n\n 7. Generating POST (create) request with empty payload.\n_________________________")
    status="NotRun"
    safety=0
    while status != "Created":
        safety += 1
        if safety > 100:
            break
        myEP.create_payload(mode="minimal")
        exam=myEP.get_payload()
        myPayload=json.dumps(exam, sort_keys=True, indent=2, separators=(',', ': '))
        if print_response:
            print(myPayload)
        myPOST.set_payload(exam[0])
        myPOST.send_request("post",False)
        #print(myPOST.response_json())
        response = json.loads(myPOST.response_json())
        status = response["httpStatus"]
        if response["status"] == "ERROR":
            for i in response["response"]["errorReports"]:
                print(i["message"])
                myEP.add_requirement(i["errorProperty"])
                print("\n\n  - adding",i["errorProperty"],"and repeating.\n_________________________")
        if response["httpStatus"] == "Created":
            # save the created id
            uid = response["response"]["uid"]
            print(uid, "created 7")
            created.append(uid)

    print("Required items:",myEP.get_required())
    mySchema = myEP.get_schema()



    # delete the items we have created up to this point
    print("\n\n 8. Generating DELETE request for previously created items.\n_________________________")
    for uid in created:
        myDELETE=apicall("/api/"+ep+"/"+uid)
        myDELETE.set_host(dhis2instance)
        myDELETE.send_request("delete",False) 
        if print_response:
            print(myDELETE.response_json())
        #could check the correct uid is reported back here
        created.pop(0)

    # catch unique values
    # correct them
    # generate a POST with all writable attributes
    print("\n\n 9. Generating POST (create) request with payload of all writable attributes.\n_________________________")
    sameseed=2
    unique_seed=4
    myEP.reseed(sameseed)
    myEP.create_payload(mode="writable")
    exam=myEP.get_payload()
    myPayload=json.dumps(exam, sort_keys=True, indent=2, separators=(',', ': '))
    #print(myPayload)
    myPOST.set_payload(exam[0])
    myPOST.send_request("post",False)
    response = json.loads(myPOST.response_json())
    status = response["httpStatus"]
    if response["httpStatus"] == "Created":
        # save the created id
        uid = response["response"]["uid"]
        print(uid, "created 9")
        created.append(uid)

        # now send again and test for conflicts
        status="NotRun"
        safety=0
        while status != "Created":
            safety += 1
            if safety > 10:
                break

            myPOST.send_request("post",False)
            response = json.loads(myPOST.response_json())
            status = response["httpStatus"]
            uniq=[]
            if response["status"] == "ERROR":
                if print_response:
                    print(myPOST.response_json())
                for i in response["response"]["errorReports"]:
                    print(i["message"])
                    try:
                        unique_prop = i["errorProperty"]
                    except KeyError:
                        unique_prop = "id"
                uniq.append(unique_prop)
                myEP.set_attributes(uniq,"unique")
                myEP.reseed(sameseed)
                myEP.reseed(unique_seed)
                unique_seed *= 2
                myEP.create_payload(mode="writable")
                exam=myEP.get_payload()
                myPOST.set_payload(exam[0])

            if response["httpStatus"] == "Created":
                # save the created id
                uid = response["response"]["uid"]
                print(uid, "created 9B")
                created.append(uid)
    else:
        if print_response:
            print(myPOST.response_json())
        exit()
    # send
    # send again
    # check for errors and repeat after recording an modifying the conflict 

    

    # delete the items we have created up to this point
    print("\n\n 10. Generating DELETE request for previously created items.\n_________________________")
    for uid in created:
        myDELETE=apicall("/api/"+ep+"/"+uid)
        myDELETE.set_host(dhis2instance)
        myDELETE.send_request("delete",False) 
        if print_response:
            print(myDELETE.response_json())
        #could check the correct uid is reported back here

    return mySchema



if __name__ == "__main__":
    components = {}
    for path in ["constants","dashboards", "categories", "categoryOptions"]:
        components[path] = explore_paths("http://localhost:8080",path)
        outfile= open("/home/philld/dhis2/api/server_logs/bigdata/ns.json",'w')
        outfile.write(json.dumps(components , sort_keys=True, indent=2, separators=(',', ': ')))
        outfile.close()
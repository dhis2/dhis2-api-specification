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

from dhis2api.explorer import endpoint_explorer
from dhis2api.explorer import specsorter
import json
from pprint import pprint





if __name__ == "__main__":
    components = {}
    #mypaths = ["constants","dashboards", "categoryCombos","categories", "categoryOptions","me"]
    #mypaths = ["organisationUnits","constants","dashboards","categoryCombos","categories", "categoryOptions"]
    mypaths = ["documents"]
    #mypaths = []

    specfile="../../docs/spec/newbase_openapi.json"
    specfilei="../../docs/spec/input_openapi.json"
    specfileo="../../docs/spec/output_openapi.json"
    ofile=open(specfile,'r')
    openapi = json.load(ofile)
    ofile.close()

    outfile= open(specfilei,'w')

    ssi = specsorter(openapi)
    outfile.write(json.dumps(ssi.sortspec() , sort_keys=True, indent=2, separators=(',', ': ')))
    outfile.close()

    #prelim="../../docs/input/schemas_api.json"
    prelim="../../docs/input/schemas.json"
    pre=open(prelim,'r')
    preliminary = json.load(pre)
    pre.close()

    #ep="../../docs/input/metadata.json"
    ep="../../docs/input/endpoints_test.json"
    epfile=open(ep,'r')
    eps = json.load(epfile)
    epfile.close()

    eps = []
    eps0 = []

    for p in preliminary["schemas"]:
        try:
            ep = p["apiEndpoint"].split("/api/")[1]
            print(p["metadata"],ep)
            if p["metadata"]:
                eps.append(ep)
        except KeyError:
            pass


    for path in eps:
        print("PATH________________________________:",path)

        single = path.split('/')[0].rstrip('s')
        if single[-2:] == 'ie':
            single = single[:-2]+'y'
        print("single:",single)
        prelimspec = None
        try:
            prelimspec = preliminary[single]
        except KeyError:
            pass

        # pprint(openapi["paths"]["/attributes"])

        epx = endpoint_explorer("http://localhost:8080",path,openapi,prelimspec)
        epx.explore()
        openapi2 = epx.get_schema()

        # print("________RETURNED________")
        # pprint(openapi2["paths"]["/attributes"])

        sso = specsorter(openapi2)
        

        outfile= open(specfileo,'w')
        outfile.write(json.dumps(sso.sortspec() , sort_keys=True, indent=2, separators=(',', ': ')))
        #json.dump(openapi2,outfile)
        outfile.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For metadata objects, it is not valid for the sharing access pattern to have
entries in the 3rd or 4th position
e.g. "rwr-----" is invalid but "rw------" is valid
This script checks the sharing of all metadata objects and sets the 3rd and
4th positions to "-" if necessary.

Run with:
python3 sharefixer.py -u <user> -p <password> -s <server> -m <mode>

Or for usage info:
python3 sharefixer.py -h

@author: philld
"""

import requests
import json
import re
import argparse
import logging

# create logger
logger = logging.getLogger('sharefixer')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

parser = argparse.ArgumentParser(description='Find and fix metadata objects with invalid sharing.')
parser.add_argument('-u','--user', action="store", help='dhis2 user', required=True)
parser.add_argument('-p','--password', action="store", help='dhis2 password', required=True)
parser.add_argument('-s','--server', action="store", help='dhis2 server instance. e.g. https://debug.dhis2.org/2.36dev', required=True)
parser.add_argument('-m','--mode', action="store", help='"check" (default) to list or "fix" to post the changes', default="check", required=False)
args = parser.parse_args()

AUTH=(args.user, args.password)


response = requests.get(args.server+"/api/schemas.json",auth=AUTH)

count=0

mode=args.mode  # "fix" or "check"

for s in response.json()['schemas']:
    # loop over all metadata types that are not data shareable
    if "apiEndpoint" in s and not s["dataShareable"]:
        logger.info("Checking: "+s["apiEndpoint"])

        sing = s["singular"]
        
        res = requests.get(s["apiEndpoint"]+".json",auth=AUTH)
        
        try:
            objs = res.json()

            for o in objs:
                # loop over all objects with the metadata type
                if o != "pager":
                    for ob in objs[o]:
                        #print(ob['id'])
                        
                        # use the sharing endpoint to get/set sharing for the object
                        share_ep = args.server+"/api/sharing?"+"type="+sing+"&id="+ob['id']
                        ress = requests.get(share_ep,auth=AUTH)

                        # convert the sharing object to string to simplify the pattern correction
                        myshare = json.dumps(ress.json())
                        mydiff = re.sub(r'([rwx-]{2})([rwx-]{2})([rwx-]{4})',r'\1--\3',myshare)
                        # if applying the correction causes a change, then post back the changes
                        if mydiff != myshare:
                            logger.info("Invalid sharing on object: "+ob['id']+":"+ob['displayName'])
                            # print(json.dumps(ress.json(),indent=2))
                            if mode == "fix":
                                logger.info("Updating...")
                                myob = json.loads(mydiff)["object"]
                                payload = {
                                    "object": {
                                        "publicAccess": myob["publicAccess"],
                                        "externalAccess": myob["externalAccess"],
                                        "user": myob["user"],
                                        "userAccesses": myob["userAccesses"],
                                        "userGroupAccesses": myob["userGroupAccesses"]
                                    }
                                }
                                #print(json.dumps(payload,indent=2))
                            
                                postr = requests.post(share_ep, auth=AUTH, json=payload)
                                print(postr.json())
                                count += 1

                        
        except json.decoder.JSONDecodeError:
            pass
        except TypeError:
            pass
        except KeyError:
            pass

logger.info("Done. Updated "+str(count)+" objects.")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 15:20:46 2020

Copyright (c) 2020, University of Oslo
All rights reserved.


@author: philld
"""
import json
import argparse
import squarify
import requests



class orgenerator:

    # constructor
    def __init__(self,args):

        self.BATCH=int(args.batch)
        self.SERVER=args.server
        self.AUTH=(args.user, args.password)
        self.X = args.coords[0]
        self.Y = args.coords[1]
        self.WIDTH = args.coords[2]
        self.HEIGHT = args.coords[3]
        self.MAX_CHILDREN=int(args.kids)

        self.top_level="uio"
        self.levels=["National","Regional","District","Chiefdom","Village","Facility","Vaccination Site"]
        max_levels=int(args.levels)
        self.MAX_LEVELS=len(self.levels)
        if max_levels < self.MAX_LEVELS:
            self.MAX_LEVELS=max_levels
        self.top_level="uio"
        self.names=["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
        # self.filename=args.outfile
        self.TOTAL=0
        self.TO_SEND=0
        self.myorgs={}

        self.total_estimate = 1
        for t in range(0,self.MAX_LEVELS):
            self.total_estimate+=self.MAX_CHILDREN**t


    def estimate(self):
        print(self.MAX_LEVELS,"levels with",self.MAX_CHILDREN,"children will give",self.total_estimate,"OUs.")


    def final(self):

        # send any remaining orgs
        if self.TO_SEND > 0:
            print("POST final batch...")
            self.import_orgs()

        print(self.TOTAL, "OU objects created")


    def import_orgs(self):
        # print(json.dumps(self.myorgs))
        url = self.SERVER + "/api/metadata.json?importMode=COMMIT&identifier=CODE&importReportMode=ERRORS&preheatMode=REFERENCE&importStrategy=CREATE_AND_UPDATE&atomicMode=ALL&mergeMode=MERGE&flushMode=AUTO&skipSharing=false&skipValidation=false&async=false&inclusionStrategy=NON_NULL&format=json"
        r = requests.post(
            url,
            data=json.dumps(self.myorgs),
            auth=self.AUTH,
            headers={'content-type': 'application/json'}
        )
        print("STATUS:",r.status_code)
        # print(r.json())

        #reset myorgs
        self.myorgs={"organisationUnits": []}
        self.TO_SEND = 0


    def ou_toplevel(self):

        X=self.X
        Y=self.Y
        WIDTH=self.WIDTH
        HEIGHT=self.HEIGHT

        obj={ "name": self.top_level, "shortName": self.top_level, "level": 1, "openingDate": "2000-01-01T00:00:00.000"}
        co = [[[X,Y],[X+WIDTH,Y],[X+WIDTH,Y+HEIGHT],[X,Y+HEIGHT],[X,Y]]]
        obj["geometry"]= {"type": "Polygon","coordinates": co}
        obj["code"]= 'UIO-OU-0'
        # myorgs["organisationUnits"].append(obj)
        self.TOTAL+=1
        self.TO_SEND+=1
        return obj


    def ou(self,name,level):

        hierarchy = []
        subunits = len(self.names)
        if self.MAX_CHILDREN < subunits:
            subunits = self.MAX_CHILDREN

        if level < self.MAX_LEVELS:
            for i in range(0,subunits):
                n=self.names[i]
                ou_name = name+'-'+n
                # call recursively to populate the next level
                ou_level = level + 1
                # print(level, ou_name)
                children = self.ou(ou_name,ou_level)
                hierarchy.append({ "name": ou_name, "shortName": ou_name, "level": level, "openingDate": "2000-01-01T00:00:00.000","children":children})
            return hierarchy
        else:
            for i in range(0,subunits):
                n=self.names[i]
                ou_name = name+'-'+n
                # print(level, ou_name)
                hierarchy.append({ "name": ou_name, "shortName": ou_name, "level": level, "openingDate": "2000-01-01T00:00:00.000"})
            return hierarchy



    def ou_builder(self,ob,parent=None):

        obj={ "name": ob["name"], "shortName": ob["name"], "level": ob["level"], "openingDate": ob["openingDate"],"geometry":ob["geometry"]}
        obj["code"]= ob['name'].replace('uio','UIO-OU-0')
        if parent != None:
            obj["parent"]={"code":parent.replace('uio','UIO-OU-0')}
        self.myorgs["organisationUnits"].append(obj)

        self.TOTAL+=1
        self.TO_SEND+=1
        if self.TO_SEND >= self.BATCH:
            print(self.TOTAL,"/",self.total_estimate,": POST batch...")
            self.import_orgs()

        # print(obj)


    # add coordinates and send
    def coordinates(self,orgtree, x, y, width, height):

        if orgtree["level"] == 1:
            self.ou_builder(orgtree)

        # if type(orgtree) is dict:
        if "children" in orgtree:
            values = [100]*len(orgtree["children"])

            values = squarify.normalize_sizes(values, width, height)
            rects = squarify.squarify(values, x, y, width, height)

            index=0
            for c in orgtree["children"]:
                x = rects[index]['x']
                y = rects[index]['y']
                dx = rects[index]['dx']
                dy = rects[index]['dy']

                if "children" in c:
                    co = [[[x,y],[x+dx,y],[x+dx,y+dy],[x,y+dy],[x,y]]]
                    c["geometry"]= {"type": "Polygon","coordinates": co}
                else:
                    c["geometry"]= {"type": "Point","coordinates": [x+dx/2,y+dy/2]}

                # print(c)
                self.ou_builder(c,orgtree["name"])
                if "children" in c:
                    self.coordinates(c,x,y,dx,dy)
                index+=1

    def orgUnitLevels(self):
        self.myorgs={"organisationUnitLevels": []}
        for l in range(0,self.MAX_LEVELS):
            name = self.levels[l]
            # print(l, name)
            obj = { "name": name, "shortName": name, "level": l+1, "CODE": 'UIO-OUL-'+str(l)}
            self.myorgs["organisationUnitLevels"].append(obj)

    def orgUnits(self):

        orgtree=self.ou_toplevel()
        children=self.ou(self.top_level,2)
        orgtree["children"]=children

        self.coordinates(orgtree,self.X,self.Y,self.WIDTH,self.HEIGHT)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Generate OUs for an empty database.')
    parser.add_argument('-u','--user', action="store", help='dhis2 user', required=False)
    parser.add_argument('-p','--password', action="store", help='dhis2 password', required=False)
    parser.add_argument('-s','--server', action="store", help='dhis2 server instance', required=True)  # e.g. https://play.dhis2.org/2.34dev
    parser.add_argument('-l','--levels', action="store", help='maximum OU levels', required=False) # e.g. tracker_dev
    parser.add_argument('-b','--batch', action="store", help='batch size for import', required=False)
    parser.add_argument('-c','--coords', nargs=4, action="append", type=int, help='coordinates specifying boundary border [x,y,dx,dy]', required=False)
    parser.add_argument('-k','--kids', action="store", help='maximum sub-units (children or "kids") at each level', required=False)
    parser.add_argument('-e','--estimate', action="store_true", help='just display an estimate of the total number of OUs, and exit')

    parser.set_defaults(levels=6,kids=10,user='admin',password='district',batch=1000, coords=[10,10,10,10])
    args = parser.parse_args()

    OUgen = orgenerator(args)
    if args.estimate:
        OUgen.estimate()
    else:
        OUgen.orgUnitLevels()
        #send the Levels first
        OUgen.import_orgs()
        OUgen.orgUnits()
        OUgen.final()

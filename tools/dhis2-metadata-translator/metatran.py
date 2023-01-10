#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2022, University of Oslo
All rights reserved.


@author: philld
"""

import requests
import json
import configargparse
import argparse
import threading
import concurrent.futures
import os
import glob
import sys
import tempfile
from translayer import tx3
import hashlib
from bs4 import BeautifulSoup
import re
import copy
from jinja2 import Template
import logging
import slugify

console = logging.StreamHandler()
mt_logger = logging.getLogger('mtran')
mt_logger.addHandler(console)



class d2t():

    def __init__(self,server, user, password, project, resource, base, tx_org='', tx_token=''):

        mt_logger.setLevel(20)
        # DHIS2 connection details
        self.dhis2_server = server
        self.dhis2_user = user
        self.dhis2_password = password
        self.dhis2_AUTH=(self.dhis2_user, self.dhis2_password)
        self.fromDHIS2={}
        self.customForms={}
        self.translatable_fields={}
        self.translatable_max_chars={}

        # package details
        self.package_filter = None

        # set the default format to STRUCTURED_JSON
        self.tx_i18n_type = "STRUCTURED_JSON"
        self.tx_resource="tempfile"

        # We need to map language codes that DHIS2 doesn't support natively
        # uz@Cyrl --> uz
        # uz@Latn --> uz_UZ
        self.langmap={'uz@Cyrl':'uz','uz@Latn':'uz_UZ'}

        if project:
            # transifex details (if a transifex project is defined)
            self.tx_project=project
            self.tx_resource_name=resource
            self.tx_resource=slugify(resource)
            
            #create an instance of a transifex organisation (pass organisation slug and transifex API token)
            self.tx = tx3.tx(tx_org,tx_token,log_level=10)
            self.txp = self.tx.project(self.tx_project)

            if self.txp.resource(self.tx_resource):
                self.tx_i18n_type = self.txp.resource(self.tx_resource).attributes['i18n_type']


        self.base_lang = 'en'
        if base:
            self.base_lang = base.split(':')[0]

        mt_logger.info("Current main locale: "+self.base_lang)
        self.form_text_prefix = 'formText_'
        self.localiser_script_id = 'localiser'
              
        class tmpdir():
            def __init__(self):
                self.name = "i18n"

        self.mode = "SYNC"  #  "SYNC" or "CONVERT"

        # self.localisation_dir =  tempfile.TemporaryDirectory(prefix="i18n")  # use this for cleanliness
        self.localisation_dir =  tmpdir()  # use this instead of above for debugging
        os.makedirs(self.localisation_dir.name, exist_ok=True)
        self.locale_file_pattern = self.localisation_dir.name + "/{m}/{p}_{l}.json"
        self.locale_file_pattern_prefix = self.localisation_dir.name + "/{m}/{p}_"
        self.source_file_pattern = self.localisation_dir.name + "/{m}/{p}.json"
        self.locale_file_glob_pattern = self.localisation_dir.name + "/{m}/{p}_*.json"
        self.all_file_pattern = self.localisation_dir.name + "/{m}/{p}*.json"

    def set_filter(self,package_url):
        """
        We try to get the list of the object IDs from the package file, and use that to filter
        the objects we translate
        """
        export_response=requests.get(package_url)
        if export_response.status_code == requests.codes['OK']:
            export=json.loads(export_response.text)
            self.package_filter = set()
            for m in self.__find_ids__("id", export):
                self.package_filter.add(m)
            return True
       
        # return false if not set
        return False
        
    def __find_ids__(self, key, var, parent=""):
        """
        Recursive function to find IDs in a package file
        """
        
        if hasattr(var,'items'):
                for k, v in var.items():
                    if k == key:
                        yield v
                    if isinstance(v, dict):
                        for result in self.__find_ids__(key, v, k):
                            yield result
                    elif isinstance(v, list):
                        for d in v:
                            for result in self.__find_ids__(key, d, k):
                                yield result

    def dhis2_to_json(self):
        """
        Extracts the translatable metadata from the DHIS2 instance and converts
        into a JSON format suitable for transifex.
        """

        print("Pulling translatable metadata from", self.dhis2_server, "...")

        # first we will find out which fields are translatable, and store them with the resource.
        tflds = {}
        tchar = {}
        dhis2_schemas = requests.get(self.dhis2_server+"/api/schemas.json",auth=self.dhis2_AUTH)
        if dhis2_schemas.status_code == 401:
            sys.exit("DHIS2 user not authorised! Aborting transifex synchronisation.")

        for schema in dhis2_schemas.json()["schemas"]:
            # mt_logger.debug(schema['name'])
            if schema['translatable'] == True and 'apiEndpoint' in schema:
                # print("\t",schema['name'])
                # print("\t\t",schema['href'])
                fields= [t for t in schema["properties"] if 'translationKey' in t]
                mapped_fields={}
                max_chars={}
                for f in fields:
                    mapped_fields[f['fieldName']]=f['translationKey']
                    max_chars[f['translationKey']]=f['length']
                    tflds[f['fieldName']]=f['translationKey']
                    tchar[f['translationKey']]=f['length']
                    # print(schema['name']+"."+f['fieldName'],"==>",f['translationKey'])
                self.translatable_fields[schema['collectionName']]=mapped_fields
                self.translatable_max_chars[schema['collectionName']]=max_chars

        # print(json.dumps(tflds, indent=2, separators=(',', ': ')))
        # print(json.dumps(tchar, indent=2, separators=(',', ': ')))


        locales={}
        locales["source"]={}
        for resource in copy.deepcopy(self.translatable_fields):
            # print(resource, translatable_fields[resource])
            tfs = ''
            for transField in self.translatable_fields[resource]:
                tfs += ','+transField
            collection = (requests.get(self.dhis2_server+"/api/"+resource+".json"+"?fields=id,translations,htmlCode"+tfs+"&paging=false",auth=self.dhis2_AUTH)).json()[resource]

            # Apply the filter for a specific package here
            if self.package_filter:
                collection = [x for x in collection if x['id'] in self.package_filter]

            for element in collection:

                # if we want to translate custom forms
                self.get_custom_form_translations(resource, element)
                try:
                    # form_dict = self.customForms[resource][element['id']]['form_dict']
                    form_trans = self.customForms[resource][element['id']]['translations']
                    # if self.base_lang in form_dict:
                    #     print(json.dumps(form_dict[self.base_lang], sort_keys=True, indent=2, ensure_ascii=False))

                    # if there was a custom form with translations, add the translations to the current element
                    element['translations'] += form_trans

                except KeyError:
                    pass


                translations= element["translations"]
                if translations != []:
                    if resource not in self.fromDHIS2:
                            self.fromDHIS2[resource] = {}
                    if element['id'] not in self.fromDHIS2[resource]:
                        self.fromDHIS2[resource][element['id']] = {}
                        self.fromDHIS2[resource][element['id']]['translations'] = translations
                    else:
                        self.fromDHIS2[resource][element['id']]['translations'] += translations
                    # print(resource, element['id'], translations)

                for transField in self.translatable_fields[resource]:
                    transFieldKey = self.translatable_fields[resource][transField]
                    # we can only create translation strings in transifex when a source base field has a value
                    if transField in element:
                        matching_translations=[m for m in translations if m['property'] == transFieldKey]
                        # print( transField, element[transField])
                        char_limit = self.translatable_max_chars[resource][transFieldKey]
                        if resource not in locales['source']:
                            locales['source'][resource] = {}
                        if element['id'] not in locales['source'][resource]:
                            locales['source'][resource][element['id']] = {}

                        if self.tx_i18n_type == 'STRUCTURED_JSON':
                            locales['source'][resource][element['id']][transFieldKey] = { "string":element[transField], "character_limit":char_limit}
                        else:
                            locales['source'][resource][element['id']][transFieldKey] = element[transField]

                        for m in matching_translations:
                            if m['locale'] not in self.langmap.keys():
                                if m['locale'] not in locales:
                                    locales[m['locale']]={}
                                if resource not in locales[m['locale']]:
                                    locales[m['locale']][resource] = {}
                                if element['id'] not in locales[m['locale']][resource]:
                                    locales[m['locale']][resource][element['id']] = {}

                                if self.tx_i18n_type == 'STRUCTURED_JSON':
                                    locales[m['locale']][resource][element['id']][transFieldKey] = { "string":m['value'], "character_limit":char_limit}
                                else:
                                    locales[m['locale']][resource][element['id']][transFieldKey] = m['value']

                    else:
                        # check and warn if we have translations with no base string
                        matching_translations=[m for m in translations if m['property'] == transFieldKey]
                        for m in matching_translations:
                            print("WARNING: Translation without base string for",resource,">",element['id'],":", m)

        mfile=open(self.localisation_dir.name + "/" + "fromDHIS2.json",'w')
        mfile.write(json.dumps(self.fromDHIS2, sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
        mfile.close()

        for locale in locales:
            locale_filename = self.locale_file_pattern.format(m=self.mode, p=self.tx_resource, l=locale)
            if locale == "source":
                locale_filename = self.source_file_pattern.format(m=self.mode, p=self.tx_resource)

            os.makedirs(os.path.dirname(locale_filename), exist_ok=True)
            jsonfile= open(locale_filename,'w')
            jsonfile.write(json.dumps(locales[locale] , sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
            jsonfile.close()

        cfile=open(self.localisation_dir.name + "/" + "fromFORMSs.json",'w')
        cfile.write(json.dumps(self.customForms, sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
        cfile.close()

    def json_to_transifex(self, force_new=False):
        print("Pushing source strings to transifex...")

        path=self.source_file_pattern.format(m=self.mode, p=self.tx_resource)
                
        if not self.txp.resource(self.tx_resource) or force_new:
            self.txp.new_resource(self.tx_resource_name,self.tx_resource,'STRUCTURED_JSON',path)
        else:
            # push a resource (source)
            self.txp.resource(self.tx_resource).push(path)

    def transifex_to_json(self):
        print("Pulling translations from transifex...")

        # get project languages
        langs = self.txp.languages()

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            for l in langs:
                print(l.code)
                
                # We need to map language codes that DHIS2 doesn't support natively
                mapped_language_code = l.code
                if l.code in self.langmap.keys():
                    mapped_language_code = self.langmap[l.code]

                path=self.locale_file_pattern.format(m=self.mode, p=self.tx_resource, l=mapped_language_code)
                # pull translation
                # self.txp.resource(self.tx_resource).pull(l.code,path,mode="onlytranslated")
                executor.submit(self.txp.resource(self.tx_resource).pull,l.code,path)

    def json_to_transifex_langs(self):
        print("Pushing translations to transifex...")

        # get project languages
        langs = self.txp.languages()

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            for l in langs:
                print(l.code)
                
                # We need to map language codes that DHIS2 doesn't support natively
                mapped_language_code = l.code
                if l.code in self.langmap.keys():
                    mapped_language_code = self.langmap[l.code]

                path=self.locale_file_pattern.format(m=self.mode, p=self.tx_resource, l=mapped_language_code)
                # pull 
                # self.txp.resource(self.tx_resource).push(path,l.code)
                executor.submit(self.txp.resource(self.tx_resource).push,path,l.code)

    def transifex_source_to_json(self):
        print("Pulling source from transifex...")

        # pull translation
        path=self.source_file_pattern.format(m=self.mode, p=self.tx_resource)
        self.txp.resource(self.tx_resource).pull_source(path)

    def resolve_updates(self):

        locales = {}

        for localefile in glob.iglob(self.locale_file_glob_pattern.format(m=self.mode, p=self.tx_resource)):
            # print(localefile)

            lfile=open(localefile,'r')
            locale = json.load(lfile)
            lfile.close()

            locale_name = localefile.replace(self.locale_file_pattern_prefix.format(m=self.mode, p=self.tx_resource),'').split('.')[0]
            if locale_name != self.base_lang:
                # print("locale", locale)
                for resource in locale:
                    # print("\tresource", resource)
                    for id in locale[resource]:
                        for property in locale[resource][id]:

                            # form text translations are written directly into the custom form
                            property_value = locale[resource][id][property]["string"]
                            if self.form_text_prefix in property:
                                if locale_name not in self.customForms[resource][id]['form_dict']:
                                    self.customForms[resource][id]['form_dict'][locale_name] = {}
                                self.customForms[resource][id]['form_dict'][locale_name][property] = property_value
                            else:
                                # print("property",property)
                                if self.tx_i18n_type == 'STRUCTURED_JSON':
                                    if property_value:
                                        translation = [{ "property": property, "locale": locale_name, "value": property_value }]
                                        entry = { resource : { id : { "translations" : translation }}}
                                        self.merge_translations(locales,entry)
                                else:
                                    property_value = locale[resource][id][property]
                                    if property_value:
                                        translation = [{ "property": property, "locale": locale_name, "value": property_value }]
                                        entry = { resource : { id : { "translations" : translation }}}
                                        self.merge_translations(locales,entry)


            # locales.merge(locale)

        # print(json.dumps(locales, sort_keys=True, indent=2, separators=(',', ': ')))

        mfile= open(self.localisation_dir.name + "/" + "toMeta.json",'w')
        mfile.write(json.dumps(locales, sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
        mfile.close()

        # compare downloaded translations with those pulled from DHIS2, so that we only have
        # to push back updates
        toDHIS2 = self.minimise_translations(self.fromDHIS2,locales)

        mfile= open(self.localisation_dir.name + "/" + "toMetaMin.json",'w')
        mfile.write(json.dumps(toDHIS2, sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
        mfile.close()

        return toDHIS2

    def json_to_dhis2(self):

        print("Pushing translations to",self.dhis2_server,"...")

        toDHIS2 = self.resolve_updates()

        for resource in toDHIS2:
            for id in toDHIS2[resource]:
                payload = json.dumps(toDHIS2[resource][id], sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': '))
                url = self.dhis2_server+"/api/"+resource+"/"+id+"/translations"
                # print("PUT ",url)
                r = requests.put(url, data=payload,auth=self.dhis2_AUTH)
                print(r.status_code,": PUT ",url)
                print("payload:",payload)
                if r.status_code > 204:
                    print(payload)
                    print(r.headers)
        
        for resource in self.customForms:
            for element in self.customForms[resource]:
                print("want to update html:",element)
                newForm = {}
                el = { 'id': element, 'htmlCode': ''}
                newForm['htmlCode'] = self.set_custom_form_translations(resource, el)                
                url = self.dhis2_server+"/api/"+resource+"/"+element
                r = requests.patch(url, json=newForm,auth=self.dhis2_AUTH,params={'mergeMode': 'REPLACE'})
                print(r.status_code,": PUT ",url)
                if r.status_code > 204:
                    print(payload)
                    print(r.headers)

    def merge_translations(self, dict1, dict2):
        """ Recursively merges dict2 into dict1 """
        if not isinstance(dict1, dict) or not isinstance(dict2, dict):
            return dict1 + dict2
        for k in dict2:
            if k in dict1:
                dict1[k] = self.merge_translations(dict1[k], dict2[k])
            else:
                dict1[k] = dict2[k]
        return dict1

    def compare_translations(self, t1, t2):

        if t1['locale'] == t2['locale']:
            if t1['property'] == t2['property']:
                if t1['value'] == t2['value']:
                    # translations are the same
                    return 0
                else:
                    # different value
                    return 1
            else:
                # different property
                return -2
        else:
            # different locale
            return -1

    def minimise_translations(self, in_trans, out_trans):
        """ Keeps only altered sets of translations """

        tin = in_trans.copy()
        if isinstance(out_trans, list):
            
            i_match = 0
            i_new = 0
            for o in out_trans:
                # s_out = json.dumps(o , sort_keys=True)
                comp = 0
                for i in in_trans:
                    # s_in = json.dumps(i , sort_keys=True)
                    comp = self.compare_translations(i,o)
                    if comp in [0,1]:
                        if comp == 1:
                            for t in tin:
                                if t['locale'] == o['locale'] and t['property'] == o['property']:
                                    t['value'] = o['value']
                        i_match += comp
                        break

                if comp < 0:
                    # if comp is less than zero at this point then the translation is new
                    i_new = 1
                    tin.append(o)

            if i_match == 0 and i_new == 0:
                # there is nothing new for this object
                return []
            else:
                # there are differences
                # we don't want to lose any translations that are only in DHIS2, so we
                # take that and merge any changes
                return tin

            return []

        delta = {}
        for k in out_trans:
            if k in in_trans:
                delta[k] = self.minimise_translations(in_trans[k], out_trans[k])
                if len(delta[k]) == 0:
                    delta.pop(k,None)
            else:
                delta[k] = out_trans[k]

        return delta



    def set_custom_form_translations(self, resource, element):


        if 'htmlCode' in element and element['id'] in self.customForms[resource] and 'htmlCode_new' in self.customForms[resource][element['id']]:
            
            html_code = self.customForms[resource][element['id']]['htmlCode_new']
            soup = BeautifulSoup(html_code, "html.parser")
            
            if resource not in self.customForms:
                # we didn't extract this so cannot push any changes back. Ignore.
                self.customForms[resource] = {}
            else:
                print("\tInserting translations into custom form",resource,element['id'])

                soup = BeautifulSoup(html_code, "html.parser")
                
                localiser_script = self.__extract_localiser_script__(soup)
                if not localiser_script:
                    # there is no localiser script in the htmlCode, so we add one.
                    localiser_script = soup.new_tag('script', id=self.localiser_script_id)
                    soup.insert(len(soup.contents), localiser_script)

                with open('src/template.js') as f:
                    script_template=f.read()
                t = Template(script_template)
                form_dict = self.customForms[resource][element['id']]['form_dict']
                localiser_script.string = t.render(form_dict=json.dumps(form_dict, indent=4, sort_keys=True, ensure_ascii=False))
                

                return str(soup)

    def __get_js_object__(self, offset, str):
        count = 0
        len = offset
        start = 0
        end = 0
        for i in str[offset:]:
            len +=1
            if i == "{":
                count += 1
                if count == 1:
                    start = len -1
            elif i == "}":
                count -= 1
                if count == 0:
                    end = len
                    return json.loads(str[start:end])

    def get_custom_form_translations(self, resource, element):

        form_trans = []
        old_to_new = {}
        form_dict = {}
        if 'htmlCode' in element:
            # print('HTML:',resource, element['id'])
            html_code = element['htmlCode']
            soup = BeautifulSoup(html_code, "html.parser")

            langspans = soup.findAll("span", {"class": "lang"})

            if langspans:
                # there are spans with class "lang" in this form, so it should be localised
                print("\tExtracting localisation strings from custom form",resource,element['id'])
                if resource not in self.customForms:
                    self.customForms[resource] = {}
                if element['id'] not in self.customForms[resource]:
                    self.customForms[resource][element['id']] = {"htmlCode":html_code, "spans":{}}

                localiser_script = self.__extract_localiser_script__(soup)

                if localiser_script:
                    # print(parse(formscript.string)[0]['declarations'][0])
                    match = re.search("arrLang =", localiser_script.string)
                    form_dict = self.__get_js_object__(match.start(),localiser_script.string)
                    
                    localiser_script['id'] = self.localiser_script_id
                    # remove the content of the html, we'll build it again when we pull translations back
                    localiser_script.string = ''  


                for langspan in langspans:
                    source = langspan.string.strip()
                    key = self.form_text_prefix + hashlib.md5(source.encode()).hexdigest()

                    # add key to translatable fields for metadata
                    # if resource_based:
                    self.translatable_fields[resource][key] = key
                    self.translatable_max_chars[resource][key] = 2147483647
                    
                    self.customForms[resource][element['id']]['spans'][key] = source
                    element[key] = source
                    # create a map of old to new keys
                    try:
                        old_to_new[langspan['langkey']] = key
                    except KeyError:
                        pass
                    langspan['langkey'] = key
                    
                # self.customForms[resource][element['id']]['htmlCode_new'] = str(soup)
                
                for l in form_dict:
                    # print(json.dumps(form_dict[l], sort_keys=True, indent=2, ensure_ascii=False))
                    # print(json.dumps(old_to_new, sort_keys=True, indent=2, ensure_ascii=False))
                    if '' in form_dict[l]:
                        del form_dict[l]['']
                    f_dic = {}
                    for k, v in form_dict[l].items():

                        if k in old_to_new:

                            if l != self.base_lang:
                                new_tran = {"locale":l,"property":old_to_new[k],"value":v}
                                form_trans.append(new_tran)

                            f_dic[old_to_new[k]] = v 
                    form_dict[l] = f_dic

                # if form_dict is empty (did not already exist) start it
                if form_dict == {}:
                    form_dict[self.base_lang] = {}

                for key,source in self.customForms[resource][element['id']]['spans'].items():
                    if key not in form_dict[self.base_lang]:
                        # add any new keys to the base language in the form_dict
                        form_dict[self.base_lang][key] = source


                localiser_script = self.__extract_localiser_script__(soup)
                if not localiser_script:
                    # there is no localiser script in the htmlCode, so we add one.
                    localiser_script = soup.new_tag('script', id=self.localiser_script_id)
                    soup.insert(len(soup.contents), localiser_script)

                with open('src/template.js') as f:
                    script_template=f.read()
                t = Template(script_template)
                localiser_script.string = t.render(form_dict=json.dumps(form_dict, indent=4, sort_keys=True, ensure_ascii=False))
                # we have converted the customForm to support localisation - save it as htmlCode_new
                # (If it already supported localisation, htmlCode_new will represent updated keys and translations)
                self.customForms[resource][element['id']]['htmlCode_new'] = str(soup)
                self.customForms[resource][element['id']]['form_dict'] = form_dict
                self.customForms[resource][element['id']]['translations'] = form_trans

        # return form_dict,form_trans
                # print(json.dumps(form_dict, sort_keys=True, indent=2, ensure_ascii=False))

    def swap_custom_form_translations(self, resource, element):

        form_dict = {}
        if 'htmlCode' in element:
            # print('HTML:',resource, element['id'])
            html_code = element['htmlCode']
            soup = BeautifulSoup(html_code, "html.parser")

            langspans = soup.findAll("span", {"class": "lang"})

            if langspans:
                # there are spans with class "lang" in this form, so it should be localised
                # as long as we have a dictionary

                localiser_script = self.__extract_localiser_script__(soup)
                if localiser_script:
                    
                    print("\tSwapping localisation strings in custom form",resource,element['id'])

                    # extract the dictionary
                    match = re.search("arrLang =", localiser_script.string)
                    form_dict = self.__get_js_object__(match.start(),localiser_script.string)
                    if self.target_lang in form_dict:
                        for langspan in langspans:
                            try:
                                if langspan['langkey'] in form_dict[self.target_lang]:
                                    langspan.string = form_dict[self.target_lang][langspan['langkey']]
                            except KeyError:
                                pass

                        element['htmlCode'] = str(soup)


    def exclude_custom_form_translations(self, resource, element):

        form_dict = {}
        if 'htmlCode' in element:
            # print('HTML:',resource, element['id'])
            html_code = element['htmlCode']
            soup = BeautifulSoup(html_code, "html.parser")

            langspans = soup.findAll("span", {"class": "lang"})

            if langspans:
                # there are spans with class "lang" in this form, so it should be localised
                # as long as we have a dictionary

                localiser_script = self.__extract_localiser_script__(soup)
                if localiser_script:
                    
                    print("\tFiltering localisation strings in custom form",resource,element['id'])

                    # extract the dictionary
                    match = re.search("arrLang =", localiser_script.string)
                    form_dict = self.__get_js_object__(match.start(),localiser_script.string)

                    if self.include_locales:
                        filtered_dict = [f for f in form_dict if f in self.include_locales]
                    else:
                        if self.exclude_locales:
                            filtered_dict = [f for f in form_dict if f not in self.exclude_locales]
                        else:
                            filtered_dict = form_dict

                    with open('src/template.js') as f:
                        script_template=f.read()
                    t = Template(script_template)
                    localiser_script.string = t.render(form_dict=json.dumps(filtered_dict, indent=4, sort_keys=True, ensure_ascii=False))

                    element['htmlCode'] = str(soup)


    def __extract_localiser_script__(self, soup):

        localiser = soup.find('script', id=self.localiser_script_id)

        if not localiser:
            # we didn't find the localiser script by id, it might be an "old" script from Manu tool
            for f_script in soup.findAll("script"):
                if "Applying translations" in f_script.string:
                    # this looks like the Manu script
                    localiser = f_script
                    break

        if localiser:
            return localiser
        else:
            return None


class f2t(d2t):
    def __init__(self, project, resource, package_url, base='', include='', exclude='', tx_org='', tx_token=''):
        d2t.__init__(self,"","","",project, resource, base, tx_org=tx_org, tx_token=tx_token)
        self.package = {}
        self.set_package(package_url)
        if not self.__valid_package__():
            sys.exit("Package file invalid! Aborting.")
        # get the DHIS2 version from the package
        self.DHIS2Version = self.package['package']['DHIS2Version']
        if self.DHIS2Version[0:2] == '2.':
            self.DHIS2Major = self.DHIS2Version[2:4]
        else:
            self.DHIS2Major = self.DHIS2Version[0:2]

        self.__set_schemas__()

        self.package_url = package_url
        self.target_lang = None
        if base and len(base.split(':')) > 1:
            self.target_lang = base.split(':')[1]
        if self.target_lang == self.base_lang:
            self.target_lang = None
        if self.target_lang:
            mt_logger.info("Target main locale: "+self.target_lang)

        self.include_locales = []
        self.exclude_locales = []
        if include:
            self.include_locales = include.split(',')
            # if there are include_locales, then exclusions will be ignored
        else:
            if exclude:
                self.exclude_locales = exclude.split(',')

    def __set_schemas__(self):

        s = open('schemas/'+self.DHIS2Major+'.json','r')
        transfields = json.load(s)
        s.close()

        self.translatable_fields = transfields['translatable_fields']
        self.translatable_max_chars = transfields['translatable_max_chars']


    def set_package(self,package_url):
        """
        We try to get the list of the object IDs from the package file, and use that to filter
        the objects we translate
        """
        if os.path.isfile(package_url):
            f = open(package_url,'r')
            self.package=json.load(f)
            f.close()
            return True
        else:
            export_response=requests.get(package_url)
            if export_response.status_code == requests.codes['OK']:
                self.package=json.loads(export_response.text)
                return True 


        # return false if not set
        return False

    def __valid_package__(self):

        if self.package:
            if 'package' in self.package:
                if 'locale' in self.package['package']:
                    if self.package['package']['locale'] == self.base_lang:
                        return True
                    else:
                        print("Package file base locale is '"+self.package['package']['locale']+"', expected '"+self.base_lang+"'")
        return False

    def file_to_json(self):
        """
        Extracts the translatable metadata from the package file and converts into a JSON format suitable for transifex.
        """

        print("Pulling translatable metadata from", self.package_url, "...")

        translatable_fields = self.translatable_fields
        translatable_max_chars= self.translatable_max_chars

        locales={}
        locales["source"]={}
        # We don't want to modify the original package, so make a deep copy
        # We will modify the copy to make it easy to pull out the custom form strings
        package = copy.deepcopy(self.package)
        for resource in package:
            # skip the object that contains the packages own metadata
            if resource != "package":

                collection = package[resource]
                for element in collection:

                    # if we want to translate custom forms
                    self.get_custom_form_translations(resource, element)
                    try:
                        # form_dict = self.customForms[resource][element['id']]['form_dict']
                        form_trans = self.customForms[resource][element['id']]['translations']
                        # if self.base_lang in form_dict:
                        #     print(json.dumps(form_dict[self.base_lang], sort_keys=True, indent=2, ensure_ascii=False))

                        # if there was a custom form with translations, add the translations
                        element['translations'] += form_trans

                    except KeyError:
                        pass


                    translations= element["translations"]
                    if translations != []:
                        if resource not in self.fromDHIS2:
                            self.fromDHIS2[resource] = {}
                        if element['id'] not in self.fromDHIS2[resource]:
                            self.fromDHIS2[resource][element['id']] = {}
                            self.fromDHIS2[resource][element['id']]['translations'] = translations
                        else:
                            self.fromDHIS2[resource][element['id']]['translations'] += translations

                    if resource in translatable_fields:
                        for transField in translatable_fields[resource]:
                            transFieldKey = translatable_fields[resource][transField]

                            # we can only create translation strings in transifex when a source base field has a value
                            if transField in element:
                                matching_translations=[m for m in translations if m['property'] == transFieldKey]
                                # print( transField, element[transField])
                                # char_limit = translatable_max_chars[transFieldKey]
                                if resource not in locales['source']:
                                    locales['source'][resource] = {}
                                if element['id'] not in locales['source'][resource]:
                                    locales['source'][resource][element['id']] = {}

                                if self.tx_i18n_type == 'STRUCTURED_JSON':
                                    locales['source'][resource][element['id']][transFieldKey] = { "string":element[transField], "character_limit":translatable_max_chars[resource][transFieldKey] }
                                else:
                                    locales['source'][resource][element['id']][transFieldKey] = element[transField]

                                for m in matching_translations:
                                    if m['locale'] not in self.langmap.keys():
                                        if m['locale'] not in locales:
                                            locales[m['locale']]={}
                                        if resource not in locales[m['locale']]:
                                            locales[m['locale']][resource] = {}
                                        if element['id'] not in locales[m['locale']][resource]:
                                            locales[m['locale']][resource][element['id']] = {}

                                        if self.tx_i18n_type == 'STRUCTURED_JSON':
                                            locales[m['locale']][resource][element['id']][transFieldKey] = { "string":m['value'], "character_limit":translatable_max_chars[resource][transFieldKey] }
                                        else:
                                            locales[m['locale']][resource][element['id']][transFieldKey] = m['value']

                            else:
                                # check and warn if we have translations with no base string
                                matching_translations=[m for m in translations if m['property'] == transFieldKey]
                                for m in matching_translations:
                                    print("WARNING: Translation without base string for",resource,">",element['id'],":", m)

        mfile=open(self.localisation_dir.name + "/" + "fromPACK.json",'w')
        mfile.write(json.dumps(self.fromDHIS2, sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
        mfile.close()

        for locale in locales:
            locale_filename = self.locale_file_pattern.format(m=self.mode, p=self.tx_resource, l=locale)
            if locale == "source":
                locale_filename = self.source_file_pattern.format(m=self.mode, p=self.tx_resource)

            os.makedirs(os.path.dirname(locale_filename), exist_ok=True)
            jsonfile= open(locale_filename,'w')
            jsonfile.write(json.dumps(locales[locale] , sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
            jsonfile.close()


        cfile=open(self.localisation_dir.name + "/" + "fromFORMS.json",'w')
        cfile.write(json.dumps(self.customForms, sort_keys=True, indent=2, ensure_ascii=False, separators=(',', ': ')))
        cfile.close()

    def json_to_file(self, filename):

        print("Generating new file",filename,"...")
        if os.path.dirname(filename):
            os.makedirs(os.path.dirname(filename), exist_ok=True)

        toFILE = self.resolve_updates()
        # start with a deep copy of the original package
        newPACK = copy.deepcopy(copy.deepcopy(self.package))

        for resource in toFILE:
            for id in toFILE[resource]:
                for element in newPACK[resource]:
                    if element['id'] == id:
                        element['translations'] = toFILE[resource][id]['translations']

        for resource in newPACK:
            collection = newPACK[resource]
            for element in collection:
                htmlCode = self.set_custom_form_translations(resource, element)
                if htmlCode:
                    element['htmlCode'] = htmlCode
            
        # if we want to change the base language, do it here
        if self.target_lang:
            newPACK = self.__change_base_locale__(newPACK)

        # If we want to filter locales
        newPACK = self.__filter_locales__(newPACK)

        
        jsonfile= open(filename,'w', encoding='utf8')
        jsonfile.write(json.dumps(newPACK , indent=4, sort_keys=True, ensure_ascii=False))
        jsonfile.close()

    def modify_locales(self, filename):
        """
        Call this to only change the base locale (no other changes) for the input package
        """
        if os.path.dirname(filename):
            os.makedirs(os.path.dirname(filename), exist_ok=True)

        # if we want to change the base language, do it here
        newPACK = self.package
        if self.target_lang:
            newPACK = self.__change_base_locale__(newPACK)

        # If we want to filter locales
        newPACK = self.__filter_locales__(newPACK)

        jsonfile= open(filename,'w', encoding='utf8')
        jsonfile.write(json.dumps(newPACK , indent=4, sort_keys=True, ensure_ascii=False))
        jsonfile.close()


    def __change_base_locale__(self, current_package):
        """
        Swap the base language of the metadata
        This requires that translations are available in the "target" base language.
        This is currently only applicable to file mode
        """        

        previous_lang = self.base_lang
        target_lang = self.target_lang
        print("Converting main locale from",previous_lang,"to",target_lang,"...")

        translatable_fields = self.translatable_fields
        translatable_max_chars= self.translatable_max_chars 

        # to change the normal object translations, we loop through
        package = copy.deepcopy(current_package)
        for resource in package:
            # skip the object that contains the packages own metadata
            if resource != "package":

                collection = package[resource]
                for element in collection:

                    # if we want to swap languages in custom forms
                    self.swap_custom_form_translations(resource, element)

                    translations= element["translations"]

                    if resource in translatable_fields:
                        for transField in translatable_fields[resource]:
                            transFieldKey = translatable_fields[resource][transField]

                            # we can only create translation strings in transifex when a source base field has a value
                            # if transField in element:
                            matching_translations=[m for m in translations if m['property'] == transFieldKey]

                            for m in matching_translations:
                                if m['locale'] == target_lang:

                                    target_string = m['value']

                                    if transField in element:
                                        m['value'] = element[transField]
                                        m['locale'] = previous_lang
                                    else:
                                        m['remove'] = True
                                        
                                    # make sure the string doesn't exceed the max characters
                                    element[transField] = target_string[0:translatable_max_chars[resource][transFieldKey]]
                            
                    # remove any translations that should be removed
                    element["translations"] = [m for m in translations if 'remove' not in m]
            else:
                # modify the package metadata accordingly
                package[resource]['locale'] = target_lang
                package[resource]['name'] = package[resource]['name'].replace('-'+previous_lang,'-'+target_lang)
                                
        return package



    def __filter_locales__(self, current_package):
        """
        exclude or include specific locales
        Include is exclusive and implies exclude of the others
        Include trumps exclude if both are defined (i.e. exclude list is ignored if there is an include list)
        """        
        if self.include_locales or self.exclude_locales:
            if self.include_locales:
                print("Including only the following locales:",self.include_locales,"...")
            else:
                print("Excluding the following locales:",self.exclude_locales,"...")


            # to change the normal object translations, we loop through
            package = copy.deepcopy(current_package)
            for resource in package:
                # skip the object that contains the packages own metadata
                if resource != "package":

                    collection = package[resource]
                    for element in collection:

                        # if we want to swap languages in custom forms
                        self.exclude_custom_form_translations(resource, element)

                        translations= element["translations"]
                        
                        # remove any translations that should be removed
                        if self.include_locales:
                            element["translations"] = [m for m in translations if m['locale'] in self.include_locales]
                        else:
                            element["translations"] = [m for m in translations if m['locale'] not in self.exclude_locales]

                                
            return package
        else:
            return current_package



if __name__ == "__main__":

    # First parse the deciding arguments.

    p = configargparse.ArgParser(default_config_files=['~/.d2t_settings'])
    p.add('-c', '--config', required=False, is_config_file=True, help='config file path')
    # mode
    p.add('--package', required=False, action="store_true")
    p.add('--instance', required=False, action="store_true")
    # instance options
    p.add('-u', '--user', required='--package' not in sys.argv, help='DHIS2 user', env_var='DHIS2_USER') 
    p.add('-p', '--password', required='--package' not in sys.argv, help='DHIS2 password', env_var='DHIS2_PASSWORD') 
    p.add('-s', '--server', required='--package' not in sys.argv, env_var='DHIS2_SERVER', help='Server URL: e.g. https://play.dhis2.org/2.39.0') 
    # file options
    p.add('-f', '--file', required='--package' in sys.argv, help='Package file (URL to metadata.json file)', env_var='PACKAGE_FILE') 
    p.add('-b', '--basex', required=False, help='Swap base language. Format "<current_code>:<target_code>"') 
    p.add('-x', '--exclude', required=False, help='Comma-separated list of language codes to exclude') 
    p.add('-i', '--include', required=False, help='Comma-separated list of language codes to include') 
    p.add('-o', '--output', required='--basex' in sys.argv or '--include' in sys.argv or '--exclude' in sys.argv or '--pull' in sys.argv, help='Output file') 
    # Transifex options
    p.add('--push', required=False, help='push source to Transifex', action="store_true") 
    p.add('--pull', required=False, help='pull translations from Transifex', action="store_true") 
    p.add('--project', required='--push' in sys.argv or '--pull' in sys.argv, help='Transifex project slug', env_var='TRANSIFEX_PROJECT') 
    p.add('-r', '--resource', required='--push' in sys.argv or '--pull' in sys.argv, help='Transifex resource slug', env_var='TRANSIFEX_RESOURCE') 
    p.add('--org', required='--push' in sys.argv or '--pull' in sys.argv, help='Transifex organisation', env_var='TX_ORGANISATION', default='hisp-uio') 
    p.add('-t', '--token', required='--push' in sys.argv or '--pull' in sys.argv, help='Transifex token', env_var='TX_TOKEN')


    options = p.parse_args()



    if options.package:
        # instantiate the f2t class
        if (options.basex or options.include or options.exclude) and not (options.push or options.pull):
            
            f2t = f2t(project="",
                        resource="",
                        package_url=options.file,
                        base=options.basex,
                        include=options.include,
                        exclude=options.exclude,
                        tx_org=options.org,
                        tx_token=options.token
                        )
            # if you supply the basex (or include/exclude) options without push or pull
            # we assume you just want to manipulate the locales without other changes

            if options.output:
                f2t.modify_locales(options.output)

        else:

            if options.output or options.push or options.pull:
                f2t = f2t(project=options.project,
                            resource=options.resource,
                            package_url=options.file,
                            base=options.basex,
                            include=options.include,
                            exclude=options.exclude,
                            tx_org=options.org,
                            tx_token=options.token
                            )

                # get the translations from the input package file
                f2t.file_to_json()

                if options.push:
                    # push source to transifex
                    f2t.json_to_transifex()
                if options.pull:
                    # pull translations from transifex
                    f2t.transifex_to_json()

                # output the updated package file
                if options.output:
                    f2t.json_to_file(options.output)

            else:
                print("No actions selected.")
                print("----------")
                print(p.format_help())
                print("----------")

    else:
        if options.push or options.pull:
            # assume options.instance - instantiate the d2t class
            d2t = d2t(  server=options.server, 
                        user=options.user, 
                        password=options.password,
                        project=options.project,
                        resource=options.resource,
                        base=options.basex,
                        tx_org=options.org,
                        tx_token=options.token
                    )

            if (options.file):
                print("setting package file as object filter.")
                d2t.set_filter(options.file)

            # get the translations from DHIS2
            d2t.dhis2_to_json()

            if options.push:
                # push source to transifex
                d2t.json_to_transifex()
            if options.pull:
                # pull translations from transifex
                d2t.transifex_to_json()
                # only push back to DHIS2 if we have pulled new translations
                d2t.json_to_dhis2()


        else:
            print("No actions selected.")
            print("----------")
            print(p.format_help())
            print("----------")


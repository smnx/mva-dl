#! /usr/bin/python

import json
import requests
import re

from bs4 import BeautifulSoup
from contextlib import closing
from pprint import pprint
from urllib.parse import urlsplit
from xml.etree import ElementTree


VID_QUALITY = '360p'
URL = 'https://mva.microsoft.com/en-US/training-courses/introduction-to-aspnet-core-10-16841'
OVERWRITE = False


def main():
    config = get_config()

    r = requests.get(config['course_url'])
    soup = BeautifulSoup(r.content, 'lxml')
    conf_script = soup.find(
            'script', text=re.compile(r'.*var Configurations .*'))
    conf_vars = get_js_vars(conf_script.text)
    
    api_url = 'https://{}/services/products/anonymous/{}'.format(
            conf_vars['mlxApiTargetHostname'],
            conf_vars['courseID'])
    r2 = requests.get(
            api_url,
            params = {
                'version': conf_vars['courseVersion'],
                'languageId': conf_vars['languageId'],
            })
    course_res_url = r2.text.replace('"', '').replace('\\', '')
    resources_url = course_res_url + '/imsmanifestlite.json'
    
    r3 = requests.get(resources_url)
    jsres = json.loads(r3.text)

    for lix, lesson in enumerate(jsres['manifest']['organizations']['organization'][0]['item'], 1):
        lesson_title = lesson['title']
        lesson_description = lesson['metadata']['description']
        print('LESSON: {}'.format(lesson_title)) 
        print('-' * 72)
        print(lesson_description)
        for rix, resource in enumerate(lesson['item'], 1):
            resource_title = re.sub(r'^Video:\s+', '', resource['title'])
            resource_type = \
                    resource['resource']['metadata']['learningresourcetype']
            resource_href = course_res_url +'/' + \
                    resource['resource']['@href'].split('?settingsUrl=')[1] + '/videosettings.xml'
            print('{}: {}'.format(resource_type, resource_title))
            print(resource_href)
            resource_info = requests.get(resource_href)
            xml_root = ElementTree.fromstring(resource_info.content)
            xquery = (
                    ".//MediaSources[@videoType='progressive']/"
                    "MediaSource[@videoMode='{}']").format(
                            config['video_quality'])
            download_url = xml_root.find(xquery).text.split('?')[0]
            extension = re.findall(r'.*\.([^\.]+)$', download_url)[0]
            print(download_url) 
            # Allow only alphanumerics, dash and underscore in the name.
            # Outer regex is there to make sure the name doesn't end in "."
            # Extension should be clean, right? Right?
            filename = '{}.{}.'.format(lix, rix) + re.sub(
                    r'[\.]+$', '', re.subn(
                        r'[^\w-]+', '.', resource_title)[0]
                    ) + '.{}'.format(extension)
            #with open(filename, 'xb') as f, \
            #        closing(requests.get(download_url, stream=True)) as r:
            print(filename)
 
            print('\n')



def get_js_vars(script):
    ret = dict()
    jstext = re.findall(
            r'var Configurations = \s*(.*?);',
            script,
            re.DOTALL | re.MULTILINE)[0]
    ret['courseID'] = int(
            re.findall(
                r"courseID: '(\d+)'",
                script)[0])
    ret['courseVersion'] = re.findall(
                r"courseVersion: '([\d\.]+)'",
                script)[0]
    ret['languageId'] = int(
            re.findall(
                r"languageId: '(\d+)'",
                script)[0])
    ret['mlxApiTargetHostname'] = re.findall(
            r"mlxApiTargetHostname: '([\w\.-]+)'",
            script)[0]
    return ret


def get_config():
    return dict(
            course_url=URL,
            video_quality=VID_QUALITY,
            overwrite_files=OVERWRITE)


if __name__ == '__main__':
    main()


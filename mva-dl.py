#! /usr/bin/python

import json
import requests
import re
from bs4 import BeautifulSoup
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

    for lesson in jsres['manifest']['organizations']['organization'][0]['item']:
        lesson_title = lesson['title']
        lesson_description = lesson['metadata']['description']
        print('LESSON: {}'.format(lesson_title)) 
        print('-' * 72)
        print(lesson_description)
        for resource in lesson['item']:
            resource_title = resource['title']
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
            print(download_url) 


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


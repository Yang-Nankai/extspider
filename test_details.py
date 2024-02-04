# -*- coding: utf-8 -*-
import requests
import os
import re
import json
import io
from collections import OrderedDict
requests.packages.urllib3.disable_warnings()

url = "https://chromewebstore.google.com/_/ChromeWebStoreConsumerFeUi/data/batchexecute"

headers = {
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
}


def _res_to_details_list(response: str):
    if response:
        # details = json.loads(response.lstrip(")]}'\n[0-9]"))
        # return json.loads(details[0][2])  # Return the extension details
        pattern = r'(\[\[.*\]\])'
        details = re.findall(pattern, response)[0]
        return json.loads(json.loads(details)[0][2])
        # TODO: Need review
    else:
        # TODO: if not get the res throw Exception
        pass

ext_req_data = '[[["xY2Ddd","[\\"knkpjhkhlfebmefnommmehegjgglnkdm\\"]",null,"1"]]]'

def get_ext_item_reps(url, req_data):
    try:
        post_data = {
            'f.req': req_data
        }
        response = requests.post(url, verify=False, headers=headers, data=post_data)
        res = response.text

        if response.status_code != 200:
            raise requests.RequestException(u"Status code error: {}".format(response.status_code))
        if response.status_code == 200:
            return res
    except requests.RequestException as e:
        return False

res = get_ext_item_reps(url, ext_req_data)
# print(res)
# print(_res_to_details_list(res))

pattern = r'(\[\[.*\]\])'
matches = re.findall(pattern, res)
data = json.loads(matches[0])
print(data[0][2])
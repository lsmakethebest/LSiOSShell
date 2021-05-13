# -*- coding:utf-8 -*-
# Author: liusong
# app store connect api

# sudo pip3 install PyJWT

import jwt
import time
import json
import requests
from datetime import datetime, timedelta

algorithm = 'ES256'
base_api_url = "https://api.appstoreconnect.apple.com"


def get_token(key, iss, key_file):
    """
    :param key:
    :param iss:
    :param key_file:
    :return:
    """
    # 读取私钥
    private_key = open(key_file, 'r').read()
    # 构造header
    header = {
        "alg": algorithm,
        "kid": key,
        "typ": "JWT"
    }
    # 构造payload
    payload = {
        "iss": iss,
        "exp": int(time.mktime((datetime.now() + timedelta(minutes=20)).timetuple())),
        "aud": "appstoreconnect-v1"
    }

    token = jwt.encode(payload=payload, key=private_key, algorithm=algorithm, headers=header)
    return token


def base_call(url, token, method="get", data=None):
    """
    :param url:
    :param token:
    :param method:
    :param data:
    :return:
    """

    re_header = {"Authorization": "Bearer %s" % token}
    r = {}
    url = base_api_url + url

    requests.adapters.DEFAULT_RETRIES = 1
    req = requests.session()
    req.keep_alive = False

    if method.lower() == "get":
        r = req.get(url, params=data, headers=re_header)

    elif method.lower() == "post":
        re_header["Content-Type"] = "application/json"
        r = req.post(url=url, headers=re_header, data=json.dumps(data))

    elif method.lower() == "patch":
        re_header["Content-Type"] = "application/json"
        r = req.patch(url=url, headers=re_header, data=json.dumps(data))
    return r.text

# ------------------ 获取具体接口的方法 ------------------


def get_devices(api_token, data=None):
    """
    获取devices信息
    :param api_token:
    :param data:
    :return:
    """
    get_devices_url = '/v1/devices'
    if data is None:
        data = {
            "filter[platform]": "IOS",
            # "filter[status]": "ENABLED",
            "limit": 100
        }
    res = base_call(get_devices_url, api_token, 'get', data)
    return res


def set_devices(api_token, data):
    """
    增加devices信息
    :param api_token:
    :param data:
    :return:
    """
    url = '/v1/devices'
    res = base_call(url, api_token, 'post', data)
    return res


def update_devices(api_token, id, data,):
    """
    增加devices信息
    :param id:
    :param api_token:
    :param data:
    :return:
    """
    url = '/v1/devices/{%s}' % id
    res = base_call(url, api_token, 'patch', data)
    return res

def get_apps(api_token):
	url = '/v1/apps/1246078802/perfPowerMetrics'
	res = base_call(url, api_token, 'get', None)
	return res


if __name__ == "__main__":

    ios_api_key = ''
    ios_api_issuer = ''
    file_key = "/Users/liusong/Downloads/AuthKey_W89XUJJUA8.p8"

    token_api = get_token(ios_api_key, ios_api_issuer, file_key)
    print(f'token:{token_api}')
    # post_data = {
    #     "data": {
    #         "attributes": {
    #             "name": "zb",
    #             "platform": "IOS",
    #             "udid": "80b677c2c****e476caf61ba0d34274000"
    #         },
    #         "type": "devices"
    #     }
    # }

    res = get_apps(token_api)
    # res = get_devices(token_api,None)
    print(res)




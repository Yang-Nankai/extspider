import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def _res_to_info_list(res=''):
    if res:
        infojson = json.loads(res.lstrip(")]}'\n"))
        return json.loads(infojson[0][2])
    else:
        # import pdb;pdb.set_trace()
        # raise Exception()
        pass

url = "https://chromewebstore.google.com/_/ChromeWebStoreConsumerFeUi/data/batchexecute?rpcids=zTyKYc&source-path=category%2Fextensions%2Flifestyle%2Fnews"

HTTP_HEADERS = {
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
}

data = {
    "f.req": '[[["zTyKYc","[[null,[[3,\\"lifestyle/news\\",null,null,2,[100,\\"QVRaWjVOa2xkTjVLVFMzb0ZaSTZrRHlwZVlZSHVOcDh5TmNfd3NkNXRJR0dNd1RSY0UycWxjRFJ0SGk5SnIzUkUtRDVZTlMwNFhvZWtxbUtOcGpWWG5LTVU2UU1ZclRKaGtTaGtidTNubFBHVGQ5NEwxT1p5aU5jTWFSRGNTcy1fcVZzSkw1bE9CSlRwdGhhRHg0LTZEaHJ1NXBVTG53cHM5NFhvQmJld0hmalNmZEFXVHBjTnVkZWJsdVNXeTRzUmY4VWZDa0p1THJaclBLdEJoLVI3aDJaRkFlc2k4SDZCZmRaZUdPbGlGNFAtZWlFOUp4eQ==\\"]]]]]",null,"generic"]]]'
}

# data = {
#     'f.req': '[[["zTyKYc","[[null,[[3,\\"productivity/communication\\",null,null,2,[100,\\"QVRaWjVOa2xkTjVLVFMzb0ZaSTZrRHlwZVlZSHVOcDh5TmNfd3NkNXRJR0dNd1RSY0UycWxjRFJ0SGk5SnIzUkUtRDVZTlMwNFhvZWtxbUtOcGpWWG5LTVU2UU1ZclRKaGtTaGtidTNubFBHVGQ5NEwxT1p5aU5jTWFSRGNTcy1fcVZzSkw1bE9CSlRwdGhhRHg0LTZEaHJ1NXBVTG53cHM5NFhvQmJld0hmalNmZEFXVHBjTnVkZWJsdVNXeTRzUmY4VWZDa0p1THJaclBLdEJoLVI3aDJaRkFlc2k4SDZCZmRaZUdPbGlGNFAtZWlFOUp4eQ==\\"]]]]]",null,"generic"]]]'
# }


# {'f.req': '[[["zTyKYc","[[null,[[3,\\"productivity/communication\\",null,null,2,[100,\\"QVRaWjVOa2xkTjVLVFMzb0ZaSTZrRHlwZVlZSHVOcDh5TmNfd3NkNXRJR0dNd1RSY0UycWxjRFJ0SGk5SnIzUkUtRDVZTlMwNFhvZWtxbUtOcGpWWG5LTVU2UU1ZclRKaGtTaGtidTNubFBHVGQ5NEwxT1p5aU5jTWFSRGNTcy1fcVZzSkw1bE9CSlRwdGhhRHg0LTZEaHJ1NXBVTG53cHM5NFhvQmJld0hmalNmZEFXVHBjTnVkZWJsdVNXeTRzUmY4VWZDa0p1THJaclBLdEJoLVI3aDJaRkFlc2k4SDZCZmRaZUdPbGlGNFAtZWlFOUp4eQ==\\"]]]]]",null,"generic"]]]'}

response = requests.post(url, verify=False, headers=HTTP_HEADERS, data=data)

# 打印响应文本
# print(response.text)

result = _res_to_info_list(response.text)

print(result[2][0])



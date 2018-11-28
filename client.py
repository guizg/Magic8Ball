import requests
import sys
import json
from flask import jsonify


IPjson = None

with open('ip.json') as f:
    IPjson = json.load(f)


IP = IPjson["ip"]
print(IP)
URL = 'http://'+IP+':5000'


palavras_pergunta = []
for i in range(1, len(sys.argv)):
    palavras_pergunta.append(sys.argv[i])
pergunta = " ".join(palavras_pergunta)

payload = json.dumps({"pergunta": pergunta})
headers = {'content-type': 'application/json'}
r = requests.get(URL + '/magicball', data=payload, headers=headers)
# print(r)
# print(r.content.decode('utf-8'))
res = r.json()
# print(r.content.decode('ascii'))
# print(json.loads(res)["answer"])

print(json.loads(res)["answer"])
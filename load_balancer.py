from flask import Flask, request, jsonify, Response
import json
import boto3
from random import choice
import requests
from threading import Thread, Timer
import pprint
import time
import sys


ACCESS_ID = sys.argv[1]
ACCESS_KEY = sys.argv[2]

ec2 = boto3.client('ec2', region_name='us-east-1', aws_access_key_id=ACCESS_ID, aws_secret_access_key= ACCESS_KEY)
ec2R = boto3.resource('ec2', region_name='us-east-1', aws_access_key_id=ACCESS_ID, aws_secret_access_key= ACCESS_KEY)
instances = {}
current_id = None
wait = False
pp = pprint.PrettyPrinter(indent=4)
ACTIVE_INSTANCES = 3


app = Flask(__name__)
@app.route('/')
def list_instances():
    global ec2
    global instances

    existing_instances = ec2.describe_instances()
    for e in existing_instances["Reservations"]:
        # pp.pprint(e["Instances"][0])

        if( "Tags" not in list(e["Instances"][0].keys()) or e["Instances"][0]["Tags"] == None):
                continue
        
        if((e["Instances"][0]["Tags"][0]["Value"]=="graicer" or e["Instances"][0]["Tags"][0]["Value"]=="worker") and (e["Instances"][0]["Tags"][1]["Value"]=="graicer" or e["Instances"][0]["Tags"][1]["Value"]=="worker") and e["Instances"][0]['State']['Name'] == "running"):
            if (e["Instances"][0]["InstanceId"]) not in list(instances.keys()):
                instances[(e["Instances"][0]["InstanceId"])] = e["Instances"][0]['PublicIpAddress']

    return jsonify(instances)


@app.route('/magicball', methods = ['GET'])
def repass():
    global instances
    # print(list(instances.keys()))
    rd = choice(list(instances.keys()))
    IP = instances[rd]
    URL = 'http://'+IP+':5000/magicball'

    if request.method == 'GET':
        nome = json.loads(request.data)['pergunta']
        payload = json.dumps({"pergunta": nome})
        headers = {'content-type': 'application/json'}
        r = requests.get(URL, data=payload, headers=headers)
        print(r)
        return jsonify(r.content.decode('utf-8'))
        


def list_instances2():
    global ec2
    global instances

    existing_instances = ec2.describe_instances()
    for e in existing_instances["Reservations"]:
        # pp.pprint(e["Instances"][0])

        if( "Tags" not in list(e["Instances"][0].keys()) or e["Instances"][0]["Tags"] == None):
                continue
        if((e["Instances"][0]["Tags"][0]["Value"]=="graicer" or e["Instances"][0]["Tags"][0]["Value"]=="worker") and (e["Instances"][0]["Tags"][1]["Value"]=="graicer" or e["Instances"][0]["Tags"][1]["Value"]=="worker") and e["Instances"][0]['State']['Name'] == "running"):
            if (e["Instances"][0]["InstanceId"]) not in list(instances.keys()):
                instances[(e["Instances"][0]["InstanceId"])] = e["Instances"][0]['PublicIpAddress']


def how_many_instances():
    global ec2
    i = 0
    existing_instances = ec2.describe_instances()
    for e in existing_instances["Reservations"]:
        if("Tags" not in list(e["Instances"][0].keys()) or e["Instances"][0]["Tags"] == None):
                continue
        if((e["Instances"][0]["Tags"][0]["Value"]=="graicer" or e["Instances"][0]["Tags"][0]["Value"]=="worker") and (e["Instances"][0]["Tags"][1]["Value"]=="graicer" or e["Instances"][0]["Tags"][1]["Value"]=="worker") and e["Instances"][0]['State']['Name'] == "running"):    
            i += 1
    return i

def new_instance():
    global ec2
    global ec2R
    global instances

    print("Creating instance")

    instance = ec2R.create_instances(
        ImageId='ami-0ac019f4fcb7cb7e6',
        InstanceType='t2.micro',
        KeyName='jorge',
        MaxCount=1,
        MinCount=1,
        Monitoring={
            'Enabled': False
        },
        SecurityGroups=[
            'grupaodojorge'
        ],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'owner',
                        'Value': 'graicer'
                    },
                    {
                        'Key': 'type',
                        'Value': 'worker'
                    }
                ]
            }
        ],
        UserData="""#!/bin/bash 
                    git clone https://github.com/guizg/Cloud_aps.git
                    cd /
                    cd Cloud_aps/
                    chmod 777 init.sh
                    ./init.sh
                    python3 magicball.py""",
    )
    inst = instance[0]
    
    print("Waiting for "+inst.id+" to be running.")
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[inst.id])
    # print("PASSOU PELA MERDA DO WAIT")
    
    public_ip_address = None

    while(public_ip_address == None):
        existing_instances = ec2.describe_instances()
        # print(existing_instances["Reservations"])
        for e in existing_instances["Reservations"]:
            # pp.pprint(e["Instances"][0])
            if("Tags" not in list(e["Instances"][0].keys()) or e["Instances"][0]["Tags"] == None):
                continue
            if((e["Instances"][0]["Tags"][0]["Value"]=="graicer" or e["Instances"][0]["Tags"][0]["Value"]=="worker") and (e["Instances"][0]["Tags"][1]["Value"]=="graicer" or e["Instances"][0]["Tags"][1]["Value"]=="worker") and e["Instances"][0]['InstanceId'] == inst.id):
                # pp.pprint(e)
                public_ip_address = e["Instances"][0]['NetworkInterfaces'][0]['Association']['PublicIp']
        # print(public_ip_address)

    instances[inst.id] = public_ip_address

    print("Instance created - "+inst.id)
    stat = None

    try:
        URL = 'http://'+public_ip_address+':5000/healthcheck'
        r = requests.get(URL)
        print(r.status_code)
    except:
        print("[Wait] Webserver not ready yet. - "+inst.id)
        pass

    while(stat != 200):
        time.sleep(2)
        try:
            URL = 'http://'+public_ip_address+':5000/healthcheck'
            r = requests.get(URL)
            stat = r.status_code
        except:
            print("[Wait] Webserver not ready yet. - "+inst.id)
            pass





def timeout():
    global pp
    global ec2
    global instances
    global ec2R
    global ACTIVE_INSTANCES

    print("TIMEOUT!")
    print(current_id)
    try:
        ec2.terminate_instances(InstanceIds=[current_id])
    except:
        pass
    instances.pop(current_id)
    # new_instance()
    # i = how_many_instances()
    i = len(instances)
    if i < ACTIVE_INSTANCES:
        print("Too few instances: "+str(i))
        new_instance()
    elif i > ACTIVE_INSTANCES:
        print("Too many instances: "+str(i))
        delete_random_instance()
    healthcheck_verification()
    

def delete_random_instance():
    global ec2
    global ec2R
    global instances
    id = list(instances.keys())[0]
    print("Deleting instance "+id)
    ec2.terminate_instances(InstanceIds=[id])
    instances.pop(id)



def healthcheck_verification():
    global instances
    global current_id
    global ACTIVE_INSTANCES
    while(True):
        list_instances2()
        time.sleep(2)
        for k in list(instances.keys()):
            tim = Timer(5.0, timeout)
            tim.start()
            current_id = k
            IP = instances[k]
            print("Starting check - "+k)
            try:
                URL = 'http://'+IP+':5000/healthcheck'
                r = requests.get(URL)
                print(r.status_code)
            except:
                print("Healthcheck not successful.")
                pass
            tim.cancel()

        # i = how_many_instances()
        i = len(instances)
        if i < ACTIVE_INSTANCES:
            print("Too few instances: "+str(i))
            new_instance()
        elif i > ACTIVE_INSTANCES:
            print("Too many instances: "+str(i))
            delete_random_instance()
        
t = Thread(target=healthcheck_verification)
t.start()


app.run(host='0.0.0.0', port=5000, debug=False)
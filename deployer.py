import boto3
import os
import rsa
import time
import json

creds = None

with open('credentials.json') as f:
    creds = json.load(f)

ec2 = boto3.client('ec2')

existing_instances = ec2.describe_instances()
for i in range(len(existing_instances["Reservations"])):
    try:
        for tag in (existing_instances["Reservations"][i]["Instances"][0]["Tags"]):
            if(tag["Value"]=="graicer"):
                ec2.terminate_instances(InstanceIds=[(existing_instances["Reservations"][i]["Instances"][0]["InstanceId"])])
                while (existing_instances["Reservations"][i]["Instances"][0]['State']['Name'] != "terminated"):
                    existing_instances = ec2.describe_instances()
                    if(existing_instances["Reservations"][i]["Instances"][0]['State']['Name'] == 'terminated'):
                        print("Finished")
                    print("[WAIT] Terminating instances.")
                    time.sleep(1)
                    continue
    except:
        pass

response = ec2.describe_key_pairs()
# print(response)

# print(response['KeyPairs'][0]['KeyName'])

for k in response['KeyPairs']:
    if(k['KeyName'] == 'jorge'):
        ec2.delete_key_pair(KeyName='jorge')

publicfile = open('jorge.pub', 'rb')
pkeydata = publicfile.read()

ec2.import_key_pair(KeyName='jorge', PublicKeyMaterial=pkeydata)


response = ec2.describe_security_groups()

# print(response['SecurityGroups'][0]['GroupName'])

for s in response['SecurityGroups']:
    if(s['GroupName'] == 'grupaodojorge'):
        ec2.delete_security_group(GroupName='grupaodojorge')

ec2.create_security_group(Description='apszinha da massa', GroupName='grupaodojorge')
ec2.authorize_security_group_ingress(
    GroupName='grupaodojorge',
    IpPermissions=[
        {'IpProtocol': 'tcp', 'FromPort': 5000, 'ToPort': 5000, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ])

ec2R = boto3.resource('ec2')


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
                    'Value': 'loadbalancer'
                }
            ]
        }
    ],
    UserData="""#!/bin/bash 
                git clone https://github.com/guizg/Cloud_aps.git
                cd /
                cd Cloud_aps/
                chmod 777 initLB.sh
                ./initLB.sh
                python3 load_balancer.py {0} {1}""".format(creds['ACCESS_ID'], creds['ACCESS_KEY']),


)

inst = instance[0]

print("Waiting for LoadBalancer to be running.")
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
        if((e["Instances"][0]["Tags"][0]["Value"]=="graicer" or e["Instances"][0]["Tags"][0]["Value"]=="loadbalancer") and (e["Instances"][0]["Tags"][1]["Value"]=="graicer" or e["Instances"][0]["Tags"][1]["Value"]=="loadbalancer") and e["Instances"][0]['InstanceId'] == inst.id):
            # pp.pprint(e)
            public_ip_address = e["Instances"][0]['NetworkInterfaces'][0]['Association']['PublicIp']
    # print(public_ip_address)


IP = {"ip":public_ip_address}

with open('ip.json', 'w') as outfile:  
    json.dump(IP, outfile)
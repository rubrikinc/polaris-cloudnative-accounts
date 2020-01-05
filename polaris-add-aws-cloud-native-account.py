#!/usr/bin/python
import requests
import json
import datetime
import getpass
import logging
import os
import boto3
import botocore
import sys
log = logging.getLogger('snap_script_logger')
log.setLevel(logging.INFO)
requests.packages.urllib3.disable_warnings()

#Auth parameters used to connect to Rubrik Polaris - consider retrieving these from a secrets manager instead - CONFIGURABLE
POLARIS_SUBDOMAIN = os.environ.get('POLARIS_SUBDOMAIN')
POLARIS_USERNAME = os.environ.get('POLARIS_USERNAME')
POLARIS_PASSWORD = os.environ.get('POLARIS_PASSWORD')
POLARIS_URL = 'https://{}.my.rubrik.com'.format(POLARIS_SUBDOMAIN)

#AWS Account Info
AWS_ACCOUNT_NUMBER = os.environ.get('AWS_ACCOUNT_NUMBER')
AWS_ACCOUNT_NAME = os.environ.get('AWS_ACCOUNT_NAME')
AWS_REGIONS = os.environ.get('AWS_REGIONS').split(",")
AWS_PROFILE = os.environ.get('AWS_PROFILE')

#Get access token
URI = POLARIS_URL + '/api/session'
HEADERS = {
    'Content-Type':'application/json',
    'Accept':'application/json'
    }
PAYLOAD = '{"username":"'+POLARIS_USERNAME+'","password":"'+POLARIS_PASSWORD+'"}'
print('Logging into Polaris...')
RESPONSE = requests.post(URI, headers=HEADERS, verify=True, data=PAYLOAD)
if RESPONSE.status_code != 200:
        raise ValueError("Something went wrong with the request")
TOKEN = json.loads(RESPONSE.text)["access_token"]
TOKEN = "Bearer "+str(TOKEN)

#GraphQL endpoint and headers
URI = POLARIS_URL + '/api/graphql'
HEADERS = {
    'Content-Type':'application/json',
    'Accept':'application/json',
    'Authorization':TOKEN
    }

# Add account

def awsNativeProtectionAccountAdd(accountId,name,regions):
    GRAPH_VARS = 'null'
    GRAPH_QUERY = '"mutation {{awsNativeProtectionAccountAdd(awsNativeProtectionAccountAddArg: {{accountId: \\"{accountId}\\", name: \\"{name}\\", regions: {regions}}}) {{cloudFormationName cloudFormationUrl cloudFormationTemplateUrl errorMessage}}}}"'.format(accountId=accountId,name=name,regions=json.dumps(regions).replace('"','\\"'))
    payload = '{{"query": {},"variables":{}}}'.format(GRAPH_QUERY,GRAPH_VARS)
    print('Adding AWS account to Polaris...')
    response = requests.post(URI, headers=HEADERS, verify=True, data=payload)
    if response.status_code != 200:
        print(response)
        print(response.text)
        raise ValueError("Query failed to run by returning code of {}.\nError text of: {}\nQuery was: \n{}".format(response.status_code,response.text, payload))
    results = json.loads(response.text)
    if 'errors' in results:
        print(results)
        raise Exception("Polaris reported an error:\n {}".format(results))
    return results


# Do the work
addAccount = awsNativeProtectionAccountAdd(AWS_ACCOUNT_NUMBER,AWS_ACCOUNT_NAME,AWS_REGIONS)

# Assumes that AWS_PROFILE environment vairable is set to the proper AWS profile.
client = boto3.client('cloudformation')
StackName = addAccount['data']['awsNativeProtectionAccountAdd']['cloudFormationName']
TemplateURL = addAccount['data']['awsNativeProtectionAccountAdd']['cloudFormationTemplateUrl']

if StackName == "":
    raise Exception ('StackName is empty. Account creation call in Polaris may have failed. Message from Polaris is:\n {}'.format(addAccount['data']['awsNativeProtectionAccountAdd']['errorMessage']))

try:
    print('Running CloudFormation Template...')
    create_stack = client.create_stack(
        StackName = StackName,
        TemplateURL = TemplateURL,
        DisableRollback=False,
        Capabilities=['CAPABILITY_IAM'],
        EnableTerminationProtection=False
    )
except Exception as e:
    print('Stack creation failed with error:\n  {}').format(str(e))

waiter = client.get_waiter('stack_create_complete')

try:
    print('Waiting for CloudFormation Template to create...')
    waiter.wait(StackName=create_stack['StackId'])

except botocore.exceptions.WaiterError as e:
    print('Failed to create stack: {}').format(StackName)
    print('{}'.format(e))
    sys.exit(1)

print('AWS account added to Polaris successfully.')
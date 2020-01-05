#!/usr/bin/python
import requests
import json
import datetime
import logging
import os
import boto3
import botocore
import sys
import time
log = logging.getLogger('snap_script_logger')
log.setLevel(logging.INFO)
requests.packages.urllib3.disable_warnings()

#Auth parameters used to connect to Rubrik Polaris - consider retrieving these from a secrets manager instead - CONFIGURABLE
POLARIS_SUBDOMAIN = os.environ.get('POLARIS_SUBDOMAIN')
POLARIS_USERNAME = os.environ.get('POLARIS_USERNAME')
POLARIS_PASSWORD = os.environ.get('POLARIS_PASSWORD')
POLARIS_DELETE_SNAPSHOTS = os.environ.get('POLARIS_DELETE_SNAPSHOTS')
POLARIS_URL = 'https://{}.my.rubrik.com'.format(POLARIS_SUBDOMAIN)

if POLARIS_DELETE_SNAPSHOTS != 'true' and POLARIS_DELETE_SNAPSHOTS != 'false':
    raise Exception ('Variable POLARIS_DELETE_SNAPSHOTS must be set to "true" or "false"')
#AWS Account Info
AWS_ACCOUNT_NUMBER = os.environ.get('AWS_ACCOUNT_NUMBER')
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

# List all Cloud Native accounts

def CloudAccountsNativeProtectionList(awsAccountNumber):
    GRAPH_VARS = '{{"awsCloudAccountsArg":{{"feature":"CLOUD_NATIVE_PROTECTION","columnSearchFilter":"{}","statusFilters":[]}}}}'.format(awsAccountNumber)
    GRAPH_QUERY = '"query CloudAccountsNativeProtectionList($awsCloudAccountsArg: AwsCloudAccountsInput!) { awsCloudAccounts(awsCloudAccountsArg: $awsCloudAccountsArg) { awsCloudAccounts { awsCloudAccount { id nativeId accountName }  featureDetails { feature roleArn stackArn status awsRegions} } } }"'
    payload = '{{"operationName":"CloudAccountsNativeProtectionList","variables":{},"query":{}}}'.format(GRAPH_VARS,GRAPH_QUERY)
    print('Getting AWS Account list from Polaris..')
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

# Disable specific account (including deleteing snapshots)
def DeleteAwsAccount(awsNativeAccountId,deleteNativeSnapshots):
    GRAPH_VARS = '{{"awsNativeAccountId":"{}","deleteNativeSnapshots":{},"awsNativeProtectionFeature":"EC2"}}'.format(awsNativeAccountId,deleteNativeSnapshots)
    GRAPH_QUERY = '"mutation DeleteAwsAccount($awsNativeAccountId: UUID!, $deleteNativeSnapshots: Boolean!, $awsNativeProtectionFeature: AwsNativeProtectionFeatureEnum!) { deleteAwsNativeAccount(awsNativeAccountId: $awsNativeAccountId, deleteNativeSnapshots: $deleteNativeSnapshots, awsNativeProtectionFeature: $awsNativeProtectionFeature) {taskchainUuid} }"'
    payload = '{{"operationName":"DeleteAwsAccount","variables":{},"query":{}}}'.format(GRAPH_VARS,GRAPH_QUERY)
    print('Disabling AWS account in Polaris..')
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


# Initiate Account Deletion
def AwsCloudAccountDeleteInitiate(cloudAccountUuid):
    GRAPH_VARS = '{{"cloudAccountUuid":"{}","awsCloudAccountDeleteInitiateArg":{{"feature":"CLOUD_NATIVE_PROTECTION"}}}}'.format(cloudAccountUuid)
    GRAPH_QUERY = '"mutation AwsCloudAccountDeleteInitiate($cloudAccountUuid: UUID!, $awsCloudAccountDeleteInitiateArg: AwsCloudAccountDeleteInitiateInput!) { awsCloudAccountDeleteInitiate(cloudAccountUuid: $cloudAccountUuid, awsCloudAccountDeleteInitiateArg: $awsCloudAccountDeleteInitiateArg) { cloudFormationUrl } } "'
    payload = '{{"operationName":"AwsCloudAccountDeleteInitiate","variables":{},"query":{}}}'.format(GRAPH_VARS,GRAPH_QUERY)
    print('Initiating deletion of AWS account in Polaris..')
    response = requests.post(URI, headers=HEADERS, verify=True, data=payload)
    if response.status_code != 200:
        print(response)
        print(response.text)
        raise ValueError("Query failed to run by returning code of {}.\nError text of: {}\nQuery was: \n{}".format(response.status_code,response.text, payload))
    results = json.loads(response.text)
    #{'data': {'awsCloudAccounts': {'awsCloudAccounts': [{'awsCloudAccount': {'accountName': 'trinity-devops', 'id': 'c98c627a-2394-407f-8af1-731cdc6894df', 'nativeId': '627297623784'}}]}}}
    if 'errors' in results:
        print(results)
        raise Exception("Polaris reported an error:\n {}".format(results))
    return results

# Delete Account from Polaris 
def AwsCloudAccountDeleteProcess(cloudAccountUuid):
    GRAPH_VARS = '{{"awsCloudAccountDeleteProcessArg":{{"feature":"CLOUD_NATIVE_PROTECTION"}},"cloudAccountUuid":"{}"}}'.format(cloudAccountUuid)
    GRAPH_QUERY = '"mutation AwsCloudAccountDeleteProcess($cloudAccountUuid: UUID!, $awsCloudAccountDeleteProcessArg: AwsCloudAccountDeleteProcessInput!) { awsCloudAccountDeleteProcess(cloudAccountUuid: $cloudAccountUuid, awsCloudAccountDeleteProcessArg: $awsCloudAccountDeleteProcessArg) { message } } "'
    payload = '{{"operationName":"AwsCloudAccountDeleteProcess","variables":{},"query":{}}}'.format(GRAPH_VARS,GRAPH_QUERY)
    print('Completing AWS account deletion in Polaris..')
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
CloudAccount = CloudAccountsNativeProtectionList(AWS_ACCOUNT_NUMBER)

try:
    externalId = (CloudAccount['data']['awsCloudAccounts']['awsCloudAccounts'][0]['awsCloudAccount']['id'])
except Exception as e:
    print('Could not find AWS account {} in Polaris.'.format(AWS_ACCOUNT_NUMBER))

DisableAwsAccount = DeleteAwsAccount(externalId,POLARIS_DELETE_SNAPSHOTS)

taskchainUuid = (DisableAwsAccount['data']['deleteAwsNativeAccount']['taskchainUuid'])

status = 'UNKNOWN'

while status != 'DISABLED':
    CloudAccount2 = CloudAccountsNativeProtectionList(AWS_ACCOUNT_NUMBER)
    status = (CloudAccount2['data']['awsCloudAccounts']['awsCloudAccounts'][0]['featureDetails'][0]['status'])
    print('AWS Account status is: {} in Polaris. Waiting for AWS account to be removed...'.format(status))
    if status == 'DISABLED':
        break
    time.sleep(10)

StackName = (CloudAccount2['data']['awsCloudAccounts']['awsCloudAccounts'][0]['featureDetails'][0]['stackArn'].split(':')[5].split('/')[1])
StackRegion = (CloudAccount2['data']['awsCloudAccounts']['awsCloudAccounts'][0]['featureDetails'][0]['stackArn'].split(':')[3])

initDeleteAwsAccount = AwsCloudAccountDeleteInitiate(externalId)

# Assumes that AWS_PROFILE environment vairable is set to the proper AWS profile.
client = boto3.client('cloudformation', region_name=StackRegion)

if StackName == "":
    raise Exception ('StackName in AWS could not be retrieved from Polaris')

try:
    print('Deleting CloudFormation Template...')
    delete_stack = client.delete_stack(StackName=StackName)
except Exception as e:
    print('Stack deletion failed with error:\n  {}').format(str(e))

waiter = client.get_waiter('stack_delete_complete')

try:
    print('Waiting for CloudFormation Template to delete...')
    waiter.wait(StackName=StackName)

except botocore.exceptions.WaiterError as e:
    print('Failed to delete stack: {}').format(StackName)
    print('{}'.format(e))
    sys.exit(1)

DeleteAwsAccount = AwsCloudAccountDeleteProcess(externalId)

print(DeleteAwsAccount['data']['awsCloudAccountDeleteProcess']['message'])



#!/usr/bin/python

import sys
import traceback
import re
import base64
import logging
import datetime
import json

import requests
import string
import os

#########################
#To get the current sprint version
#config values
AUTH_TOKEN = "token 1d726f6163785e6e7bd6c7205d1c1a806a73ace6"
giturl = "https://api.github.com/repos/devops/"
commit_message = "Automated commit to update sprint version at the beginning of sprint"
xpc_version_file = "devops/contents/sprint_version.txt?ref=master"
sha = None

def getContent(filePath):
    try:
        r = requests.get(str(giturl) + str(filePath), headers={'Authorization': AUTH_TOKEN})
        global sha
        sha = r.json()['sha']
        decodedString = base64.b64decode(r.json()['content'])
        return decodedString
    except Exception as error:
        print('There was an error while fetching contents of a file' + str(error))
        sys.exit(1)


#########################

#logging.basicConfig(level=logging.DEBUG)

USER = '/MANOHAR452'
HEADER = {"Authorization": "bearer 1d726f6163785e6e7bd6c7205d1c1a806a73ace6"}



API_PATH = "https://api.github.com/api/v3/repos"



def get_sha_of_branch(branch, user_repo):
    '''
    Gets sha commit of @branch to be used for creating 
    new branches from it
    '''
    logging.debug('branch: %s user_repo: %s' % (branch, user_repo))
    url = API_PATH + user_repo + "/git/refs/heads/" + branch
    r = requests.get(url, headers=HEADER)
    try:
        j = r.json()
        logging.debug(j)
        return j["object"]["sha"]
    except:
        traceback.print_exc(file=sys.stdout)
        print "Could not get sha of branch"
        sys.exit(1)


def create_branch_from_branch(target, base, user_repo):
    '''
    Creates a new branch named @target
    from @base
    '''
    url = API_PATH + user_repo + "/git/refs"
    sha = get_sha_of_branch(base, user_repo)
    data = {
            "ref": "refs/heads/" +  target,
            "sha": sha
            }
    try:
        r = requests.post(url, data=json.dumps(data), headers=HEADER)
        j = r.json()
        if 'message' in j:
            message = j["message"]
            print "ERROR MESSAGE:", message
            raise RuntimeError("Error message in request")
        print "Branch", target, "created from", base
    except:
        traceback.print_exc(file=sys.stdout)
        print "Could not create branch", target, "from", base
        sys.exit(1)


def get_xpc_version_of_branch(branch, user_repo):
    file_content = getContent(xpc_version_file)
    previousVersion = file_content.split('previous_sprint =')[1].split("'")[1]
    return previousVersion

def merge_branch_to_branch(user_repo, master, branch, message):
    date = datetime.date.today().strftime("%B %d, %Y")
    data = {
            "base": branch,
            "head": master,
            "commit_message": message + ': ' + date
            }
    url = API_PATH + user_repo + "/merges"
    try:
        r = requests.post(url, data=json.dumps(data), headers=HEADER)
        if r.status_code == 204:
            print "No change for merging", master, 'into', branch
            return
        j = r.json()
        if 'message' in j:
            message = j['message']
            print "ERROR MESSAGE:", message
            raise RuntimeError("Error message in request")
        print "Merged", master, 'into', branch
    except:
        traceback.print_exc(file=sys.stdout)
        print "Could not merge branch", master, "into", branch
        sys.exit(1)

def get_it_done(repo):
    user_repo = USER + repo
    version = get_xpc_version_of_branch('developn-1', user_repo)
    create_branch_from_branch(version, 'developn-1', user_repo)
    merge_branch_to_branch(user_repo, 'develop', 'developn-1', 'End of sprint merge')    

###################################
#sprint version file update
###################################

#function to update file with given String on git branch
def updateContent(filePath, branchName, encodedString):
    try:
        print sha
        put_data = { "branch": branchName, "content": encodedString, "message": commit_message, "sha": sha, "committer": { "name": "xpcgithub", "email": "xpcgithub@cable.comcast.com"}}
        r = requests.put(giturl + filePath + '?ref=' + branchName, data=json.dumps(put_data), headers={'Authorization': AUTH_TOKEN})
        if (r.status_code == 200):
            print 'Successfully updated version in ' + filePath
        else:
            print 'Error: Could not update version in ' + filePath + ' and the status_code is ' + str(r.status_code)

    except Exception as error:
        print('There was an error while updating contents of a file' + str(error))
        sys.exit(1)

#function to find the previous version and replace it with new version
def searchAndReplace(previousVersion, newVersion, branchName, file_content=None, encoded_string=None):
        
    if encoded_string:
        file_content = base64.b64decode(encoded_string)

    newContent = string.replace(file_content, previousVersion, newVersion)
    encodedString = base64.b64encode(newContent)
    return encodedString

#function to find next version based on identified version
def findNewVersion(previousVersion):
    xpc_version_major = previousVersion.split('.')[0]
    xpc_version_minor = previousVersion.split('.')[1]
    xpc_version_build = previousVersion.split('.')[2]

    #Storing current year and month in int
    today=datetime.date.today()
    cyear=today.strftime("%y")
    cmonth=today.strftime("%m").lstrip('0')

    #Version format: Major.Minor.Release
    #when year is not same, then reseting minor and release to 1.
    if (xpc_version_major != cyear):
        new_xpc_version=str(cyear) +'.1.1'
    #when month is not same, then reseting release to 1.
    elif (xpc_version_minor != cmonth):
        new_xpc_version = str(cyear) + '.' + str(cmonth) + '.1'
    #when year & month is same, then incremementing and release by 1.
    else:
        new_build = int(xpc_version_build) + 1
        new_xpc_version = str(cyear) + '.' + str(cmonth) + '.' + str(new_build)

    return new_xpc_version

if __name__ == '__main__':

    print ('working on /devops')
    get_it_done('/devops')
    print ('working on sprint_version.txt file update')
    file_content = getContent(version_file)
    previousVersion = file_content.split('current_sprint =')[1].split("'")[1]
    version_N_1 = file_content.split('previous_sprint =')[1].split("'")[1]
    newVersion = findNewVersion(previousVersion)
    updated_encoded_string = searchAndReplace(previousVersion, newVersion, 'master', file_content=file_content)
    upload_string = searchAndReplace(version_N_1, previousVersion, 'master', encoded_string=updated_encoded_string)
    updateContent(xpc_version_file, 'master', upload_string)
    sys.exit(0)

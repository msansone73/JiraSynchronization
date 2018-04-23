'''
jira.py is a high level module that implements high level features to handle REST communication with JIRA
'''
import string

__author__ = 'iterroso'

import jira
import logging
import base64

logger = logging.getLogger('QCRest')

from requests.packages import urllib3
urllib3.disable_warnings()

class JIRARest(object):
    '''
    Class that
    '''

    # Initialize connection
    def __init__(self, server=None):

        if server is None:
            # self.url_server = 'http://ptlisljira-dev.co-int.net:8080/'
            self.url_server = 'https://jira.intra.coriant.com'
            # self.url_server = 'http://jira-sandbox.intra.coriant.com:8080'
        else:
            self.url_server = server

        self.maxResults = 200

        # Jira object that will be used to do everything. It is initialized in the login
        self.jira_obj = None

        # Server options
        self.jira_options = {'server': self.url_server, 'max_retries': 1, 'verify': False}

    # Login action
    def login(self, user=None, passwd=None, **kwargs):

        if user is None:
            user = base64.b64decode('Njg1MDAzNTM=')
        if passwd is None:
            passwd = base64.b64decode('MTIzUVdFYXNkMDQ=')

        # First login and instantiate class
        self.jira_obj = jira.JIRA(self.jira_options, basic_auth = (user, passwd))

        return self.jira_obj

    # Overwrite logout from Connect to support delete session management
    def logout(self, **kwargs):

        # First stop session
        pass

    def getIssueDataFromIssueTypeProjectVersionKey(
            self, issueTypeList, projectList, fixVersionList, affectsVersionList, keyList,
            fieldNameList, changelog=False):

        fieldNameList = ['key', 'summary'] + fieldNameList
        searchString = ''

        if len(issueTypeList) > 0:

            searchString = 'issuetype in (\''

            for issueType in issueTypeList:
                searchString += issueType + '\', \''

            searchString = searchString[:-4] +  '\')'

        if len(projectList) > 0:

            searchString += ' and project in (\''

            for project in projectList:
                searchString += project + '\', \''

            searchString = searchString[:-4] +  '\')'

        if len(fixVersionList) > 0:

            searchString += ' and fixVersion in (\''

            for fixVersion in fixVersionList:
                searchString += fixVersion + '\', \''

            searchString = searchString[:-4] +  '\')'

        if len(affectsVersionList) > 0:

            searchString += ' and affectedVersion in (\''

            for affectsVersion in affectsVersionList:
                searchString += affectsVersion + '\', \''

            searchString = searchString[:-4] +  '\')'

        if len(keyList) > 0:

            searchString = 'issuekey in (\''

            for key in keyList:
                searchString += key + '\', \''

            searchString = searchString[:-4] + '\')'

        options = {'maxResults': self.maxResults}

        if changelog:
            options['expand'] = 'changelog'

        issueListTemp = self.jira_obj.search_issues(searchString, **options)

        issueList = issueListTemp[:]

        idx = self.maxResults + 1

        while len(issueListTemp) != 0:
            options['startAt'] = idx

            issueListTemp = self.jira_obj.search_issues(searchString, **options)

            issueList += issueListTemp

            idx += self.maxResults

        # Get issue data
        issueProperties = ['key', 'id']
        fieldValueList = []

        for issue in issueList:

            issueData = {}

            for fieldName in fieldNameList:

                if fieldName in issueProperties:
                    exec 'issueData[fieldName] = issue.%s' % fieldName

                else:

                    issueData[fieldName] = None

                    try:
                        exec 'issueData[fieldName] = issue.fields.%s' % fieldName

                    except:

                        logger.error(
                            'getIssueDataFromIssueTypeProjectVersionKey: Field \'%s\' does not exist in issue: %s - %s' % (
                            fieldName, issueData['key'], issueData['summary']))

                    if type(issueData[fieldName]) == jira.resources.User:

                        userData = issueData[fieldName]

                        issueData[fieldName] = {
                            'displayName': userData.displayName,
                            'emailAddress': userData.emailAddress,
                            'name': userData.name
                        }

                    elif type(issueData[fieldName]) == unicode:

                        issueData[fieldName] = str(issueData[fieldName].encode('ascii', 'ignore'))
                        non_printable = string.translate(str(issueData[fieldName]), None, string.printable)
                        issueData[fieldName] = string.translate(str(issueData[fieldName]), None, non_printable)

                    elif type(issueData[fieldName]) == jira.resources.Status:

                        issueData[fieldName] = str(issueData[fieldName].name)

                    elif type(issueData[fieldName]) == jira.resources.Resolution:

                        issueData[fieldName] = str(issueData[fieldName].name)

                    elif type(issueData[fieldName]) == type(None):

                        issueData[fieldName] = ''

            if changelog:

                entryList = issue.changelog.histories

                issueData['changelog'] = []

                for entry in entryList:
                    for item in entry.items:
                        # Item is a dict that contains 'field', 'fieldtype', 'from', 'fromString', 'to', 'toString'
                        data = {
                            'field': item.field,
                            'from': item.fromString,
                            'fromKey': item.fromString,
                            'to': item.toString,
                            'toKey': item.to
                        }
                        issueData['changelog'].append(data)

            fieldValueList.append(issueData)

        return fieldValueList

    def faultReportsLinkedToRequiredFunctionality(self, requiredFunctionality, faultReportList):

        alreadyLinked = False

        linkedFaultReports = []

        # First get links present in the RF
        jiraIssueData = self.getIssueDataFromIssueTypeProjectVersionKey(
            ['Required Functionality', 'Test Exec'], ['hiT 7300 Program'], [], [], [requiredFunctionality], [], True)[0]

        # Now get the comments of RF
        for faultReport in faultReportList:
            alreadyLinked = False
            for changelog in jiraIssueData['changelog']:
                if changelog['field'] == 'Link':
                    if changelog['toKey']:
                        if changelog['toKey'] == faultReport:
                            logger.warn('Link from FR %s was in the past already linked to RF %s' %
                                        (changelog['toKey'], requiredFunctionality))
                            alreadyLinked = True
                            break
                    if changelog['fromKey']:
                        if changelog['fromKey'] == faultReport:
                            logger.warn('Link from FR %s was in the past already linked to RF %s' %
                                        (changelog['fromKey'], requiredFunctionality))
                            alreadyLinked = True
                            break

            linkedFaultReports.append(alreadyLinked)

        # Now check which FR is present in the above
        return linkedFaultReports

    def addLink(self, srcIssue, linkType, targetIssue):

        logger.info('Adding link \'%s\' from \'%s\' to \'%s\'' % (linkType, srcIssue, targetIssue))

        comment = {
            'body': 'hiT7300 Automation: Adding link from \'%s\' to \'%s\' with relation \'%s\'' % (
            srcIssue, targetIssue, linkType),
            'visibility': {
                'type': 'role',
                'value': 'Users',
            }
        }

        self.jira_obj.create_issue_link(linkType, srcIssue, targetIssue, comment)

    def updateJiraIssueField(self, issueKey, dataDict):

        issue = self.jira_obj.issue(issueKey)

        issue.update(**dataDict)

    def transitionJiraIssue(self, issueKey, transition, comment = None):

        self.jira_obj.transition_issue(issueKey, transition)

        # Add comment
        if comment:
            self.jira_obj.add_comment(issueKey, comment)

    def saveToFile(self, info, fileName='saveToFile.info'):
        '''
        Save to file the info content of a specific request or a dictionary
        :param fileName: File name
        '''

        # Create file and save content
        filen = open(fileName, 'w')
        filen.write(info.encode('utf8'))
        filen.close()

    # Dump information related with issues and other objects
    def dumpInfo(self, path):
        '''
        Dump all entity related information to a folder
        :param fileN: Folder where files will be saved
        '''

        info = ''

        # Get issue types and format them info and save it
        issueTypeList = self.jira_obj.issue_types()

        info += 'Issue types:\n\n'

        for issueType in issueTypeList:

            info += issueType.name + ': ' + issueType.id + '\n'

        # Todo Add this info also http://jira-sandbox.intra.coriant.com:8080/rest/api/latest/field

        # Save to file
        self.saveToFile(info, path + '\\issue_info.txt')
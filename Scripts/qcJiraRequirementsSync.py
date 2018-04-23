__author__ = 'anandrad'

from JIRARest import JIRARest

try:
    import lxml.etree as ET
except:
    import xml.etree.ElementTree as ET
    print 'Consider installing lxml library which is much faster!'

import itertools, time, argparse, sys

from QCRest_hiT7300 import hiT7300_QC, ConnectionError, QCError
from QCRest_hiT7300 import  gp_config_ini

def main(argv):

    args = getArgsParser().parse_args()

    data = None

    data = getDataFromIni()

    if args.user:
        data['qc_username'] = data['jira_username'] = args.user

    if args.password:
        data['qc_passwd'] = data['jira_passwd']= args.password

    # Establish connection to QC and JIRA
    qc_con = hiT7300_QC(data['qc_server'], data['qc_project'], data['qc_domain'], release='5.50.xx')
    jira_con = JIRARest(data['jira_server'])

    # Start Time
    start_time = time.time()

    try:
        # Open connection to QC and JIRA
        qc_con.login(data['qc_username'], data['qc_passwd'])
        jira_con.login(data['jira_username'], data['jira_passwd'])

        # Start sync process to QC
        rest_time_start = time.time()

        qcJIRASyncProcess(qc_con, jira_con, data)

        print 'Sync from JIRA to QC done: %s seconds!' % (time.time() - rest_time_start)

        print 'Congratulation! Script ran successfully!'
        print '--- %s seconds ---' % ( time.time() - start_time)

    except (ConnectionError, QCError) as e:
        print ('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)
        exit(1)

    finally:

        try:
            qc_con.logout()

        except (ConnectionError, QCError) as e:
            print ('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)
            exit(1)

    print ("Bye bye!")

def qcJIRASyncProcess(qc_con, jira_con, data):

    reqIdQC = 'user-01' # Requirement ID in QC database
    reqIdJIRA = 'customfield_20691'

    qcPriorities = {
        '1 - Critical': 'Prio 1',
        '2 - Major': 'Prio 2',
        '3 - Minor': 'Prio 3',
    }

    jiraIssueDataList = jira_con.getIssueDataFromIssueTypeProjectVersionKey(
        ['Required Functionality'], [data['jira_project']], data['jira_release'], [], [],
        ['assignee', 'description', 'priority', 'fixVersions', reqIdJIRA])

    # QC RF Name will be "<JIRA Key>-<Summary>
    # QCData mapping
    qcRequirementDataList = []

    pathGlobal = r'Requirements'

    # Get release id to map it correctly to QC
    # Just do this if the target release is not know yet
    r = qc_con.Releases.getEntity('id,name')
    xml = qc_con._getXmlFromRequestQueryList(r)
    targetReleaseIdList = qc_con.Releases.getEntityDataCollectionFieldValueList(['name', 'id'], xml)
    targetReleaseDict = dict(zip(targetReleaseIdList[0], targetReleaseIdList[1]))

    for jiraIssueData in jiraIssueDataList:

        release = []

        # fixVersion can have multiple values - Save multiple values to release and last release for target release
        for version in jiraIssueData['fixVersions']:
            release.append(targetReleaseDict[version.name])

        jiraLink = jira_con.url_server + '/browse/' + jiraIssueData['key']

        qcRequirementData = {
            # ToDo Implement Path Handling
            'path': pathGlobal,
            'name': '[' + jiraIssueData['key'] + '] - ' + jiraIssueData['summary'],
            'description': 'Jira link:' + jira_con.url_server + '/browse/' + jiraIssueData['key'] + '\r\n\r\n' + jiraIssueData['description'],
            reqIdQC: jiraIssueData['key'],                                              # Requirement ID: JIRA Key
            'req-priority': qcPriorities[jiraIssueData['priority'].name],               # Priority
            'target-rel': release,
            'attachmentUrl': {'data': '[InternetShortcut]\r\nURL=' + jiraLink, 'fileName': 'Jira Link.url',
                              'description':'Jira Link: ' + jiraLink},
        }

        qcRequirementDataList.append(qcRequirementData)

    # Now get all the requirements for a specific parent requirement ID
    qc_con.syncRequirements(qcRequirementDataList, reqIdQC)

def getDataFromIni(ini_file=r'qc_jira.ini'):

    data = {
        'qc_username': '68500353',
        'qc_passwd': None,

        'jira_username': '68500353',
        'jira_passwd': None,

        'qc_server': None,
        'qc_project': None,
        'qc_domain': None,

        'jira_server': None,
    }

    iniCo = None

    # Get ini info
    try:
        iniCo = gp_config_ini.ConfigIni(ini_file)


        key, val = iniCo.read_all_values('qcJiraRequirementsSync')
        iniQcDict = dict(itertools.izip(key, val))
        data['jira_project'] = iniQcDict['project']
        # Release is a list so lets buid it
        data['jira_release'] = [e.strip() for e in iniQcDict['release'].split(',')]

    except TypeError as e:
        print 'Error: No qc_jira.ini file found!\n\nPlease create a qc_jira.ini file in the same folder as this script. ' \
              'You can rename qc_jira_template.ini to qc_jira.ini and simply update the information inside.'

    except KeyError as e:
        print 'Error: Wrong parameter defined in qc.ini: %s' % (e.message)

    try:
        key, val = iniCo.read_all_values('QC User')
        iniQcDict = dict(itertools.izip(key, val))
        data['qc_username'] = iniQcDict['username']
        data['qc_passwd'] = iniQcDict['passwd']

        key, val = iniCo.read_all_values('JIRA User')
        iniQcDict = dict(itertools.izip(key, val))
        data['jira_username'] = iniQcDict['username']
        data['jira_passwd'] = iniQcDict['passwd']

        key, val = iniCo.read_all_values('QC Server')
        iniQcDict = dict(itertools.izip(key, val))
        data['qc_server'] = iniQcDict['server']
        data['qc_project'] = iniQcDict['project']
        data['qc_domain'] = iniQcDict['domain']

        key, val = iniCo.read_all_values('JIRA Server')
        iniQcDict = dict(itertools.izip(key, val))
        data['jira_server'] = iniQcDict['server']

    except (KeyError,TypeError) as e:
        print 'Warning: Missing field in qc.ini: %s\nNo problem, default value will be used!' % (e.message)

    return data

def getArgsParser():
    parser = argparse.ArgumentParser(description='Sync QC Requirements with Jira Required Functionality')
    parser.add_argument('-u', '--user', help="Username for QC and JIRA.")
    parser.add_argument('-p', '--password', help="Password for QC and JIRA.")

    return parser

if __name__ == '__main__':
    main(sys.argv)

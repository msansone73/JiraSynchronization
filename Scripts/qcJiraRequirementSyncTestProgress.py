__author__ = 'anandrad'

from JIRARest import JIRARest, logger

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

    def convDataJiraInKeyDict(dataJira):

        dataJiraConv = {}

        for entry in dataJira:
            dataJiraConv[entry['key']] = dict(entry)
            del(dataJiraConv[entry['key']]['key'])

        return dataJiraConv

    jiraIssueTypeListSearch = ['Required Functionality', 'Test Exec']

    reqIdQC = 'user-01' # Requirement ID in QC database

    plannedJiraField = 'customfield_21890'
    failedJiraField = 'customfield_21892'
    passedJiraField = 'customfield_21891'

    filterQCType = [
        qc_con.qcDataInfo['qcRequirementTypes']['Testing'],
    ]

    dataQc, globalTestInstancesStatus = qc_con.getReleaseCycleProgressFromJiraId(data['release'], reqIdQC, filterQCType)

    dataJiraReqFunc = jira_con.getIssueDataFromIssueTypeProjectVersionKey(
        ['Required Functionality'], [data['project']], data['release'], [], [],
        [plannedJiraField, failedJiraField, passedJiraField])

    dataJiraReqFunc = convDataJiraInKeyDict(dataJiraReqFunc)

    dataJiraTestExec = jira_con.getIssueDataFromIssueTypeProjectVersionKey(
        ['Test Exec'], [data['project']], data['release'], [], [],
        [plannedJiraField, failedJiraField, passedJiraField, 'status'])

    dataJiraTestExec = convDataJiraInKeyDict(dataJiraTestExec)

    dataJira = {}
    dataJira.update(dataJiraTestExec)
    dataJira.update(dataJiraReqFunc)

    for issueKey, value in dataQc.iteritems():

        dataForJira = {}

        if issueKey not in dataJira:
            msg = 'Requirement in QC (%s) was not found in Jira with search parameters defined in qc_jira.ini:\n' % (issueKey)
            msg += '\tProject(s): \'%s\'\n' % (str(data['project']))
            msg += '\tRelease(s): \'%s\'\n' % (str(data['release']))
            msg += '\tIssue Type(s) \'%s\'\n' % (str(jiraIssueTypeListSearch))
            msg += 'No update done!'
            logger.warning(msg)
            continue

        if dataJira[issueKey][plannedJiraField] == '':                     # Jira was never updated
            dataForJira[plannedJiraField] = int(value['Total'])
        elif int(value['Total']) != int(dataJira[issueKey][plannedJiraField]):
            dataForJira[plannedJiraField] =  int(value['Total'])           # Planned Tests

        if dataJira[issueKey][failedJiraField] == '':                      # Jira was never updated
            dataForJira[failedJiraField] = int(value['Failed'])
        elif int(value['Failed']) != int(dataJira[issueKey][failedJiraField]):
            dataForJira[failedJiraField] = int(value['Failed'])            # Failed Tests

        if dataJira[issueKey][passedJiraField] == '':                      # Jira was never updated
            dataForJira[passedJiraField] = int(value['Passed'])
        elif int(value['Passed']) != int(dataJira[issueKey][passedJiraField]):
            dataForJira[passedJiraField] =  int(value['Passed'])           # Passed Tests

        # Check if status should be updated - Issue is a TestExec
        if 'status' in dataJira[issueKey].keys():

            statusOpen = 'Open'
            statusInAnalysis = 'In Analysis'
            statusInDevelopment = 'In Development'
            statusInValidation = 'In Validation'

            transitionStartAnalysis = 'Start Analysis'
            transitionStopAnalysis = 'Stop Analysis'
            transitionStartDevelopment = 'Start Development'
            transitionStopDevelopment = 'Stop Development'
            transitionStartValidation = 'Start Validation'
            transitionStopValidation = 'Stop Validation'

            if dataJira[issueKey]['status'] == statusOpen:

                if int(value['Total']) > 0:

                    logger.info('Updating issue status %s with: %s' % (issueKey, transitionStartAnalysis))
                    jira_con.transitionJiraIssue( issueKey, transitionStartAnalysis)
                    dataJira[issueKey]['status'] = statusInAnalysis

            if dataJira[issueKey]['status'] == statusInAnalysis:

                if int(value['Total']) > 0:

                    logger.info('Updating issue status %s with: %s' % (issueKey, transitionStartDevelopment))
                    jira_con.transitionJiraIssue(
                            issueKey,
                            transitionStartDevelopment,
                        'hiT7300 Automation: Status automatically changed to \'In Development\'because total number of tests is higher than zero.')
                    dataJira[issueKey]['status'] = statusInDevelopment

            if dataJira[issueKey]['status'] == statusInDevelopment:

                if int(value['Passed']) > 0 or int(value['Failed']) > 0:

                    logger.info('Updating issue status %s with: %s' % (issueKey, transitionStartValidation))
                    jira_con.transitionJiraIssue(
                            issueKey,
                            transitionStartValidation,
                        'hiT7300 Automation: Status automatically changed to \'In Validation\' because number of executed tests is higher than zero.')
                    dataJira[issueKey]['status'] = statusInValidation

            if dataJira[issueKey]['status'] == statusInValidation:

                if int(value['Passed']) == 0 and int(value['Failed']) == 0:

                    logger.info('Updating issue status %s with: %s' % (issueKey, transitionStopValidation))
                    jira_con.transitionJiraIssue(
                            issueKey,
                            transitionStopValidation,
                        'hiT7300 Automation: Status automatically changed to \'In Development\' because total number of executed tests is zero.')
                    dataJira[issueKey]['status'] = statusInDevelopment

        if len(dataForJira) > 0:

            # Update remaining fields
            logger.info('Updating issue %s with: %s' % (issueKey, str(dataForJira)))
            jira_con.updateJiraIssueField(issueKey, dataForJira)

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

        key, val = iniCo.read_all_values('qcJiraRequirementSyncTestProgress')
        iniQcDict = dict(itertools.izip(key, val))
        # Release is a list so lets buid it
        data['release'] = [e.strip() for e in iniQcDict['release'].split(',')]
        data['project'] = iniQcDict['project']

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
    parser = argparse.ArgumentParser(description='Sync QC Defects with Jira Fault Reports')
    parser.add_argument('-u', '--user', help="Username for QC and JIRA.")
    parser.add_argument('-p', '--password', help="Password for QC and JIRA.")

    return parser

if __name__ == '__main__':
    main(sys.argv)

__author__ = 'anandrad'

from JIRARest import JIRARest

try:
    import lxml.etree as ET
except:
    import xml.etree.ElementTree as ET

    print 'Consider installing lxml library which is much faster!'

import itertools, time, argparse, sys

from QCRest_hiT7300 import hiT7300_QC, ConnectionError, QCError
from QCRest_hiT7300 import gp_config_ini

import logging

logger = logging.getLogger('QCRest')


def main(argv):
    args = getArgsParser().parse_args()

    data = None

    data = getDataFromIni()

    if args.user:
        data['qc_username'] = data['jira_username'] = args.user

    if args.password:
        data['qc_passwd'] = data['jira_passwd'] = args.password

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

        jiraFaultReportToRequiredFunctionalityLinkCreation(qc_con, jira_con, data)

        print 'Sync from JIRA to QC done: %s seconds!' % (time.time() - rest_time_start)

        print 'Congratulation! Script ran successfully!'
        print '--- %s seconds ---' % (time.time() - start_time)

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


def jiraFaultReportToRequiredFunctionalityLinkCreation(qc_con, jira_con, data):
    reqIdQC = 'user-01'  # Requirement ID in QC database
    defIdQC = 'user-06'  # Field in QC that has the Jira key => Error Source
    reqTypeQC = [qc_con.qcDataInfo['qcRequirementTypes']['Testing']]

    # First get from QC the relation between the RF and FR
    logger.info('jiraFaultReportToRequiredFunctionalityLinkCreation: Retrieving RF and FR relationship from QC')
    jiraReqFuncFaultReportRelationList = qc_con.getJiraRFJiraFRRelationFromQC(data['jira_release'], reqIdQC, defIdQC,
                                                                              reqTypeQC)

    # Check if the link to FR in the RF already exists our was previously updated and should or not be created
    for jiraReqFuncFaultReportRelation in jiraReqFuncFaultReportRelationList:

        logger.info('jiraFaultReportToRequiredFunctionalityLinkCreation: Checking for RF %s if FR links exist!' %
                    jiraReqFuncFaultReportRelation['jiraId'])
        alreadyCreatedLinkList = jira_con.faultReportsLinkedToRequiredFunctionality(
            jiraReqFuncFaultReportRelation['jiraId'], jiraReqFuncFaultReportRelation['faultReportJiraIdList'])

        for defId, alreadyCreatedLink in zip(
                jiraReqFuncFaultReportRelation['faultReportJiraIdList'], alreadyCreatedLinkList):

            if not alreadyCreatedLink:
                jira_con.addLink(defId, 'Relates', jiraReqFuncFaultReportRelation['jiraId'])


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

        key, val = iniCo.read_all_values('qcJiraDefToReqFuncLinkSync')
        iniQcDict = dict(itertools.izip(key, val))
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

    except (KeyError, TypeError) as e:
        print 'Warning: Missing field in qc.ini: %s\nNo problem, default value will be used!' % (e.message)

    return data


def getArgsParser():
    parser = argparse.ArgumentParser(description='Create Links between FR to Req Func in Jira based on QC info.')
    parser.add_argument('-u', '--user', help="Username for QC and JIRA.")
    parser.add_argument('-p', '--password', help="Password for QC and JIRA.")

    return parser


if __name__ == '__main__':
    main(sys.argv)

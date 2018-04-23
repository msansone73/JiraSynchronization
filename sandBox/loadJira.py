from JIRARest import JIRARest
from jira import JIRAError
from QCRest_hiT7300 import  gp_config_ini
import itertools, time, argparse, sys

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

        key, val = iniCo.read_all_values('qcJiraDefectsSync')
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
    parser = argparse.ArgumentParser(description='Sync QC Defects with Jira Fault Reports')
    parser.add_argument('-u', '--user', help="Username for QC and JIRA.")
    parser.add_argument('-p', '--password', help="Password for QC and JIRA.")

    return parser
def main(argv):

    args = getArgsParser().parse_args()
    data = None
    data = getDataFromIni()
    if args.user:
        data['qc_username'] = data['jira_username'] = args.user
    if args.password:
        data['qc_passwd'] = data['jira_passwd']= args.password

    jira_con = JIRARest(data['jira_server'])

    try:
        jira_con.login(data['jira_username'], data['jira_passwd'])
        print('jira logado.')
        jiraIssueDataList = jira_con.getIssueDataFromIssueTypeProjectVersionKey(
            [ 'Change Request'], [data['jira_project']], [], data['jira_release'], [],
            ['assignee', 'description', 'priority', 'status', 'created', 'reporter', 'versions', 'resolution'])

        for jiraIssueData in jiraIssueDataList:
            print jiraIssueData

    except JIRAError as e:
        print e.status_code, e.text

    except (Exception) as e:
        print ('\nUps, an exception was raised: ' + e)
        exit(1)













if __name__ == '__main__':
    main(sys.argv)


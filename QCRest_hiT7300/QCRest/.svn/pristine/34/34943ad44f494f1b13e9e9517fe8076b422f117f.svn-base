'''
    Created on 2014-11-09
    @author: Rodolfo Andrade
    QC.py - Contains the QC class that defines all the methods to handle QC specific actions

    >>> qc_con = QC('http://qc.intra.coriant.com:8090', 'sandbox_hiT7300_530x', 'sandbox', proxies={ 'http': '', 'https': '',})
    >>> qc_con.login('68500353', '')
    {'login': <Response [200]>, 'session': <Response [200]>, 'isauthenticated': <Response [200]>}

    Source test file to be used
    >>> xml = qc_con.readXmlFromFile( r'.\Doctest\sxml_test.xml')

    Add test to testplan
    >>> qc_con.addTestToTestPlan(xml, True)
    [None, [None, [<Response [201]>]]]
    >>> qc_con.addTestToTestPlan(xml, False, False)
    [<Response [200]>, [None, [<Response [201]>]]]
    >>> qc_con.addTestToTestPlan(xml, False, True)
    [None]

    Add testset to test lab
    >>> qc_con.addTestSet(xml, True)
    [None, [<Response [201]>]]
    >>> qc_con.addTestSet(xml, False, True)
    [None]
    >>> qc_con.addTestSet(xml, False, False)
    [<Response [200]>, [<Response [201]>]]

    Add test instance to test lab
    >>> qc_con.addTestInstanceToTestLab(xml, True, False)
    [None, [<Response [201]>]]
    >>> qc_con.addTestInstanceToTestLab(xml, True, True)
    [<Response [200]>, [<Response [201]>]]
    >>> qc_con.addTestInstanceToTestLab(xml, False, True)
    [None]
    >>> qc_con.addTestInstanceToTestLab(xml, False, False)
    [[<Response [201]>]]

    Add test run
    >>> qc_con.addTestRunToTestLab(xml)
    [[<Response [200]>], [<Response [201]>], [<Response [200]>], [<Response [200]>, <Response [200]>, <Response [200]>]]

    Close doctests session
    >>> qc_con.logout()
    {'closeSession': <Response [200]>, 'logout': <Response [200]>}
'''
import urllib

__author__ = 'Rodolfo Andrade'

try:
    import lxml.etree as ET
except:
    import xml.etree.ElementTree as ET

from os.path import join
from connect import Connect, ConnectionError

import os
import cStringIO
import copy
import itertools
import logging.handlers

# Logging configuration
loggerFileName = '.qc.log'
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Get logger
logger = logging.getLogger('QCRest')
logger.setLevel(logging.DEBUG)

# Stream Handler
streamHand = logging.StreamHandler()
streamHand.setLevel(logging.INFO)
streamHand.setFormatter(formatter)
logger.addHandler(streamHand)

# File handler
fileHand = logging.handlers.RotatingFileHandler(loggerFileName, maxBytes=int(20 * 1024 * 1024), backupCount=1)
fileHand.setLevel(logging.DEBUG)
fileHand.setFormatter(formatter)
logger.addHandler(fileHand)


class QC_Connect(Connect):
    '''
    Class that abstracts some of the configurations needed to connect to rest API namely the login, logout
    '''

    # Initialize connection
    def __init__(self, server=None, project=None, domain=None, silent=False, session=None, proxies=None):
        # Specific QC parameter
        self.project = project
        self.domain = domain
        self.url_server = server

        # URLs for QC
        self.url_is_auth = self.url_server + '/qcbin/rest/is-authenticated'
        self.url_login = self.url_server + '/qcbin/authentication-point/authenticate'
        self.url_logout = self.url_server + '/qcbin/authentication-point/logout'
        self.url_site_session = self.url_server + '/qcbin/rest/site-session'

        if proxies is None:
            # Only way to completetly disable proxy
            os.environ['NO_PROXY'] = self.url_server

        # Init upper class
        super(QC_Connect, self).__init__(self.url_login, self.url_logout, silent, session, proxies)

    # Overwrite login from Connect to support session management
    def login(self, user=None, passwd=None, **kwargs):
        # First login
        login_r = Connect.login(self, user, passwd, **kwargs)

        # Verify if it is authenticated
        isauthenticated_r = self.isAuthenticated(**kwargs)

        # Start session
        session_r = self._openSession(**kwargs)

        return {'login': login_r, 'isauthenticated': isauthenticated_r, 'session': session_r}

    # Overwrite logout from Connect to support delete session management
    def logout(self, **kwargs):
        # First stop session
        closeSession_r = self._closeSession()

        # Then logout
        logout_r = Connect.logout(self, **kwargs)

        return {'logout': logout_r, 'closeSession': closeSession_r}

    # Is authenticated
    def isAuthenticated(self, **kwargs):

        # First send request to check if it is authenticated
        logger.debug('isAuthenticated: Checking using \'' + str(self.url_is_auth) + '\'...')

        r = self.get(self.url_is_auth, **kwargs)

        # Validate response code
        self._validateResponse(r, 'isAuthenticated')

        return r

    # Extend Session
    def extendedSession(self, **kwargs):

        # First send request to check if it is extended
        logger.debug('extendedSession: Checking using \'' + str(self.url_site_session) + '\'...')

        r = self.get(self.url_site_session, **kwargs)

        # Validate response code
        self._validateResponse(r, 'extendedSession')

        return r

    # Open session
    def _openSession(self, **kwargs):

        # Open a new session
        logger.debug('_openSession: Open Session using \'' + str(self.url_site_session) + '\'...')

        r = self.post(self.url_site_session, **kwargs)

        # Validate response code
        self._validateResponse(r, '_openSession')

        return r

    # Delete Session
    def _closeSession(self, **kwargs):
        # First send request to check if it is deleting
        logger.debug('_closeSession: Close Session using \'' + str(self.url_site_session) + '\'...')

        r = self.delete(self.url_site_session, **kwargs)

        # Validate response code
        self._validateResponse(r, '_closeSession')

        return r


class QC_Project(QC_Connect):
    '''
    Class that abstracts some of the more generic QC functions namely those applicable to projects, lists, etc
    '''

    # Initialize connection
    def __init__(self, server=None, project=None, domain=None, silent=False, session=None, proxies=None):

        # Specific QC parameter
        self.project = project
        self.domain = domain
        self.url_server = server

        # Root customization used list URL
        self.url_project_lists = server + '/qcbin/rest/domains/' + domain + '/projects/' + project + '/customization/used-lists'

        # Init upper class
        super(QC_Project, self).__init__(server, project, domain, silent, session, proxies)

    # Query the collection of project lists that are in use using name
    # "/used-lists?id=12,55"
    def getProjectLists(self, **kwargs):

        # Define url
        url = self.url_project_lists

        # Get the list collection
        logger.debug('getProjectLists: Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getProjectLists')

        return r

    # Query the collection of project lists that are in use using name
    # "/used-lists?id=12,55"
    def getProjectListsQueryName(self, query='', headers=None, **kwargs):

        # Define query - entity is plural for these queries
        if not headers:
            pass
        url = self.url_project_lists + '?name=' + urllib.quote(query)

        # Get the test collection
        logger.debug('getProjectListsQueryName: Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getProjectListsQueryName')

        return r

    # Query the collection of project lists that are in use using the list id
    # "/used-lists?name=Status,Run State"    /used-lists?id=12,55
    def getProjectListsQueryId(self, query='', headers=None, **kwargs):

        # Define headers
        if not headers:
            pass

        # Define query - entity is plural for these queries
        url = self.url_project_lists + '?id=' + urllib.quote(query)

        # Get the test collection
        logger.debug('getProjectListsQueryID: Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getProjectListsQueryID')

        return r


class QC(QC_Project, QC_Connect):
    '''
    Class that contains all the useful functions to handle QC
    '''

    def __init__(self, server, project, domain, silent=False, session=None, proxies=None):
        '''
        Initialize connection to qc_server
        :param server: QC qc_server
        :param project: QC project
        :param domain: QC domain
        :param proxies: proxies (optional)
        :param session: session (optional)
        :param silent: silent (optional)
        :return:
        '''

        # Specific QC parameter
        self.project = project
        self.domain = domain
        self.url_server = server

        # Init upper class
        super(QC, self).__init__(server, project, domain, silent, session, proxies)

        # QC Entities -> It is necessary to pass the session it is has been initialized previously
        # Test Plan - Test Folder Collection (and instances)
        self.TestPlanTestFolders = QC_Entity('test-folder', server, project, domain, silent, self.session, proxies)

        # Test Plan - Tests Collection (and instances)
        self.TestPlanTests = QC_Entity('test', server, project, domain, silent, self.session, proxies)

        # Test Plan - Design Steps Collection (and instances)
        self.TestPlanDesignSteps = QC_Entity('design-step', server, project, domain, silent, self.session, proxies)

        # Test Lab - Runs Collection (and instances)
        self.TestLabRuns = QC_Entity('run', server, project, domain, silent, self.session, proxies)

        # Test Lab - Run Steps
        self.TestLabRunStep = QC_Entity_TL_Run_Step(server, project, domain, silent, self.session, proxies)

        # Test Lab - Test Collection (and instances)
        self.TestLabTestInstances = QC_Entity_TL_Test_Instance(server, project, domain, silent, self.session, proxies)

        # Test Lab - Test Set Collection (and instances)
        self.TestLabTestSets = QC_Entity('test-set', server, project, domain, silent, self.session, proxies)

        # Test Lab - Test Set Folders Collection (and instances)
        self.TestLabTestSetFolders = QC_Entity('test-set-folder', server, project, domain, silent, self.session,
                                               proxies)

        # Test Lab - Release Cycle Collection (and instances)
        self.ReleaseCycles = QC_Entity('release-cycle', server, project, domain, silent, self.session, proxies)

        # Test Lab - Releases Collection (and instances)
        self.Releases = QC_Entity('release', server, project, domain, silent, self.session, proxies)

        # Requirements Collection (and instances)
        self.Requirements = QC_Entity('requirement', server, project, domain, silent, self.session, proxies)

        # Defect Collection (and instances)
        self.Defects = QC_Entity('defect', server, project, domain, silent, self.session, proxies)

    def addTestToTestPlan(self, sxml, updateTestIfExists=False, ignoreTestIfExists=True):
        '''
        Add tests defined in sxml file

        update      ignore
        True        True        Update test if it exists - steps are not deleted
        True        False       Update test if it exists - steps deleted before updating (links included)
        False       False       Replace test if they exist (delete and create)
        False       True        Do nothing to test if they exist (Default)

        :param sxml: SXML
        :param updateTestIfExists: See function description
        :param ignoreTestIfExists: See function description
        :return:
        '''

        logger.info('addTestToTestPlan: Start...')
        logger.debug('addTestToTestPlan: updateTestIfExists: %s' % updateTestIfExists)
        logger.debug('addTestToTestPlan: ignoreTestIfExists: %s' % ignoreTestIfExists)

        # Response list
        r = []

        # Process data
        sxmlData = SXml(sxml)

        # Get Test data to add run
        listTestData = sxmlData.getTestData()

        # Get list of test folder
        listTestLocationXml = listTestData['location']
        # Get list of test folder
        listTestPathXml = listTestData['folder']
        # Get list of test name
        listTestNameXml = listTestData['name']
        # Get list of test tags
        listTestTagsXml = listTestData['tags']
        # Get list of run steps tags
        listDesignStepsTagsXml = listTestData['designstepstags']
        # Get list of run steps tags
        listDesignStepsNameXml = listTestData['designstepsname']

        if len(listTestNameXml) == 0:
            logger.warn('addTestToTestPlan: No test found in sxml!')
            return r

        # Remove duplicates
        # Get list of test  location
        listTestLocation = []
        # Get list of test folder
        listTestPath = []
        # Get list of test name
        listTestName = []
        # Get list of test tags
        listTestTags = []
        # Get list of run steps tags
        listDesignStepsTags = []
        # Get list of run steps tags
        listDesignStepsName = []

        # Remove repeated testset and just keep the first
        for testLocation, testPath, testName, testTags, designStepsTags, designStepsName in itertools.izip(
                listTestLocationXml, listTestPathXml, listTestNameXml, listTestTagsXml,
                listDesignStepsTagsXml, listDesignStepsNameXml):

            if testLocation not in listTestLocation:

                listTestLocation.append(testLocation)
                listTestPath.append(testPath)
                listTestName.append(testName)
                listTestTags.append(testTags)
                listDesignStepsTags.append(designStepsTags)
                listDesignStepsName.append(designStepsName)

            else:
                try:
                    logger.warning('addTestToTestPlan: Found duplicated tests! '
                                   'Discarding repeated entry %s' % testLocation)
                except:
                    pass

        # Get Ids from test in test plan
        listTestFolderIds = self._getIdTestPlanFolderFromPathList(listTestPath)

        # First get the list of tests that exist or not
        listTestId = self._getIdTestPlanTestFromFolderIdTestName(listTestFolderIds, listTestName)

        # Create two lists one for the ones that exist and another for the ones that need to be created
        # List of new test folder
        listNewTestPath = []
        # List of new test tags
        listNewTestTags = []
        # List of new test names
        listNewTestNames = []
        # List of new test folder id
        listNewTestFolderIds = []
        # Get list of new design steps tags
        listNewDesignStepsTags = []
        # Get list of new design steps name
        listNewDesignStepsName = []
        # List of old test tags
        listOldTestTags = []
        # List of old test names
        listOldTestNames = []
        # List of old test folder id
        listOldTestFolderIds = []
        # Get list of old design steps tags
        listOldDesignStepsTags = []
        # Get list of old design steps name
        listOldDesignStepsName = []

        # Populate them
        for index, id in enumerate(listTestId):

            # If id is not None it already exists
            if id:
                # Get list of old test tags
                listOldTestTags.append(listTestTags[index])
                # Get list of old test names
                listOldTestNames.append(listTestName[index])
                # Get list of old design steps tags
                listOldDesignStepsTags.append(listDesignStepsTags[index])
                # Get list of old design steps name
                listOldDesignStepsName.append(listDesignStepsName[index])
                # List of old test folder id
                listOldTestFolderIds.append(listTestFolderIds[index])
            else:
                # Get list of new test folder
                listNewTestPath.append(listTestPath[index])
                # Get list of old test names
                listNewTestNames.append(listTestName[index])
                # Get list of new test tags
                listNewTestTags.append(listTestTags[index])
                # List of new test folder id
                listNewTestFolderIds.append(listTestFolderIds[index])
                # Get list of old design steps tags
                listNewDesignStepsTags.append(listDesignStepsTags[index])
                # Get list of old design steps tags
                listNewDesignStepsName.append(listDesignStepsName[index])

        # Update test if it exists and remove elements that do not exist -> None
        listTestId = [elem for elem in listTestId if elem]

        # Check if test sets exist and update them if necessary or not...
        if updateTestIfExists is True and ignoreTestIfExists is True:
            # Update tests that already exist
            r.append(self._updateTestList(listOldTestFolderIds, listOldTestTags, listTestId,
                                          listOldDesignStepsTags, listOldDesignStepsName, listOldTestNames, False))

            # Create missing tests
            r.append(self._createTestList(listNewTestFolderIds, listNewTestTags, listNewTestPath,
                                          listNewDesignStepsTags, listNewDesignStepsName, listNewTestNames))

        elif updateTestIfExists is True and ignoreTestIfExists is False:
            # Update tests that already exist but delete steps first
            r.append(self._updateTestList(listOldTestFolderIds, listOldTestTags, listTestId,
                                          listOldDesignStepsTags, listOldDesignStepsName, listOldTestNames, True))

            # Create missing tests
            r.append(self._createTestList(listNewTestFolderIds, listNewTestTags, listNewTestPath,
                                          listNewDesignStepsTags, listNewDesignStepsName, listNewTestNames))

        elif updateTestIfExists is False and ignoreTestIfExists is True:
            # Do nothing to test if they exist and create missing tests
            r.append(self._createTestList(listNewTestFolderIds, listNewTestTags, listNewTestPath,
                                          listNewDesignStepsTags, listNewDesignStepsName, listNewTestNames)),

        elif updateTestIfExists is False and ignoreTestIfExists is False:
            # Replace test if they exist (delete and create)
            r.append(self._deleteTestList(listTestId, listTestName))

            # Create missing tests
            r.append(self._createTestList(listTestFolderIds, listTestTags, listTestPath,
                                          listDesignStepsTags, listDesignStepsName, listTestName))

        logger.debug('addTestToTestPlan: return: %s' % r)
        logger.info('addTestToTestPlan: ...done!')

        return r

    def addTestSet(self, sxml, updateTestSetIfExists=True, ignoreTestsetIfExists=False):
        '''
        Add testsets defined in sxml file

        update      ignore
        True          X         Update testset if it exists (Default)
        False       False       Replace testset if they exist (delete and create)
        False       True        Do nothing to testset if they exist

        :param sxml: SXML
        :param updateTestSetIfExists: See function description
        :param ignoreTestsetIfExists: See function description
        :return:
        '''

        logger.info('addTestSet: Start...')
        logger.debug('addTestSet: updateTestSetIfExists: %s' % updateTestSetIfExists)
        logger.debug('addTestSet: ignoreTestsetIfExists: %s' % ignoreTestsetIfExists)

        # Requests list
        r = []

        # Process data
        sxmlData = SXml(sxml)

        # Get Test Instance data to add run
        listTestSetData = sxmlData.getTestSetData()

        # Get list of testset locaton
        listTestSetLocationXml = listTestSetData['location']
        # Get list of testset folder
        listTestSetPathXml = listTestSetData['folder']
        # Get list of testset name
        listTestSetNameXml = listTestSetData['name']
        # Get list of testset tags
        listTestSetTagsXml = listTestSetData['tags']

        if len(listTestSetNameXml) == 0:
            logger.warn('addTestSet: No test testset found in sxml!')
            return r

        # Remove Root from the beginning of the lab paths
        for index, path in enumerate(listTestSetPathXml):

            if 'Root' not in path:
                self._raiseError('addTestSet', 'Invalid testset path - Missing \'Root\': ' + path + '!')

            listTestSetPathXml[index] = path[5:]

        # Get list of testset locaton
        listTestSetLocation = []
        # Get list of testset folder
        listTestSetPath = []
        # Get list of testset name
        listTestSetName = []
        # Get list of testset tags
        listTestSetTags = []

        # Remove repeated testset and just keep the first
        for testSetLocation, testSetPath, testSetName, testSetTags in itertools.izip(
                listTestSetLocationXml, listTestSetPathXml, listTestSetNameXml, listTestSetTagsXml):

            if testSetLocation not in listTestSetLocation:

                listTestSetLocation.append(testSetLocation)
                listTestSetPath.append(testSetPath)
                listTestSetName.append(testSetName)
                listTestSetTags.append(testSetTags)

            else:
                try:
                    logger.warning('addTestSet: Found duplicated testset! '
                                   'Discarding repeated entry %s' % testSetLocation)
                except:
                    pass

        # Get Ids from testset folders in test lab
        listTestSetFolderIds = self._getIdTestLabTestSetFolderFromPathList(listTestSetPath)

        # First get the list of test sets that exist or not
        listTestLabTestSetId = self._getIdTestLabTestSetFromFolderIdTestSetName(
            listTestSetFolderIds, listTestSetName)

        # Create two lists one for the ones that exist and another for the ones that need to be created
        # List of new testset folder
        listNewTestSetPath = []
        # List of new testset tags
        listNewTestSetTags = []
        # List of new test set folder id
        listNewTestSetFolderIds = []
        # List of old testset tags
        listOldTestSetTags = []
        # List of old test set folder id
        listOldTestSetFolderIds = []
        # List of old test set names
        listOldTestSetName = []
        # List of new test set names
        listNewTestSetName = []

        # Populate them
        for index, id in enumerate(listTestLabTestSetId):

            # If id is not None it already exists
            if id:
                # Get list of old testset tags
                listOldTestSetTags.append(listTestSetTags[index])
                # List of old test set folder id
                listOldTestSetFolderIds.append(listTestSetFolderIds[index])
                # List of old test set names
                listOldTestSetName.append(listTestSetName[index])
            else:
                # Get list of new testset folder
                listNewTestSetPath.append(listTestSetPath[index])
                # Get list of new testset tags
                listNewTestSetTags.append(listTestSetTags[index])
                # List of new test set folder id
                listNewTestSetFolderIds.append(listTestSetFolderIds[index])
                # List of old test set names
                listNewTestSetName.append(listTestSetName[index])

        # Update testset if it exists and remove elements that do not exist -> None
        listTestLabTestSetId = [elem for elem in listTestLabTestSetId if elem]

        # Check if test sets exist and update them if necessary or not...
        if updateTestSetIfExists is True:

            # Update testsets that already exist
            r.append(self._updateTestSetList(listOldTestSetFolderIds, listOldTestSetTags,
                                             listTestLabTestSetId, listOldTestSetName))

            # Create missing testsets
            r.append(self._createTestSetList(listNewTestSetFolderIds, listNewTestSetTags,
                                             listNewTestSetPath, listNewTestSetName))

        elif updateTestSetIfExists is False and ignoreTestsetIfExists is True:

            # Do nothing to testset if they exist and create missing testsets
            r.append(self._createTestSetList(listNewTestSetFolderIds, listNewTestSetTags,
                                             listNewTestSetPath, listNewTestSetName))

        elif updateTestSetIfExists is False and ignoreTestsetIfExists is False:

            # Replace testset if they exist (delete and create)
            r.append(self._deleteTestSetList(listTestLabTestSetId, listTestSetName))

            # Create missing testsets
            r.append(self._createTestSetList(listNewTestSetFolderIds, listNewTestSetTags,
                                             listNewTestSetPath, listNewTestSetName))

        logger.debug('addTestSet: return: %s' % r)
        logger.info('addTestSet: ...done!')

        return r

    def addTestInstanceToTestLab(self, sxml, updateTestInstanceIfExists=True, ignoreTestInstanceIfExists=False):
        """
        Add Test Instance to Test Lab
        update      ignore
        True        True        Replace test instance if they exist (delete and create)
        True        False       Update test instance if it exists (Default)
        False       False       Adds a new test instance if one already exists
        False       True        Do nothing to test instance if they exist

        :param sxml: Path to xml file containing the standard xml with the test info
        :param updateTestInstanceIfExists: Defines if the test instance when exists is overwritten - Default is False
        :param ignoreTestInstanceIfExists: Defined if the test instance is ignored if it exists - Default is True
        :return: Return the http response
        """

        logger.info('addTestInstanceToTestLab: Start...')
        logger.debug('addTestInstanceToTestLab: updateTestInstanceIfExists: %s' % updateTestInstanceIfExists)
        logger.debug('addTestInstanceToTestLab: ignoreTestInstanceIfExists: %s' % ignoreTestInstanceIfExists)

        # Requests list
        r = []

        # Process data
        sxmlData = SXml(sxml)

        # Get Test Instance data
        listTestInstanceData = sxmlData.getTestInstancesData()

        # Get list of test location
        listSourceTestInstancePathXml = listTestInstanceData['location']
        # Get list of test location
        listSourceTestPathXml = listTestInstanceData['testlocation']
        # Get list of test name
        listSourceTestNameXml = listTestInstanceData['testname']
        # Get list of testset location
        listTargetTestsetPathXml = listTestInstanceData['testsetlocation']
        # Get list of tags for the test instance
        listTagsTestInstanceXml = listTestInstanceData['tags']

        if len(listSourceTestNameXml) == 0:
            logger.warn('addTestInstanceToTestLab: No test instance found in sxml!')
            return r

        # Remove test instance duplicates
        # Get list of test instance location
        listSourceTestInstancePath = []
        # Get list of test location
        listSourceTestPath = []
        # Get list of test name
        listSourceTestName = []
        # Get list of testset location
        listTargetTestsetPath = []
        # Get list of tags for the test instance
        listTagsTestInstance = []

        for sourceTestInstancePath, sourceTestPath, sourceTestName, targetTestsetPath, tagsTestInstance in itertools.izip(
                listSourceTestInstancePathXml, listSourceTestPathXml, listSourceTestNameXml, listTargetTestsetPathXml,
                listTagsTestInstanceXml):

            if sourceTestInstancePath not in listSourceTestInstancePath:
                listSourceTestInstancePath.append(sourceTestInstancePath)
                listSourceTestPath.append(sourceTestPath)
                listSourceTestName.append(sourceTestName)
                listTargetTestsetPath.append(targetTestsetPath)
                listTagsTestInstance.append(tagsTestInstance)
            else:
                try:
                    logger.warning('addTestInstanceToTestLab: Found duplicated test instance! '
                                   'Discarding repeated entry %s' % sourceTestPath)
                except:
                    pass

        # Get Ids from tests in test plan
        listTestPlanTestIds = self._getIdTestPlanTestFromPathList(listSourceTestPath)

        # Remove Root from the beginning of the lab paths
        for index, path in enumerate(listTargetTestsetPath):

            if 'Root' not in path:
                self._raiseError('_createTestSetList', 'Invalid testset path - Missing \'Root\': ' + path + '!')

            listTargetTestsetPath[index] = path[5:]

        # Get Ids from testsets in test lab
        listTestLabTestsetIds = self._getIdTestLabTestSetFromPathList(listTargetTestsetPath)

        # Get Ids of Test Instances that already exist
        listTestLabTestInstanceId = self._getIdTestLabTestInstancesFromTestsetIdTestId(
            listTestLabTestsetIds, listTestPlanTestIds)

        # Create two lists, one for the ones that already exist and the others
        # List of old test instance testset ids
        listOldTestLabTestsetIds = []
        # List of ids that already exist
        listOldTestLabTestInstanceId = []
        # List of old test instance test plan test ids
        listOldTestPlanTestIds = []
        # List of old test instance tags
        listOldTagsTestInstance = []
        # List of new test names
        listNewNameTest = []
        # List of old test names
        listOldNameTest = []
        # List of new test instance testset ids
        listNewTestLabTestsetIds = []
        # List of new test instance test plan test ids
        listNewTestPlanTestIds = []
        # List of new test instance tags
        listNewTagsTestInstance = []

        for index, id in enumerate(listTestLabTestInstanceId):

            # If id is None it is a new test instance
            if id:
                listOldTestLabTestsetIds.append(listTestLabTestsetIds[index])
                listOldTestLabTestInstanceId.append(listTestLabTestInstanceId[index])
                listOldTestPlanTestIds.append(listTestPlanTestIds[index])
                listOldTagsTestInstance.append(listTagsTestInstance[index])
                listOldNameTest.append(listSourceTestName[index])
            else:
                listNewTestLabTestsetIds.append(listTestLabTestsetIds[index])
                listNewTestPlanTestIds.append(listTestPlanTestIds[index])
                listNewTagsTestInstance.append(listTagsTestInstance[index])
                listNewNameTest.append(listSourceTestName[index])

        # Remove elements that do not exist -> None
        listTestLabTestInstanceId = [elem for elem in listTestLabTestInstanceId if elem]

        if updateTestInstanceIfExists is True and ignoreTestInstanceIfExists is True:

            # Delete test instance if exists and add a new one
            r.append(self._deleteTestInstanceList(listTestLabTestInstanceId, listSourceTestName))

            # Create test instance list
            r.append(self._createTestInstance(listTestLabTestsetIds, listTestPlanTestIds,
                                              listTagsTestInstance, listSourceTestName))

        elif updateTestInstanceIfExists is False and ignoreTestInstanceIfExists is True:

            # Do nothing to test instance if they exist and create new
            r.append(self._createTestInstance(listNewTestLabTestsetIds, listNewTestPlanTestIds,
                                              listNewTagsTestInstance, listNewNameTest))

        elif updateTestInstanceIfExists is True and ignoreTestInstanceIfExists is False:

            # Update old and create new
            r.append(self._updateTestInstance(listOldTestLabTestsetIds, listOldTestPlanTestIds,
                                              listOldTagsTestInstance, listOldTestLabTestInstanceId,
                                              listOldNameTest))

            # Create new
            r.append(self._createTestInstance(listNewTestLabTestsetIds, listNewTestPlanTestIds,
                                              listNewTagsTestInstance, listNewNameTest))

        elif updateTestInstanceIfExists is False and ignoreTestInstanceIfExists is False:
            # Adds a new test instance if one already exists
            r.append(self._createTestInstance(listTestLabTestsetIds, listTestPlanTestIds,
                                              listTagsTestInstance, listSourceTestName))

        logger.debug('addTestInstanceToTestLab: return: %s' % r)
        logger.info('addTestInstanceToTestLab: ...done!')

        return r

    def addTestRunToTestLab(self, sxml):
        '''
        Add test run to test lab based on info provided in the sxml
        :param sxml: SXml file path
        :return:
        '''

        logger.info('addTestRunToTestLab: Start...')

        # Request responses
        req = []

        # Process data
        sxmlData = SXml(sxml)

        # Get Test Instance data to add run
        listTestInstanceRunData = sxmlData.getTestInstancesRunData()

        # Get list of run steps tags
        listRunStepsTags = listTestInstanceRunData['runstepstags']
        # Get list of test location
        listSourceTestPath = listTestInstanceRunData['testlocation']
        # Get list of test instance name
        listSourceTestName = listTestInstanceRunData['testname']
        # Get list of testset location
        listTargetTestsetPath = listTestInstanceRunData['testsetlocation']
        # Get list of tags for the test run
        listTagsTestInstanceRun = listTestInstanceRunData['tags']
        # Get list of tags for the test instance
        listTagsTestInstance = listTestInstanceRunData['testinstancetags']

        if len(listSourceTestName) == 0:
            logger.warn('addTestRunToTestLab: No test instance found in sxml!')
            return req

        # Get Ids from tests in test plan
        listTestPlanTestIds = self._getIdTestPlanTestFromPathList(listSourceTestPath)

        # Check if test plan ids are None
        if None in listTestPlanTestIds:
            listOfNamesOfMissingTests = set([listSourceTestName[idx] for idx, e in enumerate(listTestPlanTestIds) if
                                             e is None])

            self._raiseError('addTestRunToTestLab', 'Following tests do not exist: %s' % listOfNamesOfMissingTests)

        # Remove Root from the beginning of the lab paths
        for index, path in enumerate(listTargetTestsetPath):

            if 'Root' not in path:
                self._raiseError('addTestRunToTestLab', 'Invalid testset path - Missing \'Root\': ' + path + '!')

            listTargetTestsetPath[index] = path[5:]

        # Get Ids from testsets in test lab
        listTestLabTestsetIds = self._getIdTestLabTestSetFromPathList(listTargetTestsetPath)

        # Check if test plan ids are None
        if None in listTestLabTestsetIds:
            listOfNamesOfMissingTestsets = set([listTargetTestsetPath[idx] for idx, e in
                                                enumerate(listTestLabTestsetIds) if e is None])

            self._raiseError('addTestRunToTestLab',
                             'Following test sets do not exist: %s' % listOfNamesOfMissingTestsets)

        # Get Ids of Test Instances that already exist
        listTestLabTestInstanceId = self._getIdTestLabTestInstancesFromTestsetIdTestId(
            listTestLabTestsetIds, listTestPlanTestIds)

        # Raise error in case tests are missing
        if None in listTestLabTestInstanceId:
            testInstanceMissing = set([e for idx, e in enumerate(listSourceTestName) if
                                       listTestLabTestInstanceId[idx] == None])

            self._raiseError('addTestRunToTestLab', 'TestInstance missing: %s' % testInstanceMissing)

            logger.debug('addTestRunToTestLab: return: %s' % None)
            logger.info('addTestRunToTestLab: ...done!')

        # Add test run
        # Get Required Fields
        testLabRunTemplateXml = self.TestLabRuns.getEntityDataTemplate()

        # Add mandatory - Not required fields
        testLabRunTemplateXml = self.TestLabRuns.addEntityDataFieldValue(
            'subtype-id', 'hp.qc.run.MANUAL', testLabRunTemplateXml)

        # Build test collection
        testLabRunCollection = None
        listTestPlanTestIdsToBeUpdate = []
        listTestLabTestInstanceIdToBeUpdate = []
        listTestLabTestsetIdsToBeUpdate = []
        listTagsTestInstanceRunToBeUpdate = []
        listSourceTestNameToBeUpdate = []
        listRunStepsTagsToBeUpdate = []

        for testPlanTestId, testLabTestInstanceId, testLabTestsetId, tagsTestInstanceRun, testName, runStepTags in itertools.izip(
                listTestPlanTestIds, listTestLabTestInstanceId, listTestLabTestsetIds, listTagsTestInstanceRun,
                listSourceTestName, listRunStepsTags):

            if len(tagsTestInstanceRun) == 0:
                logger.warn('addTestRunToTestLab: No test instance run info found in sxml for test %s!' % testName)
                continue

            listTestPlanTestIdsToBeUpdate.append(testPlanTestId)
            listTestLabTestInstanceIdToBeUpdate.append(testLabTestInstanceId)
            listTestLabTestsetIdsToBeUpdate.append(testLabTestsetId)
            listTagsTestInstanceRunToBeUpdate.append(tagsTestInstanceRun)
            listSourceTestNameToBeUpdate.append(testName)
            listRunStepsTagsToBeUpdate.append(runStepTags)

            # Create copy
            testLabRunXml = testLabRunTemplateXml

            # Update necessary fields
            # Test Id
            testLabRunXml = self.TestLabRuns.addEntityDataFieldValue(
                'test-id', testPlanTestId, testLabRunXml)
            # Test Instance
            testLabRunXml = self.TestLabRuns.addEntityDataFieldValue(
                'testcycl-id', testLabTestInstanceId, testLabRunXml)
            # Test Set
            testLabRunXml = self.TestLabRuns.addEntityDataFieldValue(
                'cycle-id', testLabTestsetId, testLabRunXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in tagsTestInstanceRun.iteritems():

                # Status cannot be updated here or test instance will not reflect the run status
                if field == 'status':
                    continue

                testLabRunXml = self.TestLabTestInstances.addEntityDataFieldValue(
                    field, value, testLabRunXml)

            # Add to collection
            testLabRunCollection = self.TestLabRuns.addEntityDataToCollection(testLabRunXml, testLabRunCollection)

        if len(listSourceTestNameToBeUpdate) == 0:
            logger.warn('addTestRunToTestLab: No test instance run info found in sxml!')
            return req

        # Add run to test instance in testlab
        logger.info('addTestRunToTestLab: Adding run to tests: %s' % listSourceTestNameToBeUpdate)
        r = self.TestLabRuns.postEntityCollection(testLabRunCollection)
        logger.info('addTestRunToTestLab: Adding run to tests done!')
        req.append(r)

        # Get ids from runs created ad update these with the correct status so that the test instance can reflect the
        # correct test status
        xml = self._getXmlFromRequestQueryList(r)
        idList = self.TestLabRuns.getEntityDataCollectionFieldValue('id', xml)

        # Order list
        idListOrd = []

        testInstanceIdList = self.TestLabRuns.getEntityDataCollectionFieldValue('testcycl-id', xml)

        for testLabTestInstanceId in listTestLabTestInstanceIdToBeUpdate:

            for idx, testInstanceId in enumerate(testInstanceIdList):

                if testInstanceId == testLabTestInstanceId:
                    idListOrd.append(idList[idx])

        # Build run collection to be updated
        testLabRunCollection = None
        for testPlanTestId, testLabTestInstanceId, testLabTestsetId, tagsTestInstanceRun, id in itertools.izip(
                listTestPlanTestIdsToBeUpdate, listTestLabTestInstanceIdToBeUpdate, listTestLabTestsetIdsToBeUpdate,
                listTagsTestInstanceRunToBeUpdate, idListOrd):

            # Create copy
            testLabRunXml = testLabRunTemplateXml

            # Update necessary fields
            # Test Id
            testLabRunXml = self.TestLabRuns.addEntityDataFieldValue(
                'test-id', testPlanTestId, testLabRunXml)
            # Test Instance
            testLabRunXml = self.TestLabRuns.addEntityDataFieldValue(
                'testcycl-id', testLabTestInstanceId, testLabRunXml)
            # Test Set
            testLabRunXml = self.TestLabRuns.addEntityDataFieldValue(
                'cycle-id', testLabTestsetId, testLabRunXml)
            testLabRunXml = self.TestLabRuns.addEntityDataFieldValue(
                'id', id, testLabRunXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in tagsTestInstanceRun.iteritems():
                testLabRunXml = self.TestLabTestInstances.addEntityDataFieldValue(
                    field, value, testLabRunXml)

            # Add to collection
            testLabRunCollection = self.TestLabRuns.addEntityDataToCollection(testLabRunXml, testLabRunCollection)

        # Update run to test instance in testlab
        logger.info('addTestRunToTestLab: Update run status of tests: %s' % listSourceTestNameToBeUpdate)
        r = self.TestLabRuns.putEntityCollection(testLabRunCollection)
        logger.info('addTestRunToTestLab: Update run status of tests done!')
        req.append(r)

        # If successful get the run IDs and TestInstance Ids
        xml = self._getXmlFromRequestQueryList(r)
        runIds = self.TestLabRuns.getEntityDataCollectionFieldValue('id', xml)
        runTestInstanceIds = self.TestLabRuns.getEntityDataCollectionFieldValue('testcycl-id', xml)

        # Order Ids list according to the info in the xml so that we can match the values
        # This ordering is based on the already ordered list listTestLabTestInstanceIds
        runIdsOrd = []
        runTestInstanceIdsOrd = []
        for testLabTestInstanceId in listTestLabTestInstanceIdToBeUpdate:

            # First check if it exists
            if testLabTestInstanceId in runTestInstanceIds:
                position = runTestInstanceIds.index(testLabTestInstanceId)

                runIdsOrd.append(runIds[position])
                runTestInstanceIdsOrd.append(runTestInstanceIds[position])

        r = self._updateRunStepsList(runIdsOrd, listRunStepsTagsToBeUpdate, listSourceTestNameToBeUpdate)
        req.append(r)

        logger.debug('addTestRunToTestLab: return: %s' % r)
        logger.info('addTestRunToTestLab: ...done!')

        return req

    def _updateTestList(self, listTestFolderIds, listTestTags, listTestId, listDesignStepsTags,
                        listDesignStepsName, listTestName, deleteSteps):
        '''
        Create test based on the test folder ids and test tags
        :param listTestFolderIds:  test folder ids
        :param listTestTags: test field information
        :param listTestId: test ids
        :param listDesignStepsTags: Design steps tags
        :param listDesignStepsName: Design steps name
        :param deleteSteps: If True deletes steps of test before -Steps always created
        :return:
        '''

        logger.info('_updateTestList: Start...')
        logger.debug('_updateTestList: listTestFolderIds: %s' % listTestFolderIds)
        logger.debug('_updateTestList: listTestTags: %s' % listTestTags)
        logger.debug('_updateTestList: listTestId: %s' % listTestId)
        logger.debug('_updateTestList: listDesignStepsTags: %s' % listDesignStepsTags)
        logger.debug('_updateTestList: listDesignStepsName: %s' % listDesignStepsName)

        # If nothing to do, do nothing!
        if len(listTestFolderIds) == 0:
            logger.debug('_updateTestList: return: %s' % None)
            logger.info('_updateTestList: ...done!')

            return None

        # Get Required Fields
        testPlanTestTemplateXml = self.TestPlanTests.getEntityDataTemplate()

        # Add mandatory - Not required fields
        testPlanTestTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'subtype-id', 'MANUAL', testPlanTestTemplateXml)

        # Build testSet collection
        testPlanTestCollection = None
        testIdsToBeUpdated = []
        for testPlanTestTags, testPlanTestFolderId, testPlanTestId in itertools.izip(
                listTestTags, listTestFolderIds, listTestId):

            # We need to be careful because there might exist more than one reference to the same test. In this case,
            # only the first will be updated
            if testPlanTestId in testIdsToBeUpdated:
                continue
            else:
                testIdsToBeUpdated.append(testPlanTestId)

            # Create copy
            testPlanTestXml = testPlanTestTemplateXml

            # Parent folder Id
            testPlanTestXml = self.TestPlanTests.addEntityDataFieldValue(
                'parent-id', testPlanTestFolderId, testPlanTestXml)

            # Id
            testPlanTestXml = self.TestPlanTests.addEntityDataFieldValue(
                'id', testPlanTestId, testPlanTestXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in testPlanTestTags.iteritems():
                testPlanTestXml = self.TestPlanTests.addEntityDataFieldValue(
                    field, value, testPlanTestXml)

            # Add to collection
            testPlanTestCollection = self.TestPlanTests.addEntityDataToCollection(
                testPlanTestXml, testPlanTestCollection)

        # Response
        r = []

        # Updating test
        logger.info('_updateTestList: Updating tests: %s' % listTestName)
        r.append(self.TestPlanTests.putEntityCollection(testPlanTestCollection))
        logger.info('_updateTestList: Updating tests done!')

        # Add Design Steps
        r.append(self._addDesignSteps(listTestId, listDesignStepsTags, listDesignStepsName, listTestName, deleteSteps))

        logger.debug('_updateTestList: return: %s' % r)
        logger.info('_updateTestList: ...done!')

        return r

    def _createTestList(self, listTestFolderIds, listTestTags, listTestPath, listDesignStepsTags,
                        listDesignStepsName, listTestName):
        '''
        Create test based on the test folder ids and test tags
        :param listTestTags:  Test folder ids - None indicates a test folder not created
        :param listTestPath: List of test path information
        :param listDesignStepsTags: List of design steps field information
        :param listDesignStepsName: List of design steps name
        :return:
        '''

        logger.info('_createTestList: Start...')
        logger.debug('_createTestList: listTestFolderIds: %s' % listTestFolderIds)
        logger.debug('_createTestList: listTestTags: %s' % listTestTags)
        logger.debug('_createTestList: listTestPath: %s' % listTestPath)
        logger.debug('_createTestList: listDesignStepsTags: %s' % listDesignStepsTags)
        logger.debug('_createTestList: listDesignStepsName: %s' % listDesignStepsName)

        # If nothing to do, do nothing!
        if len(listTestFolderIds) == 0:
            logger.debug('_createTestList: return: %s' % None)
            logger.info('_createTestList: ...done!')

            return None

        # If folders do not exist create them
        testFoldersMissing = [elem for index, elem in enumerate(listTestPath)
                              if not listTestFolderIds[index]]

        self._addTestFolderList(testFoldersMissing)

        # Get Ids from test folders in test lab
        listTestFolderIds = self._getIdTestPlanFolderFromPathList(listTestPath)

        # Add test
        # Get Required Fields
        testPlanTestTemplateXml = self.TestPlanTests.getEntityDataTemplate()

        # Add mandatory - Not required fields
        testPlanTestTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'subtype-id', 'MANUAL', testPlanTestTemplateXml)

        # Build test collection
        testPlanTestCollection = None
        for testTags, testPlanTestFolderId in itertools.izip(listTestTags, listTestFolderIds):

            # Create copy
            testPlanTestXml = testPlanTestTemplateXml

            # Parent folder ID
            testPlanTestXml = self.TestPlanTests.addEntityDataFieldValue(
                'parent-id', testPlanTestFolderId, testPlanTestXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in testTags.iteritems():
                testPlanTestXml = self.TestPlanTests.addEntityDataFieldValue(
                    field, value, testPlanTestXml)

            # Add to collection
            testPlanTestCollection = self.TestPlanTests.addEntityDataToCollection(
                testPlanTestXml, testPlanTestCollection)

        # Add test
        logger.info('_createTestList: Creating test list: %s!' % listTestName)
        r = self.TestPlanTests.postEntityCollection(testPlanTestCollection)
        logger.info('_createTestList: Creating test list done!')

        # Add Design steps
        # If successful get the test IDs
        xml = self._getXmlFromRequestQueryList(r)
        newTestIdList = self.TestPlanTests.getEntityDataCollectionFieldValue('id', xml)
        newTestFolderIdList = self.TestPlanTests.getEntityDataCollectionFieldValue('parent-id', xml)
        newTestNameList = self.TestPlanTests.getEntityDataCollectionFieldValue('name', xml)

        logger.debug('_createTestList: xml: %s' % xml)

        # Order Ids list according to the info in the xml so that we can match the values
        # This ordering is based on the already ordered list listTestLabTestInstanceIds
        testIdsOrd = []
        for testFolderId, testName in itertools.izip(listTestFolderIds, listTestName):

            for newTestFolderId, newTestName, newTestId in itertools.izip(
                    newTestFolderIdList, newTestNameList, newTestIdList):

                if newTestFolderId == testFolderId and newTestName == testName:
                    testIdsOrd.append(newTestId)

        r = self._addDesignSteps(testIdsOrd, listDesignStepsTags, listDesignStepsName, listTestName, False)

        logger.debug('_createTestList: return: %s' % r)
        logger.info('_createTestList: ...done!')

        return r

    def _deleteTestList(self, listTestId, listTestName):
        '''
        Delete Test with specific ID
        :param listTestId: test ids
        :return:
        '''

        logger.info('_deleteTestList: Start...')
        logger.debug('_deleteTestList: listTestId: %s' % listTestId)

        # If nothing to do, do nothing!
        if len(listTestId) == 0:
            logger.debug('_deleteTestList: return: %s' % None)
            logger.info('_deleteTestList: ...done!')

            return None

        # Delete test
        logger.info('_deleteTestList: Deleting test list: %s!' % listTestName)
        r = self.TestPlanTests.deleteEntityIdList(listTestId)
        logger.info('_deleteTestList: Deleting test list done!')

        logger.debug('_deleteTestList: return: %s' % r)
        logger.info('_deleteTestList: ...done!')

        return r

    def _addDesignSteps(self, testIds, listDesignStepsTags, listDesignStepsName, testNameList, deleteSteps):
        '''
        Add design Steps to a test in test plan
        :param testIds: test ids that will be updated
        :param listDesignStepsTags:  Design steps tags
        :param listDesignStepsName:  Design steps names
        :param deleteSteps: Delete steps
        :return:
        '''

        logger.info('_addDesignSteps: Start...')
        logger.debug('_addDesignSteps: testIds: %s' % testIds)
        logger.debug('_addDesignSteps: listDesignStepsTags: %s' % listDesignStepsTags)
        logger.debug('_addDesignSteps: listDesignStepsName: %s' % listDesignStepsName)

        # Expand lists
        testIdExp = []
        designStepsNameExp = []
        designStepsTagsExp = []
        listDesignStepsIds = []

        for testId, designStepsName, designStepsTags in itertools.izip(
                testIds, listDesignStepsName, listDesignStepsTags):

            # Get list of steps
            listDesignStepsIds += self._getIdTestPlanDesignStepFromTestIdStepName(
                [testId]*len(designStepsName), designStepsName)

            for dsName, dsTags in itertools.izip(designStepsName, designStepsTags):
                testIdExp.append(testId)
                designStepsNameExp.append(dsName)
                designStepsTagsExp.append(dsTags)

        # Create two lists one for the ones that exist and another for the ones that need to be created
        # List of old test ids
        oldTestIds = []
        # List of old design steps tags
        oldDesignStepsTags = []
        # List of old design steps name
        oldDesignStepName = []
        # List of testIds which do not have the corresponding step created
        newTestIds = []
        # List of new design step tags
        newDesignStepTags = []

        # Populate them
        for index, id in enumerate(listDesignStepsIds):

            # If id is not None it already exists
            if id:
                # Get list of old test ids
                oldTestIds.append(testIdExp[index])
                # Get list of old design steps tags
                oldDesignStepsTags.append(designStepsTagsExp[index])
                # Get list of old design steps name
                oldDesignStepName.append(designStepsNameExp[index])
            else:
                # Get list of new test ids
                newTestIds.append(testIdExp[index])
                # Get list of new design steps tags
                newDesignStepTags.append(designStepsTagsExp[index])

        listDesignStepsIds = [el for el in listDesignStepsIds if el]

        # Requests list
        r = []

        # Delete Steps
        if deleteSteps:
            # Delete steps
            r.append(self._deleteDesignStepsFromTestIdList(testIds))

            # Create those that not exist
            r.append(self._createDesignStepsList(testIdExp, designStepsTagsExp, testNameList))

        else:
            # Update those that exist
            r.append(self._updateDesignStepsList(oldTestIds, oldDesignStepsTags, listDesignStepsIds, testNameList))

            # Create those that not exist
            r.append(self._createDesignStepsList(newTestIds, newDesignStepTags, testNameList))

        logger.debug('_addDesignSteps: return: %s' % r)
        logger.info('_addDesignSteps: ...done!')

        return r

    def _updateDesignStepsList(self, testIds, listDesignStepsTags, listDesignStepsIds, testNameList):
        '''
        Update design steps
        :param testIds: Test ids of tests that will have its steps updated
        :param listDesignStepsTags: Design steps tags information
        :param listDesignStepsIds: Design steps ids
        :return:
        '''

        logger.info('_updateDesignStepsList: Start...')
        logger.debug('_updateDesignStepsList: testIds: %s' % testIds)
        logger.debug('_updateDesignStepsList: listDesignStepsTags: %s' % listDesignStepsTags)
        logger.debug('_updateDesignStepsList: listDesignStepsIds: %s' % listDesignStepsIds)
        logger.debug('_updateDesignStepsList: testNameList: %s' % testNameList)

        req = []

        # If nothing to do, do nothing...
        if len(testIds) == 0:
            logger.debug('_updateDesignStepsList: return: %s' % None)
            logger.info('_updateDesignStepsList: ...done!')

            return None

        # Add test design step
        # Get Required Fields
        testDesignStepTemplateXml = self.TestPlanDesignSteps.getEntityDataTemplate()

        # Build design step collection and add design step collection
        logger.info('_updateDesignStepsList: Updating steps of tests: %s' % testNameList)

        stepCollection = 500
        testPlanDesignStepCollection = None
        for idx, (testDesignStepsTags, testId, designStepsIds) in enumerate(
                itertools.izip(listDesignStepsTags, testIds, listDesignStepsIds)):

            # Create copy
            testPlanTestXml = testDesignStepTemplateXml

            # Parent folder ID
            testPlanTestXml = self.TestPlanDesignSteps.addEntityDataFieldValue(
                'parent-id', testId, testPlanTestXml)

            # Parent folder ID
            testPlanTestXml = self.TestPlanDesignSteps.addEntityDataFieldValue(
                'id', designStepsIds, testPlanTestXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in testDesignStepsTags.iteritems():
                testPlanTestXml = self.TestPlanDesignSteps.addEntityDataFieldValue(
                    field, value, testPlanTestXml)

            # Add to collection
            testPlanDesignStepCollection = self.TestPlanDesignSteps.addEntityDataToCollection(
                testPlanTestXml, testPlanDesignStepCollection)

            if ((idx+1) % stepCollection) == 0:

                req.append(self.TestPlanDesignSteps.putEntityCollection(testPlanDesignStepCollection))

                # Reset
                testPlanDesignStepCollection = None

        if testPlanDesignStepCollection:
            req.append(self.TestPlanDesignSteps.putEntityCollection(testPlanDesignStepCollection))

        logger.info('_updateDesignStepsList: Updating steps of tests done!')

        logger.debug('_updateDesignStepsList: return: %s' % req)
        logger.info('_updateDesignStepsList: ...done!')

        return req

    def _deleteDesignStepsList(self, designStepsIds):
        '''
        Delete teststeps related to a set of test instance ids
        :param designStepsIds: Design steps Ids
        :return:
        '''

        req = []

        logger.info('_deleteDesignStepsList: Start...')
        logger.debug('_deleteDesignStepsList: designStepsIds: %s' % designStepsIds)

        # If nothing to do, do nothing!
        if len(designStepsIds) == 0:
            logger.debug('_deleteDesignStepsList: return: %s' % None)
            logger.info('_deleteDesignStepsList: ...done!')

            return None

        # Delete design step
        req.append(self.TestPlanDesignSteps.deleteEntityIdList(designStepsIds))

        logger.debug('_deleteDesignStepsList: return: %s' % req)
        logger.info('_deleteDesignStepsList: ...done!')

        return req

    def _deleteDesignStepsFromTestIdList(self, testIds):
        '''
        Delete All Design Steps from Test id List
        :param testIds: list
        :return:
        '''

        req = []

        logger.info('_deleteDesignStepsFromTestIdList: Start...')
        logger.debug('_deleteDesignStepsFromTestIdList: designStepsIds: %s' % testIds)

        # If nothing to do, do nothing!
        if len(testIds) == 0:
            logger.debug('_deleteDesignStepsFromTestIdList: return: %s' % None)
            logger.info('_deleteDesignStepsFromTestIdList: ...done!')

            return None

        # Get test design steps ids
        idList = self._getIdTestPlanDesignStepFromTestId(testIds)

        # Delete Steps
        req.append(self._deleteDesignStepsList(idList))

        logger.debug('_deleteDesignStepsFromTestIdList: return: %s' % req)
        logger.info('_deleteDesignStepsFromTestIdList: ...done!')

        return req

    def _createDesignStepsList(self, testIds, listDesignStepsTags, testNameList):
        '''
        Update design steps
        :param testIds: Test ids of tests that will have its steps updated
        :param listDesignStepsTags: Design steps tags
        :return:
        '''

        logger.info('_createDesignStepsList: Start...')
        logger.debug('_createDesignStepsList: testIds: %s' % testIds)
        logger.debug('_createDesignStepsList: listDesignStepsTags: %s' % listDesignStepsTags)

        req = []

        # If nothing to do, do nothing...
        if len(testIds) == 0:
            logger.debug('_createDesignStepsList: return: %s' % None)
            logger.info('_createDesignStepsList: ...done!')

            return None

        # Add test design step
        # Get Required Fields
        testDesignStepTemplateXml = self.TestPlanDesignSteps.getEntityDataTemplate()

        # Build design step collection and add design step collection
        logger.info('_createDesignStepsList: Adding steps of tests: %s' % testNameList)

        stepCollection = 500
        testPlanDesignStepCollection = None
        for idx, (testDesignStepsTags, testId) in enumerate(
                itertools.izip(listDesignStepsTags, testIds)):

            # Create copy
            testPlanTestXml = testDesignStepTemplateXml

            # Parent folder ID
            testPlanTestXml = self.TestPlanDesignSteps.addEntityDataFieldValue(
                'parent-id', testId, testPlanTestXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in testDesignStepsTags.iteritems():
                testPlanTestXml = self.TestPlanDesignSteps.addEntityDataFieldValue(
                    field, value, testPlanTestXml)

            # Add to collection
            testPlanDesignStepCollection = self.TestPlanDesignSteps.addEntityDataToCollection(
                testPlanTestXml, testPlanDesignStepCollection)

            if ((idx+1) % stepCollection) == 0:

                req.append(self.TestPlanDesignSteps.postEntityCollection(testPlanDesignStepCollection))

                # Reset
                testPlanDesignStepCollection = None

        if testPlanDesignStepCollection:
            req.append(self.TestPlanDesignSteps.postEntityCollection(testPlanDesignStepCollection))

        logger.info('_createDesignStepsList: Adding steps of tests done!')

        logger.debug('_createDesignStepsList: return: %s' % req)
        logger.info('_createDesignStepsList: ...done!')

        return req

    def _deleteTestSetList(self, testLabTestSetIdList, listTestSetName):
        '''
        Delete TestSets with specific ID
        :param testLabTestSetIdList: test set ids
        :return:
        '''

        logger.info('_deleteTestSetList: Start...')
        logger.debug('_deleteTestSetList: testLabTestSetIdList: %s' % testLabTestSetIdList)

        # If nothing to do, do nothing!
        if len(testLabTestSetIdList) == 0:
            logger.debug('_deleteTestSetList: return: %s' % None)
            logger.info('_deleteTestSetList: ...done!')

            return None

        # Delete testset
        logger.info('_deleteTestSetList: Deleting tests: %s! % listTestSetName')
        r = self.TestLabTestSets.deleteEntityIdList(testLabTestSetIdList)
        logger.info('_deleteTestSetList: Deleting tests done!')

        logger.debug('_deleteTestSetList: return: %s' % r)
        logger.info('_deleteTestSetList: ...done!')

        return r

    def _updateTestSetList(self, listOldTestSetFolderIds, listOldTestSetTags, testLabTestSetIdList, listTestSetName):
        '''
        Create testset based on the testset folder ids and testset tags
        :param listOldTestSetFolderIds:  testset folder ids
        :param listOldTestSetTags: test set field information
        :param testLabTestSetIdList: test set ids
        :return:
        '''

        logger.info('_updateTestSetList: Start...')
        logger.debug('_updateTestSetList: listOldTestSetFolderIds: %s' % listOldTestSetFolderIds)
        logger.debug('_updateTestSetList: listOldTestSetTags: %s' % listOldTestSetTags)
        logger.debug('_updateTestSetList: testLabTestSetIdList: %s' % testLabTestSetIdList)

        # If nothing to do, do nothing!
        if len(listOldTestSetFolderIds) == 0:
            logger.debug('_updateTestSetList: return: %s' % None)
            logger.info('_updateTestSetList: ...done!')

            return None

        # Add testset
        # Get Required Fields
        testLabTestSetTemplateXml = self.TestLabTestSets.getEntityDataTemplate()

        # # Add mandatory - Not required fields
        testLabTestSetTemplateXml = self.TestLabTestSets.addEntityDataFieldValue(
            'subtype-id', 'hp.qc.test-set.default', testLabTestSetTemplateXml)

        # Build testSet collection
        testLabTestSetCollection = None
        for testSetTags, testLabTestSetFolderId, testLabTestSetId in itertools.izip(
                listOldTestSetTags, listOldTestSetFolderIds, testLabTestSetIdList):

            # Create copy
            testLabTestSetXml = testLabTestSetTemplateXml

            # Parent folder Id
            testLabTestSetXml = self.TestLabTestInstances.addEntityDataFieldValue(
                'parent-id', testLabTestSetFolderId, testLabTestSetXml)

            # Id
            testLabTestSetXml = self.TestLabTestInstances.addEntityDataFieldValue(
                'id', testLabTestSetId, testLabTestSetXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in testSetTags.iteritems():
                testLabTestSetXml = self.TestLabTestSets.addEntityDataFieldValue(
                    field, value, testLabTestSetXml)

            # Add to collection
            testLabTestSetCollection = self.TestLabTestSets.addEntityDataToCollection(
                testLabTestSetXml, testLabTestSetCollection)

        # Add testset
        logger.info('_updateTestSetList: Updating testsets: %s!' % listTestSetName)
        r = self.TestLabTestSets.putEntityCollection(testLabTestSetCollection)
        logger.info('_updateTestSetList: Updating testsets done!')

        logger.debug('_updateTestSetList: return: %s' % r)
        logger.info('_updateTestSetList: ...done!')

        return r

    def _createTestSetList(self, listNewTestSetFolderIds, listNewTestSetTags, listNewTestSetPath, listTestSetName):
        '''
        Create testset based on the testset folder ids and testset tags
        :param listNewTestSetFolderIds:  Testset folder ids - None indicates a testset folder not created
        :param listNewTestSetTags: List of test set field information
        :param listNewTestSetPath: List of test set path information
        :return:
        '''

        req = []

        logger.info('_createTestSetList: Start...')
        logger.debug('_createTestSetList: listNewTestSetFolderIds: %s' % listNewTestSetFolderIds)
        logger.debug('_createTestSetList: listNewTestSetTags: %s' % listNewTestSetTags)
        logger.debug('_createTestSetList: listNewTestSetPath: %s' % listNewTestSetPath)

        # If nothing to do, do nothing!
        if len(listNewTestSetFolderIds) == 0:
            logger.debug('_createTestSetList: return: %s' % None)
            logger.info('_createTestSetList: ...done!')

            return None

        # If folders do not exist create them
        testsetFoldersMissing = [elem for index, elem in enumerate(listNewTestSetPath)
                                 if not listNewTestSetFolderIds[index]]

        self._addTestSetFolderList(testsetFoldersMissing)

        # Get Ids from testset folders in test lab
        listNewTestSetFolderIds = self._getIdTestLabTestSetFolderFromPathList(listNewTestSetPath)

        # Add testset
        # Get Required Fields
        testLabTestSetTemplateXml = self.TestLabTestSets.getEntityDataTemplate()

        # Add mandatory - Not required fields
        testLabTestSetTemplateXml = self.TestLabTestSets.addEntityDataFieldValue(
            'subtype-id', 'hp.qc.test-set.default', testLabTestSetTemplateXml)

        # Build testSet collection
        testLabTestSetCollection = None
        for testSetTags, testLabTestSetFolderId in itertools.izip(listNewTestSetTags, listNewTestSetFolderIds):

            # Create copy
            testLabTestSetXml = testLabTestSetTemplateXml

            # Parent folder ID
            testLabTestSetXml = self.TestLabTestInstances.addEntityDataFieldValue(
                'parent-id', testLabTestSetFolderId, testLabTestSetXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in testSetTags.iteritems():
                testLabTestSetXml = self.TestLabTestSets.addEntityDataFieldValue(
                    field, value, testLabTestSetXml)

            # Add to collection
            testLabTestSetCollection = self.TestLabTestSets.addEntityDataToCollection(
                testLabTestSetXml, testLabTestSetCollection)

        # Add testset
        logger.info('_createTestSetList: Creating testsets: %s!' % listTestSetName)
        r = self.TestLabTestSets.postEntityCollection(testLabTestSetCollection)
        logger.info('_createTestSetList: Creating testsets done!')
        req.append(r)

        logger.debug('_createTestSetList: return: %s' % r)
        logger.info('_createTestSetList: ...done!')

        return req

    def _deleteTestInstanceList(self, listTestLabTestInstanceId, testNameList):
        '''
        Delete Tests instances with specific ID
        :param listTestLabTestInstanceId: test instances ids
        :return:
        '''

        logger.info('_deleteTestInstanceList: Start...')
        logger.debug('_deleteTestInstanceList: listTestLabTestInstanceId: %s' % listTestLabTestInstanceId)

        # If nothing to do, do nothing!
        if len(listTestLabTestInstanceId) == 0:
            logger.debug('_deleteTestInstanceList: return: %s' % None)
            logger.info('_deleteTestInstanceList: ...done!')

            return None

        # Delete testset
        logger.info('_deleteTestInstanceList: Delete test instances: %s' % testNameList)
        r = self.TestLabTestInstances.deleteEntityIdList(listTestLabTestInstanceId)
        logger.info('_deleteTestInstanceList: Delete test instances done!')

        logger.debug('_deleteTestInstanceList: return: %s' % r)
        logger.info('_deleteTestInstanceList: ...done!')

        return r

    def _updateTestInstance(self, listTestLabTestsetIds, listTestPlanTestIds,
                            listTagsTestInstance, listTestLabTestInstanceId, testNameList, runUpdate=False):

        logger.info('_updateTestInstance: Start...')
        logger.debug('_updateTestInstance: listTestLabTestsetIds: %s' % listTestLabTestsetIds)
        logger.debug('_updateTestInstance: listTestPlanTestIds: %s' % listTestPlanTestIds)
        logger.debug('_updateTestInstance: listTagsTestInstance: %s' % listTagsTestInstance)
        logger.debug('_updateTestInstance: listTestLabTestInstanceId: %s' % listTestLabTestInstanceId)
        logger.debug('_updateTestInstance: runUpdate: %s' % runUpdate)

        # End if there is nothing ele to do
        if len(listTestLabTestInstanceId) == 0:
            logger.debug('_updateTestInstance: return: %s' % None)
            logger.info('_updateTestInstance: ...done!')

            return None

        # Add test to test lab
        # Get design template
        testPlanTestsTemplateXml = self.TestLabTestInstances.getEntityDataTemplate()

        # Add mandatory (not required tests)
        # # Test Id
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'test-id', '', testPlanTestsTemplateXml)
        # QC parameter - hp.qc.test-instance.MANUAL
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'subtype-id', 'hp.qc.test-instance.MANUAL', testPlanTestsTemplateXml)
        # # TestSet ID
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'cycle-id', '', testPlanTestsTemplateXml)
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'test-order', '1', testPlanTestsTemplateXml)

        # Now create the test instance xml collection to be posted
        testInstanceCollection = None
        for testLabTestInstanceId, tagsTestInstance, testLabTestsetId, testPlanTestId in itertools.izip(
                listTestLabTestInstanceId, listTagsTestInstance, listTestLabTestsetIds, listTestPlanTestIds):
            # Create copy
            testLabTestInstanceXml = testPlanTestsTemplateXml

            # Update necessary fields
            # Test Id
            testLabTestInstanceXml = self.TestLabTestInstances.addEntityDataFieldValue(
                'id', testLabTestInstanceId, testLabTestInstanceXml)
            # Test Id
            testLabTestInstanceXml = self.TestLabTestInstances.addEntityDataFieldValue(
                'test-id', testPlanTestId, testLabTestInstanceXml)
            # TestSet ID
            testLabTestInstanceXml = self.TestPlanTests.addEntityDataFieldValue(
                'cycle-id', testLabTestsetId, testLabTestInstanceXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in tagsTestInstance.iteritems():

                # =======> Status is not updated in the test instance but when a test run is added  <========
                if field == 'status' and runUpdate is False:
                    continue

                testLabTestInstanceXml = self.TestLabTestInstances.addEntityDataFieldValue(
                    field, value, testLabTestInstanceXml)

            testInstanceCollection = self.TestLabTestInstances.addEntityDataToCollection(
                testLabTestInstanceXml, testInstanceCollection)

        # Update test instance in testlab
        logger.info('_updateTestInstance: Update test instances: %s' % testNameList)
        r = self.TestLabTestInstances.putEntityCollection(testInstanceCollection)
        logger.info('_updateTestInstance: Update test instances done!')

        logger.debug('_updateTestInstance: return: %s' % r)
        logger.info('_updateTestInstance: ...done!')

        return r

    def _createTestInstance(self, listTestLabTestsetIds, listTestPlanTestIds, listTagsTestInstance, testNameList):

        logger.info('_createTestInstance: Start...')
        logger.debug('_createTestInstance: listTestLabTestsetIds: %s' % listTestLabTestsetIds)
        logger.debug('_createTestInstance: listTestPlanTestIds: %s' % listTestPlanTestIds)
        logger.debug('_createTestInstance: listTagsTestInstance: %s' % listTagsTestInstance)

        # End if there is nothing ele to do
        if len(listTestLabTestsetIds) == 0 or len(listTestPlanTestIds) == 0:
            logger.debug('_createTestInstance: return: %s' % None)
            logger.info('_createTestInstance: ...done!')

            return None

        # Add test to test lab
        # Get design template
        testPlanTestsTemplateXml = self.TestLabTestInstances.getEntityDataTemplate()

        # Add mandatory (not required tests)
        # Test Id
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'test-id', '', testPlanTestsTemplateXml)
        # QC parameter - hp.qc.test-instance.MANUAL
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'subtype-id', 'hp.qc.test-instance.MANUAL', testPlanTestsTemplateXml)
        # TestSet ID
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'cycle-id', '', testPlanTestsTemplateXml)
        testPlanTestsTemplateXml = self.TestPlanTests.addEntityDataFieldValue(
            'test-order', '1', testPlanTestsTemplateXml)

        # Now create the test instance xml collection to be posted
        testInstanceCollection = None
        for testPlanTestId, testLabTestsetId, tagsTestInstance in itertools.izip(
                listTestPlanTestIds, listTestLabTestsetIds, listTagsTestInstance):
            # Create copy
            testLabTestInstanceXml = testPlanTestsTemplateXml

            # Update necessary fields
            # Test Id
            testLabTestInstanceXml = self.TestLabTestInstances.addEntityDataFieldValue(
                'test-id', testPlanTestId, testLabTestInstanceXml)
            # TestSet ID
            testLabTestInstanceXml = self.TestLabTestInstances.addEntityDataFieldValue(
                'cycle-id', testLabTestsetId, testLabTestInstanceXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in tagsTestInstance.iteritems():

                # =======> Status is not updated in the test instance but when a test run is added  <========
                if field == 'status':
                    continue

                testLabTestInstanceXml = self.TestLabTestInstances.addEntityDataFieldValue(
                    field, value, testLabTestInstanceXml)

            testInstanceCollection = self.TestLabTestInstances.addEntityDataToCollection(
                testLabTestInstanceXml, testInstanceCollection)

        # Create test instance in testlab
        logger.info('_createTestInstance: Create test instances: %s' % testNameList)
        r = self.TestLabTestInstances.postEntityCollection(testInstanceCollection)
        logger.info('_createTestInstance: Create test instances done!')

        logger.debug('_createTestInstance: return: %s' % r)
        logger.info('_createTestInstance: ...done!')

        return r

    def _deleteRunStepsList(self, runId, runStepsIds):
        '''
        Delete teststeps related to a set of test instance ids
        :param runId: Run ID from which the steps are going to be deleted
        :param runIds: run instance Ids
        :return:
        '''

        req = []

        logger.info('_deleteRunStepsList: Start...')
        logger.debug('_deleteRunStepsList: runStepsIds: %s' % runStepsIds)

        # If nothing to do, do nothing!
        if len(runStepsIds) == 0:
            logger.debug('_deleteRunStepsList: return: %s' % None)
            logger.info('_deleteRunStepsList: ...done!')

            return None

        # Delete testset
        for runStepId in runStepsIds:
            req.append(self.TestLabRunStep.deleteEntityIdList(runId, runStepId))

        logger.debug('_deleteRunStepsList: return: %s' % req)
        logger.info('_deleteRunStepsList: ...done!')

        return req

    def _updateRunStepsList(self, runIds, listRunStepsTags, testNamesList):
        '''
        Update teststeps related to a set of test instance ids
        :param runIds: run instance Ids
        :param listRunStepsTags: List run steps tags
        :return:
        '''

        logger.info('_updateRunStepsList: Start...')
        logger.debug('_updateRunStepsList: runIds: %s' % runIds)
        logger.debug('_updateRunStepsList: listRunStepsTags: %s' % listRunStepsTags)

        # Add test run step
        # Get Required Fields
        testLabRunStepTemplateXml = self.TestLabRunStep.getEntityDataTemplate()

        # Update one by one
        req = []
        for runId, runStepsTags, testName in itertools.izip(runIds, listRunStepsTags, testNamesList):

            logger.info('_updateRunStepsList: Add steps to test run of test: %s' % testName)

            # Get the runSteps IDs that will be updated
            r = self.TestLabRunStep.getEntity(runId)
            xml = self._getXmlFromRequestQuery(r)

            req.append(r)

            # Order the steps by the name
            for runST in runStepsTags:

                # Step name field
                stepName = ''

                # Create copy
                testLabRunStepXml = testLabRunStepTemplateXml

                # Update necessary fields
                # Test Instance Run Id
                testLabRunStepXml = self.TestLabRunStep.addEntityDataFieldValue(
                    'parent-id', runId, testLabRunStepXml)

                # Update remaining fields by iterating through the dictionary entries
                for field, value in runST.iteritems():
                    testLabRunStepXml = self.TestLabRunStep.addEntityDataFieldValue(
                        field, value, testLabRunStepXml)

                    if field == 'name':
                        stepName = value

                # Get Test Instance Run Step Id by Step Name field (Mandatory)
                try:
                    runStepId = self.TestLabRunStep.getEntityDataCollectionFieldValueIf(
                    'id', 'name', stepName, xml)[0]
                except:
                    self._raiseError('_updateRunStepsList', 'The test \'%s\' does not contain step \'%s\'' %
                                     (testName, stepName))

                testLabRunStepXml = self.TestLabRunStep.addEntityDataFieldValue(
                    'id', runStepId, testLabRunStepXml)

                # Post single entity
                r = self.TestLabRunStep.putEntityByID(runId, runStepId, testLabRunStepXml)

                # Save responses to return them
                req.append(r)

        logger.debug('_updateRunStepsList: return: %s' % req)
        logger.info('_updateRunStepsList: ...done!')

        return req

    def _createRunStepsList(self, runIds, listRunStepsTags, testNameList):
        '''
        Create teststeps related to a set of test instance ids
        :param runIds: run instance Ids
        :param listRunStepsTags: List run steps tags
        :return:
        '''

        logger.info('_createRunStepsList: Start...')
        logger.debug('_createRunStepsList: runIds: %s' % runIds)
        logger.debug('_createRunStepsList: listRunStepsTags: %s' % listRunStepsTags)

        # Add test run step
        # Get Required Fields
        testLabRunStepTemplateXml = self.TestLabRunStep.getEntityDataTemplate()

        # Create all steps fro each run Id
        req = []
        for runId, runStepsTags, testName in itertools.izip(runIds, listRunStepsTags, testNameList):

            logger.info('_updateRunStepsList: Add steps to test run of test: %s' % testName)
            # Get the runSteps IDs that will be updated
            r = self.TestLabRunStep.getEntity(runId)
            xml = self._getXmlFromRequestQuery(r)

            # Build collection
            testLabRunStepXmlCollection = None

            # Order the steps by the
            for runST in runStepsTags:

                # Create copy
                testLabRunStepXml = testLabRunStepTemplateXml

                # Update necessary fields
                # Test Instance Run Id
                testLabRunStepXml = self.TestLabRunStep.addEntityDataFieldValue(
                    'parent-id', runId, testLabRunStepXml)

                # Update remaining fields by iterating through the dictionary entries
                for field, value in runST.iteritems():
                    testLabRunStepXml = self.TestLabRunStep.addEntityDataFieldValue(
                        field, value, testLabRunStepXml)

                # Add to collection
                testLabRunStepXmlCollection = self.TestLabRunStep.addEntityDataToCollection(
                    testLabRunStepXml, testLabRunStepXmlCollection)

            logger.debug('_createRunStepsList: testLabRunStepXmlCollection: %s' % testLabRunStepXmlCollection)

            # Post collection
            r = self.TestLabRunStep.postEntityCollection(runId, testLabRunStepXmlCollection)

            # Save responses to return them
            req.append(r)

            logger.info('_updateRunStepsList: Add steps to test run done!')

        logger.debug('_createRunStepsList: return: %s' % req)
        logger.info('_createRunStepsList: ...done!')

        return req

    def _deleteRequirementList(self, requirementIds, requirementNames):
        '''
        Delete requirements based on their id
        :param requirementIds:  Requirements ids
        :param requirementNames: Requirements Name
        :return:
        '''

        logger.info('_deleteRequirementList: Start...')
        logger.debug('_deleteRequirementList: requirementIds: %s' % requirementIds)

        # If nothing to do, do nothing!
        if len(requirementIds) == 0:
            logger.debug('_deleteRequirementList: return: %s' % None)
            logger.info('_deleteRequirementList: ...done!')

            return None

        # Add test
        logger.info('_deleteRequirementList: Deleting Requirement list: %s!' % requirementNames)
        r = self.Requirements.deleteEntityIdList(requirementIds)
        logger.info('_deleteRequirementList: Deleting Requirement list!')

        logger.debug('_deleteRequirementList: return: %s' % r)
        logger.info('_deleteRequirementList: ...done!')

        return r

    def _createRequirementList(self, reqFolderIdList, reqTagsList, reqPathList, reqNameList):
        '''
        Create req based on the req folder id and req tags
        :param reqFolderList:  Req folder ids - None indicates a test folder not created
        :param reqNameList:  Req Names
        :param reqTagsList:  Req tags
        :param reqPathList: List of req path information
        :return:
        '''

        logger.info('_createRequirementList: Start...')
        logger.debug('_createRequirementList: reqFolderIdList: %s' % reqFolderIdList)
        logger.debug('_createRequirementList: reqTagsList: %s' % reqTagsList)
        logger.debug('_createRequirementList: reqPathList: %s' % reqPathList)
        logger.debug('_createRequirementList: reqNameList: %s' % reqNameList)

        # If nothing to do, do nothing!
        if len(reqFolderIdList) == 0:
            logger.debug('_createTestList: return: %s' % None)
            logger.info('_createTestList: ...done!')

            return None

        # If folders do not exist create them
        reqFoldersMissing = [elem for index, elem in enumerate(reqPathList)
                              if not reqFolderIdList[index]]

        self._addRequirementFolderList(reqFoldersMissing)

        # Get Ids from test folders in test lab
        reqFolderIdList = self._getIdRequirementFolderFromPathList(reqPathList)

        # Add requirement
        # Get Required Fields
        requirementTemplateXml = self.Requirements.getEntityDataTemplate()

        # Build test collection
        requirementCollection = None

        for reqTag, reqParentId, nameReq in itertools.izip(reqTagsList, reqFolderIdList, reqNameList):

            # Create copy
            requirementXml = str(requirementTemplateXml)

            # Parent folder ID
            requirementXml = self.Requirements.addEntityDataFieldValue(
                'parent-id', reqParentId, requirementXml)

            # Name
            requirementXml = self.Requirements.addEntityDataFieldValue(
                'name', nameReq, requirementXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in reqTag.iteritems():

                requirementXml = self.Requirements.addEntityDataFieldValue(
                    field, value, requirementXml)

            # Add to collection
            requirementCollection = self.Requirements.addEntityDataToCollection(
                requirementXml, requirementCollection)

        # Add test
        logger.info('_createRequirementList: Creating Requirement list: %s!' % reqNameList)
        r = self.Requirements.postEntityCollection(requirementCollection)
        logger.info('_createRequirementList: Creating test list done!')

        logger.debug('_createRequirementList: return: %s' % r)
        logger.info('_createRequirementList: ...done!')

        return r

    def _updateRequirementList(self, reqFolderIdList, reqTagsList, reqIdList, reqNameList):

        '''
        Create req based on the test folder ids and test tags
        :param reqTagsList:  Test folder ids - None indicates a test folder not created
        :param reqTagsList: List of requirement tags
        :return:
        '''

        logger.info('_updateRequirementList: Start...')
        logger.debug('_updateRequirementList: reqIdList: %s' % reqIdList)
        logger.debug('_updateRequirementList: reqTagsList: %s' % reqTagsList)

        # If nothing to do, do nothing!
        if len(reqIdList) == 0:
            logger.debug('_updateRequirementList: return: %s' % None)
            logger.info('_updateRequirementList: ...done!')

            return None

        # Add requirement
        # Get Required Fields
        requirementTemplateXml = self.Requirements.getEntityDataTemplate()

        # Build test collection
        requirementCollection = None

        for reqTag, reqId, reqName, reqFolderId in itertools.izip(reqTagsList, reqIdList, reqNameList, reqFolderIdList):

            # Create copy
            requirementXml = str(requirementTemplateXml)

            # Req parent-id
            requirementXml = self.Requirements.addEntityDataFieldValue(
                'parent-id', reqFolderId, requirementXml)

            # Req ID
            requirementXml = self.Requirements.addEntityDataFieldValue(
                'id', reqId, requirementXml)

            # Req name
            requirementXml = self.Requirements.addEntityDataFieldValue(
                'name', reqName, requirementXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in reqTag.iteritems():

                requirementXml = self.Requirements.addEntityDataFieldValue(
                    field, value, requirementXml)

            # Add to collection
            requirementCollection = self.Requirements.addEntityDataToCollection(
                requirementXml, requirementCollection)

        # Add test
        logger.info('_updateRequirementList: Updating Requirement list: %s!' % reqNameList)
        r = self.Requirements.putEntityCollection(requirementCollection)
        logger.info('_updateRequirementList: Updating Requirement list done!')

        logger.debug('_updateRequirementList: return: %s' % r)
        logger.info('_updateRequirementList: ...done!')

        return r

    def _addRequirementAttachList(self, reqIdList, reqNameList, attachDataList, attachFileNameList, attachDescList,
                                  attachOverwriteList, attachRichTextList):
        '''
        Add attachment requirement
        :param reqIdList: Requirement IDs
        :param reqNameList: Requirements Name List
        :param attachDataList: Attach Data
        :param attachFileNameList: Attachment file name
        :param attachDescList: attachDescription
        :param attachOverwriteList: Attach overwrite option
        :param attachRichTextList: attachment Rich Text option
        :return:
        '''

        logger.info('_addRequirementAttachList: Start...')
        logger.debug('_addRequirementAttachList: reqIdList: %s' % reqIdList)
        logger.debug('_addRequirementAttachList: reqNameList: %s' % reqNameList)
        logger.debug('_addRequirementAttachList: attachFileNameList: %s' % attachFileNameList)
        logger.debug('_addRequirementAttachList: attachDescList: %s' % attachDescList)
        logger.debug('_addRequirementAttachList: attachOverwriteList: %s' % attachOverwriteList)
        logger.debug('_addRequirementAttachList: attachRichTextList: %s' % attachRichTextList)

        if len(reqIdList) == 0:
            logger.debug('_addRequirementAttachList: return: %s' % None)
            logger.info('_addRequirementAttachList: ...done!')

            return None

        for reqId, reqName, attachData, attachFileName, attachDesc, attachOverwrite, attachRichText in itertools.izip(
                reqIdList, reqNameList, attachDataList, attachFileNameList, attachDescList, attachOverwriteList,
                attachRichTextList):

             self.Requirements.postEntityAttachmentByID(reqId, attachFileName, attachDesc, attachData, attachOverwrite,
                                                        attachRichText)

    def _deleteDefectList(self, defectIds, defectsNames):
        '''
        Delete defects based on their id
        :param defectIds:  Defects ids
        :param defectIds:  Defects ids
        :param defectsNames: Defects Name
        :return:
        '''
        # ToDo Not tested, need to be review

        logger.info('_deleteDefectList: Start...')
        logger.debug('_deleteDefectList: defectIds: %s' % defectIds)

        # If nothing to do, do nothing!
        if len(defectIds) == 0:
            logger.debug('_deleteDefectList: return: %s' % None)
            logger.info('_deleteDefectList: ...done!')

            return None

        # Add test
        logger.info('_deleteDefectList: Deleting Defects list: %s!' % defectsNames)
        r = self.Defects.deleteEntityIdList(defectIds)
        logger.info('_deleteDefectList: Deleting Defects list!')

        logger.debug('_deleteDefectList: return: %s' % r)
        logger.info('_deleteDefectList: ...done!')

        return r

    def _createDefectList(self, defTagsList, defNameList):
        '''
        Create req based on the req folder id and req tags
        :param defNameList:  Def Names
        :param defTagsList:  Def tags
        :return:
        '''

        logger.info('_createDefectList: Start...')
        logger.debug('_createDefectList: defTagsList: %s' % defTagsList)
        logger.debug('_createDefectList: defNameList: %s' % defNameList)

        # If nothing to do, do nothing!
        if len(defNameList) == 0:
            logger.debug('_createDefectList: return: %s' % None)
            logger.info('_createDefectList: ...done!')

            return None

        # Add defects
        # Get Required Fields
        defTemplateXml = self.Defects.getEntityDataTemplate()

        # Build test collection
        defCollection = None

        for reqTag, nameReq in itertools.izip(defTagsList, defNameList):

            # Create copy
            defXml = str(defTemplateXml)

            # Name
            defXml = self.Defects.addEntityDataFieldValue(
                'name', nameReq, defXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in reqTag.iteritems():

                defXml = self.Defects.addEntityDataFieldValue(
                    field, value, defXml)

            # Add to collection
            defCollection = self.Requirements.addEntityDataToCollection(
                defXml, defCollection)

        # Add Defect
        logger.info('_createDefectList: Creating defect list: %s!' % defNameList)
        r = self.Defects.postEntityCollection(defCollection)
        logger.info('_createDefectList: Creating defect list done!')

        logger.debug('_createDefectList: return: %s' % r)
        logger.info('_createDefectList: ...done!')

        return r

    def _updateDefectList(self, defTagsList, defIdList, defNameList):

        '''
        Create def based on the def ids and def tags
        :param defIdList: List of def ids that already exist
        :param defNameList:  Def Names
        :param defTagsList:  Def tags
        :return:
        '''

        logger.info('_updateDefectList: Start...')
        logger.debug('_updateDefectList: defIdList: %s' % defIdList)
        logger.debug('_updateDefectList: defTagsList: %s' % defTagsList)

        # If nothing to do, do nothing!
        if len(defIdList) == 0:
            logger.debug('_updateDefectList: return: %s' % None)
            logger.info('_updateDefectList: ...done!')

            return None

        # Add Defect
        # Get Required Fields
        defTemplateXml = self.Defects.getEntityDataTemplate()

        # Build test collection
        defCollection = None

        for reqTag, reqId, reqName in itertools.izip(defTagsList, defIdList, defNameList):

            # Create copy
            defXml = str(defTemplateXml)

            # Req ID
            defXml = self.Defects.addEntityDataFieldValue(
                'id', reqId, defXml)

            # Req name
            defXml = self.Defects.addEntityDataFieldValue(
                'name', reqName, defXml)

            # Update remaining fields by iterating through the dictionary entries
            for field, value in reqTag.iteritems():

                defXml = self.Defects.addEntityDataFieldValue(
                    field, value, defXml)

            # Add to collection
            defCollection = self.Defects.addEntityDataToCollection(
                defXml, defCollection)

        # Add test
        logger.info('_updateDefectList: Updating Defects list: %s!' % defNameList)
        r = self.Defects.putEntityCollection(defCollection)
        logger.info('_updateDefectList: Updating Defects list done!')

        logger.debug('_updateDefectList: return: %s' % r)
        logger.info('_updateDefectList: ...done!')

        return r

    def _addTestFolderList(self, pathList, ignoreFolderIfExists=True):
        '''
        Add a folder to the test plan. Intermediate folder will be created.
        :param pathList: Path that will be created
        :param ignoreFolderIfExists: Ignores Folder if it exists, else fail and exit
        :return:
        '''
        self._addFolderList(pathList, 'Plan', ignoreFolderIfExists)

    def _addTestSetFolderList(self, pathList, ignoreFolderIfExists=True):
        '''
        Add a folder to the test lab. Intermediate folder will be created.
        :param pathList: Path that will be created
        :param ignoreFolderIfExists: Ignores Folder if it exists, else fail and exit
        :return:
        '''
        self._addFolderList(pathList, 'Lab', ignoreFolderIfExists)

    def _addRequirementFolderList(self, pathList, ignoreFolderIfExists=True):
        '''
        Add a folder to the requirement list. Intermediate folder will be created.
        :param pathList: Path that will be created
        :param ignoreFolderIfExists: Ignores Folder if it exists, else fail and exit
        :return:
        '''
        self._addFolderList(pathList, 'Requirement', ignoreFolderIfExists)

    def _addFolderList(self, pathList, location='Lab', ignoreFolderIfExists=True):
        '''
        Add a test lab folder with the given path
        :param pathList: Path that will be created
        :param ignoreFolderIfExists: Ignores Folder if it exists, else fail and exit
        :param location: Decides if we are working in the test 'Lab' or test 'Plan'
        :param ignoreFolderIfExists: Ignores Folder if it exists, else fail and exit
        :return: None if list is empty
        '''

        # If list is empty return None
        if len(pathList) == 0:
            return None

        # First check which exist or not
        folderIds = self._getIdFromPathList(pathList, location)

        for folderId, path in itertools.izip(folderIds, pathList):

            # If path does not exist
            if folderId is None:
                # Create path
                r = self._addFolder(path, location, ignoreFolderIfExists)

        if folderIds.count(None) == 0 and ignoreFolderIfExists is False:
            self._raiseError('_addFolderList', 'Folder exists! ignoreFolderIfExists=True')

    def _addFolder(self, path, location='Lab', ignoreFolderIfExists=True):
        '''
        Allows the creation of folders in the test Lab or Plan
        :param path: path that will be created
        :param location: Decides if we are working in the test 'Lab' or test 'Plan'
        :param ignoreFolderIfExists: Ignores Folder if it exists, else fail and exit
        :return:
        '''

        logger.debug('_addFolder: Start...')
        logger.debug('_addFolder: path: %s' % path)
        logger.debug('_addFolder: location: %s' % location)
        logger.debug('_addFolder: ignoreFolderIfExists: %s' % ignoreFolderIfExists)

        # First check to which level the folder tree is created
        # This is done by looking for the several levels of folders e.g. Sandbox/test_1/lab_1 the search will be:
        # ['Sandbox/test_1/lab_1', 'Sandbox/test_1', 'Sandbox']
        folderList = path.split('\\')
        pathList = []
        lastFolder = ''
        for folder in folderList:
            pathList.append(lastFolder + folder)
            lastFolder += folder + '\\'

        folderIds = self._getIdFromPathList(pathList, location)

        # Now create the folders
        parentFolderId = '0'
        for folderId, folder in itertools.izip(folderIds, folderList):

            # Check for folder in path that do not exist and create them
            if folderId is None:

                # Create folder
                if location == 'Lab':
                    folderXml = self.TestLabTestSetFolders.getEntityDataTemplate()

                    folderXml = self.TestLabTestSetFolders.addEntityDataFieldValue(
                        'name', folder, folderXml)
                    folderXml = self.TestLabTestSetFolders.addEntityDataFieldValue(
                        'parent-id', parentFolderId, folderXml)

                    r = self.TestLabTestSetFolders.postEntity(folderXml)

                    # Get Id of created folder
                    parentFolderId = self.TestLabTestSetFolders.getEntityDataFieldValue('id', r.content)[0]

                elif location == 'Plan':
                    folderXml = self.TestPlanTestFolders.getEntityDataTemplate()

                    folderXml = self.TestPlanTestFolders.addEntityDataFieldValue(
                        'name', folder, folderXml)
                    folderXml = self.TestPlanTestFolders.addEntityDataFieldValue(
                        'parent-id', parentFolderId, folderXml)

                    r = self.TestPlanTestFolders.postEntity(folderXml)

                    # Get Id of created folder
                    parentFolderId = self.TestPlanTestFolders.getEntityDataFieldValue('id', r.content)[0]

                elif location == 'Requirement':
                    folderXml = self.Requirements.getEntityDataTemplate()

                    folderXml = self.Requirements.addEntityDataFieldValue(
                        'name', folder, folderXml)
                    folderXml = self.Requirements.addEntityDataFieldValue(
                        'parent-id', parentFolderId, folderXml)
                    folderXml = self.Requirements.addEntityDataFieldValue(
                        'type-id', '1', folderXml)

                    r = self.Requirements.postEntity(folderXml)

                    # Get Id of created folder
                    parentFolderId = self.TestPlanTestFolders.getEntityDataFieldValue('id', r.content)[0]

            else:
                parentFolderId = folderId

        if folderIds.count(None) == 0 and ignoreFolderIfExists is False:
            self._raiseError('_addFolder', 'Folder exists! ignoreFolderIfExists=True')

        logger.debug('_addFolder: ...done!')

    def _getIdTestPlanDesignStepFromTestIdStepName(self, testIdList, designStepNameList):
        '''
        Get Test Plan Design Steps Ids based on its path and name
        :param testIdList:  List with test Ids
        :param designStepNameList: List with design step names
        :return: List of corresponding design steps ids
        '''

        logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: Start...')
        logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: fieldList: %s' % testIdList)
        logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: valueListList: %s' % designStepNameList)

        # Removed elements that we already know they do not exist
        designStepNameListFiltered = [elem for index, elem in enumerate(designStepNameList) if testIdList[index]]
        testIdListFiltered = [elem for index, elem in enumerate(testIdList) if elem]

        if len(designStepNameListFiltered) == 0 or len(testIdListFiltered) == 0:
            logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: return: %s' % None)
            logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: ...done!')
            return [None] * len(designStepNameList)

        # Build Query
        query = self._getQueryListOrAnd(['parent-id', 'name'], [testIdListFiltered, designStepNameListFiltered])

        r = self.TestPlanDesignSteps.getEntityQueryList(query, 'parent-id,name,id')

        xml = self._getXmlFromRequestQueryList(r)

        lists = self.TestPlanDesignSteps.getEntityDataCollectionFieldValueListIf(
            ['parent-id', 'id'], 'name', designStepNameList, xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        designStepIds = []
        for parentIdList, idList, testId in itertools.izip(lists['parent-id'], lists['id'], testIdList):

            # Match?
            match = False
            for idx, parentId in enumerate(parentIdList):

                if parentId == testId:
                    # Add them it to the list
                    designStepIds.append(idList[idx])
                    match = True
                    break

            if not match:
                designStepIds.append(None)

        logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: return: %s' % designStepIds)
        logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: ...done!')

        return designStepIds

    def _getIdTestPlanDesignStepFromTestId(self, testIdList):
        '''
        Get Test Plan Design Steps Ids based on its path and name
        :param testIdList:  List with test Ids
        :return: List of corresponding design steps ids
        '''

        logger.debug('_getIdTestPlanDesignStepFromTestId: Start...')
        logger.debug('_getIdTestPlanDesignStepFromTestId: fieldList: %s' % testIdList)

        # Removed elements that we already know they do not exist
        testIdListFiltered = [elem for index, elem in enumerate(testIdList) if elem]

        if len(testIdListFiltered) == 0:
            logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: return: %s' % None)
            logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: ...done!')
            return None

        # Build Query
        query = self._getQueryListOrAnd(['parent-id'], [testIdListFiltered])

        r = self.TestPlanDesignSteps.getEntityQueryList(query, 'parent-id,name,id')

        xml = self._getXmlFromRequestQueryList(r)

        designStepIds = self.TestPlanDesignSteps.getEntityDataCollectionFieldValue(
            'id', xml)

        logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: return: %s' % designStepIds)
        logger.debug('_getIdTestPlanDesignStepFromTestIdStepName: ...done!')

        return designStepIds

    def _getIdTestPlanTestFromPathList(self, testPathList):
        '''
        Get parent-id from a test in test plan - path + name e.g. 'Subject\Sandbox\testsetA'
        :param testPathList: Test path list
        :return: List of ids from test path
        '''

        logger.debug('_getIdTestPlanTestFromPathList: Start...')
        logger.debug('_getIdTestPlanTestFromPathList: fieldList: %s' % testPathList)

        # First grab list of paths and get all parent IDs
        pathList = []
        testList = []
        for testPath in testPathList:
            # Get test
            test = testPath.split('\\')[-1]

            # Get path
            path = testPath[:-(len(test) + 1)]

            # Add path and test to respective lists
            pathList.append(path)
            testList.append(test)

        # For this list of paths get all the possible parent IDs by order
        pathListIds = self._getIdFromPathList(pathList, 'Plan')

        # Fail if there are tests ( id = None) that do not exist
        if None in pathListIds:
            # List of tests that do not exist
            testsMissing = set([testPathList[idx] for idx, id in enumerate(pathListIds) if id is None])

            # Raise exception
            self._raiseError('_getIdTestPlanTestFromPathList',
                             'There are some tests that do not exist: %s' % testsMissing)

        # Query - Since we cannot use OR between fields we cannot use a single query for parent-id and name so the
        # idea is to get all the entities that match the condition parentId[testFolder1 OR testFolderX]; name[ .. OR ..]
        # This query, however, can return not valid entities so it is important to be validated
        query = self._getQueryListOrAnd(['name', 'parent-id'], [testList, pathListIds])

        r = self.TestPlanTests.getEntityQueryList(query, 'parent-id,name,id')
        xml = self._getXmlFromRequestQueryList(r)

        lists = self.TestPlanTests.getEntityDataCollectionFieldValueListIf(
            ['parent-id', 'id'], 'name', testList, xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        testIds = []
        for parentIdList, idList, testId in itertools.izip(lists['parent-id'], lists['id'], pathListIds):

            # Match?
            match = False
            for idx, parentId in enumerate(parentIdList):

                if parentId == testId:
                    # Add them it to the list
                    testIds.append(idList[idx])
                    match = True
                    break

            if not match:
                testIds.append(None)

        logger.debug('_getIdTestPlanTestFromPathList: return: %s' % testIds)
        logger.debug('_getIdTestPlanTestFromPathList: ...done!')

        return testIds

    def _getIdTestPlanTestFromTestInstanceIdList(self, ids):
        '''
        Get list id for all test instances in a specific folder identified by ID
        A list of Ids can also be provided as a argument
        :param ids: List of test instance ids
        :return: Test plan test ids
        '''

        # Build query for list of id - a testset is identified in the testinstance
        query = self._getQueryListOrAnd(['id'], [ids])

        # Get all folder that contain as parent id the given ids
        r = self.TestLabTestInstances.getEntityQueryList(query, 'id,test-id')
        xml = self._getXmlFromRequestQueryList(r)
        tiTestIdList = self.TestLabTestInstances.getEntityDataCollectionFieldValue('test-id', xml)
        tiIdList = self.TestLabTestInstances.getEntityDataCollectionFieldValue('id', xml)

        idListOrd = []

        # Order list
        for testInstanceId in ids:

            for idx, tiId in enumerate(tiIdList):

                if tiId == testInstanceId:
                    idListOrd.append(tiTestIdList[idx])

        return idListOrd

    def _getIdTestPlanTestFromFolderIdList(self, folderIdList):
        '''
        Get Test Plan Test Ids based on its path
        :param folderIdList:  List with folder Ids
        :return: List of test ids
        '''

        # Removed elements that we already know they do not exist
        folderIdListFiltered = [elem for index, elem in enumerate(folderIdList) if elem]

        if len(folderIdListFiltered) == 0:
            return [None] * len(folderIdList)

        # Build Query
        query = self._getQueryListOrAnd(['parent-id'], [folderIdListFiltered])

        r = self.TestPlanTests.getEntityQueryList(query, 'parent-id,id')
        xml = self._getXmlFromRequestQueryList(r)

        testIds = []

        xmlList = self.TestPlanTests.getEntityDataCollectionFieldValueList(['parent-id','id'], xml)

        parentIdListXml = xmlList[0]
        idListXml = xmlList[1]

        for folderId in folderIdList:

            for parentIdXml, idXml in itertools.izip(parentIdListXml, idListXml):

                if parentIdXml ==folderId:

                    testIds.append(idXml)

        return testIds

    def _getIdTestPlanTestFromFolderIdTestName(self, folderIdList, testNameList):
        '''
        Get Test Plan Test Ids based on its path and name
        :param folderIdList:  List with folder Ids
        :param testNameList: List with test names
        :return: List of corresponding test ids
        '''

        # Removed elements that we already know they do not exist
        testNameListFiltered = [elem for index, elem in enumerate(testNameList) if folderIdList[index]]
        folderIdListFiltered = [elem for index, elem in enumerate(folderIdList) if elem]

        if len(testNameListFiltered) == 0 or len(folderIdListFiltered) == 0:
            return [None] * len(testNameList)

        # Build Query
        query = self._getQueryListOrAnd(['parent-id', 'name'], [folderIdListFiltered, testNameListFiltered])

        r = self.TestPlanTests.getEntityQueryList(query, 'parent-id,name,id')
        xml = self._getXmlFromRequestQueryList(r)

        lists = self.TestPlanTests.getEntityDataCollectionFieldValueListIf(
            ['parent-id', 'id'], 'name', testNameList, xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        testIds = []
        for parentIdList, idList, testId in itertools.izip(lists['parent-id'], lists['id'], folderIdList):

            # Match?
            match = False
            for idx, parentId in enumerate(parentIdList):

                if parentId == testId:
                    # Add them it to the list
                    testIds.append(idList[idx])
                    match = True
                    break

            if not match:
                testIds.append(None)

        return testIds

    def _getIdRequirementFromReqFolderIdReqName(self, folderIdList, reqNameList):
        '''
        Get Test Plan Test Ids based on its path and name
        :param folderIdList:  List with folder Ids
        :param reqNameList: List with test names
        :return: List of corresponding test ids
        '''

        # Removed elements that we already know they do not exist
        reqNameListFiltered = [elem for index, elem in enumerate(reqNameList) if folderIdList[index]]
        folderIdListFiltered = [elem for index, elem in enumerate(folderIdList) if elem]

        if len(reqNameListFiltered) == 0 or len(folderIdListFiltered) == 0:
            return [None] * len(reqNameList)

        # Build Query
        query = self._getQueryListOrAnd(['parent-id', 'name'], [folderIdListFiltered, reqNameListFiltered])

        r = self.TestPlanTests.getEntityQueryList(query, 'parent-id,name,id')
        xml = self._getXmlFromRequestQueryList(r)

        lists = self.TestPlanTests.getEntityDataCollectionFieldValueListIf(
            ['parent-id', 'id'], 'name', reqNameList, xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        reqIds = []
        for parentIdList, idList, testId in itertools.izip(lists['parent-id'], lists['id'], folderIdList):

            # Match?
            match = False
            for idx, parentId in enumerate(parentIdList):

                if parentId == testId:
                    # Add them it to the list
                    reqIds.append(idList[idx])
                    match = True
                    break

            if not match:
                reqIds.append(None)

        return reqIds

    def _getIdTestPlanFolderFromPathList(self, pathList):
        '''
        Get id from a path e.g. 'Subject\Sandbox'
        :param pathList: Folder path list
        :return: List with IDs
        '''

        return self._getIdFromPathList(pathList, 'Plan')

    def _getIdRequirementFolderFromPathList(self, pathList):
        '''
        Get id from a path e.g. 'Subject\Sandbox'
        :param pathList: Folder path list
        :return: List with IDs
        '''

        # Requirements are one of the entities that can be created right after the root folder and so in this particular
        # case, if the pathlist is empty "", it means the parent is '0'

        idList = self._getIdFromPathList(pathList, 'Requirement')

        for idx, path in enumerate(pathList):

            if path == '':
                idList[idx] = '0'

        return idList

    def _getIdTestPlanSubFoldersFromPathList(self, pathList):
        '''
        Get list id for all sub folders in a path including the root path e.g. 'Subject\Sandbox'
        :param pathList: List of Test Lab Folders
        :return: List of Test Lab Folders inside the path list
        '''

        # Path List IDs
        pathListIDs = []

        for path in pathList:
            # Folder Id list
            idList = []

            # Get parent ID from path
            idRootPath = self._getIdTestPlanFolderFromPathList([path])[0]

            # Get sub folder which have this parent id recursively
            idList += self._getIdTestPlanSubFoldersFromFolderId(idRootPath)

            # Include the root path
            idList.append(idRootPath)

            pathListIDs.append(idList)

        return pathListIDs

    def _getIdTestPlanSubFoldersFromFolderId(self, ids):
        '''
        Get list id for all folders in a specific path ID e.g. 'Subject\Sandbox'.
        A list of Ids can also be provided as a argument
        :param ids: Folder IDs
        :return: Testset IDs
        '''

        # Convert Id to list if it is a scalar
        if type(ids) != list:
            ids = [ids]

        # Build query for list of id
        query = self._getQueryListOrAnd(['parent-id'], [ids])

        # Get all folder that contain as parent id the given ids
        r = self.TestPlanTestFolders.getEntityQueryList(query, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        idList = self.TestPlanTestFolders.getEntityDataCollectionFieldValue('id', xml)

        # Check again subfolders and add them to the list
        if len(idList) > 0:
            idList += self._getIdTestPlanSubFoldersFromFolderId(idList)

        return idList

    def _getIdTestLabTestSetFromPathList(self, testSetPathList):
        '''
        Get id from a test set e.g. 'Subject\Sandbox\testsetA'
        :param testSetPathList: List of paths of testsets
        :return: Ordered list with the IDs of the testset folders
        '''

        logger.debug('_getIdTestLabTestSetFromPathList: Start...')
        logger.debug('_getIdTestLabTestSetFromPathList: testSetPathList: %s' % testSetPathList)

        # First grab list of paths and get all parent IDs
        pathList = []
        testSetList = []
        for testSetPath in testSetPathList:
            # Get test
            testSet = testSetPath.split('\\')[-1]

            # Get path
            path = testSetPath[:-(len(testSet) + 1)]

            # Add path and test to respective lists
            pathList.append(path)
            testSetList.append(testSet)

        # For this list of paths get all the possible parent IDs by order
        pathListIds = self._getIdFromPathList(pathList, 'Lab')

        logger.debug('_getIdTestLabTestSetFromPathList: pathListIds: %s' % pathListIds)

        # Fail if there are tests ( id = None) that do not exist
        if None in pathListIds:
            # List of tests that do not exist
            testsMissing = set([testSetPathList[idx] for idx, id in enumerate(pathListIds) if id is None])

            # Raise exception
            self._raiseError('_getIdTestLabTestSetFromPathList',
                             'There are some test sets that do not exist: %s' % testsMissing)

        # Query - Since we cannot use OR between fields we cannot use a single query for parent-id and name so the
        # idea is to get all the entities that match the condition parentId[testFolder1 OR testFolderX]; name[ .. OR ..]
        # This query, however, can return not valid entities so it is important to be validated
        query = self._getQueryListOrAnd(['name', 'parent-id'], [testSetList, pathListIds])

        r = self.TestLabTestSets.getEntityQueryList(query, 'parent-id,name,id')
        xml = self._getXmlFromRequestQueryList(r)

        logger.debug('_getIdTestLabTestSetFromPathList: xml: %s' % xml)

        lists = self.TestLabTestSets.getEntityDataCollectionFieldValueListIf(
            ['parent-id', 'id'], 'name', testSetList, xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        testSetIds = []
        for parentIdList, idList, testId in itertools.izip(lists['parent-id'], lists['id'], pathListIds):

            # Match?
            match = False
            for idx, parentId in enumerate(parentIdList):

                if parentId == testId:
                    # Add them it to the list
                    testSetIds.append(idList[idx])
                    match = True
                    break

            if not match:
                testSetIds.append(None)

        logger.debug('_getIdTestLabTestSetFromPathList: return: %s' % testSetIds)
        logger.debug('_getIdTestLabTestSetFromPathList: ...done!')

        return testSetIds

    def _getIdTestLabTestSetFromFolderId(self, ids):
        '''
        Get list id for all testsets in a specific folder identified by ID
        A list of Ids can also be provided as a argument
        :param ids: List of Folder Id
        :return: List of Test Lab TestSet Id
        '''

        # Ids List

        # Convert Id to list if it is a scalar
        if type(ids) != list:
            ids = [ids]

        # Build query for list of id
        query = self._getQueryListOrAnd(['parent-id'], [ids])

        # Get all folder that contain as parent id the given ids
        r = self.TestLabTestSets.getEntityQueryList(query, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        idList = self.TestLabTestSets.getEntityDataCollectionFieldValue('id', xml)

        return idList

    def _getIdTestLabTestSetFromTestInstanceIdList(self, ids):
        '''
        Get list id for all testsets from a list of test instances ids
        A list of Ids can also be provided as a argument
        :param ids: List of test instance ids
        :return: List of Test Lab TestSet Id
        '''

        # Build query for list of id
        query = self._getQueryListOrAnd(['id'], [ids])

        # Get all test instances
        r = self.TestLabTestInstances.getEntityQueryList(query, 'id,cycle-id')
        xml = self._getXmlFromRequestQueryList(r)

        tiList = self.TestLabTestInstances.getEntityDataCollectionFieldValueList(['id', 'cycle-id'], xml)
        tiIdList = tiList[0]
        tiTestsetIdList = tiList[1]

        testSetIdList = []

        for testInstid in ids:

            for idx, tiId in enumerate(tiIdList):

                if tiId == testInstid:
                    testSetIdList.append(tiTestsetIdList[idx])

        return testSetIdList

    def _getIdTestLabTestSetFromFolderIdTestSetName(self, folderIdList, testSetNameList):
        '''
        Return a list with testset ids that exists or None if they do not exist. The list folder Id can contain None.
        These are returned as None in the id list
        :param folderIdList: folder id list of the testsets
        :param testSetNameList: testset name list
        :return: list with testset id if they exist or None if they do not exist
        '''

        # Removed elements that we already know they do not exist
        testSetNameListFiltered = [elem for index, elem in enumerate(testSetNameList) if folderIdList[index]]
        folderIdListFiltered = [elem for index, elem in enumerate(folderIdList) if elem]

        if len(testSetNameListFiltered) == 0 or len(folderIdListFiltered) == 0:
            return [None] * len(testSetNameList)

        # Build Query
        query = self._getQueryListOrAnd(['parent-id', 'name'], [folderIdListFiltered, testSetNameListFiltered])

        r = self.TestLabTestSets.getEntityQueryList(query, 'parent-id,name,id')
        xml = self._getXmlFromRequestQueryList(r)

        lists = self.TestLabTestSets.getEntityDataCollectionFieldValueListIf(
            ['parent-id', 'id'], 'name', testSetNameList, xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        testSetIds = []
        for parentIdList, idList, testId in itertools.izip(lists['parent-id'], lists['id'], folderIdList):

            # Match?
            match = False
            for idx, parentId in enumerate(parentIdList):

                if parentId == testId:
                    # Add them it to the list
                    testSetIds.append(idList[idx])
                    match = True
                    break

            if not match:
                testSetIds.append(None)

        return testSetIds

    def _getIdTestLabTestSetFolderFromPathList(self, pathList):
        '''
        Returns the ids of test lab folders corresponding to a list of paths
        :param pathList: list of paths
        :return: list of ids corresponding to paths
        '''
        return self._getIdFromPathList(pathList, 'Lab')

    def _getIdTestLabSubFoldersFromPathList(self, pathList):
        '''
        Get list id for all sub folders in a path including the root path e.g. 'Subject\Sandbox'
        :param pathList: List of Test Lab Folders
        :return: List of Test Lab Folders inside the path list
        '''

        # Path List IDs
        pathListIDs = []

        for path in pathList:
            # Folder Id list
            idList = []

            # Get parent ID from path
            idRootPath = self._getIdTestLabTestSetFolderFromPathList([path])[0]

            # Get sub folder which have this parent id recursively
            idList += self._getIdTestLabSubFoldersFromFolderId(idRootPath)

            # Include the root path
            idList.append(idRootPath)

            pathListIDs.append(idList)

        return pathListIDs

    def _getIdTestLabSubFoldersFromFolderId(self, ids):
        '''
        Get list id for all folders in a specific path ID e.g. 'Subject\Sandbox'.
        A list of Ids can also be provided as a argument
        :param ids: Folder IDs
        :return: Testset IDs
        '''

        # Convert Id to list if it is a scalar
        if type(ids) != list:
            ids = [ids]

        # Build query for list of id
        query = self._getQueryListOrAnd(['parent-id'], [ids])

        # Get all folder that contain as parent id the given ids
        r = self.TestLabTestSetFolders.getEntityQueryList(query, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        idList = self.TestLabTestSetFolders.getEntityDataCollectionFieldValue('id', xml)

        # Check again subfolders and add them to the list
        if len(idList) > 0:
            idList += self._getIdTestLabSubFoldersFromFolderId(idList)

        return idList

    def _getIdTestLabTestInstancesFromTestsetId(self, ids):
        '''
        Get list id for all testinstances in a specific folder identified by ID
        A list of Ids can also be provided as a argument
        :param ids: List of testSet Ids
        :return: List of test lab test instance
        '''

        # Convert Id to list if it is a scalar
        if type(ids) != list:
            ids = [ids]

        # Build query for list of id - a testset is identified in the testinstance
        query = self._getQueryListOrAnd(['cycle-id'], [ids])

        # Get all folder that contain as parent id the given ids
        r = self.TestLabTestInstances.getEntityQueryList(query, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        idList = self.TestLabTestInstances.getEntityDataCollectionFieldValue('id', xml)

        return idList

    def _getIdTestLabTestInstancesFromTestsetIdTestId(self, testSetList, testList):
        '''
        Get list id for all testinstances in a specific folder identified by ID that belong to a specific testSet and
        test, None is returned in the list if no element exists
        :param testSetList:
        :param testList:
        :return:
        '''

        logger.debug('_getIdTestLabTestInstancesFromTestsetIdTestId: testSetList (%s len:%s) %s' % (
        type(testSetList), len(testSetList), testSetList ))
        logger.debug('_getIdTestLabTestInstancesFromTestsetIdTestId: testList (%s len:%s) %s' % (
        type(testList), len(testList), testList ))

        # Build Query
        query = self._getQueryListOrAnd(['cycle-id', 'test-id'], [testSetList, testList])

        r = self.TestLabTestInstances.getEntityQueryList(query, 'cycle-id,test-id,id')
        xml = self._getXmlFromRequestQueryList(r)

        logger.debug('_getIdTestLabTestInstancesFromTestsetIdTestId: xml (%s len:%s) %s' % (type(xml), len(xml), xml ))

        lists = self.TestLabTestInstances.getEntityDataCollectionFieldValueListIf(
            ['cycle-id', 'id'], 'test-id', testList, xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        testInstanceIds = []
        for parentIdList, idList, testId in itertools.izip(lists['cycle-id'], lists['id'], testSetList):

            # Match?
            match = False
            for idx, parentId in enumerate(parentIdList):

                if parentId == testId:
                    # Add them it to the list
                    testInstanceIds.append(idList[idx])
                    match = True
                    break

            if not match:
                testInstanceIds.append(None)

        logger.debug('_getIdTestLabTestInstancesFromTestsetIdTestId: return (%s len:%s) %s' % (
        type(testInstanceIds), len(testInstanceIds), testInstanceIds ))

        return testInstanceIds

    def _getIdTestLabTestRunFromTestsetIdTestId(self, testSetList, testList):
        '''
        Get list id for all testinstances in a specific folder identified by ID that belong to a specific testSet and
        test, None is returned in the list if no element exists
        :param testSetList:
        :param testList:
        :return:
        '''

        # Build Query
        query = self._getQueryListOrAnd(['cycle-id', 'test-id'], [testSetList, testList])

        r = self.TestLabRuns.getEntityQueryList(query, 'cycle-id,test-id,id')
        xml = self._getXmlFromRequestQueryList(r)

        retlist = self.TestLabRuns.getEntityDataCollectionFieldValueList(
            ['cycle-id', 'test-id', 'id'], xml)

        # Match xml data with initial data to see if everything is as expected and create a ordered list
        # This list cannot be ordered one to one because we have a relation of many to one
        orderedList = []
        for testSetListId, testListId in itertools.izip(testSetList, testList):

            for testsetId, testId, runId in itertools.izip(retlist[0], retlist[1], retlist[2]):

                if testsetId == testSetListId and testListId == testId:
                    # Add them it to the list
                    orderedList.append(runId)

        return orderedList

    def _getFolderPathListFromTestLabTestSetIdList(self, testSetIdList):

        pathList = []

        if len(testSetIdList) == 0:
            return pathList

        # Filter None from list
        testSetIdListFiltererd = [e for e in testSetIdList if e]
        testSetIdListFiltererd = list(set(testSetIdListFiltererd))

        # First get the parent if folder o testsets
        # Build Query
        query = self._getQueryListOrAnd(['id'], [testSetIdListFiltererd])

        r = self.TestLabTestSets.getEntityQueryList(query, 'parent-id,id,name')
        xml = self._getXmlFromRequestQueryList(r)

        retlist = self.TestLabTestSetFolders.getEntityDataCollectionFieldValueList(
            ['parent-id', 'id', 'name'], xml)

        testSetParentIdListXml = retlist[0]
        testSetIdListXml = retlist[1]
        testSetNameListXml = retlist[2]

        # Get all parent folder IDs until root
        parentFolderIdList = self._getParentFolderFromTestLabTestFolderIdList(testSetParentIdListXml)

        # Now get all the folder information needed
        query = self._getQueryListOrAnd(['id'], [parentFolderIdList])

        r = self.TestLabTestSetFolders.getEntityQueryList(query, 'parent-id,id,name')
        xml = self._getXmlFromRequestQueryList(r)

        retlist = self.TestLabTestSetFolders.getEntityDataCollectionFieldValueList(
            ['parent-id','id','name'], xml)

        folderParentIdListXml = retlist[0]
        folderIdListXml = retlist[1]
        folderNameListXml = retlist[2]

        # Build path for each test according to input
        for testSetId in testSetIdList:

            for testSetParentIdXml, testSetIdXml, testSetNameXml in itertools.izip(
                    testSetParentIdListXml, testSetIdListXml, testSetNameListXml):

                if testSetId == testSetIdXml:

                    # Calculate path
                    path = 'Root' + '\\' + self._getFolderPathFromFolderId(
                        testSetParentIdXml, folderIdListXml, folderParentIdListXml, folderNameListXml)

                    pathList.append(path + '\\' + testSetNameXml)

                    break

            else:
                # Add None
                pathList.append(None)

        return pathList

    def _getFolderPathListFromTestPlanTestIdList(self, testIdList):

        pathList = []

        if len(testIdList) == 0:
            return pathList

        # Filter None from list
        testIdListFiltererd = [e for e in testIdList if e]
        testIdListFiltererd = list(set(testIdListFiltererd))

        # First get the parent if folder o testsets
        # Build Query
        query = self._getQueryListOrAnd(['id'], [testIdListFiltererd])

        r = self.TestPlanTests.getEntityQueryList(query, 'parent-id,id,name')
        xml = self._getXmlFromRequestQueryList(r)

        retlist = self.TestPlanTestFolders.getEntityDataCollectionFieldValueList(
            ['parent-id', 'id', 'name'], xml)

        testParentIdListXml = retlist[0]
        testIdListXml = retlist[1]
        testNameListXml = retlist[2]

        # Get all parent folder IDs until subject
        parentFolderIdList = self._getParentFolderFromTestPlanTestFolderIdList(testParentIdListXml)

        # Now get all the folder information needed
        query = self._getQueryListOrAnd(['id'], [parentFolderIdList])

        r = self.TestPlanTestFolders.getEntityQueryList(query, 'parent-id,id,name')
        xml = self._getXmlFromRequestQueryList(r)

        retlist = self.TestPlanTestFolders.getEntityDataCollectionFieldValueList(
            ['parent-id','id','name'], xml)

        folderParentIdListXml = retlist[0]
        folderIdListXml = retlist[1]
        folderNameListXml = retlist[2]

        # Build path for each test according to input
        for testId in testIdList:

            for testParentIdXml, testIdXml, testNameXml in itertools.izip(
                    testParentIdListXml, testIdListXml, testNameListXml):

                if testId == testIdXml:

                    # Calculate path
                    path = self._getFolderPathFromFolderId(
                        testParentIdXml, folderIdListXml, folderParentIdListXml, folderNameListXml)

                    pathList.append(path)

                    break

            else:
                # Add None
                pathList.append(None)

        return pathList

    def _getParentFolderFromTestLabTestFolderIdList(self, folderIdList):

        # Filter None from list and also the ones that are already at the top
        folderIdList = [e for e in folderIdList if e]
        folderIdList = [e for e in folderIdList if e != '0']
        folderIdList = list(set(folderIdList))

        if len(folderIdList) == 0:
            return []

        # Get Ids of parent folders
        # Build Query
        query = self._getQueryListOrAnd(['id'], [folderIdList])

        r = self.TestLabTestSetFolders.getEntityQueryList(query, 'parent-id')
        xml = self._getXmlFromRequestQueryList(r)

        retlist = self.TestLabTestSetFolders.getEntityDataCollectionFieldValueList(
            ['parent-id'], xml)

        folderIdList += self._getParentFolderFromTestLabTestFolderIdList(retlist[0])

        return folderIdList

    def _getParentFolderFromTestPlanTestFolderIdList(self, folderIdList):

        # Filter None from list and also the ones that are already at the top
        folderIdList = [e for e in folderIdList if e]
        folderIdList = [e for e in folderIdList if e != '0']
        folderIdList = list(set(folderIdList))

        if len(folderIdList) == 0:
            return []

        # Get Ids of parent folders
        # Build Query
        query = self._getQueryListOrAnd(['id'], [folderIdList])

        r = self.TestPlanTestFolders.getEntityQueryList(query, 'parent-id')
        xml = self._getXmlFromRequestQueryList(r)

        retlist = self.TestPlanTestFolders.getEntityDataCollectionFieldValueList(
            ['parent-id'], xml)

        folderIdList += self._getParentFolderFromTestPlanTestFolderIdList(retlist[0])

        return folderIdList

    def _getFolderPathFromFolderId(self, folderId, folderIdList, folderParentIdList, folderNameList):

        if folderId not in folderIdList:
            return ''

        idx = folderIdList.index(folderId)

        path = folderNameList[idx]

        folderId = folderParentIdList[idx]
        folderIdListTemp = folderIdList[:]
        folderParentIdListTemp = folderParentIdList[:]
        folderNameListTemp = folderNameList[:]

        folderIdListTemp.pop(idx)
        folderParentIdListTemp.pop(idx)
        folderNameListTemp.pop(idx)

        pathTemp = self._getFolderPathFromFolderId(folderId, folderIdListTemp, folderParentIdListTemp,
                                                   folderNameListTemp)

        if pathTemp != '':
            path = pathTemp + '\\' + path

        return path

    def _getXmlFromRequestQuery(self, req=None):
        '''
        Get a single xml from a query request answer of a list of request answers
        :param req: List of requests answers
        :return: Request content in a single XML
        '''

        # Check if it is a list
        if type(req) is list:

            # For some reason sometimes we get more than we asked for...
            numberEntities = int(ET.fromstring(req[0].content).get('TotalResults'))

            dstXml = ET.fromstring('<Entities TotalResults=\"%s\"/>' % numberEntities)

            entityNumber = 0
            for r in req:

                # Add remaining to the first
                rootXml = ET.fromstring(r.content)

                for node in rootXml.findall('./Entity'):

                    if entityNumber == numberEntities:
                        break

                    dstXml.append(node)

                    entityNumber += 1

            return ET.tostring(dstXml)

        else:

            # Just return the text
            return req.content

    def _getXmlFromRequestQueryList(self, req=None):
        '''
        Get a single xml from a query request answer of a list of request answers
        :param req: List of requests answers
        :return: Request content in a single XML
        '''

        # Check if it is a list
        if type(req) is list:

            totalNumberOfEntities = 0

            dstXml = ET.fromstring('<Entities/>')
            # Handle each request individually to check if the number of entities are correct
            for resp in req:

                # There is a special case of put and post responses that do not return multiple pages but always a
                # single response and so in this case we will not have list, so we convert them to lists
                if type(resp) is not list:
                    # Make it
                    resp = [resp]

                # For some reason sometimes we get more than we asked for...
                numberEntities = int(ET.fromstring(resp[0].content).get('TotalResults'))

                totalNumberOfEntities += numberEntities

                entityNumber = 0
                for r in resp:

                    # Add remaining to the first
                    rootXml = ET.fromstring(r.content)

                    for node in rootXml.findall('./Entity'):

                        if entityNumber == numberEntities:
                            break

                        dstXml.append(node)

                        entityNumber += 1

                dstXml.set('TotalResults', str(totalNumberOfEntities))

            return ET.tostring(dstXml)

        else:

            # Just return the text
            return req.content

    def _getIdFromPathList(self, pathList, location='Lab'):
        '''
        Get id from a path e.g. 'Subject\Sandbox'
        :param pathList: Path list
        :param location: "Lab" - Testset Folder ot "Plan" - Test Folder
        :return: Id list corresponding of folder elements
        '''

        nameList = []
        parentIdList = []
        folderIdList = []

        # First break path in each of its components ( for all paths )
        testFolderList = []
        for path in pathList:
            testFolderList += path.split('\\')

        # Remove duplicated values
        testFolderList = list(set(testFolderList))

        # Next build query to get the parent-id, id and name of all folders from list
        if len(testFolderList) == 0:
            self._raiseError('getParentId', 'Path is not valid: ' + str(testFolderList) + ' was not found!')

        query = self._getQueryListOrAnd(['name'], [testFolderList])

        if location == 'Lab':
            # Make query to folder list
            r = self.TestLabTestSetFolders.getEntityQueryList(query, 'name,parent-id,id')
            xml = self._getXmlFromRequestQueryList(r)

            # Extract info from xml
            nameList = self.TestLabTestSetFolders.getEntityDataCollectionFieldValue('name', xml)
            parentIdList = self.TestLabTestSetFolders.getEntityDataCollectionFieldValue('parent-id', xml)
            folderIdList = self.TestLabTestSetFolders.getEntityDataCollectionFieldValue('id', xml)

        if location == 'Plan':
            # Make query to folder list
            r = self.TestPlanTestFolders.getEntityQueryList(query, 'name,parent-id,id')
            xml = self._getXmlFromRequestQueryList(r)

            # Extract info from xml
            nameList = self.TestPlanTestFolders.getEntityDataCollectionFieldValue('name', xml)
            parentIdList = self.TestPlanTestFolders.getEntityDataCollectionFieldValue('parent-id', xml)
            folderIdList = self.TestPlanTestFolders.getEntityDataCollectionFieldValue('id', xml)

        if location == 'Requirement':
            # Make query to folder list
            r = self.Requirements.getEntityQueryList(query, 'name,parent-id,id')
            xml = self._getXmlFromRequestQueryList(r)

            # Extract info from xml
            nameList = self.Requirements.getEntityDataCollectionFieldValue('name', xml)
            parentIdList = self.Requirements.getEntityDataCollectionFieldValue('parent-id', xml)
            folderIdList = self.Requirements.getEntityDataCollectionFieldValue('id', xml)

        # Change to upper all strings
        nameList = [e.upper() for e in nameList]

        # List to save all paths
        idList = []
        # Now, for each path in pathList calculate the path
        for path in pathList:

            nameListTemp = list(nameList)
            parentIdListTemp = list(parentIdList)
            folderIdListTemp = list(folderIdList)

            # First remove elements not necessary for the path in question
            testFolderList = path.split('\\')

            testFolderList = [e.upper() for e in testFolderList]

            for name in nameListTemp:

                # Folder does not exist
                if name not in testFolderList:
                    # Remove elements
                    index = nameListTemp.index(name)

                    del (nameListTemp[index])
                    del (parentIdListTemp[index])
                    del (folderIdListTemp[index])

            # Process folder and save results
            try:
                idPath = self._processFolderFromNameParentIdFolderId(path, testFolderList, nameListTemp,
                                                                     parentIdListTemp, folderIdListTemp)

                idList.append(idPath)

            except(QCError):

                # Path Not found
                idList.append(None)

        return idList

    def _processFolderFromNameParentIdFolderId(self, path, testFolderList, nameList, parentIdList, folderIdList):
        '''
        Process list of folders - testFolderList - to find the corresponding folder ID of a specific path
        nameList, parentIdList, folderIdList are lists of parameters retrieved from QC
        :param path:  Reference path
        :param testFolderList: Corresponding Test Folder List
        :param nameList: Corresponding Name List
        :param parentIdList: Corresponding Parent Id List
        :param folderIdList: Corresponding Folder Id List
        :return:
        '''

        # Check if all folders were found and so if path is valid
        for folder in testFolderList:
            if folder not in nameList:
                self._raiseError('_processFolderFromNameParentIdFolderId',
                                 'Path is not valid: ' + str(testFolderList) + ' was not found!', False)

        # Search for a valid path
        pathOk = False
        val = '0'
        while not pathOk:

            # Ok lets build path starting from '0'
            val = '0'

            for folder in testFolderList:

                if val not in parentIdList:
                    self._raiseError('_processFolderFromNameParentIdFolderId', 'Path incorrect - ' + path, False)

                if (val in parentIdList) and (folder == nameList[parentIdList.index(val)]):

                    pathOk = True
                    val = folderIdList[parentIdList.index(val)]
                else:
                    pathOk = False

                    # Remove last value since it is not valid
                    index = parentIdList.index(val)
                    del (nameList[index])
                    del (parentIdList[index])
                    del (folderIdList[index])

                    break

        # Return val
        return val

    def _getQueryOrAnd(self, fieldList, valueListList):
        '''
        Returns a query type field1[valueList1 or valueList2 or ...]; field2[valueList1 or valueList2 or ...]
        :param fieldList: list of field to be query
        :param valueListList: List of lists of values
        :return: query
        '''

        # Query
        query = ''

        # Build Query
        for field, valueList in itertools.izip(fieldList, valueListList):

            if query != '':
                query += ';'

            query += field + '[\"' + valueList[0] + '\"'
            for value in valueList[1:]:
                query = query + ' or \"' + value + '\"'
            query += ']'

        return query

    def _getQueryListOrAnd(self, fieldList, valueListList, entitySplit=200):
        '''
        Returns a list of query type field1[valueList1 or valueList2 or ...]; field2[valueList1 or valueList2 or ...]
        that can be split in several calls - fields list values are related
        :param fieldList: list of field to be query
        :param valueListList: List of lists of values
        :return: query
        '''

        logger.debug('_getQueryListOrAnd: Start...')
        logger.debug('_getQueryListOrAnd: fieldList: %s' % fieldList)
        logger.debug('_getQueryListOrAnd: valueListList: %s' % valueListList)
        logger.debug('_getQueryListOrAnd: entitySplit: %s' % entitySplit)

        valueListSplit = []
        numberOfQueries = 1

        # Guarantee that the size of the request is not much higher than aprox. 4000. => error 413
        maxCharNumber = 3000 / len(valueListList)
        # Guarantee that the number of entities is limited to the pre defined => error 413
        entitySplit /= len(valueListList)

        # List with the number of entities each list should have to guarantee the max number of chars
        # Get number of max entities we should have to guarantee this => Not efficient but works
        # ToDo => Decide this per query
        for valueList in valueListList:

            splitList = []
            entitySize = 0
            for value in valueList:

                if len(('%s' % splitList).replace(', ', ' or ')) > maxCharNumber:

                    if entitySize < entitySplit:
                        entitySplit = entitySize

                    entitySize = 0

                    # Start again
                    splitList = [value]
                else:
                    splitList.append(value)
                    entitySize += 1

        # Split list into the entitySplit number of entries - This will give us the number of queries
        for valueList in valueListList:
            split = [valueList[i * entitySplit:(i + 1) * entitySplit] for i in range((len(valueList) / entitySplit) + 1)
                     if len(valueList[i * entitySplit:(i + 1) * entitySplit]) > 0]

            valueListSplit.append(split)

        # Query List
        queryList = ['']

        for field, valueList in itertools.izip(fieldList, valueListSplit):

            queryListTemp = []

            # Iterate through split values
            for val in valueList:

                for query in queryList:

                    if query != '':
                        query += ';'

                    query += field + '[\"' + val[0] + '\"'

                    for value in val[1:]:
                        query += ' or \"' + value + '\"'
                    query += ']'

                    queryListTemp.append(query)

            queryList = queryListTemp

        logger.debug('_getQueryListOrAnd: return: %s' % queryList)
        logger.debug('_getQueryListOrAnd: ...done!')

        return queryList

    def _getEntityDataTemplateCollectionFromQueryXml(self, sourceXml, templateXml):
        '''
        Generate XML based on parameters present in template XML but with the information of the source Xml
        Useful when re-using a query
        :param sourceXml: Source XML
        :param templateXml: Xml that will be merged to the source Xml
        :return: Merged XML
        '''

        # Extract info from xml
        sourceXmlRoot = ET.fromstring(sourceXml)

        # Get entity required fields
        templateXmlRoot = ET.fromstring(templateXml)

        # Destination Xml
        dstXml = ET.Element('Entities')

        for srcNode in sourceXmlRoot.findall('.//Entity'):

            # Get a template copy
            tmpRoot = copy.deepcopy(templateXmlRoot)

            # Get attribute to search from template
            for tmpField in tmpRoot.findall('.//Field'):
                # Update value
                tmpField.find('Value').text = srcNode.find(
                    './/Field[@Name=\'' + tmpField.get('Name') + '\']/Value').text

            dstXml.append(copy.deepcopy(tmpRoot))

        return ET.tostring(dstXml)

    def _raiseError(self, function='None', message='', logError=True):
        '''
        Raise Error
        :param function: Function where error occurred
        :param message: Error message
        :return:
        '''

        if logError:
            logger.error(function + ': ' + message)

        raise QCError('Error!', function + ': ' + message)

    def saveXmlDictToFolder(self, xml, location='.'):
        '''
        Save to file the XML content of a dictionary of XMLs
        :param location: Location of file
        '''

        # Check each xml in dict and save it
        for xml_id in xml:

            # Create file and save content
            # Check if it is an xml file and if not add extension
            if xml_id[-4::1] == '.xml':
                xmlFileName = xml_id
            else:
                xmlFileName = xml_id + '.xml'

            filen = open(join(location, xmlFileName), 'w')
            filen.write(xml[xml_id])
            filen.close()

    def saveXmlToFile(self, xml, fileName='saveXmlToFile.xml'):
        '''
        Save to file the xml content of a specific request or a dictionary
        :param fileName: File name
        '''

        # Create file and save content
        filen = open(fileName, 'w')
        filen.write(xml.encode('utf-8'))
        filen.close()

    def readXmlFromFile(self, fileName=None):
        '''
        Read a XML file and return string
        :return: XML String
        '''

        # Return
        return open(fileName).read()

    def dumpEntityInfo(self, path):
        '''
        Dump all entity related information to a folder
        :param path: Folder where files will be saved
        '''

        # Get TestPlanTests info and save it
        dumpDict = self.TestPlanTests.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get TestPlanDesignSteps info and save it
        dumpDict = self.TestPlanDesignSteps.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get TestPlanTestFolders info and save it
        dumpDict = self.TestPlanTestFolders.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get TestLabRuns info and save it
        dumpDict = self.TestLabRuns.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get TestPlanRunStep info and save it
        dumpDict = self.TestLabRunStep.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get TestLabTestInstances info and save it
        dumpDict = self.TestLabTestInstances.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get TestLabTestSetFolders info and save it
        dumpDict = self.TestLabTestSetFolders.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get TestLabTestSets info and save it
        dumpDict = self.TestLabTestSets.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get Release info and save it
        dumpDict = self.Releases.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get Release Cycle info and save it
        dumpDict = self.ReleaseCycles.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get Requirements info and save it
        dumpDict = self.Requirements.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)

        # Get Defects info and save it
        dumpDict = self.Defects.dumpInfo()
        self.saveXmlDictToFolder(dumpDict, path)


class QC_Entity(QC_Connect):
    '''
    Class that abstracts the entity concept in QC
    '''

    # Initialize connection
    def __init__(self, entity=None, server=None, project=None, domain=None, silent=False, session=None, proxies=None):

        # Root Entity URL
        self.url_entity = server + '/qcbin/rest/domains/' + domain + '/projects/' + project + '/' + entity

        # Root customization entity URL - important to get field information
        self.url_entity_customization = server + '/qcbin/rest/domains/' + domain + '/projects/' + \
                                        project + '/customization/entities/'

        # Entity
        self.entity = entity

        # Entity Data - structure containing the information regarding entity (either in xml or json)
        self.entityData = None

        # Page size - Max number of pages to get during one query / get
        self.pageSize = 500

        # Collection size - Max number of entities sent in a single put / post
        self.collectionSize = 50

        # Silent mode
        self.silent = silent

        # Init upper class
        super(QC_Entity, self).__init__(server, project, domain, silent, session, proxies)

    # Return the entity e.g. return the Collection of Test Folder (limited to max. size of 5000 entities)
    # Note: Only first page is returned to limit the number of calls to qc_server
    def getEntity(self, fieldsFilter='', **kwargs):

        logger.debug('getEntity: Start...')
        logger.debug('getEntity: fieldsFilter: %s' % fieldsFilter)

        # Request list to be returned.. or not
        req = []

        # Define query - entity is plural for these queries
        url = self.url_entity + 's?page-size=' + str(self.pageSize)

        # Add filters if defined
        if fieldsFilter != '':
            url += '&fields=' + fieldsFilter

        # Get the test collection
        logger.debug('getEntity: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        req.append(r)

        # Validate response code
        self._validateResponse(r, 'getEntityQuery: ' + self.entity)

        # Now lets check if we got everything -> check the number of entities found
        numberEntities = int(ET.fromstring(r.content).get('TotalResults'))

        # List with the next page sizes
        pageList = []

        for pageNum in range(self.pageSize + 1, numberEntities + 1, self.pageSize):
            # Add page sizes
            pageList.append(pageNum)

        # Lets get the remaining pages
        for page in pageList:
            url = self.url_entity + 's?page-size=' + str(self.pageSize) + '&start-index=' + str(page)

            # Get the test collection
            logger.debug('getEntity: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.get(url, **kwargs)

            # Validate response code
            self._validateResponse(r, 'getEntity: ' + self.entity)

            # Add to list that will be returned
            req.append(r)

        logger.debug('getEntity: return: %s' % req)
        logger.debug('getEntity: ...done!')

        return req

    # Create a specific entity
    def postEntityCollection(self, content, **kwargs):

        logger.debug('postEntityCollection: Start...')

        # Define headers
        headers = {'Content-type': 'application/xml;type=collection'}

        # Define query - entity is plural for these queries
        url = self.url_entity + 's'

        # Request list to be returned.. or not
        req = []

        # Break content in several that contain the max number of entities
        contentList = self.breakEntityCollection(content)

        logger.debug('postEntityCollection: contentList: %s' % contentList)

        # Do several updates depending on the number of entities
        for lst in contentList:
            # Get the test collection
            logger.debug('postEntityCollection: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.post(url, data=lst, headers=headers, **kwargs)

            # Validate response code
            self._validateResponse(r, 'postEntityCollection: ' + self.entity, 201)

            # Add to list that will be returned
            req.append(r)

        logger.debug('postEntityCollection: return: %s' % req)
        logger.debug('postEntityCollection: ...done!')

        return req

    # Create a specific entity
    def postEntity(self, content, **kwargs):

        # Define headers
        headers = {'Content-type': 'application/xml'}

        # Define query - entity is plural for these queries
        url = self.url_entity + 's'

        # Get the entity
        logger.debug('postEntity: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.post(url, data=content, headers=headers, **kwargs)

        # Validate response code
        self._validateResponse(r, 'postEntity: ' + self.entity, 201)

        return r

    # Post attachment to an entity ID
    def postEntityAttachmentByID(self, entityID, filename, description, data, override=True, richContent=False,
                                 octectStream=False,**kwargs):

        multiPartData = ''
        boundary = '2q346ytfugbijnhok)/(&&'

        # Define headers
        if octectStream:
            headers = {'Content-type': 'application/octet-stream', 'Slug': filename, 'Descripton': description}

        else:
            # self._raiseError('postEntityAttachmentByID', 'Content-type: multipart/form-data not supported yet')
            headers = {'Content-type': 'multipart/form-data; boundary=' + boundary}

            if override is True:
                override = 'Y'
            else:
                override = 'N'

            if richContent is True:
                richContent = '1'
            else:
                richContent = '0'

            multiPartData += '--' + boundary + '\r\n'
            multiPartData += 'Content-Disposition: form-data; name=\"filename\"\r\n\r\n' + filename + '\r\n'
            multiPartData += '--' + boundary + '\r\n'
            multiPartData += 'Content-Disposition: form-data; name=\"description\"\r\n\r\n' + description +'\r\n'
            multiPartData += '--' + boundary + '\r\n'
            multiPartData += 'Content-Disposition: form-data; name=\"override-existing-attachment\"\r\n\r\n' + override + '\r\n'
            multiPartData += '--' + boundary + '\r\n'
            multiPartData += 'Content-Disposition: form-data; name=\"ref-subtype\"\r\n\r\n' + richContent + '\r\n'
            multiPartData += '--' + boundary + '\r\n'
            multiPartData += 'Content-Disposition: form-data; name=\"file\"; filename=\"' + filename + '\"\r\n'
            multiPartData += 'Content-Type: text/plain\r\n\r\n' + data + '\r\n'
            multiPartData += '--' + boundary + '--'

        # Define query - entity is plural for these queries
        url = self.url_entity + 's/' + str(entityID) + '/attachments'

        # Get the
        logger.debug('postEntityAttachmentByID: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.post(url, data=multiPartData, headers=headers, **kwargs)

        # Validate response code - This must be validated differently because when overwrite is active it can return
        # either 200 or 201 dependently if it already exists or not
        if override is 'N':
            self._validateResponse(r, 'postEntityAttachmentByID: ' + self.entity, 201)

        elif (r.status_code != 200 and r.status_code != 201):
            logger.debug(' Oops something went wrong! (' + str(r.status_code) + '). Details follow:\n' +
                         r.text + '\n')

            # Slient exit?
            if not self.silent:
                raise ConnectionError('Status code != 200 and 201 (' + str(r.status_code) + ')',
                                      'postEntityAttachmentByID: The status code is not the expected! Details follow:\n')
        else:
            # Nothing to report
            logger.debug(' OK! (' + str(r.status_code) + ')')

        return r

    # Query the entity e.g. query the Collection of Test Folder (limited to max. size of 5000 entities)
    # Query always returns a max of 100 elements per page (defined in qc_server)
    # Can return a request or a list of requests depending if more than one get is necessary
    def getEntityQuery(self, query='', **kwargs):

        logger.debug('getEntityQuery: Start...')
        logger.debug('getEntityQuery: fieldList: %s' % query)

        # Request list to be returned.. or not
        req = []

        # Define query - entity is plural for these queries
        url = self.url_entity + 's?page-size=' + str(self.pageSize) + '&query={' + query + '}'

        # Get the test collection
        logger.debug('getEntityQuery: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        req.append(r)

        # Validate response code
        self._validateResponse(r, 'getEntityQuery: ' + self.entity)

        # Now lets check if we got everything -> check the number of entities found
        numberEntities = int(ET.fromstring(r.content).get('TotalResults'))

        # List with the next page sizes
        pageList = []

        for pageNum in range(self.pageSize + 1, numberEntities + 1, self.pageSize):
            # Add page sizes
            pageList.append(pageNum)

        # Lets get the remaining pages
        for page in pageList:
            url = self.url_entity + 's?page-size=' + str(self.pageSize) + '&start-index=' \
                  + str(page) + '&query={' + query + '}'

            # Get the test collection
            logger.debug('getEntityQuery: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.get(url, **kwargs)

            # Validate response code
            self._validateResponse(r, 'getEntityQuery: ' + self.entity)

            # Add to list that will be returned
            req.append(r)

        if len(req) > 1:
            logger.debug('getEntityQuery: return: %s' % req)
            logger.debug('getEntityQuery: ...done!')

            return req
        else:
            logger.debug('getEntityQuery: return: %s' % r)
            logger.debug('getEntityQuery: ...done!')
            return r

    def getEntityQueryList(self, queryList=[], fieldsFilter='', **kwargs):
        '''
        Query the entity several times - queryList e.g. query the Collection of Test Folder
        Query always returns a max of 100 elements per page (defined in qc_server)
        Can return a request or a list of requests depending if more than one get is necessary
        :param queryList: List of queries to be done
        :param kwargs:
        :return:
        '''

        logger.debug('getEntityQueryList: Start...')
        logger.debug('getEntityQueryList: queryList: %s' % queryList)
        logger.debug('getEntityQueryList: fieldsFilter: %s' % fieldsFilter)

        # Request list to be returned.. or not
        req = []

        for query in queryList:

            # Request response from single query
            req_response = []

            # Define query - entity is plural for these queries
            url = self.url_entity + 's?page-size=' + str(self.pageSize) + '&query={' + urllib.quote(query) + '}'

            # Add filters if defined
            if fieldsFilter != '':
                url += '&fields=' + fieldsFilter

            # Get the test collection
            logger.debug('getEntityQueryList: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.get(url, **kwargs)

            req_response.append(r)

            # Validate response code
            self._validateResponse(r, 'getEntityQueryList: ' + self.entity)

            # Now lets check if we got everything -> check the number of entities found
            numberEntities = int(ET.fromstring(r.content).get('TotalResults'))

            # List with the next page sizes
            pageList = []

            for pageNum in range(self.pageSize + 1, numberEntities + 1, self.pageSize):
                # Add page sizes
                pageList.append(pageNum)

            # Lets get the remaining pages
            for page in pageList:
                url = self.url_entity + 's?page-size=' + str(self.pageSize) + '&start-index=' \
                      + str(page) + '&query={' + urllib.quote(query) + '}'

                # Add filters if defined
                if fieldsFilter != '':
                    url += '&fields=' + fieldsFilter

                # Get the test collection
                logger.debug('getEntityQueryList: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

                r = self.get(url, **kwargs)

                # Validate response code
                self._validateResponse(r, 'getEntityQueryList: ' + self.entity)

                # Add to list that will be returned
                req_response.append(r)

            req.append(req_response)

        logger.debug('getEntityQueryList: return: %s' % req)
        logger.debug('getEntityQueryList: ...done!')

        return req

    # Get entity by its ID
    def getEntityByID(self, entityID='1', **kwargs):

        # Define query - entity is plural for these queries
        url = self.url_entity + 's/' + str(entityID)

        # Get the test collection
        logger.debug('getEntityID: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getEntityID: ' + self.entity)

        return r

    # Update entity by its ID
    def putEntityByID(self, entityID='1', content=None, headers=None, **kwargs):

        # Define headers
        if not headers:
            headers = {'Content-type': 'application/xml'}

        # Define query - entity is plural for these queries
        url = self.url_entity + 's/' + str(entityID)

        # Get the test collection
        logger.debug('putEntityID: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.put(url, data=content, headers=headers, **kwargs)

        # Validate response code
        self._validateResponse(r, 'putEntityID: ' + self.entity)

        return r

    def putEntityCollection(self, content, **kwargs):
        '''
        Update an entity collection
        :param content: content to be updated
        :param headers: header
        :param kwargs:
        :return:
        '''

        logger.debug('putEntityCollection: Start...')

        # Define headers
        headers = {'Content-type': 'application/xml;type=collection'}

        # Define query - entity is plural for these queries
        url = self.url_entity + 's'

        # Request list to be returned.. or not
        req = []

        # Break content in several that contain the max number of entities
        contentList = self.breakEntityCollection(content)

        # Do several updates depending on the number of entities
        for lst in contentList:
            logger.debug('putEntityCollection: list: %s' % lst)

            # Get the test collection
            logger.debug('putEntityCollection: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.put(url, data=lst, headers=headers, **kwargs)

            # Validate response code
            self._validateResponse(r, 'putEntityCollection: ' + self.entity)

            # Add to list that will be returned
            req.append(r)

        logger.debug('putEntityCollection: return: %s' % req)
        logger.debug('putEntityCollection: ...done!')

        return req

    # Delete entity Id list
    def deleteEntityIdList(self, entityIds, **kwargs):

        req = []

        # if not a list create a new one
        if type(entityIds) != list:
            entityIds = [entityIds]

        # Because of the list size we can sometimes generate queries that are too long. So too avoid this (413)
        # we have to break the list in to smaller lists - Max in server is around 4000, assuming that each ID has less
        # than 10 chars we get:
        numberOfElements = 4000 / 10

        for i in range(0, len(entityIds), numberOfElements):

            entityIdsSub = entityIds[i:i + numberOfElements]

            # list of ids format
            idList = ''
            for entityId in entityIdsSub:
                idList = idList + entityId + ','

            idList = idList[:-1]

            # Define query - entity is plural for these queries
            url = self.url_entity + 's?ids-to-delete=' + idList

            # Get the test collection
            logger.debug('deleteEntityIdList: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.delete(url, **kwargs)

            # Validate response code
            self._validateResponse(r, 'deleteEntityIdList: ' + self.entity)

            req.append(r)

        return req

    # Query the entities fields
    def getEntityFields(self, **kwargs):

        # Define query
        url = self.url_entity_customization + self.entity + '/fields'

        # Get the test collection
        logger.debug('getEntityFields: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getEntityFields: ' + self.entity)

        return r

    # Query the required entities fields
    def getEntityFieldsRequired(self, **kwargs):

        # Define query
        url = self.url_entity_customization + self.entity + '/fields' + '?required=true'

        # Get the test collection
        logger.debug('getEntityFieldsRequired: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getEntityFieldsRequired: ' + self.entity)

        return r

    # Query the entities fields which can be used as a filter
    def getEntityFieldsCanFilter(self, **kwargs):

        # Define query
        url = self.url_entity_customization + self.entity + '/fields' + '?can-filter=true'

        # Get the test collection
        logger.debug('getEntityFieldsCanFilter: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getEntityFieldsCanFilter: ' + self.entity)

        return r

    # Query the collection of lists related to a specific entity
    def getEntityLists(self, **kwargs):

        # Define query - entity is plural for these queries
        url = self.url_entity_customization + self.entity + '/lists'

        # Get the test collection
        logger.debug('getEntityLists: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getEntityLists: ' + self.entity)

        return r

    # Query the collection of entity relations in the project or the info related to a specific relation
    def getEntityRelations(self, relationship=None, **kwargs):

        # If relationship is defined add it to query
        if relationship is not None:
            relationship = '/' + relationship
        else:
            relationship = ''

        # Define query - entity is plural for these queries
        url = self.url_entity_customization + self.entity + '/relations' + relationship

        # Get the test collection
        logger.debug('getEntityRelations: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getEntityRelations: ' + self.entity)

        return r

    # Get data template - returns xml
    def getEntityDataTemplate(self, withAllFields=False, withRequiredFields=True, dataType='xml'):

        if dataType == 'xml':

            data = '<Entity Type=\"' + self.entity + '\"><Fields></Fields></Entity>'

            # Data Query
            requiredFields = None

            if withAllFields:

                requiredFields = self.getEntityFields()

            elif withRequiredFields:

                requiredFields = self.getEntityFieldsRequired()

            entityDataRoot = ET.fromstring(requiredFields.content)

            # Add fields found in query to template xml
            for node in entityDataRoot.findall('./Field'):
                data = self.addEntityDataFieldValue(node.get('Name'), None, data)

            return data

        else:

            self._raiseError('getEntityDataTemplate', 'Only xml is currently supported')

    # Get value from entity data
    def getEntityDataCollectionFieldValue(self, field, entityData=None, dataType='xml'):

        logger.debug('getEntityDataCollectionFieldValue: Start...')

        data = self.getEntityDataCollectionFieldValueList([field], entityData, dataType)[0]

        logger.debug('getEntityDataCollectionFieldValue: ...done!')

        return data

    # Get value from entity data
    def getEntityDataCollectionFieldValueList(self, fieldList, entityData=None, dataType='xml'):

        logger.debug('getEntityDataCollectionFieldValueList: Start...')
        logger.debug('getEntityDataCollectionFieldValueList: fieldList: %s' % fieldList)

        # List of values founds
        listValueList = [[] for e in range(len(fieldList))]

        if dataType == 'xml':

            if entityData is None:
                entityData = self.entityData

            for event, elem in ET.iterparse(cStringIO.StringIO(entityData)):

                if elem.tag == 'Field':

                    for idx, field in enumerate(fieldList):

                        if elem.attrib.get('Name') == field:

                            data = None

                            for child in elem.findall('Value'):

                                if data is None:
                                    data = child.text
                                else:
                                    if type(data) is not list:
                                        data = [data]
                                    data.append(child.text)

                            listValueList[idx].append(data)

                    elem.clear()

            logger.debug('getEntityDataCollectionFieldValueList: ...done!')

            return listValueList

        else:

            self._raiseError('getEntityDataCollectionFieldValue', 'Only xml is currently supported')

    # Get value from entity data if condField equal to condValue
    def getEntityDataCollectionFieldValueIf(self, field, condField, condValue=None, entityData=None, dataType='xml'):

        # List of values founds
        listValues = []

        if dataType == 'xml':

            if entityData is None:
                entityData = self.entityData

            entityDataRoot = ET.fromstring(entityData)

            # Condition
            conditionAttrib = '[@Name=\'' + condField + '\']'

            if condValue is not None:
                conditionAttrib += '/Value/../..'

            for node in entityDataRoot.findall('./Entity/Fields/Field' + conditionAttrib):

                # If conditional value exists it needs to be checked
                if condValue is not None:

                    nodeValue = node.find('Field[@Name=\'' + condField + '\']').find('Value')

                    if nodeValue is not None:

                        # Check value condition
                        if nodeValue.text != condValue:
                            # Bad luck... continue
                            continue

                # Get value
                for childValue in node.findall('Field[@Name=\'' + field + '\']/Value'):
                    listValues.append(childValue.text)

            return listValues

        else:

            self._raiseError('getEntityDataCollectionFieldValue', 'Only xml is currently supported')

    # Get value from entity data if condField equal to condValue
    def getEntityDataCollectionFieldValueListIf(self, fieldList, condField, condValueList=None,
                                                entityData=None, dataType='xml'):

        # List to save data
        data = [[[] for i in range(len(condValueList))] for i in range(len(fieldList))]

        # List of values founds
        listValues = dict(itertools.izip(fieldList, data))

        if dataType == 'xml':

            if entityData is None:
                entityData = self.entityData

            entityDataRoot = ET.fromstring(entityData)

            # Condition
            conditionAttrib = '[@Name=\'' + condField + '\']'

            if condValueList is not None:
                conditionAttrib += '/Value/../..'

            for node in entityDataRoot.findall('./Entity/Fields/Field' + conditionAttrib):

                # value found
                value = None

                # If conditional value exists it needs to be checked
                if condValueList is not None:

                    nodeValue = node.find('Field[@Name=\'' + condField + '\']').find('Value')

                    if nodeValue is not None:

                        # Check value condition
                        if nodeValue.text not in condValueList:
                            # Bad luck... continue
                            continue
                        else:
                            # This works
                            value = nodeValue.text

                # Get value for field in the list
                for field in fieldList:
                    for childValue in node.findall('Field[@Name=\'' + field + '\']/Value'):

                        for idx, condValue in enumerate(condValueList):

                            if condValue == value:
                                listValues[field][idx].append(childValue.text)

            return listValues

        else:

            self._raiseError('getEntityDataCollectionFieldValue', 'Only xml is currently supported')

    # Get value from entity data
    def getEntityDataFieldValue(self, field, entityData=None, dataType='xml'):

        # List of values founds
        listValues = []

        if dataType == 'xml':

            if entityData is None:
                entityData = self.entityData

            entityDataRoot = ET.fromstring(entityData)

            for node in entityDataRoot.findall('./Fields/Field[@Name=\'' + field + '\']'):

                for child in node.findall('Value'):
                    listValues.append(child.text)

            return listValues

        else:

            self._raiseError('getEntityDataCollectionFieldValue', 'Only xml is currently supported')

    # Add value to entity Data Field
    def addEntityDataCollectionFieldValue(self, field, value, entityData=None, dataType='xml'):

        # Temporary entity data
        entityDataTemp = entityData

        if dataType == 'xml':

            if entityData is None:
                entityDataTemp = self.entityData

            entityDataTemp = ET.fromstring(entityDataTemp)

            # Parse each node individually
            for node in entityDataTemp.findall('Entity'):

                # Check if element was updated or not
                childUpdated = False

                # Search for the corresponding field and update value
                for child in node.findall('./Fields/Field[@Name=\'' + field + '\']'):

                    # Check if child 'Value' exists
                    childValue = child.find('Value')

                    if childValue is None:
                        # Add child 'Value' with value
                        childValue = ET.SubElement(child, 'Value')

                    # Update / add value
                    childValue.text = value

                    # Updated
                    childUpdated = True

                # if child does not exist create it
                if not childUpdated:
                    newElem = ET.Element('Field', {'Name': field})
                    valElem = ET.SubElement(newElem, 'Value')
                    valElem.text = value

                    node.find('Fields').append(newElem)

            # Return xml string
            return ET.tostring(entityDataTemp)

        else:

            self._raiseError('_getEntityDataFieldValue', 'Only xml is currently supported')

    def addEntityDataFieldValue(self, field, value, entityData=None, dataType='xml'):
        '''
        Add value to entity Data Field. Value can be None
        :param field: field to be added
        :param value: value of field - can be a list or None
        :param entityData: entityData to be updated (optional)
        :param dataType: dataType - xml / json (currently not supported)
        :return:
        '''

        # If list handle it separately
        if type(value) is list:
            return self._addEntityDataFieldValueList(field, value, entityData, dataType)

        # Temporary entity data
        entityDataTemp = entityData

        if dataType == 'xml':

            if entityData is None:
                entityDataTemp = self.entityData

            entityDataTemp = ET.fromstring(entityDataTemp)

            element = entityDataTemp.find('Fields')

            # Check if field exists
            for child in element.iter('Field'):

                if child.get('Name') == field:

                    # Add value element
                    valElem = child.find('Value')

                    if value is not None:
                        valElem.text = value

                    return ET.tostring(entityDataTemp)

            # If it does not exist just add one
            newElem = ET.Element('Field', {'Name': field})
            ET.SubElement(newElem, 'Value')

            if value is not None:
                valElem = newElem.find('Value')
                valElem.text = value

            element.append(newElem)

            # Save value
            if entityData is None:
                self.entityData = ET.tostring(entityDataTemp)

            return ET.tostring(entityDataTemp)

        else:

            self._raiseError('addEntityDataFieldValue', 'Only xml is currently supported')

    def _addEntityDataFieldValueList(self, field, valueList, entityData=None, dataType='xml'):
        '''
        Add value to entity Data Field. Value can be None
        :param field: field to be added
        :param valueList: list of values of field
        :param entityData: entityData to be updated (optional)
        :param dataType: dataType - xml / json (currently not supported)
        :return:
        '''

        # Temporary entity data
        entityDataTemp = entityData

        if dataType == 'xml':

            if entityData is None:
                entityDataTemp = self.entityData

            entityDataTemp = ET.fromstring(entityDataTemp)

            element = entityDataTemp.find('Fields')

            # Check if field exists and delete it
            for child in element.iter('Field'):

                if child.get('Name') == field:
                    element.remove(child)

            # Now that it does not exist just add it
            newElem = ET.Element('Field', {'Name': field})

            for value in valueList:
                ET.SubElement(newElem, 'Value')

            for value, valElem in itertools.izip(valueList, newElem.findall('Value')):

                if value is not None:
                    valElem.text = value

            element.append(newElem)

            # Save valueList
            if entityData is None:
                self.entityData = ET.tostring(entityDataTemp)

            return ET.tostring(entityDataTemp)

        else:

            self._raiseError('addEntityDataFieldValue', 'Only xml is currently supported')

    # Add entity info to a collection and return it
    def addEntityDataToCollection(self, data, dataCollection=None, dataType='xml'):

        if dataType == 'xml':

            if dataCollection is None:
                dataCollection = '<Entities/>'

            dataCollectionRoot = ET.fromstring(dataCollection)

            dataRoot = ET.fromstring(data)

            dataCollectionRoot.append(dataRoot)

            return ET.tostring(dataCollectionRoot)

        else:

            self._raiseError('addEntityDataToCollection', 'Only xml is currently supported')

    # Break entity collection file into a list of collectionSize entities
    def breakEntityCollection(self, content):

        # Src xml
        srcXml = ET.fromstring(content)

        # List of xmls to be returned
        listXml = []

        # Temp xml
        dstXmlRoot = ET.fromstring('<Entities/>')

        # Iterations
        iter = 0

        # Iterate all
        for nodeSrcXml in srcXml:

            # Add
            dstXmlRoot.append(nodeSrcXml)

            iter += 1

            # Update iteration
            if iter == self.collectionSize:
                listXml.append(ET.tostring(dstXmlRoot))

                # Initialize
                iter = 0
                dstXmlRoot = ET.fromstring('<Entities/>')

        # Save to list remaining
        if iter != 0:
            listXml.append(ET.tostring(dstXmlRoot))

        return listXml

    # Get Entity full information in a (xml) dictionary
    def dumpInfo(self):

        # Dictionary
        info = dict()

        info[self.entity + '_fields'] = self.getEntityFields().content
        info[self.entity + '_lists'] = self.getEntityLists().content
        info[self.entity + '_requiredFields'] = self.getEntityDataTemplate()

        try:
            info[self.entity + '_relations'] = self.getEntityRelations().content
        except:
            logger.warning('dumpInfo: %s' % ('getEntityRelations not possible'))

        return info

    # Raise Error
    def _raiseError(self, function='None', message=''):

        if self.silent:
            logger.error(function + ': ' + message)

        # Slient exit?
        if not self.silent:
            raise QCEntityError('Error!', function + ': ' + message)


class QC_Entity_TL_Run_Step(QC_Entity):
    '''
    Class that specifies a specific type of entity - run steps
    '''

    # Initialize connection
    def __init__(self, server=None, project=None, domain=None, silent=False, session=None, proxies=None):

        # Init upper class
        super(QC_Entity_TL_Run_Step, self).__init__('run-step', server, project, domain, silent, session, proxies)

        # Save qc_server
        self.server = server

        # Save project
        self.project = project

        # Save domain
        self.domain = domain

        # Root Entity URL
        self.url_entity = server + '/qcbin/rest/domains/' + domain + '/projects/' + project + '/runs/runid/' + self.entity

    # Return the entity e.g. return the Collection of Test Folder (limited to max. size of 5000 entities)
    # Note: Only first page is returned to limit the number of calls to qc_server
    def getEntity(self, runId, **kwargs):

        logger.debug('getEntity: Start...')

        # Request list to be returned.. or not
        req = []

        # Define query - entity is plural for these queries
        url = self.url_entity.replace('runid', runId) + 's?page-size=' + str(self.pageSize)

        # Get the test collection
        logger.debug('getEntity: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        req.append(r)

        # Validate response code
        self._validateResponse(r, 'getEntityQuery: ' + self.entity)

        # Now lets check if we got everything -> check the number of entities found
        numberEntities = int(ET.fromstring(r.content).get('TotalResults'))

        # List with the next page sizes
        pageList = []

        for pageNum in range(self.pageSize + 1, numberEntities + 1, self.pageSize):
            # Add page sizes
            pageList.append(pageNum)

        # Lets get the remaining pages
        for page in pageList:
            url = self.url_entity.replace('runid', runId) + 's?page-size=' + str(self.pageSize) + '&start-index=' + str(
                page)

            # Get the test collection
            logger.debug('getEntity: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.get(url, **kwargs)

            # Validate response code
            self._validateResponse(r, 'getEntity: ' + self.entity)

            # Add to list that will be returned
            req.append(r)

        logger.debug('getEntity: return: %s' % req)
        logger.debug('getEntity: ...done!')

        return req

    # Can return a request or a list of requests depending if more than one get is necessary
    def getEntityQuery(self, runId, query='', **kwargs):

        # Request list to be returned.. or not
        req = []

        # Define query - entity is plural for these queries
        url = self.url_entity.replace('runid', runId) + 's?page-size=' + str(self.pageSize) + '&query={' + urllib.quote(query) + '}'

        # Get the test collection
        logger.debug('getEntityQuery: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        req.append(r)

        # Validate response code
        self._validateResponse(r, 'getEntityQuery: ' + self.entity)

        # Now lets check if we got everything -> check the number of entities found
        numberEntities = int(ET.fromstring(r.content).get('TotalResults'))

        # List with the next page sizes
        pageList = []

        for pageNum in range(self.pageSize + 1, numberEntities + 1, self.pageSize):
            # Add page sizes
            pageList.append(pageNum)

        # Lets get the remaining pages
        for page in pageList:
            url = self.url_entity.replace('runid', runId) + 's?page-size=' + str(self.pageSize) + '&start-index=' \
                  + str(page) + '&query={' + urllib.quote(query) + '}'

            # Get the test collection
            logger.debug('getEntityQuery: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

            r = self.get(url, **kwargs)

            # Validate response code
            self._validateResponse(r, 'getEntityQuery: ' + self.entity)

            # Add to list that will be returned
            req.append(r)

        if len(req) > 1:
            return req
        else:
            return r

    # Get entity by its ID
    def getEntityByID(self, runId, entityID='1', **kwargs):

        # Define query - entity is plural for these queries
        url = self.url_entity.replace('runid', runId) + 's/' + str(entityID)

        # Get the test collection
        logger.debug('getEntityID: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.get(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'getEntityID: ' + self.entity)

        return r

    # Update entity by its ID
    def putEntityByID(self, runId, entityID='1', content=None, versioning='lock', headers=None, **kwargs):

        # Define headers
        if not headers:
            headers = {'Content-type': 'application/xml'}

        # Define query - entity is plural for these queries
        url = self.url_entity.replace('runid', runId) + 's/' + str(entityID)

        # Get the test collection
        logger.debug('putEntityID: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.put(url, data=content, headers=headers, **kwargs)

        # Validate response code
        self._validateResponse(r, 'putEntityID: ' + self.entity)

        return r

    # Update entity collection
    def putEntityCollection(self, runId, content=None, headers=None, **kwargs):

        # NOT SUPPORTED YET
        self._raiseError('putEntityCollection', 'Bulk update is currently not supported by HP')

    # Delete entity Id
    def deleteEntityIdList(self, runId, entityId, **kwargs):

        # Define query - entity is plural for these queries
        url = self.url_entity.replace('runid', runId) + 's/' + entityId

        # Get the test collection
        logger.debug('deleteEntityID: ' + self.entity + ': Checking using \'' + str(url) + '\'...')

        r = self.delete(url, **kwargs)

        # Validate response code
        self._validateResponse(r, 'deleteEntityIdList: ' + self.entity)

        return r

    def dumpInfo(self):
        '''
        Get Entity full information in a (xml) dictionary
        :return
        '''

        # Dictionary
        info = dict()

        info[self.entity + '_fields'] = self.getEntityFields().content
        info[self.entity + '_lists'] = self.getEntityLists().content
        info[self.entity + '_requiredFields'] = self.getEntityDataTemplate()

        try:
            info[self.entity + '_relations'] = self.getEntityRelations().content
        except:
            logger.warning('dumpInfo: %s' % ('getEntityRelations not possible'))

        return info


class QC_Entity_TL_Test_Instance(QC_Entity):
    '''
    Class that specifies a specific type of entity - test instance
    '''

    # Initialize connection
    def __init__(self, server=None, project=None, domain=None, silent=False, session=None, proxies=None):
        # Init upper class
        super(QC_Entity_TL_Test_Instance, self).__init__('test-instance', server, project, domain, silent, session,
                                                         proxies)

        # Collection size - Max number of entities sent in a single put / post / limited to 20 because of test instances
        # that trigger the creation of test runs when status is changed
        self.collectionSize = 20


class SXml(object):
    '''
    Class that processes the standard Xml file and serves as an input to the major QC functions in QC class
    '''

    # Initialize class - input is the xml string
    def __init__(self, sxml, silent=False):

        # Silent mode - no exception is raised only messages are sent to console when using _raiseError()
        self.silent = silent

        # Xml string
        self.sxml = sxml

        # Root of xml
        self._sxmlRoot = ET.fromstring(sxml)

        # data dictionary containing all the necessary information
        self._data = {
            'test': [],
            'testset': [],
            'testinstance': [],
            'testinstancerun': []
        }

        # Testset Data
        self.testSetData = None

        # Test Instance Data
        self.testInstanceData = None

        # Test Instance Data
        self.testInstanceRunData = None

        # Test Data
        self.testData = None

        # Process xml file
        self._processXml()

    # Return testSet Data dict
    def getTestSetData(self, forceUpdate=False):

        if forceUpdate is True:

            # Process everything again
            self._processXml()

        elif self.testSetData is not None:

            # If update is not enforced and list already exists... use it!
            return self.testSetData

        # Test location list
        testSetNameList = []
        for testSet in self._data['testset']:
            # Add test location
            testSetNameList.append(testSet['name'])

        # Test location list
        testSetLocationList = []
        for testSet in self._data['testset']:
            # Add test location
            testSetLocationList.append(testSet['location'])

        # Test tags list
        testSetTagList = []
        for testSet in self._data['testset']:
            # Add test location
            testSetTagList.append(testSet['tags'])

        # Test folder list
        testSetFolderList = []
        for testSet in self._data['testset']:
            # Add test location
            testSetFolderList.append(testSet['folder'])

        # Save for future use
        self.testSetData = {
            'location': testSetLocationList,
            'tags': testSetTagList,
            'folder': testSetFolderList,
            'name': testSetNameList
        }

        return self.testSetData

    # Return test data dict
    def getTestData(self, forceUpdate=False):

        if forceUpdate is True:

            # Process everything again
            self._processXml()

        elif self.testData is not None:

            # If update is not enforced and list already exists... use it!
            return self.testData

        # Test folder list
        testFolderList = []
        # Test name list
        testNameList = []
        # Test location list
        testLocationList = []
        # Test location list
        testTagList = []
        # Test design steps tags
        testDesignStepsTagsList = []
        # Test design steps name
        testDesignStepsNameList = []

        for test in self._data['test']:
            # Add test folder
            testFolderList.append(test['folder'])
            # Add test folder
            testNameList.append(test['name'])
            # Add test location
            testLocationList.append(test['location'])
            # Add test location
            testTagList.append(test['tags'])
            # Add test run steps tags
            testDesignStepsTagsList.append(test['designsteps']['tags'])
            # Add test run steps name
            testDesignStepsNameList.append(test['designsteps']['name'])

        # Save for future use
        self.testData = {
            'location': testLocationList,
            'tags': testTagList,
            'folder': testFolderList,
            'name': testNameList,
            'designstepstags': testDesignStepsTagsList,
            'designstepsname': testDesignStepsNameList
        }

        return self.testData

    # Return test instances data in a dic
    def getTestInstancesData(self, forceUpdate=False):

        if forceUpdate is True:

            # Process everything again
            self._processXml()

        elif self.testInstanceData is not None:

            # If update is not enforced and list already exists... use it!
            return self.testInstanceData

        # Test instance info lists
        testInstanceLocationList = []
        testInstanceTagList = []
        testInstanceTestLocationList = []
        testInstanceTestNameList = []
        testInstanceTestTagsList = []
        testInstanceTestSetLocationList = []
        testInstanceTestSetTagsList = []

        for testInstance in self._data['testinstance']:
            # Add test instance location
            testInstanceLocationList.append(testInstance['location'])
            # Add test instance tag
            testInstanceTagList.append(testInstance['tags'])
            # Add test location
            testInstanceTestLocationList.append(testInstance['test']['location'])
            # Add test name
            testInstanceTestNameList.append(testInstance['test']['name'])
            # Add test tags
            testInstanceTestTagsList.append(testInstance['test']['tags'])
            # Add test set location
            testInstanceTestSetLocationList.append(testInstance['testset']['location'])
            # Add test set tags
            testInstanceTestSetTagsList.append(testInstance['testset']['tags'])

        # Save for future use
        self.testInstanceData = {
            'location': testInstanceLocationList,
            'tags': testInstanceTagList,
            'testlocation': testInstanceTestLocationList,
            'testtags': testInstanceTestTagsList,
            'testname': testInstanceTestNameList,
            'testsetlocation': testInstanceTestSetLocationList,
            'testsettags': testInstanceTestSetTagsList
        }

        return self.testInstanceData

    # Return test instances run data in a dic
    def getTestInstancesRunData(self, forceUpdate=False):

        if forceUpdate is True:

            # Process everything again
            self._processXml()

        elif self.testInstanceRunData is not None:

            # If update is not enforced and list already exists... use it!
            return self.testInstanceRunData

        # Test instance info lists
        testInstanceLocationList = []
        testInstanceTagList = []
        testInstanceTestLocationList = []
        testInstanceTestNameList = []
        testInstanceTestTagsList = []
        testInstanceTestRunTagsList = []
        testInstanceTestSetLocationList = []
        testInstanceTestSetTagsList = []

        for testInstanceRun in self._data['testinstancerun']:
            # Add test instance location
            testInstanceLocationList.append(testInstanceRun['testinstance']['location'])
            # Add test instance tag
            testInstanceTagList.append(testInstanceRun['testinstance']['tags'])
            # Add test location
            testInstanceTestLocationList.append(testInstanceRun['testinstance']['test']['location'])
            # Add test tags
            testInstanceTestTagsList.append(testInstanceRun['testinstance']['test']['tags'])
            # Add test name
            testInstanceTestNameList.append(testInstanceRun['testinstance']['test']['name'])
            # Add test set location
            testInstanceTestSetLocationList.append(testInstanceRun['testinstance']['testset']['location'])
            # Add test set tags
            testInstanceTestSetTagsList.append(testInstanceRun['testinstance']['testset']['tags'])
            # Add test run steps tags
            testInstanceTestRunTagsList.append(testInstanceRun['runsteps']['tags'])

        # Get test instance run tags
        testInstanceRunTagList = []
        for testinstancerun in self._data['testinstancerun']:
            # Add test instance run tags
            testInstanceRunTagList.append(testinstancerun['tags'])

        # Save for future use
        self.testInstanceRunData = {
            'testinstancelocation': testInstanceLocationList,
            'testinstancetags': testInstanceTagList,
            'testlocation': testInstanceTestLocationList,
            'testtags': testInstanceTestTagsList,
            'testname': testInstanceTestNameList,
            'testsetlocation': testInstanceTestSetLocationList,
            'testsettags': testInstanceTestSetTagsList,
            'runstepstags': testInstanceTestRunTagsList,
            'tags': testInstanceRunTagList
        }

        return self.testInstanceRunData

    # Process xml to populate the dataDic related to test instances present in sxml
    def _processXml(self):

        # Information needs to be updated!
        # Testset information
        dataTestset = {
            'location': None,  # List of testset locations - composed by folder path + testset name
            'tags': None,  # List of testset tags ( name, value )
            'folder': None,  # List of folder where the testset is in
            'name': None  # List with testset name
        }

        # Testset List
        testSetList = []
        testList = []
        testInstanceList = []
        testInstanceRunsList = []

        # Search for testset
        for testSet in self._sxmlRoot.findall('./test_sets/test_set'):

            # Initialize testset dict
            dataTestset['location'] = None
            dataTestset['tags'] = None
            dataTestset['folder'] = None
            dataTestset['name'] = None

            # tag dictionary
            tagsTestSet = {}
            for testSetChild in testSet:

                # Populate tag dictionary
                if testSetChild.tag != 'test_cases':
                    if testSetChild.get('tl_name') is not None:
                        tagsTestSet[testSetChild.get('tl_name')] = testSetChild.text

                # Fill test set information
                dataTestset['tags'] = tagsTestSet

            dataTestset['location'] = testSet.get('path') + '\\' + dataTestset['tags']['name']
            dataTestset['name'] = dataTestset['tags']['name']
            dataTestset['folder'] = testSet.get('path')

            # Now lets check the tests / tests instances
            testL, testInstanceL, testInstanceRunL = self._processTestCases(testSet, dataTestset)

            # Concatenate lists
            testList += testL
            testInstanceList += testInstanceL
            testInstanceRunsList += testInstanceRunL

            # Add testset to list
            testSetList.append(copy.deepcopy(dataTestset))

        self._data['test'] = testList
        self._data['testset'] = testSetList
        self._data['testinstance'] = testInstanceList
        self._data['testinstancerun'] = testInstanceRunsList

    # Process testcases in testSet element
    def _processTestCases(self, testSet, dataTestset):

        # Test information
        dataTest = {
            'location': None,  # test location - path + test name
            'tags': None,  # List of test tags ( name, value )
            'name': None,  # List of test name
            'folder': None,  # List of test path
            'designsteps': None  # List of test path
        }
        # Test instance information
        dataTestInstance = {
            'testset': None,  # testset information
            'test': None,  # test information
            'location': None,  # test instance location - path + testset + testintance name
            'tags': None  # List of test instance tags ( name, value )
        }
        # Test instance information
        dataTestInstanceRun = {
            'testinstance': None,  # test instance information
            'tags': None,  # List of test instance tags ( name, value )
            'runsteps': None  # Run steps information
        }
        # Test instance runs information
        dataTestInstanceRunSteps = {
            'tags': None  # List of run steps tags {tagX, tagY, ...}
        }
        # Test step information
        dataTestDesignSteps = {
            'tags': None,  # List of design steps tags {tagX, tagY, ...}
            'name': None  # List of design steps name tag
        }

        testList = []
        testInstanceList = []
        testInstanceRunList = []

        if testSet.find('./test_cases') is not None:

            for testCase in testSet.find('./test_cases'):

                # Initialize dicts
                dataTest['location'] = None
                dataTest['tags'] = None
                dataTest['name'] = None
                dataTest['folder'] = None
                dataTest['designsteps'] = None
                dataTestInstance['testset'] = None
                dataTestInstance['location'] = None
                dataTestInstance['test'] = None
                dataTestInstance['tags'] = None
                dataTestInstanceRun['testinstance'] = None
                dataTestInstanceRun['tags'] = None
                dataTestInstanceRun['runsteps'] = None
                dataTestInstanceRunSteps['tags'] = None
                dataTestDesignSteps['tags'] = None
                dataTestDesignSteps['name'] = None

                # test tag dictionary
                tagsTest = {}
                # test instances tag dictionary
                tagsTestInstance = {}
                # test instances tag dictionary
                tagsTestInstanceRun = {}
                # Test Instance Run Step List
                testRunStepList = []
                # Test Design Step List
                testDesignStepList = []
                # Name Design Step List
                nameDesignStepList = []

                for testCaseChild in testCase:

                    # Populate tag dictionary for test instance
                    if testCaseChild.tag != 'test_case_steps' and testCaseChild.tag != 'test_case_run':

                        # Check if field contains multiple values or single value - no value field
                        if testCaseChild.find('value') is None:

                            # Populate test instance
                            if testCaseChild.get('tl_name') is not None:
                                tagsTestInstance[testCaseChild.get('tl_name')] = testCaseChild.text

                            # Populate test
                            if testCaseChild.get('tp_name') is not None:
                                tagsTest[testCaseChild.get('tp_name')] = testCaseChild.text

                        else:
                            # Multiple values found
                            testValue = []
                            testInstanceValue = []

                            # Populate test instance
                            if testCaseChild.get('tl_name') is not None:

                                for valueField in testCaseChild.findall('value'):
                                    testInstanceValue.append(valueField.text)

                                tagsTestInstance[testCaseChild.get('tl_name')] = testInstanceValue

                            # Populate test
                            if testCaseChild.get('tp_name') is not None:

                                for valueField in testCaseChild.findall('value'):
                                    testValue.append(valueField.text)

                                tagsTest[testCaseChild.get('tp_name')] = testValue

                    # Populate tag dictionary for test instance run
                    elif testCaseChild.tag == 'test_case_run':

                        for testInstanceRunChild in testCaseChild:

                            # Check if field contains multiple values or single value - no value field
                            if testInstanceRunChild.find('value') is None:

                                # Populate test instance run
                                if testInstanceRunChild.get('tl_name') is not None:
                                    tagsTestInstanceRun[testInstanceRunChild.get('tl_name')] = testInstanceRunChild.text

                            else:
                                # Multiple values found
                                testInstanceRunValue = []

                                # Populate test instance Run
                                if testInstanceRunChild.get('tl_name') is not None:

                                    for valueField in testInstanceRunChild.findall('value'):
                                        testInstanceRunValue.append(valueField.text)

                                    tagsTestInstanceRun[testInstanceRunChild.get('tl_name')] = testInstanceRunValue

                    # Now lets look at the test run steps
                    elif testCaseChild.tag == 'test_case_steps':

                        testRunStepListTemp, testDesignStepListTemp, nameDesignStep = self._processTestCaseSteps(
                            testCaseChild)

                        testRunStepList += testRunStepListTemp
                        testDesignStepList += testDesignStepListTemp
                        nameDesignStepList += nameDesignStep

                # Update data
                dataTestDesignSteps['tags'] = testDesignStepList
                dataTestDesignSteps['name'] = nameDesignStepList

                dataTest['tags'] = tagsTest
                dataTest['location'] = testCase.get('path') + '\\' + dataTest['tags']['name']
                dataTest['name'] = dataTest['tags']['name']
                dataTest['folder'] = testCase.get('path')
                dataTest['designsteps'] = dataTestDesignSteps

                dataTestInstance['tags'] = tagsTestInstance
                dataTestInstance['location'] = dataTestset['location'] + '\\' + dataTest['tags']['name']
                dataTestInstance['testset'] = dataTestset
                dataTestInstance['test'] = dataTest

                dataTestInstanceRunSteps['tags'] = testRunStepList

                dataTestInstanceRun['tags'] = tagsTestInstanceRun
                dataTestInstanceRun['testinstance'] = dataTestInstance
                dataTestInstanceRun['runsteps'] = dataTestInstanceRunSteps  # List with all run steps data

                # Add caught values to respective lists
                testList.append(copy.deepcopy(dataTest))
                testInstanceList.append(copy.deepcopy(dataTestInstance))
                testInstanceRunList.append(copy.deepcopy(dataTestInstanceRun))

        return testList, testInstanceList, testInstanceRunList

    # Process Test Case Steps in testStepNode element
    def _processTestCaseSteps(self, testStepsNode):

        # testRunStep List
        tagsRunStepList = []
        # testDesignStep List
        tagsDesignStepList = []
        # test design steps name list
        nameDesignSteps = []

        # Process test steps
        for testStep in testStepsNode:

            # test instances tag dictionary
            tagsRunSteps = {}
            # test instances tag dictionary
            tagsDesignSteps = {}

            for testStepChild in testStep:

                # Check if field contains multiple values or single value - no value field
                if testStepChild.find('value') is None:

                    # Populate test instance run
                    if testStepChild.get('tl_name') is not None:
                        tagsRunSteps[testStepChild.get('tl_name')] = testStepChild.text

                    # Populate test instance run
                    if testStepChild.get('tp_name') is not None:
                        tagsDesignSteps[testStepChild.get('tp_name')] = testStepChild.text

                else:
                    # Multiple values found
                    testRunStepValue = []
                    # Multiple values found
                    testDesignStepValue = []

                    # Populate test instance Run
                    if testStepChild.get('tl_name') is not None:

                        for valueField in testStepChild.findall('value'):
                            testRunStepValue.append(valueField.text)

                        tagsRunSteps[testStepChild.get('tl_name')] = testRunStepValue

                    # Populate test instance Run
                    if testStepChild.get('tp_name') is not None:

                        for valueField in testStepChild.findall('value'):
                            testDesignStepValue.append(valueField.text)

                        tagsDesignSteps[testStepChild.get('tp_name')] = testDesignStepValue

            # Save run step to list
            tagsRunStepList.append(tagsRunSteps)
            tagsDesignStepList.append(tagsDesignSteps)

            if len(tagsDesignSteps) != 0:
                nameDesignSteps.append(tagsDesignSteps['name'])

        return tagsRunStepList, tagsDesignStepList, nameDesignSteps

    # Raise Error
    def _raiseError(self, function='None', message=''):

        if self.silent:
            logger.error(function + ': ' + message)

        # Slient exit?
        if not self.silent:
            raise SXmlError('Error!', function + ': ' + message)


class QCError(Exception):
    '''
    Class to handle specific error when using class QC
    '''

    def __init__(self, expr, msg):
        '''
        Exception raised for errors when using QC

        :param expr: input expression in which the error occurred
        :param msg: explanation of the error
        :return:
        '''
        self.expr = expr
        self.msg = msg


class QCEntityError(Exception):
    '''
    Class to handle specific error when using class QC entities
    '''

    def __init__(self, expr, msg):
        '''
        Exception raised for errors when using QC

        :param expr: input expression in which the error occurred
        :param msg: explanation of the error
        :return:
        '''
        self.expr = expr
        self.msg = msg


class SXmlError(Exception):
    '''
    Class to handle especific error when using class SXml
    '''

    def __init__(self, expr, msg):
        '''
        Exception raised for errors when using QC

        :param expr: input expression in which the error occurred
        :param msg: explanation of the error
        :return:
        '''
        self.expr = expr
        self.msg = msg


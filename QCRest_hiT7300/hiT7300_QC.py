
__author__ = 'Rodolfo Andrade'

import base64
import itertools
import logging
import re

from QCRest import QC

logger = logging.getLogger('QCRest')

class hiT7300_QC(QC):
    '''
    hiT7300 specific class
    '''

    # Initialize connection
    def __init__(self, server=None, project=None, domain=None, silent=False, session=None, proxies=None, release=None):

        releaseInfo = {
            '5.40.xx': {
                'server': 'http://qc.intra.coriant.com:8090',
                'project': 'hiT7300_530x',
                'domain': 'ON',
                'user': base64.b64decode('Njg1MDAzNTM='),
                'passwd': base64.b64decode('MTIzUVdFYXNkMDQ='),
            },
            '5.50.xx': {
                'server': 'http://qc.intra.coriant.com:8090',
                'project': 'hiT7300_550x',
                'domain': 'ON',
                'user': base64.b64decode('Njg1MDAzNTM='),
                'passwd': base64.b64decode('MTIzUVdFYXNkMDQ='),
            },
            'SANDBOX': {
                'server': 'http://qc.intra.coriant.com:8090',
                'project': 'SANDBOX_hiT7300_530x',
                'domain': 'SANDBOX',
                'user': base64.b64decode('Njg1MDAzNTM='),
                'passwd': base64.b64decode('MTIzUVdFYXNkMDQ='),
            }
        }

        self.releaseDict = None

        # Configure default values
        if release is not None:
            try:
                self.releaseDict = releaseInfo[release]

                server = self.releaseDict['server']
                project = self.releaseDict['project']
                domain = self.releaseDict['domain']

            except KeyError as e:
                logger.error('Release parameter %s passed in hiT7300_QC is incorrect! Choose one of the %s.' % (release, releaseInfo.keys()))
                raise e

        self.qcDataInfo = {
            # Needs to be updated
            'qcRequirementTypes': {
                'Undefined': '0',
                'Folder': '1',
                'Group': '2',
                'Functional': '3',
                'Business': '4',
                'Testing': '5',
                'Performance': '6',
                'Business Model': '7',
                'Non-Functional': '8',
            }
        }

        super(hiT7300_QC, self).__init__(server, project, domain, silent, session, proxies)

    def login(self, user=None, passwd=None, **kwargs):

        if self.releaseDict is not None and user is None:
            logger.info('Using default user!')

            user = self.releaseDict['user']
            passwd = self.releaseDict['passwd']

        # login using default user
        login_r = QC.login(self, user, passwd, **kwargs)

        return login_r

    def syncDefects(self, fieldDataList, jiraKey, deleteReq=True):

        req = []

        # First check the defects that exist
        # Build Query
        r = self.Defects.getEntity('name,id,%s' % jiraKey)
        xml = self._getXmlFromRequestQueryList(r)

        defectsInfoList = self.Defects.getEntityDataCollectionFieldValueList(
            ['id','name',jiraKey], xml)

        defectsInfoXml = {
            'id': defectsInfoList[0],
            'name': defectsInfoList[1],
            jiraKey: defectsInfoList[2],
            }

        # Split these in new, old that need to be updated and old that need to be deleted
        # The match will be done by the HflId or name
        defInfoToBeUpdated = {'id':[], 'tags':[], 'name':[]}
        defInfoToBeCreated = {'tags':[], 'name':[]}

        # requirementIdsToBeDeleted = defectsInfoXml['id'][:]

        for fieldData in fieldDataList:

            tagsList = {}

            # Compare using the HFLId and if they exist mark them to be updated ( and by name )
            if fieldData[jiraKey] in defectsInfoXml[jiraKey] or fieldData['name'] in defectsInfoXml['name']:

                idx = None
                if fieldData[jiraKey] in defectsInfoXml[jiraKey]:
                    idx = defectsInfoXml[jiraKey].index(fieldData[jiraKey])

                else:
                    idx = defectsInfoXml['name'].index(fieldData['name'])

                defInfoToBeUpdated['id'].append(defectsInfoXml['id'][idx])

                for k,v in fieldData.iteritems():

                    if k == 'name':
                        defInfoToBeUpdated['name'].append(v)

                        # if v in defectsInfoXml['name']:
                        #     idx = requirementNamesToBeDeleted.index(v)
                        #
                        #     del(requirementNamesToBeDeleted[idx])
                        #     del(requirementIdsToBeDeleted[idx])

                    elif k == 'attachmentUrl':
                        # Attachments need to be handled apart
                        fieldData['attachmentUrl']['create'] = False
                        pass

                    else:
                        tagsList[k] = v

                defInfoToBeUpdated['tags'].append(tagsList)

            else:
                # These are new and need to be created
                for k,v in fieldData.iteritems():

                    if k == 'name':
                        defInfoToBeCreated['name'].append(v)

                    elif k == 'attachmentUrl':
                        # Attachments need to be handled apart
                        fieldData['attachmentUrl']['create'] = True
                        pass

                    else:
                        tagsList[k] = v

                defInfoToBeCreated['tags'].append(tagsList)

        # Add the missing defects
        req.append(self._createDefectList(defInfoToBeCreated['tags'], defInfoToBeCreated['name']))


        # Update the defects
        req.append(self._updateDefectList(defInfoToBeUpdated['tags'], defInfoToBeUpdated['id'],
                                          defInfoToBeUpdated['name']))

        # # Delete requirements that do not exist in Jira
        # if deleteReq:
        #     req.append(self._deleteRequirementList(requirementIdsToBeDeleted, requirementNamesToBeDeleted))

        # Now lets take care of attachments

        #  First get requirement IDs
        # Build Query
        r = self.Defects.getEntity('id,' + jiraKey)
        xml = self._getXmlFromRequestQueryList(r)

        defectsInfoList = self.Defects.getEntityDataCollectionFieldValueList(['id', jiraKey], xml)

        defectsInfoXml = {
            'id': defectsInfoList[0],
            jiraKey: defectsInfoList[1],
        }

        # Lets create only the new ones - the others are fixed
        logger.info('syncDefects: Adding attachments...')
        for fieldData in fieldDataList:

            idx = defectsInfoXml[jiraKey].index(fieldData[jiraKey])

            reqId = defectsInfoXml['id'][idx]

            # Compare using the reqIdQC and if they exist mark them to be updated ( and by name )
            if fieldData[jiraKey] in defectsInfoXml[jiraKey] and fieldData['attachmentUrl']['create']:
                self.Defects.postEntityAttachmentByID(reqId, fieldData['attachmentUrl']['fileName'],
                                                           fieldData['attachmentUrl']['description'],
                                                           fieldData['attachmentUrl']['data'])
        logger.info('syncDefects: Adding attachments...done')

        return

    def syncRequirements(self, fieldDataList, reqIdQC, deleteReq=True):

        req = []

        # First check the requirements that exist
        # Build Query
        r = self.Requirements.getEntity('name,id,' + reqIdQC + ',parent-id,target-rcyc,target-rel,type-id')
        xml = self._getXmlFromRequestQueryList(r)
        requirementInfoList = self.Requirements.getEntityDataCollectionFieldValueList(
            ['id', 'name', reqIdQC, 'parent-id', 'target-rcyc', 'target-rel', 'type-id'], xml)

        requirementInfoXmlQC = {
            'id': requirementInfoList[0],
            'name': requirementInfoList[1],
            reqIdQC: requirementInfoList[2],
            'parent-id': requirementInfoList[3],
            'target-rcyc': requirementInfoList[4],          # Target Cycle
            'target-rel': requirementInfoList[5],           # Release
            'type-id': requirementInfoList[6],  # Requirement Type
            }

        # Now lets get the relation between target cycles and releases
        # Build Query
        r = self.ReleaseCycles.getEntity('name,id,parent-id')
        xml = self._getXmlFromRequestQueryList(r)
        releaseCycleInfoList = self.ReleaseCycles.getEntityDataCollectionFieldValueList(
            ['id','parent-id','name'], xml)

        targetCyclesAndReleasesDict = dict(zip(releaseCycleInfoList[0], releaseCycleInfoList[1]))

        # Split these in new, old that need to be updated and old that need to be deleted
        # The match will be done by the HflId or name
        reqInfoToBeUpdated = {'id':[], 'path':[], 'tags':[], 'folderId':[], 'name':[]}
        reqInfoToBeCreated = {'path':[], 'tags':[], 'name':[], 'folderId':[]}

        # requirementIdsToBeDeleted = requirementInfoXmlQC['id'][:]

        attachmentList = []

        for fieldData in fieldDataList:

            # If it is a new requirement force requirement type to testing - Needs to be updated if req. exists
            tagsList = {'type-id': self.qcDataInfo['qcRequirementTypes']['Testing']}

            # Compare using the reqIdQC and if they exist mark them to be updated ( and by name )
            if fieldData[reqIdQC] in requirementInfoXmlQC[reqIdQC] or fieldData['name'] in requirementInfoXmlQC['name']:

                idx = None
                if fieldData[reqIdQC] in requirementInfoXmlQC[reqIdQC]:
                    idx = requirementInfoXmlQC[reqIdQC].index(fieldData[reqIdQC])

                else:
                    idx = requirementInfoXmlQC['name'].index(fieldData['name'])

                # Update requirement type
                tagsList['type-id'] = requirementInfoXmlQC['type-id'][idx]

                reqInfoToBeUpdated['id'].append(requirementInfoXmlQC['id'][idx])
                reqInfoToBeUpdated['folderId'].append(requirementInfoXmlQC['parent-id'][idx])

                # Check if release from jira to be updated is consistent with TC in QC requirement
                # TC to be sent in update
                tagsList['target-rcyc'] = []

                # Check for each release in QC if these will be available or not after update
                if requirementInfoXmlQC['target-rcyc'][idx] is not None:

                    # This is to avoid issues with string
                    if type(requirementInfoXmlQC['target-rcyc'][idx]) is not list:
                        requirementInfoXmlQC['target-rcyc'][idx] = [requirementInfoXmlQC['target-rcyc'][idx]]

                    tagsList['target-rcyc'] = list(requirementInfoXmlQC['target-rcyc'][idx])

                    # This is to avoid issues with string
                    if type(requirementInfoXmlQC['target-rel'][idx]) is not list:
                        requirementInfoXmlQC['target-rel'][idx] = [requirementInfoXmlQC['target-rel'][idx]]

                    for relQC in requirementInfoXmlQC['target-rel'][idx]:

                        if relQC not in fieldData['target-rel']:

                            # Lets look at the TC and check which are still valid ( their release is selected )
                            if requirementInfoXmlQC['target-rcyc'][idx] is not None:

                                # This is to avoid issues with strings
                                if type(requirementInfoXmlQC['target-rcyc'][idx]) is not list:
                                    requirementInfoXmlQC['target-rcyc'][idx] = [requirementInfoXmlQC['target-rcyc'][idx]]

                                for tcQC in requirementInfoXmlQC['target-rcyc'][idx]:

                                    if targetCyclesAndReleasesDict[tcQC] == relQC:

                                        if type(tagsList['target-rcyc']) is str:
                                            tagsList['target-rcyc'] = None
                                        else:
                                            tagsList['target-rcyc'].remove(tcQC)

                if len(tagsList['target-rcyc']) == 0:
                    tagsList['target-rcyc'] = None

                for k,v in fieldData.iteritems():

                    if k == 'path':
                        reqInfoToBeUpdated['path'].append(v)

                    elif k == 'name':
                        reqInfoToBeUpdated['name'].append(v)

                        # if v in requirementInfoXmlQC['name']:
                        #     idx = requirementNamesToBeDeleted.index(v)
                        #
                        #     del(requirementNamesToBeDeleted[idx])
                        #     del(requirementIdsToBeDeleted[idx])

                    elif k == 'attachmentUrl':
                        # Attachments need to be handled apart
                        pass

                    else:
                        tagsList[k] = v

                reqInfoToBeUpdated['tags'].append(tagsList)

            elif fieldData[reqIdQC] is None or fieldData[reqIdQC] is '':

                logger.warning('syncRequirements: Jira Issue \'%s\' does not have a hfl ID!' % (fieldData['name']))

            else:
                # These are new and need to be created
                for k,v in fieldData.iteritems():

                    if k == 'path':

                        reqInfoToBeCreated['path'].append(v)

                    elif k == 'name':
                        reqInfoToBeCreated['name'].append(v)

                    elif k == 'attachmentUrl':
                        # Attachments need to be handled apart
                        pass

                    else:
                        tagsList[k] = v

                reqInfoToBeCreated['tags'].append(tagsList)

        # Remove Requirements
        for path in reqInfoToBeCreated['path']:

            if 'Requirements' not in path:
                # Raise exception
                self._raiseError('_getIdRequirementFolderFromPathList',
                                 'The requirement path must always start with Requirements: %s' % path)

        reqInfoToBeCreated['path'] = [ e[13:] for e in reqInfoToBeCreated['path']]

        if len(reqInfoToBeCreated['name']) > 0:
            reqInfoToBeCreated['folderId'] = self._getIdRequirementFolderFromPathList(reqInfoToBeCreated['path'])

        # Add the missing requirements
        req.append(self._createRequirementList(reqInfoToBeCreated['folderId'], reqInfoToBeCreated['tags'],
                                               reqInfoToBeCreated['path'], reqInfoToBeCreated['name']))

        # Update the requirement
        req.append(self._updateRequirementList(reqInfoToBeUpdated['folderId'], reqInfoToBeUpdated['tags'],
                                               reqInfoToBeUpdated['id'], reqInfoToBeUpdated['name']))

        # # Delete requirements that do not exist in Jira
        # if deleteReq:
        #     req.append(self._deleteRequirementList(requirementIdsToBeDeleted, requirementNamesToBeDeleted))

        # Now lets take care of attachments

        #  First get requirement IDs
        # Build Query
        r = self.Requirements.getEntity('name,id,' + reqIdQC + ',parent-id')
        xml = self._getXmlFromRequestQueryList(r)

        requirementInfoList = self.Requirements.getEntityDataCollectionFieldValueList(
            ['id',reqIdQC], xml)

        requirementInfoXmlQC = {
            'id': requirementInfoList[0],
            reqIdQC: requirementInfoList[1],
            }

        for fieldData in fieldDataList:

            idx = requirementInfoXmlQC[reqIdQC].index(fieldData[reqIdQC])

            reqId = requirementInfoXmlQC['id'][idx]

            # Compare using the reqIdQC and if they exist mark them to be updated ( and by name )
            if fieldData[reqIdQC] in requirementInfoXmlQC[reqIdQC]:
                self.Requirements.postEntityAttachmentByID(reqId, fieldData['attachmentUrl']['fileName'],
                                                           fieldData['attachmentUrl']['description'],
                                                           fieldData['attachmentUrl']['data'])

        return

    def getJiraRFJiraFRRelationFromQC(self, release, reqIdQC, defIdQC, filterQCType):

        # Get Release id
        idReleaseQuery = self._getQueryListOrAnd(['name'], [release])
        r = self.Releases.getEntityQueryList(idReleaseQuery, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        releaseIdList = self.Releases.getEntityDataCollectionFieldValueList(['id'], xml)[0]

        # Get all target cycles associated with this release
        idReleaseCyclesQuery = self._getQueryListOrAnd(['parent-id'], [releaseIdList])
        r = self.ReleaseCycles.getEntityQueryList(idReleaseCyclesQuery, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        releaseCyclesIdList = self.ReleaseCycles.getEntityDataCollectionFieldValueList(['id'], xml)[0]

        # Get Requirements associated with specific release
        r = self.Requirements.getEntity('id,target-rcyc,type-id,' + reqIdQC)
        xml = self._getXmlFromRequestQueryList(r)
        idRequirementsInfo = self.Requirements.getEntityDataCollectionFieldValueList(
            ['id', 'target-rcyc', reqIdQC, 'type-id'], xml)
        idRequirements = idRequirementsInfo[0]
        idRequirementsTargetCycle = idRequirementsInfo[1]
        idRequirementsJiraId = idRequirementsInfo[2]
        idRequirementsType = idRequirementsInfo[3]

        data = []

        # Now for each Requirement we will get the tests that are associated with specific target cycles
        for reqId, tcList, jiraId, reqType, in itertools.izip(
                idRequirements, idRequirementsTargetCycle, idRequirementsJiraId, idRequirementsType):

            elem = {'jiraId': jiraId, 'faultReportJiraIdList': []}

            # Requirement is not of the correct type - do not sync
            if reqType not in filterQCType:
                continue

            # if no tcList is defined skip
            if tcList is None:
                continue

            # TC can be a list or str
            if type(tcList) is str:
                tcList = [tcList]

            # We need to filter the TC per release or we might end up up with TC that are not from this release
            tcList = list(set(tcList).intersection(releaseCyclesIdList))

            # If no tc match's, skip
            if len(tcList) == 0:
                continue

            # Get tests
            idTestsQuery = self._getQueryListOrAnd(
                ['requirement.id', 'test-instance.assign-rcyc'], [[reqId], tcList])
            r = self.TestPlanTests.getEntityQueryList(idTestsQuery, 'id')
            xml = self._getXmlFromRequestQueryList(r)
            idTests = self.TestPlanTests.getEntityDataCollectionFieldValueList(['id'], xml)[0]

            # Get defects
            r = self.Defects.getEntity('id')
            xml = self._getXmlFromRequestQueryList(r)
            defectsIdList = self.Defects.getEntityDataCollectionFieldValueList(['id'], xml)[0]

            # Get test instances that have a defect associated and are related to the req in question
            idTestInstanceQuery = self._getQueryListOrAnd(['defect.id', 'test.id'], [defectsIdList, idTests])
            r = self.TestLabTestInstances.getEntityQueryList(idTestInstanceQuery, 'id')
            xml = self._getXmlFromRequestQueryList(r)
            testInstancesIdList = self.TestLabTestInstances.getEntityDataCollectionFieldValueList(['id'], xml)[0]

            # Now for each test instance lets see the defects associated
            for tId in testInstancesIdList:

                # Get defects associated
                idDefectQuery = self._getQueryListOrAnd(['test-instance.id'], [[tId]])
                r = self.Defects.getEntityQueryList(idDefectQuery, 'id,' + defIdQC)
                xml = self._getXmlFromRequestQueryList(r)
                defectJiraIdList = self.Defects.getEntityDataCollectionFieldValueList([defIdQC], xml)[0]

                for defectJiraId in defectJiraIdList:
                    elem['faultReportJiraIdList'].append(defectJiraId)

            elem['faultReportJiraIdList'] = list(set(elem['faultReportJiraIdList']))

            if len(elem['faultReportJiraIdList']) > 0:
                data.append(elem)

        return data

    def getReleaseCycleProgressFromJiraId(self, release, reqIdQC, filterQCType):

        # Function to recursively join Requirements
        # elem = {'idReq': None, 'idParent': None, 'idQC': None, 'testStatus': {'Passed': 0, 'Failed':0, 'Total':0}}
        def _aggregateRequirements(idReq, elem, data):

            # If this is not a 'valid' requirement make it count 0
            if not elem['reqTestStatus']:
                elem['testStatus'] = {'Passed': 0, 'Failed': 0, 'Total': 0}

            # Find from the list passed all the req that have as parent the target req id
            for dataElem in data:

                # Save the ones that are child and check if these have sub Req
                if dataElem['idParent'] == idReq:
                    testStatus = _aggregateRequirements(dataElem['idReq'], dataElem, data)

                    elem['testStatus']['Passed'] += testStatus['Passed']
                    elem['testStatus']['Failed'] += testStatus['Failed']
                    elem['testStatus']['Total'] += testStatus['Total']

            return elem['testStatus']

        # Get Release id
        idReleaseQuery = self._getQueryListOrAnd(['name'], [release])
        r = self.Releases.getEntityQueryList(idReleaseQuery, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        releaseIdList = self.Releases.getEntityDataCollectionFieldValueList(['id'], xml)[0]

        # Get all target cycles associated with this release
        idReleaseCyclesQuery = self._getQueryListOrAnd(['parent-id'], [releaseIdList])
        r = self.ReleaseCycles.getEntityQueryList(idReleaseCyclesQuery, 'id')
        xml = self._getXmlFromRequestQueryList(r)
        releaseCyclesIdList = self.ReleaseCycles.getEntityDataCollectionFieldValueList(['id'], xml)[0]

        # Get Requirements associated with specific release
        r = self.Requirements.getEntity('id,target-rcyc,parent-id,type-id,target-rel,' + reqIdQC)
        xml = self._getXmlFromRequestQueryList(r)
        idRequirementsInfo = self.Requirements.getEntityDataCollectionFieldValueList(
            ['id', 'target-rcyc', 'parent-id', reqIdQC, 'type-id', 'target-rel'], xml)
        idRequirements = idRequirementsInfo[0]
        idRequirementsTargetCycle = idRequirementsInfo[1]
        idRequirementsParent = idRequirementsInfo[2]
        idRequirementsIdQC = idRequirementsInfo[3]
        idRequirementsType = idRequirementsInfo[4]
        idRequirementsRelease = idRequirementsInfo[5]

        data = []

        uniqueTestInstanceIdList = []

        # Now for each Requirement we will get the tests that are associated with specific target cycles
        for reqId, tcList, idQC, idParent, reqType, reqRel in itertools.izip(
                idRequirements, idRequirementsTargetCycle, idRequirementsIdQC, idRequirementsParent,
                idRequirementsType, idRequirementsRelease):

            elem = {
                'idReq': None, 'idParent': None, 'idQC': None, 'testStatus': {'Passed': 0, 'Failed': 0, 'Total': 0},
                'reqType': None, 'reqRel': None, 'reqSync': False, 'reqTestStatus': False,
            }

            elem['idReq'] = reqId
            elem['idParent'] = idParent
            elem['idQC'] = idQC
            elem['reqType'] = reqType
            elem['reqRel'] = reqRel if type(reqRel) is list else [reqRel]

            # Release to be taken into account?
            relVal = not set(elem['reqRel']).isdisjoint(releaseIdList)

            elem['reqSync'] = True if elem['idQC'] and relVal else False
            elem['reqTestStatus'] = False if elem['reqType'] not in filterQCType or not relVal else True

            # if no tcList is defined skip
            if tcList is None:
                data.append(elem)
                continue

            # TC can be a list or str
            if type(tcList) is str:
                tcList = [tcList]

            # We need to filter the TC per release or we might end up up with TC that are not from this release
            tcList = list(set(tcList).intersection(releaseCyclesIdList))

            # If no tc match's skip
            if len(tcList) == 0:
                data.append(elem)
                continue

            # Get tests
            idTestsQuery = self._getQueryListOrAnd(
                ['requirement.id', 'test-instance.assign-rcyc'], [[reqId], tcList])
            r = self.TestPlanTests.getEntityQueryList(idTestsQuery, 'id')
            xml = self._getXmlFromRequestQueryList(r)
            idTests = self.TestPlanTests.getEntityDataCollectionFieldValueList(['id'], xml)[0]

            # Get test instances status
            idTestInstanceQuery = self._getQueryListOrAnd(['test.id', 'assign-rcyc'],
                                                          [idTests, tcList])
            r = self.TestLabTestInstances.getEntityQueryList(idTestInstanceQuery, 'status,id')
            xml = self._getXmlFromRequestQueryList(r)
            testInstancesData = self.TestLabTestInstances.getEntityDataCollectionFieldValueList(['status', 'id'], xml)

            testInstancesStatus = testInstancesData[0]
            testInstancesId = testInstancesData[1]

            uniqueTestInstanceIdList = list(set(testInstancesId + uniqueTestInstanceIdList))

            # For each target cycle, extract corresponding info
            for tiSt in testInstancesStatus:

                if tiSt == 'Passed':
                    elem['testStatus']['Passed'] += 1
                    elem['testStatus']['Total'] += 1

                elif tiSt == 'Failed':
                    elem['testStatus']['Failed'] += 1
                    elem['testStatus']['Total'] += 1

                elif tiSt == 'No Run':
                    elem['testStatus']['Total'] += 1

                else:
                    elem['testStatus']['Total'] += 1

            data.append(elem)

        # Sum Req info with sub requirements
        requirements = {}
        for elem in data:
            if elem['reqSync']:
                testStatus = _aggregateRequirements(elem['idReq'], elem, data)
                requirements[elem['idQC']] = testStatus

        # Get Global test instances status
        idTestInstanceQuery = self._getQueryListOrAnd(['id'], [uniqueTestInstanceIdList])
        r = self.TestLabTestInstances.getEntityQueryList(idTestInstanceQuery, 'status,id')
        xml = self._getXmlFromRequestQueryList(r)
        testInstancesStatusList = self.TestLabTestInstances.getEntityDataCollectionFieldValueList(['status'], xml)[0]

        globalTestInstancesStatus = {'Passed': 0, 'Failed': 0, 'Total': 0}

        for testInstancesStatus in testInstancesStatusList:

            if testInstancesStatus == 'Passed':
                globalTestInstancesStatus['Passed'] += 1
                globalTestInstancesStatus['Total'] += 1

            elif testInstancesStatus == 'Failed':
                globalTestInstancesStatus['Failed'] += 1
                globalTestInstancesStatus['Total'] += 1

            elif testInstancesStatus == 'No Run':
                globalTestInstancesStatus['Total'] += 1

            else:
                globalTestInstancesStatus['Total'] += 1

        return requirements, globalTestInstancesStatus

    def addRequirement(self, sxml, updateReqIfExists=True, ignoreReqIfExists=False):
        # Todo Broken - do not use
        '''
        Add requirements defined in sxml file #ToDo Currently info is passed through a dict with a list of location,
        folder, name and tags

        update      ignore
        True          X         Update requirement if it exists (Default)
        False       False       Replace requirement if they exist (delete and create)
        False       True        Do nothing to requirement if they exist

        :param sxml: SXML
        :param updateReqIfExists: See function description
        :param ignoreReqIfExists: See function description
        :return:
        '''

        logger.info('addRequirement: Start...')
        logger.debug('addRequirement: updateReqIfExists: %s' % updateReqIfExists)
        logger.debug('addRequirement: ignoreReqIfExists: %s' % ignoreReqIfExists)

        # Get list of req location
        listReqLocationXml = sxml['location']
        # Get list of req folder
        listReqPathXml = sxml['folder']
        # Get list of req name
        listReqNameXml = sxml['name']
        # Get list of req tags
        listReqTagsXml = sxml['tags']

        # Remove duplicates
        listReqInfo = {'location':[], 'path':[], 'name':[], 'tags':[]}

        # Remove repeated req and just keep the first
        for testLocation, testPath, testName, testTags in itertools.izip(
                listReqLocationXml, listReqPathXml, listReqNameXml, listReqTagsXml):

            if testLocation not in listReqInfo['location']:

                listReqInfo['location'].append(testLocation)
                listReqInfo['path'].append(testPath)
                listReqInfo['name'].append(testName)
                listReqInfo['tags'].append(testTags)

            else:
                try:
                    logger.warning('addRequirement: Found duplicated requirement! '
                                   'Discarding repeated entry %s' % testLocation)
                except:
                    pass

        # Get Ids from req in test plan
        listReqFolderIds = self._getIdRequirementFolderFromPathList(listReqInfo['path'])

        # First get the list of req that exist or not
        listReqId = self._getIdRequirementFromReqFolderIdReqName(listReqFolderIds, listReqInfo['name'])

        # Create two lists one for the ones that exist and another for the ones that need to be created
        listReqNew = {'path':[], 'tags':[], 'name':[], 'folderId':[]}
        listReqOld = {'tags':[], 'name':[], 'folderId':[]}

        # Populate them
        for index, id in enumerate(listReqId):

            # If id is not None it already exists
            if id:
                # Get list of old test tags
                listReqOld['tags'].append(listReqInfo['tags'][index])
                # Get list of old test names
                listReqOld['name'].append(listReqInfo['name'][index])
                # List of old test folder id
                listReqOld['folderId'].append(listReqFolderIds[index])
            else:
                # Get list of old test tags
                listReqNew['tags'].append(listReqInfo['tags'][index])
                # Get list of old test names
                listReqNew['name'].append(listReqInfo['name'][index])
                # List of old test folder id
                listReqNew['folderId'].append(listReqFolderIds[index])
                # Get list of new test folder
                listReqNew['path'].append(listReqInfo['path'][index])

        # Update test if it exists and remove elements that do not exist -> None
        listReqId = [elem for elem in listReqId if elem]
        listReqOld['id'] = [elem for elem in listReqId if elem]

        # Requests list
        r = []

        # Check if test sets exist and update them if necessary or not...
        if updateReqIfExists is True:
            # Update tests that already exist
            r.append(self._updateRequirementList(listReqOld['folderId'], listReqOld['tags'], listReqId,
                                                 listReqOld['name']))

            # Create missing tests
            r.append(self._createRequirementList(listReqNew['folderId'], listReqNew['tags'], listReqNew['path'],
                                                 listReqNew['name']))

        elif updateReqIfExists is False and ignoreReqIfExists is True:
            # Do nothing to test if they exist and create missing tests
            r.append(self._createRequirementList(listReqNew['folderId'], listReqNew['tags'], listReqNew['path'],
                                                 listReqNew['name']))

        elif updateReqIfExists is False and ignoreReqIfExists is False:
            # Replace test if they exist (delete and create)
            r.append(self._deleteRequirementList(listReqOld['id'], listReqOld['name']))

            # Create missing tests
            r.append(self._createRequirementList(listReqFolderIds, listReqInfo['tags'], listReqInfo['path'],
                                                 listReqInfo['name']))

        logger.debug('addRequirement: return: %s' % r)
        logger.info('addRequirement: ...done!')

        return r

    def getCSVWithRunsFromTargetCycle(self, qcRelease, releaseName=None):

        runList = []

        if releaseName is None:

            print "Getting ALL RUNS"
            # Get all runs
            r = self.TestLabRuns.getEntity('id,name,status,assign-rcyc,test-id,testcycl-id')

            xml = self._getXmlFromRequestQueryList(r)

            runList = self.TestLabRuns.getEntityDataCollectionFieldValueList(
                ['id', 'name', 'status', 'testcycl-id'], xml)

        else:

            print "Getting only " + releaseName + " RUNS"
            # Get all runs from target release
            query = self._getQueryListOrAnd(['user-03'], [[releaseName]])

            r = self.TestLabRuns.getEntityQueryList(query, 'id,name,status,assign-rcyc,test-id,testcycl-id')

            xml = self._getXmlFromRequestQueryList(r)

            runList = self.TestLabRuns.getEntityDataCollectionFieldValueList(
                ['id', 'name', 'status', 'testcycl-id'], xml)

        runIdList = runList[0]
        runNameList = runList[1]
        runStatusList = runList[2]
        testInstanceIdList = runList[3]

        # Get id of Release
        idReleaseQuery = self._getQueryListOrAnd(['name'], [[qcRelease]])

        r = self.Releases.getEntityQueryList(idReleaseQuery, 'id')

        xml = self._getXmlFromRequestQueryList(r)

        idRelease = self.Releases.getEntityDataCollectionFieldValue('id', xml)

        # Get all target cycles associated with release
        query = self._getQueryListOrAnd(['parent-id'], [[idRelease[0]]])

        r = self.ReleaseCycles.getEntityQueryList(query, 'name,id')

        xml = self._getXmlFromRequestQueryList(r)

        releaseCycleList = self.ReleaseCycles.getEntityDataCollectionFieldValueList(
            ['id', 'name'], xml)

        idTargetCyclesXml = releaseCycleList[0]
        nameTargetCyclesXml = releaseCycleList[1]

        # Get all test instances id that have this target cycle
        query = self._getQueryListOrAnd(['assign-rcyc'], [idTargetCyclesXml])

        r = self.TestLabTestInstances.getEntityQueryList(query, 'test-id,assign-rcyc,status')

        xml = self._getXmlFromRequestQueryList(r)

        testLabTestInstanceList = self.TestLabTestInstances.getEntityDataCollectionFieldValueList(
            ['test-id', 'id', 'assign-rcyc', 'status'], xml)

        testIdList = testLabTestInstanceList[0]
        testInstIdList = testLabTestInstanceList[1]
        testTargetCycleIdList = testLabTestInstanceList[2]
        testInstStatusList = testLabTestInstanceList[3]

        # Get test names from their ID
        query = self._getQueryListOrAnd(['id'], [testIdList])

        r = self.TestPlanTests.getEntityQueryList(query, 'name,id,user-12,user-26')

        xml = self._getXmlFromRequestQueryList(r)

        testList = self.TestPlanTests.getEntityDataCollectionFieldValueList(['name', 'id','user-12','user-26'], xml)

        testNameListXml = testList[0]
        testIdListXml = testList[1]
        testInstAutoLevelListXml = testList[2]
        testInstDetailAutoLevelListXml = testList[3]

        testNameList = []
        targetCyclesNameList = []
        testInstAutoLevelList = []
        testInstDetailAutoLevelList = []

        for testId, targetCycle in itertools.izip(testIdList, testTargetCycleIdList):

            for testNameXml, testIdXml,testInstAutoLevelXml, testInstDetailAutoLevelXml in itertools.izip(
                    testNameListXml, testIdListXml, testInstAutoLevelListXml, testInstDetailAutoLevelListXml):

                if testIdXml == testId:
                    testNameList.append(testNameXml)
                    testInstAutoLevelList.append(testInstAutoLevelXml)
                    testInstDetailAutoLevelList.append(testInstDetailAutoLevelXml)

                    break

            else:
                testNameList.append(None)
                testInstAutoLevelList.append(None)
                testInstDetailAutoLevelList.append(None)

            for idTargetCycleXml, nameTargetCycleXml in itertools.izip(idTargetCyclesXml, nameTargetCyclesXml):

                if idTargetCycleXml == targetCycle:
                    targetCyclesNameList.append(nameTargetCycleXml)

                    break

            else:
                targetCyclesNameList.append(None)

        dataCSV = 'Run ID,Run Name,Status,Test Instance Name,Test Instance Status,Target Cycle,TI_id,Automation Level,Detailed Automation Level\n'

        # List of tc mapped
        tcMapped = []

        # List of ti mapped
        tiMapped = []

        for runId, runName, runStatus, testInstanceId in itertools.izip(
                runIdList, runNameList, runStatusList, testInstanceIdList):

            if testInstanceId in testInstIdList:
                idx = testInstIdList.index(testInstanceId)

                if runStatus is None:
                    runStatus = ''

                if testInstAutoLevelList[idx] is None:
                    testInstAutoLevelList[idx] = ''

                if testInstDetailAutoLevelList[idx] is None:
                    testInstDetailAutoLevelList[idx] = ''

                if testInstStatusList[idx] is None:
                    testInstStatusList[idx] = ''

                dataCSV += runId + ','
                dataCSV += runName.replace(",", "#") + ','
                dataCSV += runStatus + ','
                dataCSV += testNameList[idx].replace(",", "#") + ','
                dataCSV += testInstStatusList[idx].replace(",", "#") + ','
                dataCSV += targetCyclesNameList[idx].replace(",", "#") + ','
                dataCSV += testInstanceId.replace(",", "#") + ','
                dataCSV += testInstAutoLevelList[idx].replace(",", "#") + ','
                dataCSV += testInstDetailAutoLevelList[idx].replace(",", "#") + '\n'

                # Add tc to a TC list so we know which are already mapped
                tcMapped.append(targetCyclesNameList[idx])
                tiMapped.append(testInstanceId)

        # Iterate through test instance list and the ones which do not have runs
        for idx, tiId in enumerate(testInstIdList):

            if tiId not in tiMapped:

                if testInstAutoLevelList[idx] is None:
                    testInstAutoLevelList[idx] = ''

                if testInstDetailAutoLevelList[idx] is None:
                    testInstDetailAutoLevelList[idx] = ''

                if testInstStatusList[idx] is None:
                    testInstStatusList[idx] = ''

                dataCSV += ','
                dataCSV += ','
                dataCSV += ','
                dataCSV += testNameList[idx].replace(",", "#") + ','
                dataCSV += testInstStatusList[idx].replace(",", "#") + ','
                dataCSV += targetCyclesNameList[idx].replace(",", "#") + ','
                dataCSV += testInstIdList[idx].replace(",", "#") + ','
                dataCSV += testInstAutoLevelList[idx].replace(",", "#") + ','
                dataCSV += testInstDetailAutoLevelList[idx].replace(",", "#") + '\n'

                # Add TC to a TC list so we know which are already mapped
                tcMapped.append(targetCyclesNameList[idx])

        # Add remaining target cycle if they do not have a run nor a test
        for tcName in nameTargetCyclesXml:

            if tcName not in tcMapped:
                dataCSV += ',,,,,' + tcName.replace(",", "#") + ',,,\n'

        return dataCSV

    def getCSVWithRunsFromTargetCycleAndMultipleReleases(self, qcReleaseList, releaseNameList=None):

        runList = []

        if releaseNameList is None:

            print "Getting ALL RUNS"
            # Get all runs
            r = self.TestLabRuns.getEntity('id,name,status,assign-rcyc,test-id,testcycl-id')

            xml = self._getXmlFromRequestQueryList(r)

            runList = self.TestLabRuns.getEntityDataCollectionFieldValueList(
                ['id', 'name', 'status', 'testcycl-id'], xml)

        else:

            print "Getting only " + str(releaseNameList) + " RUNS"
            # Get all runs from target release
            query = self._getQueryListOrAnd(['user-03'], [releaseNameList])

            r = self.TestLabRuns.getEntityQueryList(query, 'id,name,status,assign-rcyc,test-id,testcycl-id')

            xml = self._getXmlFromRequestQueryList(r)

            runList = self.TestLabRuns.getEntityDataCollectionFieldValueList(
                ['id', 'name', 'status', 'testcycl-id'], xml)

        runIdList = runList[0]
        runNameList = runList[1]
        runStatusList = runList[2]
        testInstanceIdList = runList[3]

        # Get id of Release
        idReleaseQuery = self._getQueryListOrAnd(['name'], [qcReleaseList])

        r = self.Releases.getEntityQueryList(idReleaseQuery, 'id')

        xml = self._getXmlFromRequestQueryList(r)

        idRelease = self.Releases.getEntityDataCollectionFieldValue('id', xml)

        # Get all target cycles associated with release
        query = self._getQueryListOrAnd(['parent-id'], [idRelease])

        r = self.ReleaseCycles.getEntityQueryList(query, 'name,id')

        xml = self._getXmlFromRequestQueryList(r)

        releaseCycleList = self.ReleaseCycles.getEntityDataCollectionFieldValueList(
            ['id', 'name'], xml)

        idTargetCyclesXml = releaseCycleList[0]
        nameTargetCyclesXml = releaseCycleList[1]

        # Get all test instances id that have this target cycle
        query = self._getQueryListOrAnd(['assign-rcyc'], [idTargetCyclesXml])

        r = self.TestLabTestInstances.getEntityQueryList(query, 'test-id,assign-rcyc,status')

        xml = self._getXmlFromRequestQueryList(r)

        testLabTestInstanceList = self.TestLabTestInstances.getEntityDataCollectionFieldValueList(
            ['test-id', 'id', 'assign-rcyc', 'status'], xml)

        testIdList = testLabTestInstanceList[0]
        testInstIdList = testLabTestInstanceList[1]
        testTargetCycleIdList = testLabTestInstanceList[2]
        testInstStatusList = testLabTestInstanceList[3]

        # Get test names from their ID
        query = self._getQueryListOrAnd(['id'], [testIdList])

        r = self.TestPlanTests.getEntityQueryList(query, 'name,id,user-12,user-26')

        xml = self._getXmlFromRequestQueryList(r)

        testList = self.TestPlanTests.getEntityDataCollectionFieldValueList(['name', 'id', 'user-12', 'user-26'], xml)

        testNameListXml = testList[0]
        testIdListXml = testList[1]
        testInstAutoLevelListXml = testList[2]
        testInstDetailAutoLevelListXml = testList[3]

        testNameList = []
        targetCyclesNameList = []
        testInstAutoLevelList = []
        testInstDetailAutoLevelList = []

        for testId, targetCycle in itertools.izip(testIdList, testTargetCycleIdList):

            for testNameXml, testIdXml, testInstAutoLevelXml, testInstDetailAutoLevelXml in itertools.izip(
                    testNameListXml, testIdListXml, testInstAutoLevelListXml, testInstDetailAutoLevelListXml):

                if testIdXml == testId:
                    testNameList.append(testNameXml)
                    testInstAutoLevelList.append(testInstAutoLevelXml)
                    testInstDetailAutoLevelList.append(testInstDetailAutoLevelXml)

                    break

            else:
                testNameList.append(None)
                testInstAutoLevelList.append(None)
                testInstDetailAutoLevelList.append(None)

            for idTargetCycleXml, nameTargetCycleXml in itertools.izip(idTargetCyclesXml, nameTargetCyclesXml):

                if idTargetCycleXml == targetCycle:
                    targetCyclesNameList.append(nameTargetCycleXml)

                    break

            else:
                targetCyclesNameList.append(None)

        dataCSV = 'Run ID,Run Name,Status,Test Instance Name,Test Instance Status,Target Cycle,TI_id,Automation Level,Detailed Automation Level\n'

        # List of tc mapped
        tcMapped = []

        # List of ti mapped
        tiMapped = []

        for runId, runName, runStatus, testInstanceId in itertools.izip(
                runIdList, runNameList, runStatusList, testInstanceIdList):

            if testInstanceId in testInstIdList:
                idx = testInstIdList.index(testInstanceId)

                if runStatus is None:
                    runStatus = ''

                if testInstAutoLevelList[idx] is None:
                    testInstAutoLevelList[idx] = ''

                if testInstDetailAutoLevelList[idx] is None:
                    testInstDetailAutoLevelList[idx] = ''

                if testInstStatusList[idx] is None:
                    testInstStatusList[idx] = ''

                dataCSV += runId + ','
                dataCSV += runName.replace(",", "#") + ','
                dataCSV += runStatus + ','
                dataCSV += testNameList[idx].replace(",", "#") + ','
                dataCSV += testInstStatusList[idx].replace(",", "#") + ','
                dataCSV += targetCyclesNameList[idx].replace(",", "#") + ','
                dataCSV += testInstanceId.replace(",", "#") + ','
                dataCSV += testInstAutoLevelList[idx].replace(",", "#") + ','
                dataCSV += testInstDetailAutoLevelList[idx].replace(",", "#") + '\n'

                # Add tc to a TC list so we know which are already mapped
                tcMapped.append(targetCyclesNameList[idx])
                tiMapped.append(testInstanceId)

        # Iterate through test instance list and the ones which do not have runs
        for idx, tiId in enumerate(testInstIdList):

            if tiId not in tiMapped:

                if testInstAutoLevelList[idx] is None:
                    testInstAutoLevelList[idx] = ''

                if testInstDetailAutoLevelList[idx] is None:
                    testInstDetailAutoLevelList[idx] = ''

                if testInstStatusList[idx] is None:
                    testInstStatusList[idx] = ''

                dataCSV += ','
                dataCSV += ','
                dataCSV += ','
                dataCSV += testNameList[idx].replace(",", "#") + ','
                dataCSV += testInstStatusList[idx].replace(",", "#") + ','
                dataCSV += targetCyclesNameList[idx].replace(",", "#") + ','
                dataCSV += testInstIdList[idx].replace(",", "#") + ','
                dataCSV += testInstAutoLevelList[idx].replace(",", "#") + ','
                dataCSV += testInstDetailAutoLevelList[idx].replace(",", "#") + '\n'

                # Add TC to a TC list so we know which are already mapped
                tcMapped.append(targetCyclesNameList[idx])

        # Add remaining target cycle if they do not have a run nor a test
        for tcName in nameTargetCyclesXml:

            if tcName not in tcMapped:
                dataCSV += ',,,,,' + tcName.replace(",", "#") + ',,,\n'

        return dataCSV

    def getTestStepsDictFromTestPlanPath(self, tp_path):

        testInfoDict = {}

        # First get all the tests that exist in this path
        testPlanFolderIdList = self._getIdTestPlanSubFoldersFromPathList([tp_path])[0]

        testPlanTestIdListXml = self._getIdTestPlanTestFromFolderIdList(testPlanFolderIdList)

        # Now get the test name list
        query = self._getQueryListOrAnd(['id'], [testPlanTestIdListXml])

        r = self.TestPlanTests.getEntityQueryList(query, 'id,name,description,user-12,user-26,user-15,user-43')
        
        xml = self._getXmlFromRequestQueryList(r)

        testPlanTestInfoList = self.TestPlanTests.getEntityDataCollectionFieldValueList(
            ['id','name','description','user-12','user-26','user-15', 'user-43'], xml)

        testPlanTestIdListXml = testPlanTestInfoList[0]
        testPlanTestNameListXml = testPlanTestInfoList[1]
        testPlanTestDescriptionListXml = testPlanTestInfoList[2]
        testPlanTestAutoLevelListXml = testPlanTestInfoList[3]
        testPlanTestDetailAutoLevelListXml = testPlanTestInfoList[4]
        testPlanTestWorthRegressionTestListXml = testPlanTestInfoList[5]
        testPlanTestPriorityListXml = testPlanTestInfoList[6]

        # Now get the test steps for all the tests
        query = self._getQueryListOrAnd(['parent-id'], [testPlanTestIdListXml])

        r = self.TestPlanDesignSteps.getEntityQueryList(query, 'description,expected,parent-id,name')

        xml = self._getXmlFromRequestQueryList(r)

        testPlanTestStepInfoList = self.TestPlanDesignSteps.getEntityDataCollectionFieldValueList(
            ['description','expected','parent-id','name'], xml)

        testPlanTestStepDescriptionListXml = testPlanTestStepInfoList[0]
        testPlanTestStepExpectedListXml = testPlanTestStepInfoList[1]
        testPlanTestStepParentIdListXml = testPlanTestStepInfoList[2]
        testPlanTestStepNameListXml = testPlanTestStepInfoList[3]

        # Ok, so lets get everything ordered and build the test info dict
        for testPlanTestIdXml, testPlanTestNameXml, testPlanTestDescriptionXml, testPlanTestAutoLevelXml, testPlanTestDetailAutoLevelXml, testPlanTestWorthRegressionTestXml, testPlanTestPriorityXml  in itertools.izip(
                testPlanTestIdListXml, testPlanTestNameListXml, testPlanTestDescriptionListXml, testPlanTestAutoLevelListXml, testPlanTestDetailAutoLevelListXml, testPlanTestWorthRegressionTestListXml, testPlanTestPriorityListXml):

            testInfoDict[testPlanTestNameXml] = {'description': testPlanTestDescriptionXml, 'Automation_Level': testPlanTestAutoLevelXml, 'Detailed_Automation_Level': testPlanTestDetailAutoLevelXml, 'Worth_Regression_Test':testPlanTestWorthRegressionTestXml, 'Priority':testPlanTestPriorityXml}            
            testInfoDict[testPlanTestNameXml]['steps'] = []

            testStepsDescriptionList = []
            testStepsExpectedList = []
            testStepsNameList = []

            # First match the test ID
            for testPlanTestStepParentIdXml, testPlanTestStepExpectedXml, \
                testPlanTestStepDescriptionXml, testPlanTestStepNameXml in itertools.izip(
                    testPlanTestStepParentIdListXml, testPlanTestStepExpectedListXml,
                    testPlanTestStepDescriptionListXml, testPlanTestStepNameListXml):

                if testPlanTestStepParentIdXml == testPlanTestIdXml:

                    testStepsDescriptionList.append(testPlanTestStepDescriptionXml)
                    testStepsExpectedList.append(testPlanTestStepExpectedXml)
                    testStepsNameList.append(testPlanTestStepNameXml)

            # Now we need to order the steps
            for i in range(len(testStepsNameList)):

                matchString = 'Step\s+' + str(i+1)

                for idx,testStepsName in enumerate(testStepsNameList):

                    if re.findall(matchString, testStepsName):

                        # Ok found it so add it
                        testInfoDict[testPlanTestNameXml]['steps'].append(
                            [testStepsDescriptionList[idx], testStepsExpectedList[idx]])

                        break

        return testInfoDict

    def getTestDictFromTestLabPath(self, tl_path):

        testInfoDict = {}

        if 'Root' not in tl_path:
            self._raiseError('getTestDictFromTestLabPath', 'Invalid testset path - Missing \'Root\': ' + tl_path + '!')

        tl_path = tl_path[5:]

        # First get all the tests that exist in this path
        testLabFolderIdList = self._getIdTestLabSubFoldersFromPathList([tl_path])[0]

        # Get test set list
        testsetIdList = self._getIdTestLabTestSetFromFolderId(testLabFolderIdList)

        # Retrieve lab location
        testLabTestInstancePathList = self._getFolderPathListFromTestLabTestSetIdList(testsetIdList)

        # Get test instance list
        testInstancesIdList = self._getIdTestLabTestInstancesFromTestsetId(testsetIdList)

        # Get test plan test list
        testPlanTestIdList = self._getIdTestPlanTestFromTestInstanceIdList(testInstancesIdList)

        # Now get the test name list
        query = self._getQueryListOrAnd(['id'], [testPlanTestIdList])

        r = self.TestPlanTests.getEntityQueryList(query, 'id,name,description,user-12,user-26,user-15')

        xml = self._getXmlFromRequestQueryList(r)

        testPlanTestInfoList = self.TestPlanTests.getEntityDataCollectionFieldValueList(
            ['id','name','description','user-12','user-26','user-15'], xml)

        testPlanTestIdList = testPlanTestInfoList[0]
        testPlanTestNameListXml = testPlanTestInfoList[1]
        testPlanTestDescriptionListXml = testPlanTestInfoList[2]
        testPlanTestAutoLevelListXml = testPlanTestInfoList[3]
        testPlanTestDetailAutoLevelListXml = testPlanTestInfoList[4]
        testPlanTestWorthRegressionTestListXml = testPlanTestInfoList[5]

        # Retrieve plan location
        testPlanTestPathList = self._getFolderPathListFromTestPlanTestIdList(testPlanTestIdList)

        # Now get the test steps for all the tests
        query = self._getQueryListOrAnd(['parent-id'], [testPlanTestIdList])

        r = self.TestPlanDesignSteps.getEntityQueryList(query, 'description,expected,parent-id,name')

        xml = self._getXmlFromRequestQueryList(r)

        testPlanTestStepInfoList = self.TestPlanDesignSteps.getEntityDataCollectionFieldValueList(
            ['description','expected','parent-id','name'], xml)

        testPlanTestStepDescriptionListXml = testPlanTestStepInfoList[0]
        testPlanTestStepExpectedListXml = testPlanTestStepInfoList[1]
        testPlanTestStepParentIdListXml = testPlanTestStepInfoList[2]
        testPlanTestStepNameListXml = testPlanTestStepInfoList[3]

        # Now get all the information of target test instances to map them to testset IDs  and test
        query = self._getQueryListOrAnd(['id'], [testInstancesIdList])

        r = self.TestLabTestInstances.getEntityQueryList(query, 'cycle-id,id,test-id')

        xml = self._getXmlFromRequestQueryList(r)

        testLabTestInstanceInfoList = self.TestPlanDesignSteps.getEntityDataCollectionFieldValueList(
            ['cycle-id','id','test-id'], xml)

        testLabTestInstanceTestSetListXml = testLabTestInstanceInfoList[0]
        testLabTestInstanceIdListXml = testLabTestInstanceInfoList[1]
        testLabTestInstanceTestIdListXml = testLabTestInstanceInfoList[2]

        # Add test lab information
        for testLabTestInstanceTestSetXml, testLabTestInstanceIdXml, testLabTestInstanceTestIdXml in itertools.izip(
                testLabTestInstanceTestSetListXml, testLabTestInstanceIdListXml, testLabTestInstanceTestIdListXml):

            # Ok, so lets get everything ordered and build the test info dict
            for testPlanTestIdXml, testPlanTestNameXml, testPlanTestDescriptionXml, testPlanTestAutoLevelXml,\
                testPlanTestDetailAutoLevelXml, testPlanTestWorthRegressionTestXml, testPlanTestPath in itertools.izip(
                    testPlanTestIdList, testPlanTestNameListXml, testPlanTestDescriptionListXml,
                    testPlanTestAutoLevelListXml, testPlanTestDetailAutoLevelListXml,
                    testPlanTestWorthRegressionTestListXml, testPlanTestPathList):

                if testLabTestInstanceTestIdXml == testPlanTestIdXml:

                    # Add prefix for multiple test instances pointing to same test
                    testPlanTestNameXml = testPlanTestNameXml + '_0000'

                    while testInfoDict.has_key(testPlanTestNameXml):

                        testPlanTestNameXml = testPlanTestNameXml[:-4] + '%04d' % (int(testPlanTestNameXml[-4:]) + 1)

                    # Add test plan information
                    testInfoDict[testPlanTestNameXml] = {'description': testPlanTestDescriptionXml,
                                                         'Automation_Level': testPlanTestAutoLevelXml,
                                                         'Detailed_Automation_Level': testPlanTestDetailAutoLevelXml,
                                                         'Worth_Regression_Test':testPlanTestWorthRegressionTestXml,
                                                         'Test Plan Path': testPlanTestPath}

                    testInfoDict[testPlanTestNameXml]['Test Lab Path'] = testLabTestInstancePathList[
                        testsetIdList.index(testLabTestInstanceTestSetXml)]

                    testInfoDict[testPlanTestNameXml]['steps'] = []

                    testStepsDescriptionList = []
                    testStepsExpectedList = []
                    testStepsNameList = []

                    # First match the test ID
                    for testPlanTestStepParentIdXml, testPlanTestStepExpectedXml, \
                        testPlanTestStepDescriptionXml, testPlanTestStepNameXml in itertools.izip(
                            testPlanTestStepParentIdListXml, testPlanTestStepExpectedListXml,
                            testPlanTestStepDescriptionListXml, testPlanTestStepNameListXml):

                        if testPlanTestStepParentIdXml == testPlanTestIdXml:

                            testStepsDescriptionList.append(testPlanTestStepDescriptionXml)
                            testStepsExpectedList.append(testPlanTestStepExpectedXml)
                            testStepsNameList.append(testPlanTestStepNameXml)

                    # Now we need to order the steps
                    for i in range(len(testStepsNameList)):

                        matchString = 'Step\s+' + str(i+1)

                        for idx,testStepsName in enumerate(testStepsNameList):

                            if re.findall(matchString, testStepsName):

                                # Ok found it so add it
                                testInfoDict[testPlanTestNameXml]['steps'].append(
                                    [testStepsDescriptionList[idx], testStepsExpectedList[idx]])

                                break

                    # Exit loop
                    break

        return testInfoDict

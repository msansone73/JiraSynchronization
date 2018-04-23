# QC Specific variables

import logging

from QCRest_hiT7300.QCRest_Robot import QCRest_Robot

logger = logging.getLogger('QCRest')

rootPathTL = 'Root\\5.50 00 BR2-1'
rootPathTP = 'Subject\\hiT7300_Test Plan_(wo transponders)'
release = '5.50 00 BR2-1'

testerUserName = '60000008'  # Update with your user name!

class qc_info(object):

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, path, fail_test='default'):
        # Default values for the different dicts - Additional values may be added in the corresponding functions
        self.testcase = {
            'test_set': None,
            'test_set_name': None,
            'test_set_release': release,
            'test_case_sw_build': None,
            'test_case': None,
            'test_case_name': None,
            'test_case_automation_level': 'Fully automated',
            'test_case_level_and_area': 'EnTe - Functional Test',
            'test_case_status':  'Design',
            'test_case_worth_regression_test': 'Yes',
            'test_case_products_concerned': '',
            'test_case_release': release,
            'test_case_responsible_tester': testerUserName,
            # 'test_case_responsible_person': None,
            # 'test_case_release_concerned': [release],
            # 'test_case_designer': None,
            }

        self.teststep = {
            # 'step_description': None,
            # 'step_expected': None,
            # 'step_status': 'Passed',
            # 'step_actual': None,
            }

        self.testrun = {
            # 'test_case_run_status': None,
            }

        self.mod = QCRest_Robot(path, fail_test)

    def qc_create_testcase(self, test_case_name, test_set_name, test_set, test_case, test_case_sw_build,
                           test_case_automation_level='Fully automated'):
        '''
        Allows the creation of testcase entry in sxml file
        :param test_case_name: Name of the test (Test Plan and Test Lab)
        :param test_set_name: Name of the testset where test will be created
        :param test_set: Path of the test set where the test set will be created
        :param test_case: Path of the test case where the test will be created
        :param test_case_sw_build: APS SW Build
        :param test_case_automation_level: Automation Level
        :param test_case_designer: Designer of the test in test plan
        :param test_case_release_concerned: Releases concerned - can have multiple values so a list should be given
        :return:
        '''

        self.testcase.update(dict((k, v) for k, v in locals().iteritems() if v and k != 'self'))

        self.testcase['test_set'] = rootPathTL + '\\' + self.testcase['test_set']
        self.testcase['test_case'] = rootPathTP + '\\' + self.testcase['test_case']

        logger.info("Create Test Case: " + str(self.testcase))

        self.mod.qc_test_case(self.testcase)

    def qc_add_teststep(self, step_description, step_expected, step_status='Passed', step_actual=None):
        '''
        Adds a test set to the test case previously open in the test case
        :param step_description: Description of the step
        :param step_expected: Expected result
        :param step_status: Status of the test applicable to the run only
        :param step_actual: Actual result of the test
        :return:
        '''

        self.teststep.update(dict((k, v) for k, v in locals().iteritems() if v and k != 'self'))

        logger.info("Add Test Step=" + str(self.teststep))

        self.mod.qc_test_step(self.teststep)

    def qc_close_testcase(self, test_case_run_status):
        '''
        Use to indicate that no more entries will be added to the testcase
        :param test_case_run_status: Status of the test run
        :return:
        '''

        self.testrun.update(dict((k, v) for k, v in locals().iteritems() if v and k != 'self'))
		
        logger.info("Close Test=" + str(self.testrun))

        self.mod.qc_close_test_case(self.testrun)

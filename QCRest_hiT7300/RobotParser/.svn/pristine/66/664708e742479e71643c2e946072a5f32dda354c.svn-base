__author__ = 'Matteo Feroldi'

import logging
import socket
import time
from platform import system
from xml.sax.saxutils import escape

import gp_config_ini

logger = logging.getLogger('QCRest')

#Validation for jython
if system() == "Java":  
    import xml.etree.ElementTree as etree

else:
    try:
        import lxml.etree as etree
    except:
        logger.warn('lxml lib not found, ElementTree is used')
        import xml.etree.ElementTree as etree


class xml_gen(object):


    def __init__(self, path, d_initPath, qc_robotPath, w_always = False, fail_test='default', forceLastStepFail = True):

        # path of the output standard xml file
        self.path = path

        # flag used to decide if write the tree for each action or just at the qc_close_test_case
        self.w_always = w_always

        # root generation
        self.root = etree.Element('report')
        self.tree = etree.ElementTree(self.root)

        # temp var to load in memory the actual test_sets used
        self.test_sets = None

        # temp var to load in memory the actual test_cases used
        self.test_cases = None

        # temp var to load in memory the actual test_case used
        self.test_case = None

        # temp var to load in memory the last test_step used
        self.step = None

        # If set this will force the last step of a failed step to go to fail
        self.forceLastStepFail = forceLastStepFail

        # populate the dictionary of information read from ini files (used just in the children classes)
        # these variables will be rewritten by the children class
        self.d_qc = None
        self.d_init = None

        # Path to ini data
        self.d_initPath = d_initPath
        self.qc_robotPath = qc_robotPath

        self.in_test_set = False

        # get run timestamp
        self.start_parse = str(int(time.time()))

        # get hostname
        self.hostname = socket.gethostname()

        # fail_test has 3 possible values : 'default', 'not_import', '...insert by user...'
        # default              = the test_case_status is read and write as it is
        # not_import           = if the test_case_status is Failed the test is skipped and not imported
        # ...insert by user... = if the test_case_status is Failed write status as the string read in the variable passed

        self.fail_test = fail_test

        if self.w_always == True and self.fail_test == 'not_import':
            logger.error('the combiniation of w_always = True and fail_test = not_import is not supported')

    # initialization of report header with start_time and hostname

    def _init_report(self):
        self.root.set('run_timestamp', self.start_parse)
        self.root.set('hostname', self.hostname)

    # read qc_robot file and save the information in a dictionary, the output is a dictionary of dictionaries

    def _read_qc_robot(self):

        qc_robot_path = self.qc_robotPath                    # path of qc_robot
        qc_robot = gp_config_ini.ConfigIni(qc_robot_path)   # Quality Center tag names

        qc = dict()

        sections = qc_robot.read_sections()                 # read all the sections in the ini file

        for section in sections:
            data = qc_robot.read_all_values(section)
            d = dict(zip(data[0], data[1])) # escape will be usued to escape special chars, such as: <, &, >
            qc.update({section: d})

        return qc


    # read init file and save the information in a dictionary, the output is a dictionary of lists

    def _read_init(self):

        init_path = self.d_initPath                          # path of init
        init = gp_config_ini.ConfigIni(init_path)           # input dictionary keys (used for consistency check)

        qc = dict()

        sections = init.read_sections()

        for section in sections:
            data = init.read_all_values(section)
            qc.update({section: data[1]})

        return qc


    # initialize input dictionary/list, all the requested values are appended as None if not present in the input

    def _init_dict(self, input_data, dict_name):

        d = {}

        if type(input_data) is dict:

            for option in self.d_init[dict_name]:

                if option not in input_data.keys():
                    d.update({option : None})
                else:
                    d.update({option : input_data[option]})
        else:
            # not implemented yet
            logger.error('input_data has to be a dictionary, list is not supported yet')

        return d


    # validate the dictionary, check is some values are None

    def _validate_dict(self, input_dict):

        # list of parameter set to None
        l = []

        validator = True

        for opt in input_dict.keys():
            if input_dict[opt] == None:
                l.append(opt)
                validator = False               

        if l != []:
            logger.info('In the input dictionary, the following parameters are missing: %s' % l)

        return validator


    def qc_test_case(self, input_data):

        # dictionaries initialization
        tags_robot_test_set = self._init_dict(input_data, 'tags_robot_test_set')
        tags_robot_test_case = self._init_dict(input_data, 'tags_robot_test_case')

        # dictionaries validation
        self._validate_dict(tags_robot_test_set)
        self._validate_dict(tags_robot_test_case)


        # test_sets generation if doesn't exist

        if self.root.find('.//test_sets') == None:
            self.test_sets = etree.Element('test_sets')
            self.root.append(self.test_sets)

        self.in_test_set = False

        # check if the test case below to an existing test_set, if not the new test_set is created

        test_set_name = tags_robot_test_set['test_set_name']
        test_set_path = tags_robot_test_set['test_set']

        for ele in self.root.findall(".//test_set[@path='%s']/test_set_name" % test_set_path):
            if test_set_name == ele.text:
                self.in_test_set = True

        # if the test set for this test case doesn't exist yet
        if self.in_test_set == False:
            # test_set generation
            self.test_sets = self.root.find('.//test_sets')
            self.test_set = etree.Element('test_set')


            for option in self.d_init['tags_robot_test_set']:
                if option == 'test_set':
                    self.test_set.set('path', escape(tags_robot_test_set['test_set']))
                else:
                    if option in tags_robot_test_set.keys():
                        elem = etree.Element('%s' % option)
                        self.test_set.append(elem)
                        elem.text = tags_robot_test_set['%s' % option]
                        d = self.d_qc[option]
                        for val in d.keys():
                            elem.set(val, d[val])

            # test_cases generation

            self.test_cases = etree.Element('test_cases')
            self.test_set.append(self.test_cases)

        # the test set for this qc_test_case already exist
        else:

            # get the test_set where the qc_test_case below
            match = False
            for ele in self.root.findall(".//test_set[@path='%s']" % test_set_path):
                t_test_set = ele
                for el in ele.findall("./test_set_name"):
                    if el.text == test_set_name:
                        self.test_set = t_test_set
                        match = True
                        break
                if match:
                    break

            # get the test_cases where the qc_test_case below

            for node in self.test_set.getchildren():
                if node.tag == 'test_cases':
                    self.test_cases = node
                    break

        # qc_test_case generation
        self.test_case = etree.Element('test_case')


        for option in self.d_init['tags_robot_test_case']:
            if option == 'test_case':
                self.test_case.set('path', escape(tags_robot_test_case['test_case']))
            # check if the input is list
            elif type(tags_robot_test_case['%s' % option]) is list:
                elem = etree.Element('%s' % option)
                self.test_case.append(elem)
                d = tags_robot_test_case['%s' % option]
                for value in d:
                    val = etree.Element('value')
                    elem.append(val)
                    val.text = value
                d = self.d_qc[option]
                for val in d.keys():
                    elem.set(val, d[val])
            else:
                if option in tags_robot_test_case.keys():
                    elem = etree.Element('%s' % option)
                    self.test_case.append(elem)
                    elem.text = tags_robot_test_case['%s' % option]
                    d = self.d_qc[option]
                    for val in d.keys():
                        elem.set(val, d[val])

        # print etree.tostring(self.root)

        # write file
        if self.w_always:

            if self.in_test_set == False:
                self.test_sets.append(self.test_set)
            self.test_cases.append(self.test_case)

            self.tree.write(self.path)


    def qc_test_step(self, input_data):

        tags_robot_test_case_step = self._init_dict(input_data, 'tags_robot_test_case_step')

        # dictionary validation
        self._validate_dict(tags_robot_test_case_step)

        # check if the qc_test_case is loaded in memory
        if self.test_case == None:
            logger.error('no qc_test_case defined for the qc_test_step')

        else:

            # check if test_case_steps already exist for the current qc_test_case
            if self.test_case.find('.//test_case_steps') == None:
                # if doesn't exist yet a new test_case_steps is created
                test_case_steps = etree.Element('test_case_steps')
                self.test_case.append(test_case_steps)
            else:
                test_case_steps = self.test_case.find('.//test_case_steps')

            test_case_step = etree.Element('test_case_step')
            test_case_steps.append(test_case_step)

            # write in temp var the actual qc_test_step used
            self.step = test_case_step

            for step in tags_robot_test_case_step.keys():
                elem = etree.Element('%s' % step)
                test_case_step.append(elem)
                elem.text = tags_robot_test_case_step[step]
                d = self.d_qc[step]
                for val in d.keys():
                    elem.set(val, d[val])

            # print etree.tostring(self.root)

            # write file
            if self.w_always:
                self.tree.write(self.path)


    def qc_close_test_case(self, input_data):

        tags_robot_test_case_run = self._init_dict(input_data, 'tags_robot_test_case_run')

        # dictionary validation
        self._validate_dict(tags_robot_test_case_run)

        if self.test_case == None:
            logger.error('no qc_test_case defined, close the qc_test_case is not possible')

        else:

            test_case_run_status = tags_robot_test_case_run['test_case_run_status']

            # check the fail_test mode and set the test_status
            # if fail_test = 'not_import' and test_status = 'Failed' -> skip the test
            if self.fail_test == 'not_import' and test_case_run_status == 'Failed':
                # the test_case pre build is not added to the root
                pass
            else:
                if self.fail_test != 'default' and test_case_run_status == 'Failed':
                        tags_robot_test_case_run.update({'test_case_run_status' : self.fail_test})

                # add the test_set to the test_sets if is already created
                if self.in_test_set == False and self.w_always == False:
                    self.test_sets.append(self.test_set)

                # append the test_case
                if self.w_always == False:
                    self.test_cases.append(self.test_case)

                test_case_run = etree.Element('test_case_run')
                self.test_case.append(test_case_run)

                for option in tags_robot_test_case_run.keys():
                    d = self.d_qc[option]

                    elem = etree.Element('%s' % option)
                    test_case_run.append(elem)
                    elem.text = tags_robot_test_case_run['%s' % option]
                    for val in d.keys():
                        elem.set(val, d[val])
            '''

            <<< This part is not used any more, in tag v1.3 this code is available >>>

            else:
                if self.fail_test != 'default' and test_case_run_status == 'Failed':
                    tags_robot_test_case_run.update({'test_case_run_status' : self.fail_test})


                # add the test_set to the test_sets if is already created
                if self.in_test_set == False and self.w_always == False:
                    self.test_sets.append(self.test_set)

                # append the test_case
                if self.w_always == False:
                    self.test_cases.append(self.test_case)

                test_case_run = etree.Element('test_case_run')
                self.test_case.append(test_case_run)

                step_status=None
                if self.step != None:
                    for node in self.step.getchildren():
                        if node.tag == 'step_status':
                            step_status = node

                for option in tags_robot_test_case_run.keys():
                    d = self.d_qc[option]

                    # write on the last test_case_step the value of test_case_run_status
                    if option == 'test_case_run_status' and self.step != None and self.forceLastStepFail:
                        step_status.text = tags_robot_test_case_run[option]

                    elem = etree.Element('%s' % option)
                    test_case_run.append(elem)
                    elem.text = tags_robot_test_case_run['%s' % option]
                    for val in d.keys():
                        elem.set(val, d[val])
            '''
            # print etree.tostring(self.root)

            # write file
            self.tree.write(self.path)
from __builtin__ import object

__author__ = 'Matteo Feroldi'


try:
    import lxml.etree as etree
except:
    print '> Warning : lmxl lib not found, ElementTree is used'
    print ''
    import xml.etree.ElementTree as etree

import gp_config_ini

from datetime import datetime


class RobotTags(object):


    def __init__(self, xml_in_path, xml_out_path, initPath, qc_robotPath, fail_test='default'):

        self.iniCo = gp_config_ini.ConfigIni(initPath)
        self.qcRobot = gp_config_ini.ConfigIni(qc_robotPath)
        self.xml_in_path = xml_in_path
        self.xml_out_path = xml_out_path
        self.fail_test = fail_test

        # fail_test has 3 possible values : 'default', 'not_import', '...insert by user...'
        # default = the test status is read and write as it is
        # not_import = if the status is Failed the test is skipped and not imported
        # ...insert by user... = if the status is failed write status as the string read in the variable passed



    # return a dictionary with all the information of the TEST SET and TEST CASES
    # {  'd_1':{---test info---}, 'd_2':{---test info---}, ... , 'd_n':{---test info---}}
    def get_tags(self):

        # parsing start time
        start_parse = datetime.now()
        print 'Robot Parser start processing: %s' % start_parse
        print ''

        # dictionary result used to build the output xml
        tags = {}

        # read actual system used
        system = self.iniCo.read_value('system', 's')

        # tag label generation for test set
        tag = 'tags_' + system + '_test_set'

        # read qc tags of the actual system
        qc_tags_options = self.iniCo.read_all_values(tag)[0]
        qc_tags_values = self.iniCo.read_all_values(tag)[1]

        # read path to get information tags from old (v1) and new (v2)  version of Robot Mainframe
        v = 'tags_' + system
        v1 = self.iniCo.read_value(v, 'v1')
        v2 = self.iniCo.read_value(v, 'v2')


        # read the flag to use to check the version of the xml file
        flag = self.iniCo.read_value(v, 'flag')


        t_id = 1
        for event, elem in etree.iterparse(self.xml_in_path, events=("start", "end")):

            # parsing test by test
            if elem.tag == 'test' and event == 'end':
                test_case_id = elem.attrib.get('id')
                test_case_name = elem.attrib.get('name')

                # check the version of Robot Mainframe
                if elem.find(flag) is not None:
                    value = v2
                else:
                    value = v1


                # check the test status
                val = "./status"
                test_stat = elem.find(val).attrib.get('status')
                if test_stat == 'PASS':
                    test_status = 'Passed'
                else:
                    test_status = 'Failed'


                # this is the location of the tag for the hiT7300 functional test run with robot framework
                val = value

                # check the fail_test mode and set the test_status
                # if fail_test = 'not_import' and test_status = 'Failed' -> skip the test
                if self.fail_test == 'not_import' and test_status == 'Failed':
                    pass
                else:
                    if self.fail_test != 'default' and test_status == 'Failed':
                        test_status = self.fail_test

                    if test_case_id:
                        tags.update({'d_%s' % t_id: self.get_test_case_tags(test_case_name, elem, test_status, val, qc_tags_options, qc_tags_values)})
                        t_id += 1

                # log
                print test_case_id + ' - ' + test_case_name + ' : status = ' + test_status

                # delete element already parsed from memory
                elem.clear()

        stop_parse = datetime.now()
        tot_parse = stop_parse - start_parse
        print ''
        print 'total test parsed = %s, execution time: %s' % (t_id-1, str(tot_parse))

        return tags


    # sub function of get_tags()
    # return a dictionary for the the case selected by test_case_name and element
    def get_test_case_tags(self, test_case_name, element, test_status, tags_path, qc_tags_options, qc_tags_values):

        # initialize tag dict
        tags = {}

        for el in element.findall(tags_path):
            raw_value = el.text
            # print raw_value
            if raw_value:

                # scanning the TEST SET tags and parse the raw values
                for qc_tags_option, qc_tags_value in zip(qc_tags_options, qc_tags_values):

                    # update the dictionary with test_set information
                    if qc_tags_value in raw_value:
                        tags.update({qc_tags_option: raw_value.split('::')[1]})


        tags.update({'test_case_name': test_case_name})

        # read actual system used
        system = self.iniCo.read_value('system', 's')

        # read path to get steps location and step info
        v = 'tags_' + system
        steps = self.iniCo.read_value(v, 'steps')
        step_inf = self.iniCo.read_value(v, 'step_inf')



        # +++++++ TAGS label generation  for test case: test_case_id +++++++

        # tag label generation for test case: tags_robot_test_case
        tag = 'tags_' + system + '_test_case'
        # read qc tags of test case
        qc_tags_options = self.iniCo.read_all_values(tag)[0]
        qc_tags_values = self.iniCo.read_all_values(tag)[1]

        test_case_status = self.iniCo.read_value(tag, 'test_case_status')

        if test_case_status:
            tags.update({'test_case_status': test_case_status})

        # tag label generation for test case step: tags_robot_test_case_step
        tag = 'tags_' + system + '_test_case_step'
        # read qc tags of the test case step
        for option in self.iniCo.read_all_values(tag)[0]:
            qc_tags_options.append(option)
        for value in self.iniCo.read_all_values(tag)[1]:
            qc_tags_values.append(value)

        # tag label generation for test case run: tags_robot_test_case_run
        tag = 'tags_' + system + '_test_case_run'
        # read qc tags of the test case run
        for option in self.iniCo.read_all_values(tag)[0]:
            qc_tags_options.append(option)
        for value in self.iniCo.read_all_values(tag)[1]:
            qc_tags_values.append(value)


        # Owner that will be used for test_case_run_tester
        owner = ''

        val = tags_path
        for el in element.findall(val):
            raw_value = el.text
            if raw_value:
                # scanning the TEST CASE tags and parse the raw values
                for qc_tags_option, qc_tags_value in zip(qc_tags_options, qc_tags_values):
                    if qc_tags_value in raw_value:
                        # 'QC_TP_Product_Concerned' is the only tag with array values
                        if qc_tags_value == 'QC_TP_Product_Concerned':
                            tags.update({qc_tags_option: raw_value.split('::')[1].split(',')})
                        elif qc_tags_option == 'None':
                            pass
                        else:
                            # update the dictionary with qc_test_case information
                            info = raw_value.split('::')
                            if len(info) > 1:
                                tags.update({qc_tags_option: info[1]})

                        if str(qc_tags_value) == 'QC_TL_ResponsabileTests':
                            owner = raw_value.split('::')[1]


        # --- this tags are not inside the xml file, need to be build one by one ---
        val = "./status"
        raw_date_time = element.findall(val)[0].attrib.get('starttime')
        r_date = raw_date_time.split('.')[0].split(' ')[0]
        test_case_run_exec_time = raw_date_time.split('.')[0].split(' ')[1]
        test_case_run_exec_date = r_date[:4] + '-' + r_date[4:6] + '-' + r_date[6:8]
        test_case_run_name = 'Run ' + test_case_run_exec_date + ' ' + test_case_run_exec_time
        test_case_creation_date = test_case_run_exec_date
        tags.update({'test_case_run_name': test_case_run_name})
        tags.update({'test_case_creation_date': test_case_creation_date})
        tags.update({'test_case_run_exec_date': test_case_run_exec_date})
        tags.update({'test_case_run_exec_time': test_case_run_exec_time})
        tags.update({'test_case_run_tester': owner})


        # scanning for TEST STEP information

        i = 1
        step_tot = len(element.findall(steps))
        for child in element.findall(steps):

            if i == step_tot:
                if test_status == 'Failed' or test_status == 'Passed':
                    step_status = test_status
                else:
                    step_status = 'Failed'
            else:
                step_status = 'Passed'
            step = []
            for el in child.findall(step_inf):
                step.append(el.text)
            step_name = step[0].split('=')[1].strip()
            step_description = step[1].split('=')[1].strip()
            step_expected = step[2].split('=')[1].strip()
            step_num = 'step_%s' % i
            i += 1

            # update the dictionary with qc_test_step information
            tags.update({step_num: [step_name, step_description, step_expected, step_status]})

        return tags


    # read qc_tags from ini file and generate a dictionary as output
    def read_qc_tags(self):


        qc_tags = {}
        sections = self.qcRobot.read_sections()

        for section in sections:
            data = self.qcRobot.read_all_values(section)
            d = dict(zip(data[0], data[1]))
            qc_tags.update({section: d})

        return qc_tags


    # MAIN function: read the information from get_tags() and generate the xml output
    def gen_xml(self, writeFile = True):

        # load data
        data = self.get_tags()

        # load qc tags
        qc_tags = self.read_qc_tags()

        # check number of qc_test_case
        i = 1
        while 'd_%s' % i in data.keys():
            i += 1
        n_test_case = i - 1


        # tag label generation
        system = self.iniCo.read_value('system', 's')
        tag = 'tags_' + system + '_test_set'

        # read qc tags of test set
        qc_tags_options_set = self.iniCo.read_all_values(tag)[0]

        # tag label generation

        tag = 'tags_' + system + '_test_case'

        # read qc tags of test case
        qc_tags_options_case = self.iniCo.read_all_values(tag)[0]

        # tag label generation

        tag = 'tags_' + system + '_test_case_step'

        # read qc tags of test case
        qc_tags_options_steps = self.iniCo.read_all_values(tag)[0]

        root = etree.Element('report')
        # root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        # root.set('xsi:noNamespaceSchemaLocation', 'report-schema.xsd')

        tree = etree.ElementTree(root)

        ''' *******************   define test_sets  ******************* '''
        test_sets = etree.Element('test_sets')
        root.append(test_sets)

        in_test_set = False

        for n in range(n_test_case):
            in_test_case = False
            i = n + 1

            ''' *****************   define test_set  ****************** '''

            test_set_name = data['d_%s' % i]['test_set_name']

            if in_test_set == False:
                for ele in root.findall(".//test_set_name"):
                    if test_set_name == ele.text:
                        in_test_set = True

            if in_test_set == False:

                test_set = etree.Element('test_set')
                test_sets.append(test_set)


                for option in qc_tags_options_set:
                    if option == 'test_set':
                        test_set.set('path', data['d_%s' % i]['test_set'])
                    else:
                        if option in data['d_%s' % i].keys():
                            elem = etree.Element('%s' % option)
                            test_set.append(elem)
                            elem.text = data['d_%s' % i]['%s' % option]
                            d = qc_tags[option]
                            for val in d.keys():
                                elem.set(val, d[val])

                ''' *******************   define test_cases  ******************* '''
                test_cases = etree.Element('test_cases')
                test_set.append(test_cases)

            ''' *******************   define qc_test_case  ******************* '''
            test_case = etree.Element('qc_test_case')
            test_cases.append(test_case)
            for option in qc_tags_options_case:
                if option == 'qc_test_case':
                    test_case.set('path', data['d_%s' % i]['qc_test_case'])
                elif option == 'test_case_products_concerned':
                    elem = etree.Element('%s' % option)
                    test_case.append(elem)
                    d = data['d_%s' % i]['%s' % option]
                    for value in d:
                        val = etree.Element('value')
                        elem.append(val)
                        val.text = value
                    d = qc_tags[option]
                    for val in d.keys():
                        elem.set(val, d[val])
                else:
                    if option in data['d_%s' % i].keys():
                        elem = etree.Element('%s' % option)
                        test_case.append(elem)
                        elem.text = data['d_%s' % i]['%s' % option]
                        d = qc_tags[option]
                        for val in d.keys():
                            elem.set(val, d[val])

            ''' *******************   define test_case_step  ******************* '''

            test_case_steps = etree.Element('test_case_steps')
            test_case.append(test_case_steps)

            # check number of qc_test_case step
            l = 1
            while 'step_%s' % l in data['d_%s' % i].keys():
                l += 1
            n_case_step = l - 1
            step_stat = 'Not Analyzed'
            for n in range(n_case_step):
                k = n + 1
                test_case_step = etree.Element('test_case_step')
                test_case_steps.append(test_case_step)

                if data['d_%s' % i]['step_%s' % k][3] != 'Passed':
                    step_stat = 'Failed'
                elif step_stat == 'Not Analyzed':
                    step_stat = 'Passed'

                m = 0
                for step in qc_tags_options_steps:
                    elem = etree.Element('%s' % step)
                    test_case_step.append(elem)
                    elem.text = data['d_%s' % i]['step_%s' % k][m]
                    m += 1
                    d = qc_tags[step]
                    for val in d.keys():
                        elem.set(val, d[val])

            ''' *******************   define test_case_run  ******************* '''

            test_case_run = etree.Element('test_case_run')
            test_case.append(test_case_run)

            tag = 'tags_' + system + '_test_case_run'

            # read qc tags of test case
            qc_tags_options_run = self.iniCo.read_all_values(tag)[0]

            for option in qc_tags_options_run:
                d = qc_tags[option]
                if option == 'test_case_run_status':
                    elem = etree.Element('%s' % option)
                    test_case_run.append(elem)
                    if self.fail_test != 'default' and step_stat == 'Failed':
                        elem.text = self.fail_test
                    else:
                        elem.text = step_stat
                    for val in d.keys():
                        elem.set(val, d[val])
                if option in data['d_%s' % i].keys():
                    elem = etree.Element('%s' % option)
                    test_case_run.append(elem)
                    elem.text = data['d_%s' % i]['%s' % option]
                    for val in d.keys():
                        elem.set(val, d[val])

        if writeFile:
            tree.write(open(self.xml_out_path, 'w'))
        else:
            return etree.tostring(root)



if __name__ == '__main__':
    RobotTags("C:\\Data\\test result\\Noutput.xml", "C:\\Data\\test result\\out.xml").gen_xml()
   # RobotTags("C:\\Data\\test result\\Noutput.xml", "C:\\Data\\test result\\out.xml").get_tags()
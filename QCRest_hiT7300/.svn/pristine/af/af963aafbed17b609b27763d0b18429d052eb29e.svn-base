__author__ = 'Rodolfo Andrade'

try:
    import lxml.etree as ET
except:
    import xml.etree.ElementTree as ET

    print 'Consider installing lxml library which is much faster!'

import argparse
import itertools
import logging
import os
import sys
import time

from QCRest_hiT7300 import RobotTags, gp_config_ini
from QCRest_hiT7300 import hiT7300_QC, ConnectionError, QCError

logger = logging.getLogger('QCRest')

def main(argv):

    args = getArgsParser().parse_args()

    path = args.inputsxml_file

    sxmlFileType = 'sxml.xml'

    if args.input_file_type == 'xml':
        sxmlFileType = '.xml'

    release = args.release

    # Establish connection to QC
    qc_con = hiT7300_QC(None, None, None, release=release)

    # Start Time
    start_time = time.time()

    # SXml
    sxml = '<report><test_sets/></report>'

    try:
        # Open connection to QC
        qc_con.login(None, None)

        if os.path.isfile(path):

            # If sxml already exists use it!
            if path[-8:] == 'sxml.xml':

                sxml = qc_con.readXmlFromFile(path)

            else:

                try:
                    process_time = time.time()

                    sxml = processFile(path)

                    parse_time = time.time() - process_time

                    logger.info('qcCreateStructure: %s, %s' % (path, parse_time))

                except:
                    # Error found
                    logger.info('qcCreateStructure: %s,-,-' % (path))

        else:

            root = ET.fromstring(sxml)

            for fileFound in getFileList(path):

                if fileFound.endswith("sxml.xml"):

                    try:
                        process_time = time.time()

                        xml = qc_con.readXmlFromFile(fileFound)

                        parse_time = time.time() - process_time

                        toAdd = ET.fromstring(xml)

                        for node in toAdd.findall('*/test_set'):
                            root[0].append(node)

                        logger.info('qcCreateStructure: %s, %s' % (fileFound, parse_time))

                    except:
                        # Error found
                        logger.info('qcCreateStructure: %s,-' % (fileFound))

                else:

                    try:
                        process_time = time.time()

                        xml = processFile(fileFound)

                        parse_time = time.time() - process_time

                        toAdd = ET.fromstring(xml)

                        for node in toAdd.findall('*/test_set'):
                            root[0].append(node)

                        logger.info('qcCreateStructure: %s, %s' % (fileFound, parse_time))

                    except:
                        # Error found
                        logger.info('qcCreateStructure: %s,-' % (fileFound))

            sxml = ET.tostring(root)

        if args.gen_sxml:
            # qc_con.saveXmlToFile(sxml, '.sxml.xml')
            exit()

        # Save xml for possible debug
        qc_con.saveXmlToFile(sxml, '.sxml.xml')

        # Upload to QC
        rest_time_start = time.time()

        if sxml == '<report><test_sets/></report>':

            logger.warning('Sxml file is empty! Please check if the file(s) exist!')

        else:

            processRest(qc_con, sxml, args)

        print 'Upload to REST: %s seconds!' % (time.time() - rest_time_start)

        print 'Congratulation! Script ran successfully!'
        print '--- %s seconds ---' % (time.time() - start_time)

    except (ConnectionError, QCError) as e:
        print ('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)

    finally:

        try:
            qc_con.logout()

        except (ConnectionError, QCError) as e:
            print ('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)

    print ("Bye bye!")

    if not args.silence:
        # Do a read just so that the window does not close
        raw_input('Press return to exit')

def getDataFromIni(ini_file=r'qc.ini'):
    data = {
        'qc_domain': None,
        'qc_server': None,
        'qc_project': None,
        'username': None,
        'passwd': None,
    }

    iniCo = None

    # Get ini info
    try:
        iniCo = gp_config_ini.ConfigIni(ini_file)

        key, val = iniCo.read_all_values('QC Server')
        iniQcDict = dict(itertools.izip(key, val))
        data['qc_domain'] = iniQcDict['qc_domain']
        data['qc_server'] = iniQcDict['qc_server']
        data['qc_project'] = iniQcDict['qc_project']

        key, val = iniCo.read_all_values('User')
        iniQcDict = dict(itertools.izip(key, val))
        data['username'] = iniQcDict['username']
        data['passwd'] = iniQcDict['passwd']

        key, val = iniCo.read_all_values('qcCreateStructure')
        iniQcDict = dict(itertools.izip(key, val))
        data['path'] = iniQcDict['path']

    except TypeError as e:
        print 'Info: No %s file found!\n\nIf your are not passing arguments, please create a qc.ini file in the same ' \
              'folder as this script. You can rename qc_template.ini to qc.ini and simply update the information ' \
              'inside.' % (ini_file)

    except KeyError as e:
        print 'Error: Wrong parameter defined in qc.ini: %s' % (e.message)

    return data

def processFile(fileFound):
    # Process file
    xml = RobotTags(fileFound, None).gen_xml(False)

    return xml

def processRest(qc_con, xml, args):
    if args.testplan or not (args.testplan or args.testlab):
        process_time = time.time()
        logger.info('qcCreateStructure: Start adding tests to test plan')
        qc_con.addTestToTestPlan(xml, True, False)
        logger.info('qcCreateStructure: Done in %ss' % (time.time() - process_time))

    if args.testlab or not (args.testplan or args.testlab):
        process_time = time.time()
        logger.info('qcCreateStructure: Start adding testsets to test lab')
        qc_con.addTestSet(xml)
        logger.info('qcCreateStructure: Done in %ss' % (time.time() - process_time))
        process_time = time.time()
        logger.info('qcCreateStructure: Start adding test instance to test lab')
        qc_con.addTestInstanceToTestLab(xml)
        logger.info('qcCreateStructure: Done in %ss' % (time.time() - process_time))

def warning(data):
    msg = '\nPlease be aware, you are importing the tests in folder/file \'%s\' to:\n\n' % (data['path'])
    msg += 'QC Server: %s\n' % (data['qc_server'])
    msg += 'QC Domain: %s\n' % (data['qc_domain'])
    msg += 'QC Project: %s\n' % (data['qc_project'])
    msg += '\nwith user \'%s\'!\n' % (data['username'])

    print msg

    if raw_input('\nIf you which to continue write \'Yes\'!') != 'Yes':
        exit()

def getArgsParser():
    parser = argparse.ArgumentParser(description='Create QC test lab and plan structure based on robot run!')
    parser.add_argument('-x', '--inputsxml_file', help="sxml Path: Path for file or folder with sxml files.")
    parser.add_argument('-s', '--input_file_type',
                        help="File type should be either \'sxml\' or \'xml\'. Default is \'sxml\'")
    parser.add_argument('-r', '--release', help="Release name: If passed, default login and QC server info is used." +
                                                "Supported values are: \'5.40.xx\' or \'5.50.xx\'")
    return parser

def getFileList(path):
    # Get list of files
    for currentDir, subFolders, files in os.walk(path, False):

        for fileinfolder in files:

            if fileinfolder.__contains__('.xml'):
                yield os.path.join(currentDir, fileinfolder)

if __name__ == '__main__':
    main(sys.argv)

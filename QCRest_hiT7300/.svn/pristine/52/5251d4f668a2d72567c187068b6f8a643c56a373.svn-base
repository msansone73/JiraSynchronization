__author__ = 'Rodolfo Andrade'

try:
    import lxml.etree as ET
except:
    import xml.etree.ElementTree as ET
    print 'Consider installing lxml library which is much faster!'

import argparse
import logging
import os
import sys
import time

try:
    from QCRest_hiT7300 import RobotTags
    from QCRest_hiT7300 import hiT7300_QC, ConnectionError, QCError
    
except:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)).rsplit("\\", 2)[0])

    from QCRest_hiT7300 import RobotTags
    from QCRest_hiT7300 import hiT7300_QC, ConnectionError, QCError

from QCRest_hiT7300 import RobotTags
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

    # Default import rule for failed tests (applicable for Transponders only)
    importFailRule = 'not_import'

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

                    sxml = processFile(path, importFailRule)

                    parse_time = time.time() - process_time

                    print '%s, %s' % (path, parse_time)

                except:
                    # Error found
                    print '%s,-,-' % (path)

        else:

            root = ET.fromstring(sxml)

            for fileFound in getFileList(path, sxmlFileType):

                if fileFound.endswith("sxml.xml"):

                    try:
                        process_time = time.time()
                        
                        xml = qc_con.readXmlFromFile(fileFound)
    
                        parse_time = time.time() - process_time
    
                        toAdd = ET.fromstring(xml)
    
                        for node in toAdd.findall('*/test_set'):
                            root[0].append(node)
    
                        print '%s, %s' % (fileFound, parse_time)
    
                    except:
                        # Error found
                        print '%s,-' % (fileFound)
                
                else:

                    try:
                        process_time = time.time()
    
                        xml = processFile(fileFound, importFailRule)
    
                        parse_time = time.time() - process_time
    
                        toAdd = ET.fromstring(xml)
    
                        for node in toAdd.findall('*/test_set'):
                            root[0].append(node)
    
                        print '%s, %s' % (fileFound, parse_time)
    
                    except:
                        # Error found
                        print '%s,-' % (fileFound)
            
            sxml = ET.tostring(root)

        # Save xml for possible debug
        qc_con.saveXmlToFile(sxml, '.sxml.xml')

        # Upload to QC
        rest_time_start = time.time()

        if sxml == '<report><test_sets/></report>':

            logger.warning('Sxml file is empty! Please check if the file(s) exist!')

        else:

            processRest(qc_con, sxml)

        print 'Upload to REST: %s seconds!' % (time.time() - rest_time_start)
            
        print 'Congratulation! Script ran successfully!'
        print '--- %s seconds ---' % ( time.time() - start_time)

    except (ConnectionError, QCError) as e:
        raise AssertionError('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)
        #print ('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)

    finally:

        try:
            qc_con.logout()

        except (ConnectionError, QCError) as e:
            raise AssertionError('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)
            #print ('\nUps, an exception was raised: ' + e.expr + ' - ' + e.msg)

    print ("Bye bye!")

def processFile(fileFound, update_fail_tests_with_status):

    # Process file
    xml = RobotTags(fileFound, None, update_fail_tests_with_status).gen_xml(False)

    return xml

def processRest(qc_con, xml):

    process_time = time.time()
    print '\nQCREST: Start adding tests to test plan'
    qc_con.addTestToTestPlan(xml, True, False)
    print 'QCREST: Done in %ss' % (time.time() - process_time)
    process_time = time.time()
    print '\nQCREST: Start adding testsets to test lab'
    qc_con.addTestSet(xml)
    print 'QCREST: Done in %ss' % (time.time() - process_time)
    process_time = time.time()
    print '\nQCREST: Start adding test instance to test lab'
    qc_con.addTestInstanceToTestLab(xml)
    print 'QCREST: Done in %ss' % (time.time() - process_time)

    process_time = time.time()
    print '\nQCREST: Start adding test run to test lab'
    qc_con.addTestRunToTestLab(xml)
    print 'QCREST: Done in %ss' % (time.time() - process_time)

def getArgsParser():
    parser = argparse.ArgumentParser(description='Create QC test lab and plan structure based on robot run and add' +
                                                 'run info!')
    parser.add_argument('-x','--inputsxml_file', help="sxml Path: Path for file or folder with sxml files.")
    parser.add_argument('-s','--input_file_type', help="File type should be either \'sxml\' or \'xml\'. Default is \'sxml\'")
    parser.add_argument('-r','--release', help="Release name: If passed, default login and QC server info is used." +
                                               "Supported values are: \'5.40.xx\' or \'5.50.xx\'")
    return parser

def getFileList(path, sxmlFileType):

    # Get list of files
    for currentDir, subFolders, files in os.walk(path, False):

        for fileinfolder in files:

            if fileinfolder.__contains__(sxmlFileType):

                yield os.path.join(currentDir, fileinfolder)

if __name__ == '__main__':
    main(sys.argv)
    

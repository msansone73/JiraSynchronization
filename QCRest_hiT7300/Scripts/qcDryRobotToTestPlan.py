#!/usr/bin/python
'''
Created on 22/12/2015

@author: jenkins
'''

import sys
import getopt
import os

from tempfile import mkstemp
from shutil import move
from subprocess import Popen

def main(argv):
    '''
    '''
    
    try:
        args = getopt.getopt(sys.argv, "hi:o:",["RobotFile="])[1]
        
    except getopt.GetoptError:
        print "\n"
        print "--------------------------------------------------------------"
        print "|                                                            |"
        print "| Error: RobotToTestPlan.py -f <RobotFile>                   |"
        print "|                                                            |"
        print "--------------------------------------------------------------"
        print "\n"
        
    if len(args) == 2:
        print "\n"
        print "--------------------------------------------------------------"
        print "|                                                            |"
        print "| Help:                                                      |"
        print "|                                                            |"
        print "| This convert the Robot Test (.txt and .robot) in Dry Test. |"
        print "| This Test should be use to run in Robot only to created    |"
        print "| the QC Test Plan and QC Test Lab.                          |"
        print "|                                                            |"
        print "| After run the Test, you need to use the qcAddRuns.py       |"
        print "| to add the Test to the QC.                                 |"
        print "|                                                            |"
        print "| Usage:  qcDryRobotToTestPlan.py -f <RobotFile>             |"
        print "| Output: <RobotFile>_RobottoQCImpot.<txt or robot>          |"
        print "|                                                            |"
        print "--------------------------------------------------------------"
        print "\n"
        sys.exit()
        
    elif len(args) != 3:
        print "\n"
        print "--------------------------------------------------------------"
        print "|                                                            |"
        print "| Error: qcDryRobotToTestPlan.py -f <RobotFile>              |"
        print "|                                                            |"
        print "--------------------------------------------------------------"
        print "\n"
        sys.exit()
    
    for x in range(len(args)):
        if args[x] == '-h' or args[x] == '--help':
            print "\n"
            print "--------------------------------------------------------------"
            print "|                                                            |"
            print "| Error: qcDryRobotToTestPlan.py -f <RobotFile>              |"
            print "|                                                            |"
            print "--------------------------------------------------------------"
            print "\n"
            sys.exit()
        
        if args[x] in ("-f"):
            RobotPath = args[x+1]
    
    #Check if robot fine is in .robot or .txt
    if RobotPath.rsplit(".", 1)[-1] != "robot" and RobotPath.rsplit(".", 1)[-1] != "txt":
        print "\nError: Only Support .txt and .robot files\n"
        sys.exit()
        
    RobotPath = RobotPath.replace("/","\\")
    
    # Read file to a variable
    file_Robot = open(RobotPath, 'r')
    datafile = file_Robot.read().splitlines()
    file_Robot.close()
    
    fh, temp_new_file = mkstemp()
    temp_new_file = temp_new_file + "." + RobotPath.rsplit(".", 1)[1]
    
    print "\nInfo: Created Temp File"
    print "\n      " + temp_new_file
    
    # Write new file
    new_file = open(temp_new_file, 'w')
    
    new_datafile = [datafile[0]]
    for n_item in range(1, len(datafile)):
        if "..." in datafile[n_item][4:7] or "..." in datafile[n_item][9:12]:
            new_datafile[-1] = new_datafile[-1].rsplit("\r\n",1)[0] + datafile[n_item].split("...",1)[1]
            
        else:
            new_datafile.append(datafile[n_item])
    
    #Extract QC kw
    Qckw = ['QCCREATETESTCASE', 'QCCLOSETESTCASE', 'QCADDTESTSTEP', 'QC_INFO', ':FOR', "[TIMEOUT]", "[TAGS]", "SETVARIABLE"]
    
    for readline in new_datafile:        
        if "    " in readline[:5]:
            writefile = False
            for QCkwfind in Qckw:
                if QCkwfind in readline.replace(" ","").upper():
                    writefile = True
            
            if writefile:
                if "[TEARDOWN]" in readline.upper():
                    teardown_line = "    [Teardown]"
                    readline = readline.replace("${TEST_STATUS}","No Run", 1)
                    teardown_kw = readline.split("    ")
                    
                    for n_item in range(0, len(teardown_kw)):
                        if "QCCLOSETESTCASE" in teardown_kw[n_item].replace(" ","").upper(): 
                            teardown_line = teardown_line + "    " + teardown_kw[n_item] + "    " + teardown_kw[n_item + 1]
                            new_file.write(teardown_line + "\n")
                            break
                
                elif "QCADDTESTSTEP" in readline.replace(" ","").upper():
                    QCADDTESTSTEP_line_split = readline.split("    ")

                    for x in QCADDTESTSTEP_line_split:
                        if x.replace(" ","").upper() == "QCADDTESTSTEP":
                            QC_Step_kw = x
                            break
                    
                    QCADDTESTSTEP_line_split_1 = readline.split(QC_Step_kw, 1)
                    
                    Add_to_run = QCADDTESTSTEP_line_split_1[1].split("    ")
                    
                    if len(Add_to_run) >= 4 :
                        Add_to_run[3] = "No Run"
                    
                    else:
                        Add_to_run.append("No Run")
                    
                    QCADDTESTSTEP_line_to_write = QCADDTESTSTEP_line_split_1[0] + x + "    ".join(Add_to_run)

                    new_file.write(QCADDTESTSTEP_line_to_write + "\n")
                
                elif "QCCREATETESTCASE" in readline.replace(" ","").upper():
                    QCADDTESTSTEP_line_split = readline.split("    ")

                    for x in QCADDTESTSTEP_line_split:
                        if x.replace(" ","").upper() == "QCCREATETESTCASE":
                            QC_Step_kw = x
                            break
                    
                    QCADDTESTSTEP_line_split_1 = readline.split(QC_Step_kw, 1)
                    
                    Add_to_run = QCADDTESTSTEP_line_split_1[1].split("    ")
                    
                    #Test_APS Test APS to NoApplicable
                    if len(Add_to_run) >= 6 :
                        Add_to_run[5] = "NoApplicable"
                    
                    else:
                        Add_to_run.append("NoApplicable")
  
                    #if missing automation_level to Fully automated
                    if len(Add_to_run) >= 7 :
                        pass
                    
                    else:
                        Add_to_run.append("Fully automated")
                    
                    QCADDTESTSTEP_line_to_write = QCADDTESTSTEP_line_split_1[0] + x + "    ".join(Add_to_run)

                    new_file.write(QCADDTESTSTEP_line_to_write + "\n")
                
                else:
                    new_file.write(readline + "\n")
                
            else:
                if "\\" in readline[:6]:
                    new_file.write(readline.replace("    \    ","    \    Comment    ") + "\n")
                
                else:
                    if "[TEARDOWN]" in readline.replace(" ","").upper():
                        new_file.write(readline.replace("[Teardown]","[Teardown]    Comment", 1) + "\n")
                        
                    else:
                        new_file.write(readline.replace("    ","    Comment    ", 1) + "\n")
                        
        else:
            if "LIBRARY" in readline[:10].upper():
                if "QC" in readline.upper():
                    new_file.write(readline + "\n")
                    
                else:
                    pass
            
            elif "RESOURCE" in readline[:10].upper():
                pass
            
            else:
                new_file.write(readline + "\n")
    
    new_file.close()
    os.close(fh)
    
    new_file_path = RobotPath.rsplit(".", 1)[0] + "_RobottoQCImpot." + RobotPath.rsplit(".", 1)[1]
    
    if os.path.isfile(new_file_path):
        print "\nInfo: Delete File"
        print "\n      " + new_file_path
        os.remove(new_file_path)
    
    move(temp_new_file, new_file_path)
    print "\nInfo: Created File"
    print "\n      " + new_file_path
    
    #Add find the run.py path
    sitepackages_path = "C:\\Python27\\Lib\\site-packages"
    name_run = "run.py"
    
    for root, dirs, files in os.walk(sitepackages_path):
        if name_run in files:
            runner = os.path.join(root, name_run)
            break
    
    #Run Robot Test
    QC_File = "--variable QC_File:\"" + new_file_path.replace("_RobottoQCImpot." + RobotPath.rsplit(".", 1)[1], "_sxml.xml") + "\""
    cmd = runner + " --pythonpath \"" + RobotPath.rsplit("\\", 1)[0] + "\":\"" + os.getcwd() + "\" " + QC_File + " --log NONE --report NONE \"" + new_file_path + "\""
    
    print "\nInfo: Run in Robot"
    print "\n      " + cmd
    
    c = Popen("python " + cmd, shell=True)
    c.wait()
    r = c.communicate()
    r = str(r[0])
    c.kill()
    
    #remove Temp file
    print "\nInfo: Delete File"
    print "\n      " + new_file_path
    os.remove(new_file_path)
    
    QC_import = raw_input("\nINFO: Import to QC? (Yes\\No) -> ")
    
    if QC_import[0].upper() == "Y":
        
        QC_import_version = raw_input("\nQC Version? (x.xx.xx) -> ")[:4] + ".xx"
        
        cmd = "\"" + os.getcwd() + "\\qcAddRuns.py\" -r " + QC_import_version + " -x \"" + new_file_path.replace("_RobottoQCImpot." + RobotPath.rsplit(".", 1)[1], "_sxml.xml") + "\""

        print "\nInfo: Run in qcAddRuns.py"
        print "\n      " + cmd
        
        c = Popen("python " + cmd, shell=True)
        c.wait()
        r = c.communicate()
        r = str(r[0])
        c.kill()
        
        print "\n WARN: Requirements and Target Cycle need to set manual in the QC."
    
    else:
        pass
    
    print "\n INFO: qcDryRobotToTestPlan End."
    QC_import = raw_input("\nType any key to close.")
    
if __name__ == "__main__":
    main(sys.argv)
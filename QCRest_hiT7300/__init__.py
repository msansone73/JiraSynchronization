# Import main class to handle QC
from hiT7300_QC import hiT7300_QC

# Import main Exception Classes for QC
from QCRest.qc import QCError
from QCRest.connect import ConnectionError

from QCRest_Robot import RobotTags
from RobotParser import gp_config_ini
# from RobotParser import gp_config_ini, gp_logger

from QCRest_Robot import QCRest_Robot as QCRest_hiT7300
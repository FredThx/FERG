#!/usr/bin/env python
# -*- coding:utf-8 -*
from FUTIL.my_logging import *
my_logging(console_level = DEBUG, logfile_level = INFO, details = False)

from node_red_dashboard import *
dash=node_red_dashboard('T-HOME/PI-DEUX')
dash.publish('test',33)

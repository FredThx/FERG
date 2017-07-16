#!/usr/bin/env python
# -*- coding:utf-8 -*

'''
	Programme principal de comptage electrique
	et enregistrement dans base de données
	
	la config se trouve dans 
			config.py
'''

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')
import time

from FUTIL.my_logging import *

my_logging(console_level = DEBUG, logfile_level = INFO, details = False)

import config

logging.info('comptage.py démarre')

home = config.get_installation()

home.start_comptage_secondaire()
home.start_comptage_general()

print 'press CTRL-C to stop process'

try: #Ca permet de pouvoir planter le thread avec un CTRL-C
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	home.stop_comptage_secondaire()
	home.stop_comptage_general()

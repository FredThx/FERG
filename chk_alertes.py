#!/usr/bin/env python
# -*- coding:utf-8 -*

####################################
'''
Lecture de la base de données des températures
Et envoie de mail si alerte.

Plus création des conso déduites.
'''
#################################### 

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FGPIO')
sys.path.insert(0,'../FUTIL')

import FERG.tempeDB
import FERG.installation
from FUTIL.my_logging import *
import FUTIL.mails


my_logging(console_level = INFO, logfile_level = INFO)

logging.info("Execution de chk_alertes.py")

#Gestion des consos electriques
import config
install = config.get_installation(physical_device = False)

install.deduit_conso_arithmetic()
install.deduit_conso_typiques()
install.calc_fuel()
install.check_alertes()

# Gestion des températures : même base que pour les consos electrique, mais pas même class
db = FERG.tempeDB.tempeDB(db_name=install.db.db_name, user=install.db.user, passwd=install.db.passwd, host=install.db.host, \
							mail = install.db.smtp, display = install.display)
db.check_alertes()
db.chk_mesures()

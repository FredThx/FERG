#!/usr/bin/env python
# -*- coding:utf-8 -*

####################################
'''
Enregistrement sur une Base de donnée 
des températures mesurés et transmise par RF
'''
#################################### 
#Pour travailler sur les sources
import sys
sys.path.insert(0,'../../FGPIO')
sys.path.insert(0,'../../FUTIL')

from FGPIO.rf_recept_io import *
from FERG.tempeDB import *
import datetime
from FUTIL.my_logging import *
import json

my_logging(console_level = DEBUG, logfile_level = DEBUG)

logging.info('rf_temp_io démarre')

db=tempeDB()

f_json = "rf_temp_io.json"
valeurs = {}

pc = rpiduino_io()
rf = temperature_rf_recept_io(pc.bcm_pin(4))

while True:
	capteurs = db.get_capteurs()
	if capteurs:
		for capteur in capteurs:
			if capteur[0] in rf.sensors:
				if rf.sensors[capteur[0]]!=capteur[1]:
					rf.sensors[capteur[0]]=capteur[1]
					logging.info("Nom du capteur %s modifié de %s à %s." % (capteur[0], rf.sensors[capteur[0]],capteur[1]))
			else:
				rf.add_sensor(capteur[0], capteur[1])
				logging.info("Capteur %s : %s ajoute" % (capteur[0:2]))
			logging.debug("Mesure de %s ..." % capteur[1])
			valeur = rf.read(capteur[1])
			logging.info("Mesure de %s : %s." % (capteur[1], valeur))
			if valeur != None :
				if capteur[2] != None and capteur[2] != '':
					try:
						valeur = eval(capteur[2])
					except Exception, e:
						logging.error("Error in function of the sensor : '%s'. %e" % (capteur[2], e))
						valeur = None
			if valeur != None:
				valeur = round(valeur,2)
				valeurs[capteur[1]]=valeur
				with open(f_json,"w") as f:
					json.dump(valeurs, f)
				db.add(capteur[1], datetime.datetime.now(), valeur)
	time.sleep(60)


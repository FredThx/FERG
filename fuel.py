#!/usr/bin/env python
# -*- coding:utf-8 -*

####################################
'''
Lecture de la base de données du niveau de la cuve de fuel
Et création des consos journalière.
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


jour = dernier_jour_calculé() +1 # = format datetime 

while jour < heure_derniere_mesure:
	date_dernière_mesure_J, dernière_mesure_J = dernière_mesure(jour) # mesure avant J(23:59)
	date_prochaine_mesure_J, prochaine_mesure_J = prochaine_mesure(jour) # mesure après J(23:59)
	mesure = prochaine_mesure_J + (dernière_mesure_J - prochaine_mesure_J)*(date_prochaine_mesure_J - jour(23:59) ) / (date_prochaine_mesure_J-date_dernière_mesure_J)
	enregistre(jour, mesure)
	jour+=1

	
#TODO : bien coder tout ça!
	
#!/usr/bin/env python
# -*- coding:utf-8 -*
from FERG.tempeDB import *
from FUTIL.my_logging import *

my_logging(console_level = DEBUG, logfile_level = DEBUG, details = False)

db_elect_init = conso_electriqueDB( \
				db_name = 'tempeDB', \
				user = 'fred', \
				passwd='achanger', \
				host = '192.168.10.10')
db_elect_fin = conso_electriqueDB( \
				db_name = 'tempeDB', \
				user = 'fred', \
				passwd='achanger', \
				host = '192.168.10.174')
				
cursor_init = db_elect_init.db.cursor()
req = "SELECT  Id, circuit, date_debut, date_fin, energie, puissance, compteur, type_horaire, analyse, archived " \
	+ "FROM consos_electrique WHERE Id > 6970749"
logging.debug('SQL==> '+req)
cursor_init.execute(req)

for (Id, circuit, date_debut, date_fin, energie, puissance, compteur, type_horaire, analyse, archived)  in cursor_init:
	logging.debug("%s,%s,%s-%s:%s,%s,%s,%s,%s,%s" % (Id, circuit, date_debut, date_fin, energie, puissance, compteur, type_horaire, analyse, archived))
	req = "INSERT INTO consos_electrique (circuit, date_debut, date_fin, energie, puissance, compteur, type_horaire, analyse, archived) " \
		+ "VALUES (%s, %s, %s , %s, %s, %s, %s, %s, %s)"
	db_elect_fin.action_sql_req(req, circuit, date_debut, date_fin, energie, puissance, compteur, type_horaire, analyse, archived)
cursor_init.close()

			
#!/usr/bin/env python
# -*- coding:utf-8 -*
from FERG.tempeDB import *
from FUTIL.my_logging import *

my_logging(console_level = DEBUG, logfile_level = DEBUG, details = False)

db_init = conso_electriqueDB( \
				db_name = 'tempeDB', \
				user = 'fred', \
				passwd='achanger', \
				host = '192.168.10.10')
db_fin = conso_electriqueDB( \
				db_name = 'tempeDB', \
				user = 'fred', \
				passwd='achanger', \
				host = '192.168.10.174')
				
cursor_init = db_init.db.cursor()
req = "SELECT  Id, capteur, date, temperature " \
	+ "FROM mesures WHERE Id > 954070"
logging.debug('SQL==> '+req)
cursor_init.execute(req)

for (Id, capteur, date, temperature)  in cursor_init:
	logging.debug("%s,%s,%s:%s" % (Id, capteur, date, temperature))
	req = "INSERT INTO mesures (capteur, date, temperature) " \
		+ "VALUES (%s, %s, %s)"
	db_fin.action_sql_req(req, capteur, date, temperature)
cursor_init.close()

			
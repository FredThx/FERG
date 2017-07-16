#!/usr/bin/env python
# -*- coding:utf-8 -*

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../../FGPIO')
sys.path.insert(0,'../../FUTIL')

import mysql.connector
import time
import functools
import threading
import datetime
import logging
from circuit import *
from FUTIL.mails import *


class DB:
	""" Classe pour une base de données pour enregistrement données"""
	def __init__(self, db_name="tempeDB", user="fred", passwd="achanger", host="192.168.10.10", mail = None):
		'''Initialisation
			- db_name		:	nom de la base de données
			- user			:	user de la base de données
			- passwd		:	password de la base de données
			- host			:	host de la base de données
			- mail			:	FUTIL.mails.gmail
		'''
		self.db_name = db_name
		self.user = user
		self.passwd = passwd
		self.host = host
		self.db = None
		self.connect()
		self.smtp = mail
		self._sql_reqs = [] # Stock les requetes actions (INSERT) avant de les executer
		self.lock = threading.Lock()
	
				
	def connect(self):
		'''Connecte the database
		'''
		try:
			self.db =  mysql.connector.connect(database=self.db_name, user = self.user, password = self.passwd, host = self.host)
		except mysql.connector.errors.Error, e:
			logging.error('mysql Reconnection failed. ' + str(e))
	
	@staticmethod
	def unError(fonction):
		'''Decorateur pour eviter les erreurs
		Si erreur dans une des methodes, on essaye de reconnecter la base de données 1 fois
		Si ca ne passe toujours pas, on abandonne'''
		@functools.wraps(fonction) # ca sert pour avoir un help(SBClient) utile
		def UnErrorFonction(self,*args, **kwargs):
			try:
				return fonction(self,*args, **kwargs)
			except mysql.connector.errors.Error as e: # pour uniquement mysql : mysql.connector.errors.Error
				logging.warning(repr(e) + ' in ' + fonction.__name__)
				logging.warning("Reconnection en cours ...")
				self.connect()
				try:
					return fonction(self,*args, **kwargs)
				except Exception, e:
					logging.error('Reconnection failed. ' + str(e))
		return UnErrorFonction
		
		
	def chk_mesures(self, nom = None):
		''' Vérifie que les mesures sont bien réalisées
			Envoie un email cas échéant
		'''
		cursor = self.db.cursor()
		req = "SELECT id, nom, table_donnees, duree, message, contact, duree_repetition, date_envoie FROM grandeur_mesuree WHERE test_enregistrement = 1"
		if nom != None:
			req += " AND nom = %s"
			cursor.execute(req,(nom))
		else:
			cursor.execute(req)
		grandeur_mesurees = cursor.fetchall()
		for grandeur_mesuree in grandeur_mesurees:
			[alerte_id, nom, table_donnees, duree, message, contact, duree_repetition, date_envoie] = grandeur_mesuree
			duree = datetime.timedelta(hours = float(duree))
			if table_donnees == 'consos_electrique':
				champ_date = 'date_fin'
				champ_mesure = 'circuit'
			else:
				champ_date = 'date'
				champ_mesure = 'capteur'
			# Pour éviter le risque injection SQL sur table_donnees, on limite à 40 caracteres
			table_donnees = table_donnees[:40]
			req = "SELECT " + champ_date + " FROM "+ table_donnees +" WHERE " + champ_mesure + " = %s AND " + champ_date + " = (SELECT MAX(" + champ_date + ") FROM "+ table_donnees +" WHERE " + champ_mesure + " = %s)"
			cursor.execute(req,(nom, nom))
			derniere_mesure = cursor.fetchone()
			if derniere_mesure != None:
				derniere_mesure = derniere_mesure[0]
				test =  datetime.datetime.now() - derniere_mesure > duree
				if test and (date_envoie==None or date_envoie + datetime.timedelta(hours=duree_repetition) < datetime.datetime.now()):
					if '%s' in message:
						message = message % derniere_mesure
					req = "SELECT email FROM contacts WHERE nom = '%s'" % (contact)
					cursor.execute(req)
					email = cursor.fetchone()
					if self.smtp.send_mail(email[0], u'Alerte enregistrement', message):
						req = "UPDATE grandeur_mesuree SET date_envoie = %s WHERE id = %s"
						cursor.execute(req,(datetime.datetime.now(), alerte_id))
						self.db.commit()

class DB_buffered(DB):
	'''Juste pour que l'héritage de @DB.unError fonctionne
	'''
	@DB.unError
	def _action_sql_req(self):
		''' Execute the request in _sql_reqs on database.
		'''
		cursor = self.db.cursor()
		while self._sql_reqs:
			req = self._sql_reqs[0][0]
			args = self._sql_reqs[0][1]
			logging.debug('SQL==> "%s"%s' % (req, args))
			cursor.execute(req, args)
			self.db.commit()
			del self._sql_reqs[0]
			logging.debug('SQL=> ok')

	def action_sql_req(self, req, *args):
		'''Add the request in _sql_reqs
			and run _action_sql_req
			- req		:	sql resquest
			- *args		:	les arguments de la requetes (qui vont avec  %s)
		'''
		with self.lock:
			self._sql_reqs.append([req,args])
			self._action_sql_req()

		
class tempeDB(DB_buffered):
	""" Classe pour une base de données pour enregistrement de la temperature"""
#	def __init__(self, db_name="tempeDB", user="fred", passwd="achanger", host="192.168.10.10"):
#		DB.__init__(self,db_name, user, passwd, host)
	
	@DB.unError	
	def add(self, capteur, date, temperature):
		""" INSERT sur la table "mesures" une date et une température"""
		(min, max) = self.get_min_max(capteur)
		if min < temperature < max:
			req = "INSERT INTO mesures (capteur, date, temperature) VALUES ( '%s', '%s' , %s)" % (capteur, date.strftime('%Y-%m-%d %H:%M:%S'), temperature)
			self.action_sql_req(req)
		else:
			logging.error('Temperature (%s) out of range : %s (must be between %s and %s)' % (capteur, temperature, min, max))
	
	def get_min_max(self, capteur):
		'''Renvoie un tuple (min, max) représentant les valeurs possibles mini et maxi de la mesure
		'''
		try:
			req = "SELECT min, max FROM capteurs WHERE nom = '%s'" % capteur
			cursor = self.db.cursor()
			cursor.execute(req)
			result = cursor.fetchone()
			logging.debug("get_min_max : result = " + str(result))
			(a,b) = result
		except:
			return (-99999,99999)
		else:
			return result
	
	@DB.unError
	def last_temperature(self, capteur=None):
		'''Return the last temperature 
		'''
		if capteur == None:
			capteurs = [n[1] for n in self.get_capteurs()]
		else:
			capteurs = [capteur]
		result = {}
		cursor = self.db.cursor()
		for capt in capteurs:
			req = "SELECT  temperature FROM mesures WHERE capteur=%s AND date = (SELECT MAX(date) FROM mesures WHERE capteur=%s)"
			cursor.execute(req,(capt, capt))
			temperature = cursor.fetchone()
			if temperature != None:
				result[capt] = float(temperature[0])
		if capteur != None:
			try:
				return result[capteur]
			except KeyError:
				return None
		else:
			return result
			
	@DB.unError			
	def check_alertes(self):
		'''Vérifie la tables des alertes 
			et envoie un mail si besoin.
		'''
		cursor = self.db.cursor()
		req = "SELECT `id`,`capteur`,`min_max`,`valeur`,`message`,`contact`,`duree_repetition`,`date_envoie` FROM `alertes`";
		cursor.execute(req)
		alertes = cursor.fetchall()
		for alerte in alertes:
			[alerte_id, capteur, min_max, valeur, message, contact, duree_repetition, date_envoie] = alerte
			req = "SELECT temperature FROM mesures WHERE capteur=%s AND date = (SELECT MAX(date) FROM mesures WHERE capteur=%s)"
			cursor.execute(req,(capteur, capteur))
			temperature = cursor.fetchone()
			if temperature != None:
				temperature = temperature[0]
				if min_max=='MIN':
					test = temperature < valeur
				else:
					test = temperature > valeur
				if test and (date_envoie==None or date_envoie + datetime.timedelta(hours=duree_repetition) < datetime.datetime.now()):
					if '%s' in message:
						message = message % temperature
					req = "SELECT email from contacts where nom = '%s'" % contact
					cursor.execute(req)
					email = cursor.fetchall()
					if self.smtp.send_mail(email[0][0], u'Alerte températures', message):
						req = "UPDATE alertes SET date_envoie = '%s' WHERE id = '%s'" % (datetime.datetime.now(), alerte_id)
						cursor.execute(req)
						self.db.commit()
	
	@DB.unError					
	def get_capteurs(self):
		'''Renvoie la liste des capteurs
		'''
		cursor = self.db.cursor()
		req = "SELECT `id`, `nom`, `formule` FROM `capteurs`"
		logging.debug('SQL==> '+req)
		cursor.execute(req)
		result = cursor.fetchall()
		if isinstance(result, list):
			return result
		else:
			return []
	

class conso_electriqueDB(DB_buffered):
	''' Classe pour une base de données pour enregistrement des consos electriques
	'''
	@DB.unError
	def add(self, circuit, date_debut, date_fin, energie, puissance, compteur, type_horaire=''):
		""" INSERT sur la table "consos_electrique" les infos de consommation"""
		req = "INSERT INTO consos_electrique (circuit, date_debut, date_fin, energie, puissance, compteur, type_horaire) VALUES (%s, %s, %s , %s, %s, %s, %s)"
		self.action_sql_req(req, circuit, date_debut.strftime('%Y-%m-%d %H:%M:%S'), date_fin.strftime('%Y-%m-%d %H:%M:%S'), energie, puissance, compteur, type_horaire)
	
	@DB.unError
	def get_last_counter(self, circuit):
		''' recherche la dernière valeur du compteur
		'''
		cursor = self.db.cursor()
		req = "SELECT  compteur  FROM consos_electrique WHERE circuit = %s AND date_debut = (SELECT MAX(date_debut) FROM  consos_electrique WHERE circuit = %s)"
		logging.debug('SQL==> ' + req + str((circuit, circuit)))
		cursor.execute(req, (circuit, circuit))
		result = cursor.fetchone()
		cursor.close()
		if result:
			result = float(result[0])
		else:
			result = 0
		return result

	@DB.unError
	def eclate_circuit(self):
		'''Analyse les consommations et éclate les valeurs sur des sous-circuits ou electric_device
		'''
		pass
		
	@DB.unError
	def get_circuits_mesures(self):
		'''Extrait les circuits
		'''
		cursor = self.db.cursor()
		req = "SELECT  nom, parent, eclatable, puissance_maxi, energie_maxi_jour FROM circuit"
		logging.debug('SQL==> '+req)
		cursor.execute(req)
		circuits = []
		for (nom, parent, eclatable, puissance_maxi, energie_maxi_jour)  in cursor:
			circuits.append(circuit_mesure(nom, parent, eclatable, puissance_maxi, energie_maxi_jour))
		logging.debug("get_circuits_mesures : %s" % str(circuits))
		cursor.close()
		return circuits
		
	@DB.unError
	def get_electric_devices(self):
		'''Extrait les circuits electric_device
		'''
		cursor = self.db.cursor()
		req = "SELECT  nom, parent, puissance_maxi, energie_maxi_jour, puissance_typique FROM electric_device"
		logging.debug('SQL==> '+req)
		cursor.execute(req)
		circuits = []
		for (nom, parent, puissance_maxi, energie_maxi_jour, puissance_typique)  in cursor:
			logging.debug("electric_device : %s puissance_typique = %s" % (nom, puissance_typique))
			circuits.append(electric_device(nom, parent, puissance_maxi, energie_maxi_jour, puissance_typique))
		logging.debug("get_electric_devices : %s" % str(circuits))
		cursor.close()
		return circuits
	
	#@DB.unError
	def get_conso(self, nom_circuit, date_debut):
		'''renvoie la conso d'un circuit à une date de début
		'''
		cursor = self.db.cursor()
		req = u'SELECT  Id, date_debut, date_fin, energie, puissance, type_horaire FROM consos_electrique WHERE circuit = %s AND date_debut = %s;'
		logging.debug('SQL==> '+ req )
		logging.debug('nom_circuit : %s, date_debut : %s' % (nom_circuit, date_debut.__repr__()))
		cursor.execute(req, (nom_circuit, date_debut))
		results = cursor.fetchall()
		cursor.close()
		if len(results)==0:
			logging.warning("Pas de conso pour le circuit : %s at %s" % (nom_circuit, date_debut))
			return None
		elif len(results)>1:
			logging.warning("Trop de conso pour le circuit : %s at %s" % (nom_circuit, date_debut))
			logging.warning("Seule la premiere conso est prise en compte")
		return results[0]
	
	@DB.unError
	def get_last_power(self, nom_circuit):
		''' Renvoie la dernière puissance d'un circuit
		'''
		cursor = self.db.cursor()
		req = u'SELECT  puissance FROM consos_electrique WHERE circuit=%s AND date_debut = (SELECT MAX(date_debut) FROM consos_electrique WHERE circuit=%s)'
		logging.debug('SQL==> '+ req )
		logging.debug('nom_circuit : %s' % (nom_circuit))
		cursor.execute(req, (nom_circuit))
		power = cursor.fetchone()
		return power
	
	@DB.unError
	def get_last_date(self, nom_circuit):
		''' Renvoie la derniere date a laquelle la puissance du circuit a ete enregistree
		'''
		cursor = self.db.cursor()
		req = u"SELECT MAX(date_debut) FROM consos_electrique WHERE circuit = '%s'" % nom_circuit
		logging.debug('SQL==> '+ req )
		cursor.execute(req)
		result = cursor.fetchone()
		try:
			return result[0]
		except IndexError:
			return None
	
	@DB.unError
	def get_last_date_power_under_than(self, nom_circuit, power_level):
		''' Renvoie la derniere date a laquelle la puissance du circuit a ete en dessous de power_level
		'''
		cursor = self.db.cursor()
		req = u'SELECT MAX(date_debut) FROM `consos_electrique` WHERE circuit = %s and puissance < %s'
		logging.debug('SQL==> '+ req )
		logging.debug('nom_circuit : %s, powel_level : %s' % (nom_circuit, power_level))
		cursor.execute(req, (nom_circuit, power_level))
		result = cursor.fetchone()
		try:
			return result[0]
		except IndexError:
			return None
	
	@DB.unError
	def get_average_power(self, nom_circuit, duration = 3600):
		'''Renvoie la puissance moyenne pendant la période.
			- nom_circuit	:	nom du circuit electriques
			- duration		:	durée en seconde
		'''
		cursor = self.db.cursor()
		date_now = datetime.datetime.now()
		date_init = date_now - datetime.timedelta(seconds=duration)
		req = u'SELECT SUM(energie) FROM consos_electrique WHERE circuit = %s and date_debut BETWEEN %s and %s'
		logging.debug('SQL==> '+ req )
		logging.debug('nom_circuit : %s, date_debut : %s / %s' % (nom_circuit, date_init, date_now))
		cursor.execute(req, (nom_circuit, date_init, date_now))
		result = cursor.fetchone()
		try:
			return result[0] / duration * 3600
		except IndexError, TypeError:
			return 0
	
	@DB.unError
	def get_not_eclate_consos(self, nom):
		'''Renvoie les consommations qui ne sont pas notées éclatées
		'''
		cursor = self.db.cursor()
		req = "SELECT  Id, date_debut, date_fin, energie, puissance, type_horaire FROM `consos_electrique` " \
				+ "WHERE circuit = '%s' AND analyse = false" % nom
		logging.debug('SQL==> '+req+'->'+nom)
		cursor.execute(req)
		results = cursor.fetchall()
		cursor.close()
		return results
	
	@DB.unError
	def set_analyse(self, Id, analyse):
		''' Update the Id conso_electrique with flag analyse
		'''
		cursor = self.db.cursor()
		req = "UPDATE consos_electrique SET analyse = %s WHERE Id = %s" % (analyse, Id)
		logging.debug('SQL==> '+req)
		cursor.execute(req)
		self.db.commit()
		cursor.close()

class DBError(Exception): 
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return self.message

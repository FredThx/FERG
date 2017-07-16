#!/usr/bin/env python
# -*- coding:utf-8 -*

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../../FGPIO')
sys.path.insert(0,'../../FUTIL')

import time
import datetime
import json
from tempeDB import *
from FERG.circuit import *
from FUTIL.my_logging import *
from FUTIL.mails import *
from FGPIO.f_thread import *
from FGPIO.SCT013_v_io import *
from FERG.compteur_edf import *

#my_logging(console_level = INFO, logfile_level = DEBUG)

class installation:
	'''Installation electrique
	'''
	def __init__(self, db, circuits_mesures = [], electric_devices = [], seuil_delestage = None, buzzer = None, f_json = 'installation.json'):
		'''Initialisation
		'''
		self.db = db
		self.circuits_mesures = circuits_mesures
		self.electric_devices = electric_devices
		self.compteurs_secondaires = self.get_compteurs_secondaires()
		self.th_enregistre_circuits = None
		self.last_date_time_compteur_general = None
		self.update()
		self.seuil_delestage = seuil_delestage
		self.delestage = False
		self.f_json = f_json
		self.values = {}
		self.buzzer = buzzer
	
	def get_compteur_general(self):
		'''Renvoie le circuit général
		'''
		for circuit in self.circuits_mesures:
			if isinstance(circuit, circuit_general):
				return circuit
	
	@property
	def compteur_general(self):
		return self.get_compteur_general().compteur
	
	@property
	def nom_compteur_general(self):
		return self.get_compteur_general().nom
	
	
	def get_compteurs_secondaires(self):
		'''renvoie la liste des compteurs secondaire pour mesure par tore
		'''
		compteurs_secondaires = []
		for circuit in self.circuits_mesures:
			if isinstance(circuit, circuit_mesure) and not isinstance(circuit, circuit_general):
				compteurs_secondaires.append(circuit)
		return compteurs_secondaires
	
	def set_value(self, nom, value):
		'''Enregistre une valeur instantannée et met à jour fichier json
		'''
		self.values[nom] = value
		with open(self.f_json,"w") as f:
			json.dump(self.values, f)
	
	#########################################################
	#														#
	#				COMPTAGE GENERAL						#
	#														#
	#########################################################
		
	def start_comptage_general(self):
		'''Execution du deamon pour lecture du compteur edf
		'''
		self.last_date_time_compteur_general = datetime.datetime.now()
		if self.compteur_general:
			self.compteur_general.init_record()
			self.th_enregistre_general = f_thread(self.compteur_general.record, self.comptage_general_rec_function)
			self.th_enregistre_general.start()
	
	def stop_comptage_general(self):
		'''Stoppe le comptage principal
		'''
		if self.th_enregistre_general:
			self.compteur_general.stop_record()
			self.th_enregistre_general.stop()
		
	def comptage_general_rec_function(self, date_time, energy, power, counter):
		'''Fonction qui est executé à chaque mesure du compteur (soit nb_cycles tour de roue)
		'''
		logging.info("Enregistrement dans la base du compteur : %s" % str((self.nom_compteur_general, self.last_date_time_compteur_general, date_time, energy, power, counter/1000., self.compteur_general.type_horaire())))
		self.db.add(self.nom_compteur_general, self.last_date_time_compteur_general, date_time, energy, power, counter/1000., self.compteur_general.type_horaire())
		self.last_date_time_compteur_general = date_time
		# Delestage
		self.delest(power)
		# Enregistrement de la puissance instantanee
		self.set_value(self.nom_compteur_general, power)
			
		
	def delest(self, power):
		if power > self.seuil_delestage:
			logging.info("Puissance trop élevée : Delestage ...")
			self.delestage = 0
			for circuit in self.circuits_mesures + self.electric_devices:
				if circuit.delest:
					circuit.delest.on()
					self.delestage +=circuit.puissance_typique
					logging.info("Delestage de %s" % circuit.nom)
			if self.delestage == 0:
				self.delestage = 1
		elif self.delestage and power < self.seuil_delestage*0.9 - self.delestage:
			for circuit in self.circuits_mesures + self.electric_devices:
				if circuit.delest:
					circuit.delest.off()
					logging.info("Fin de delestage pour %s" % circuit.nom)
			self.delestage = False
				
	
	#########################################################
	#														#
	#				COMPTAGE SECONDAIRE						#
	#														#
	#########################################################
	
	def start_comptage_secondaire(self):
		'''Execution du deamon pour lecture des circuits secondaires
		'''
		if self.compteurs_secondaires:
			self.th_enregistre_circuits = f_thread(self.enregistre_circuits_secondaires)
			self.th_enregistre_circuits.start()
			
	def stop_comptage_secondaire(self):
		'''Stoppe le comptage secondaire
		'''
		if self.th_enregistre_circuits:
			self.th_enregistre_circuits.stop()
	
	def enregistre_circuits_secondaires(self):
		'''Mesure la puissance instantanée de chaque circuit toutes les secondes
			et enregistre une moyenne au bout d'une minute.
			Cette méthode doit tourner 24H/24H.
		'''
		date_debut = datetime.datetime.now()
		fin = time.time() + 60
		somme_mesure = {}
		nb_mesure = {}
		for circuit in self.compteurs_secondaires:
			somme_mesure[circuit.nom] = 0
			nb_mesure[circuit.nom] = 0
		#Mesures toutes les secondes pendant 1 minute
		while time.time()<fin and not self.th_enregistre_circuits.terminated:
			for circuit in self.compteurs_secondaires:
				somme_mesure[circuit.nom] += circuit.compteur.read()
				nb_mesure[circuit.nom] += 1
			time.sleep(1)
		if not self.th_enregistre_circuits.terminated:			
			#Calcul des moyennes et enregistrement database
			type_horaire = self.compteur_general.type_horaire()
			date_fin = datetime.datetime.now()
			for circuit in self.compteurs_secondaires:
				if nb_mesure[circuit.nom] == 0: #On ne sait jamais!!!
					moyenne = 0
				else:
					moyenne = somme_mesure[circuit.nom] / nb_mesure[circuit.nom]
				energie = moyenne * ((date_fin - date_debut).seconds) / 3600.0
				logging.info("Enregistrement dans la base du compteur : %s, du %s à %s : %s, %s, %s, %s" % (circuit.nom, date_debut, date_fin, energie, moyenne,0,type_horaire))
				self.db.add(circuit.nom, date_debut, date_fin, energie, moyenne,0,type_horaire)
				self.set_value(circuit.nom, moyenne)
	
	
	#########################################################
	#														#
	#			GESTION DES CIRCUITS : ECLATAGES ...		#
	#														#
	#########################################################	
	

	def update(self):
		'''Calcul les champs .enfants des circuits
		'''
		#self.circuits_mesures = self.db.get_circuits_mesures()
		#self.electric_devices = self.db.get_electric_devices()
		for circuit_parent in self.circuits:
			for circuit_enfant in self.circuits:
				if circuit_enfant.parent == circuit_parent:
					logging.debug("%s.enfants.append(%s)" % (circuit_parent.nom, circuit_enfant.nom))
					circuit_parent.enfants.append(circuit_enfant)
		# self.general = self.get_general()
		# if not self.general:
			# logging.error('Aucun circuit general dans la base de données')
			
	def deduit_conso_typiques(self):
		'''Deduit les consommations des electric_device quand
			dans un sous-circuit, tous les circuits non mesurés ont des consos typiques
		'''
		logging.info("----Eclatage typique----")
		for circuit_mes in self.circuits_mesures:
			if circuit_mes.is_deductible_typically():
				logging.info("Eclatage (typique) du circuit : %s" % circuit_mes.nom)
				compteur_conso = 0
				compteur_conso_enfants = 0
				#Calcul des possibilités
				possibilite = circuit_mes.combinaisons_enfants_typiques()
				# Tri des possibilité par puissances croissante
				possibilite.sort(key = lambda solution: circuit_mes.comb_sum(solution))
				logging.debug("Liste des possibilites : %s" % possibilite)
				# liste des valeurs correspondantes
				possibilite_valeur = [circuit_mes.comb_sum(solution) for solution in possibilite]
				logging.debug("Liste des valeurs des possibilites : %s" % possibilite_valeur)
				# Analyse de toutes les consomations
				for (Id, date_debut, date_fin, energie, puissance, type_horaire) in self.db.get_not_eclate_consos(circuit_mes.nom):
					logging.debug("Eclatage : Id = %s ,%.2f watts à %s" % (Id, puissance, str(date_debut)))
					compteur_conso += 1
					#Recherche de la solution la plus proche
					idx_solution = self.idx_nearest(possibilite_valeur, puissance)
					puissance_combinee = possibilite_valeur[idx_solution]
					logging.debug('Solution la plus proche trouvée : Idx=%s, val=%s' % (idx_solution, puissance_combinee))
					# création des consos eclatées pour les circuits qui sont dans la solution
					for circuit_enfant in possibilite[idx_solution]:
						compteur_conso_enfants += 1
						puissance_enfant = 1.0*circuit_enfant.puissance_typique * puissance / puissance_combinee
						energie_enfant = puissance_enfant * ((date_fin - date_debut).seconds) / 3600.0
						self.db.add(circuit_enfant.nom, \
									date_debut, \
									date_fin, \
									energie_enfant, \
									puissance_enfant, \
									0, \
									type_horaire)
						self.set_value(circuit_enfant.nom, puissance_enfant)
					# création des consos à zéro pour les circuits qui ne sont pas dans la solution
					for circuit_enfant in circuit_mes.enfants:
						if circuit_enfant not in possibilite[idx_solution]:
							compteur_conso_enfants += 1
							self.db.add(circuit_enfant.nom, \
									date_debut, \
									date_fin, \
									0, \
									0, \
									0, \
									type_horaire)
							self.set_value(circuit_enfant.nom, 0)
					self.db.set_analyse(Id, True)
				logging.info("Eclatage terminé : \n\t Nb de consos analysées : %s\n\t nb de consos crées (y compris les 0) : %s" % (compteur_conso, compteur_conso_enfants))
	
	def deduit_conso_arithmetic(self):
		'''Deduit les consommations des electric_device quand
			dans un sous-circuit, il n'y a qu'un seul circuit non mesuré
		'''
		logging.info("----Eclatage arithmetique----")
		for circuit_mes in self.circuits_mesures:
			deductible = circuit_mes.is_deductible_arithmetically()
			if deductible:
				logging.info("Eclatage arithmetique du circuit : %s" % circuit_mes.nom)
				compteur_conso = 0
				compteur_conso_enfants = 0
				for (Id, date_debut, date_fin, energie, puissance, type_horaire) in self.db.get_not_eclate_consos(circuit_mes.nom):
					logging.debug("Eclatage : Id = %s ,%.2f watts à %s" % (Id, puissance, str(date_debut)))
					compteur_conso += 1
					puissance_enfant = puissance
					energie_enfant = energie
					eclate = True
					for circuit_a_soustraire in deductible[1]:
						conso_cas = self.db.get_conso(circuit_a_soustraire.nom, date_debut)
						logging.debug("A soustraire : %s" % str(conso_cas))
						if conso_cas:
							(Id_cas, date_debut_cas, date_fin_cas, energie_cas, puissance_cas, type_horaire_cas) = conso_cas
							if date_fin != date_fin_cas:
								logging.warning("Incohérences dans les dates de fin!")
							puissance_enfant -= puissance_cas
							energie_enfant -= energie_cas
						else:
							logging.warning("Soustraction impossible pour %s de %s at %s" % (circuit_mes, circuit_a_soustraire, date_debut))
							eclate = False
					if eclate:
						logging.debug("Puissance calculee : %s sur %s" % (puissance_enfant, deductible[0]))
						compteur_conso_enfants += 1
						if puissance_enfant < 0 :
							logging.warning("Puissance négative : %s watts : corrige a zero." % puissance_enfant)
							puissance_enfant = 0
						if energie_enfant < 0 :
							logging.warning("Puissance négative : %s watts : corrige a zero" % energie_enfant)
							energie_enfant = 0
						self.db.add(deductible[0].nom, \
									date_debut, \
									date_fin, \
									energie_enfant, \
									puissance_enfant, \
									0, \
									type_horaire)
						self.db.set_analyse(Id, True)
						self.set_value(deductible[0].nom, puissance_enfant)
					else:
						# Si il s'agit d'une vieille mesure : aucune chance de la résoudre...
						if date_debut < datetime.datetime.now()-datetime.timedelta(days=1):
							self.db.set_analyse(Id, True)
				logging.info("Eclatage termine : \n\t Nb de consos analysees : %s\n\t nb de consos crees : %s" % (compteur_conso, compteur_conso_enfants))
	
	@property
	def circuits(self):
		return self.circuits_mesures + self.electric_devices
		
	# def get_general(self):
		# '''return the main circuit
		# '''
		# for circuit in self.circuits_mesures:
			# if isinstance(circuit, circuit_general):
				# return circuit
		
	
	def __repr__(self):
		repr = "Installation Electrique : \n"
		repr += "%s\n" % self.nom_compteur_general
		return repr
	
	####################
	# GESTION DES ALERTES
	####################	
	
	def check_alertes(self):
		''' A partir de la base de données,
			Vérifie les alertes programmées
				- puissance maxi dépassée
				- durée de fonctionnement trop long
				- .... TODO
			Et gènère les actions :
				- par defaut : mail
				- TODO : liste d'actions
		'''
		for circuit in self.circuits:
			if circuit.fonctionement_max and circuit.puissance_typique:
				last_date_under = self.db.get_last_date_power_under_than(circuit.nom, circuit.puissance_typique*0.50)
				last_date = self.db.get_last_date(circuit.nom)
				if last_date - last_date > datetime.timedelta(seconds = circuit.fonctionement_max):
					message = 'Alerte, le circuit %s a dépassé sa duree de fonctionnement maximum' % circuit.nom
					logging.info(message)
					self.db.smtp.send_mail('fredthx@gmail.com', 'Alerte Compteur', message)
					self.buzzer.bip_bip(time_end=30)
			if circuit.max_average_power and circuit.puissance_typique:
				average_power = self.db.get_average_power(circuit.nom, circuit.duration_average_power)
				if average_power > circuit.max_average_power:
					message = 'Alerte, le circuit %s a dépassé son taux de fonctionnement normal' % circuit.nom
					logging.info(message)
					self.db.smtp.send_mail('fredthx@gmail.com', 'Alerte Compteur', message)
					self.buzzer.bip_bip(time_end=30)
	
	####################
	# UTILS
	####################
	
	@staticmethod
	def idx_nearest(liste, val):
		''' liste must be sorted.
			return the index of the nearest value than val (cooking anglais!!)
		'''
		if len(liste) == 0:
			return None
		if len(liste) == 1 or val <= (liste[0] + liste[1])/2.0 : 
			return 0
		else:
			return 1 + installation.idx_nearest(liste[1:], val)
		
		
#########################################################
#                                                       #
#		EXEMPLE                                         #
#                                                       #
#########################################################

if __name__ == '__main__':
	db = conso_electriqueDB()
	install = installation(db)
	#install.deduit_conso_typiques()
	#install.deduit_conso_arithmetic()
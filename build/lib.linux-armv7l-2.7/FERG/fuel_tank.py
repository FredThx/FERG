#!/usr/bin/env python
# -*- coding:utf-8 -*

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')

from FUTIL.my_logging import *
import datetime

class fuel_tank(object):
	'''Une cuve fuel dont on mesure le niveau par un capteur ultrason.
		Le capteur est lu et transmis via wifi par un ESP8266 a la base de donnee
	'''
	loading_ratio = 0.25
	def __init__(self, bdd_name, pci = 11.86, density = 0.845, capacity = 1500):
		'''
			bdd_name		:	nom du capteur dans la base de données
			pci				:	Pouvoir Calorifique Inférieur (kWh/kg)
			density			:	densité en kg/litre
			capacity		:	capacity in liters
		'''
		self.bdd_name = bdd_name
		self.pci = pci
		self.density = density
		self.capacity = capacity
	
	def calculate_conso(self, db):
		'''calcul la conso journalière à partir de l'historique des hauteurs de cuve
			Le niveau de la cuve est enregistrée dans la table mesures (avec les températures)
			La consommation sera enregistree dans la table consos_electrique
				avec 
					- energie : l'énergie consommée dans la journée en Watts
					- puissance : le nb de litres consommés dans la journée
		'''
		logging.info('---- Calcul de la consommation en fuel ----')
		db_tempe = db.tempeDB() #La base de données des temperatures (en supposant que ce soit le même que celle des consos electriques)
		jour = db.get_last_date(self.bdd_name)
		if jour == None:
			# pour le premier enregistrement de consommation, on va rechercher la mesure de la cuve la plus vieille
			jour = db_tempe.get_next_mesure(self.bdd_name)
			if jour == None:
				return #S'il n'y a vraiment aucune données, on ne fait rien!
			else:
				jour = jour[0].date()
		jour +=datetime.timedelta(1) # Le lendemain
		jour = datetime.datetime.combine(jour,datetime.time(0)) # On va travailler avec des datetime TODO : refaire ci-dessus
		
		#Determination de la derniere mesure effectuee
		datetime_derniere_mesure = db_tempe.get_last_mesure(self.bdd_name)
		if datetime_derniere_mesure:
			datetime_derniere_mesure = datetime_derniere_mesure[0]
		
		while jour < datetime_derniere_mesure:
			jour_plus1 = jour + datetime.timedelta(1)
			date_derniere_mesure_J, derniere_mesure_J = db_tempe.get_last_mesure(self.bdd_name, jour) # mesure avant J(23:59)
			next_mesure = db_tempe.get_next_mesure(self.bdd_name, jour_plus1)  # mesure après J(23:59)
			if next_mesure:
				date_prochaine_mesure_J, prochaine_mesure_J = next_mesure
				mesure = (derniere_mesure_J - prochaine_mesure_J)/((date_prochaine_mesure_J - date_derniere_mesure_J).days)
				logging.info("Conso fuel du %s : %s" % (jour, mesure))
				#enregistre dans la base de donnees des conso electriques sauf s'il s'agit d'un remplissage
				if mesure > -self.capacity*fuel_tank.loading_ratio:
					db.add(circuit = self.bdd_name, \
							date_debut = jour, \
							date_fin = jour_plus1, \
							energie = mesure * self.density * self.pci * 1000., \
							puissance = mesure)
			jour = jour_plus1
		logging.info('---- Fin du calcul de la consommation en fuel ----')
#!/usr/bin/env python
# -*- coding:utf-8 -*
'''
	Fichier de configuration pour FERG
	
	Déclaration de l'installation
	
	
'''
#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FGPIO')
sys.path.insert(0,'../FUTIL')
sys.path.insert(0,'../isqueeze')

try:
	from FGPIO.mcp300x_hspi_io import *
	from FGPIO.SCT013_v_io import *
	from FGPIO.relay_io import *
	from FGPIO.lcd_i2c_io import *
	from FGPIO.lum_capteur_io import *
	from FGPIO.buzz_io import *
	from FGPIO.i2c_device_io import *
	from FERG.compteur_edf import *
except ImportError: 
	pass
try:
	from isqueeze import *
except ImportError:
	pass

from FERG.tempeDB import *
from FERG.installation import *
from FERG.circuit import *
from FERG.fuel_tank import *
from FERG.node_red_dashboard import *
import FUTIL.mails

def get_installation(physical_device = True):
	'''Renvoie une installation configurée
		si physical_device == False : on ne déclara pas les capteurs, mais uniquement le "squelette" de l'installation
	'''
	#
	#########################################################
	#														#
	#				GENERALITES								#
	#														#
	#########################################################
	#
	installation_name = "Le compteur du futur"
	# tres facultatif : un afficheur pour les alertes.
	display = SBClient('192.168.10.10', 9090, "CUISINE") #Ici une squeezeBox
	#
	#########################################################
	#														#
	#				BASE DE DONNEES							#
	#														#
	#########################################################
	#
	# Base de données pour les consos electriques
	db_elect = conso_electriqueDB( \
					db_name = 'tempeDB', \
					user = 'fred', \
					passwd='achanger', \
					host = '192.168.10.174', \
					mail = FUTIL.mails.gmail(gmail_account='monmail@gmail.com', gmail_pwd='xxxxx'))
	#
	#########################################################
	#														#
	#				DASHBOARD   							#
	#														#
	#########################################################
	#
	# Un dashboard red-node-ui
	dashboard = node_red_dashboard('T-HOME/FERG')
	
	#########################################################
	#														#
	#				MATERIEL								#
	#														#
	#########################################################
	#
	nom_compteur = 'General'

	# Nano pc : un Raspberry (ou pcduino)
	pc = rpiduino_io()
		
	if physical_device:		
		# Nano pc : un Raspberry (ou pcduino)
		pc = rpiduino_io()
		#
		#Le capteur heure creuse est réalisé avec un detecteur de tension
		# Il fonctionne comme un bouton poussoir vers la masse.
		capteur_heure_creuse = bt_io(pc.bcm_pin(24))
		#
		#Convertisseur Analogique/Numérique pour lecture analogique sur Rpi
		mcp3008 = mcp3008_hspi_io()
		#
		# CAPTEUR DE BANDE NOIRE DU COMPTEUR
		# 2 solutions : 
		#	- le capteur directement banché sur le Raspberry
		# Detecteur optique pour detection bande noire sur roue du compteur edf
		#capteur_roue = qrd1114_analog_io(mcp3008.pin[0])		
		#	- le capteur banché sur un arduino qui transmet l'info par i2c (atmega = i2c_device_io(pc=pc, addr = 0x12))
		# Atmega 328 pour detection bande noire sur roue du compteur edf connecté en mode i2c
		atmega = i2c_device_io(pc=pc, addr = 0x12)
		#
		#
		# Led qui s'allume quand la bande noire de la roue est détectée
		led = led_io(pc.bcm_pin(16))
		#
		#
		# Led qui s'allume en heures Creuses
		#led = led_io(pc.bcm_pin(20))
		#
		# Vieux compteur EDF
		compteur = compteur_edf( \
					#capteur = capteur_roue, 
					micro_controleur = atmega, \ # Selon choix du type de branchement du capteur optique
					capteur_hc = capteur_heure_creuse, \
					led = led, \
					intensity_max = 45, \
					energy_tr = 2.5, \
					nb_tours_mesure = 10)
		#
		# Les tores pour mesurer le courant sur différents circuits
		tores = {'circuit_1': SCT013_v_io(mcp3008.pin[1], Imax = 30.0, Vmax = 1.0), \
					'circuit_ce': SCT013_v_io(mcp3008.pin[2], Imax = 30.0, Vmax = 1.0), \
					'circuit_frigo': SCT013_v_io(mcp3008.pin[3], Imax = 30.0, Vmax = 1.0), \
					'circuit_ext_haut': SCT013_v_io(mcp3008.pin[4], Imax = 30.0, Vmax = 1.0), \
					'circuit_frigo_cuisine': SCT013_v_io(mcp3008.pin[5], Imax = 30.0, Vmax = 1.0), \
					'circuit_divers': SCT013_v_io(mcp3008.pin[6], Imax = 30.0, Vmax = 1.0) \
					}
		#
		#Relais de delestage du chauffe eau
		deleste_chauffe_eau = relay_io(pc.bcm_pin(23))
		deleste_chauffe_eau.off() # off : circuit fermé (pas de délestage)
		#
		
	else:
		tores = {'circuit_1': None, \
					'circuit_ce': None, \
					'circuit_frigo': None, \
					'circuit_ext_haut': None, \
					'circuit_frigo_cuisine': None, \
					'circuit_divers': None \
					}
		compteur = None
		deleste_chauffe_eau = None
	
	buzzer = buzz_io(pc.bcm_pin(25))
	#########################################################
	#														#
	#				LES CIRCUITS							#
	#														#
	#########################################################
	#
	
	# Circuit général avec Compteur EDF de type vieux!
	circuit_0 = circuit_general( \
		nom = nom_compteur, \
		puissance_maxi = 10000,
		energie_maxi_jour = 50000, \
		compteur = compteur)

	#Circuits secondaires mesurés
	
	circuit_1 = circuit_mesure( \
			nom = 'circuit_1', \
			parent = circuit_0, \
			eclatable = True, \
			puissance_maxi = 2000, \
			energie_maxi_jour = 7000, \
			compteur = tores['circuit_1'])

	circuit_ce = circuit_mesure( \
			nom = 'circuit_ce', \
			parent = circuit_1, \
			puissance_maxi = 1500, \
			energie_maxi_jour = 7000, \
			compteur = tores['circuit_ce'], \
			delest = deleste_chauffe_eau, \
			puissance_typique = 1300)

	circuit_frigo_cuisine = circuit_mesure( \
			nom = 'circuit_frigo_cuisine', \
			parent = circuit_0, \
			eclatable = True, \
			puissance_maxi = 2000, \
			energie_maxi_jour = 7000, \
			compteur = tores['circuit_frigo_cuisine'])

	circuit_frigo = circuit_mesure( \
			nom = 'circuit_frigo', \
			parent = circuit_frigo_cuisine, \
			eclatable = True, \
			puissance_maxi = 350, \
			energie_maxi_jour = 3000, \
			compteur = tores['circuit_frigo'])
	
	circuit_ext_haut = circuit_mesure( \
			nom = 'circuit_ext_haut', \
			parent = circuit_0, \
			eclatable = True, \
			puissance_maxi = 2000, \
			energie_maxi_jour = 7000, \
			compteur = tores['circuit_ext_haut'])
			
	circuit_divers = circuit_mesure( \
			nom = 'circuit_divers', \
			parent = circuit_0, \
			eclatable = True, \
			puissance_maxi = 2000, \
			energie_maxi_jour = 7000, \
			compteur = tores['circuit_divers'])
			
	circuits_mesures = [circuit_0, circuit_1, circuit_ce, circuit_frigo, circuit_ext_haut, circuit_frigo_cuisine, circuit_divers]
		
	# Circuit physique (ou appareil) non mesuré
	
	congelateur = electric_device( \
			nom = 'Congelateur', \
			parent = circuit_frigo, \
			puissance_maxi = 130, \
			energie_maxi_jour = 1500, \
			puissance_typique = 110, \
			max_average_power = 0.80*110, \
			duration_average_power = 2*3600,\
			fonctionement_max = 3600 # Si la conso est > 50% de la puisance typique pendant 1 heure : alerte
			)
	
	refrigerateur = electric_device( \
			nom = 'Refrigerateur', \
			parent = circuit_frigo, \
			puissance_maxi = 230, \
			energie_maxi_jour = 2800, \
			puissance_typique = 190, \
			max_average_power = 0.75*190,\
			duration_average_power = 2*3600,\
			fonctionement_max = 2*3600 # Si la conso est > 50% de la puisance typique pendant 2 heures : alerte
			)
			
	buanderie = electric_device( \
			nom = 'Buanderie_chaufferie', \
			parent = circuit_1 \
			)
	
	cuisine = electric_device( \
			nom = 'Cuisine', \
			parent = circuit_frigo_cuisine \
			)
	
	# total_tores = electric_device( \
			# nom = 'Total tores', \
			# fils = [circuit_1, circuit_ext_haut, circuit_frigo_cuisine, circuit_divers] \
			# )
	
	electric_devices = [congelateur, refrigerateur, buanderie, cuisine]

	#
	#########################################################
	#														#
	#				LA CUVE DE FUEL (facultatif)			#
	#														#
	#########################################################
	#

	cuve_fuel = fuel_tank("Cuvefuel")
	
	#
	#########################################################
	#														#
	#				L'INSTALLATION							#
	#														#
	#########################################################
	#
	return installation( \
				db = db_elect, \
				circuits_mesures = circuits_mesures, \
				electric_devices = electric_devices, \
				seuil_delestage = 8000, \
				buzzer = buzzer, \
				display = display, \
				name = installation_name, \
				fuel_tank = cuve_fuel, \
				dashboard = dashboard
				)
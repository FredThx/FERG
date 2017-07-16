#!/usr/bin/env python
# -*- coding:utf-8 -*
import itertools
import logging

class circuit():
	''' Un circuit électrique
	'''
	def __init__(self, nom, parent=None, puissance_maxi = None, energie_maxi_jour = None, delest = None, puissance_typique = None, fonctionement_max = None, max_average_power = None, duration_average_power = 3600):
		'''Initialisation
			- nom					:	nom du circuit
			- parent				:	circuit parent
			- puissance_maxi		:	puissance maximal (non utilise pour l'instant) TODO : alertes
			- energie_maxi_jour		:	energie_maxi_jour (non utilise pour l'instant) TODO : alertes
			- delest				:	relay_io qui peut couper le circuit quand l'installation totale est en delestage
			- puissance_typique		:	puissance quand l'apareil est en fonctionnement (utilisé pour déduire des consommation ou gérer le delestage)
			- fonctionement_max		:	temps de fonctionnement maximum (en secondes) de l'apareil à > 50% de la puissance typique. Gère une alerte.
			- max_average_power		:	puissance moyenne maximum. Gère une alerte.
			- duration_average_power:	temps en secondes pour calcul max_average_power
		'''
		self.nom = nom
		self.parent = parent
		self.puissance_maxi = puissance_maxi
		self.energie_maxi_jour = energie_maxi_jour
		self.enfants = []
		self.delest = delest
		self.puissance_typique = puissance_typique
		self.fonctionement_max = fonctionement_max
		self.max_average_power = max_average_power
		self.duration_average_power = duration_average_power
		
	# def __repr__(self):
		# repr = self.nom + "\n"
		# for circuit in self.enfants:
			# repr += "|__%s\n" % circuit
		# return repr
				
class circuit_mesure(circuit):
	'''Un circuit mesuré
	'''
	def __init__(self,  nom, compteur, parent=None, eclatable = False, puissance_maxi= None, energie_maxi_jour= None, delest = None, puissance_typique = None, fonctionement_max = None, max_average_power = None, duration_average_power = 3600):
		'''Initialisation
		'''
		self.eclatable = eclatable
		self.compteur = compteur
		circuit.__init__(self, nom, parent, puissance_maxi, energie_maxi_jour, delest, puissance_typique, fonctionement_max, max_average_power, duration_average_power)
	
	def __repr__(self):
		return "Circuit_mesure : %s" % self.nom
	
	def is_deductible_typically(self):
		'''renvoie True si
			est eclatagle et
			tous les circuits enfants ont des consos typiques
			et les valeurs de conso typiques 'vont bien' pour déduire
		'''
		if not self.eclatable:
			return False
		for enfant in self.enfants:
			try:
				if enfant.puissance_typique in (0, None) :
					return False
			except AttributeError:
				return False
		combinaisons = self.combinaisons_enfants_typiques()
		for i in range(0, len(combinaisons)):
			for j in range(i+1, len(combinaisons)):
				ratio = 1.*self.comb_sum(combinaisons[i])/self.comb_sum(combinaisons[j])
				if ratio>0.8 and ratio < 1.2: #Conditions : 80% - 120%
					return False
		return True
	
	def is_deductible_arithmetically(self):
		'''Renvoie un tuple de 2 elements avec 
				- le circuit calculable
				- les circuits à soustraire
			Si
				- est eclatable
				- il n'a y qu'un seul sous-circuit non mesuré
			Sinon, renvoie None
		'''
		if self.eclatable:
			circuits_calculable = []
			circuits_a_soustraire = []
			for enfant in self.enfants:
				if isinstance(enfant, circuit_mesure):
					circuits_a_soustraire.append(enfant)
				else:
					circuits_calculable.append(enfant)
			if len(circuits_calculable) == 1:
				return circuits_calculable[0], circuits_a_soustraire
	
	def combinaisons_enfants_typiques(self):
		'''renvoie les combinaisons possibles de circuits
		'''
		combinaisons = []
		for i in range(0,len(self.enfants)+1):
			for combinaison in itertools.combinations(self.enfants, i):
				combinaisons.append(combinaison)
		return combinaisons
	
	@staticmethod
	def comb_sum(combinaison):
		'''calcul la somme des conso typiques d'une liste de circuit
		'''
		somme = 0
		for circuit in combinaison:
			somme += circuit.puissance_typique
		return somme
		
class circuit_general(circuit_mesure):
	'''Circuit général
	'''
	def __init__(self,  nom, compteur = None, eclatable = False, puissance_maxi= None, energie_maxi_jour= None):
		'''Initialisation
		'''
		circuit_mesure.__init__(self, nom, compteur, None, eclatable, puissance_maxi, energie_maxi_jour, None)
	
	def __repr__(self):
		return "Circuit_général : %s" % self.nom

class electric_device(circuit):
	'''Un circuit physique mais non mesuré
	'''
	def __repr__(self):
		return "Circuit_device : %s" % self.nom
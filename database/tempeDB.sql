-- phpMyAdmin SQL Dump
-- version 4.3.0
-- http://www.phpmyadmin.net
--
-- Client :  localhost
-- Généré le :  Dim 17 Mai 2015 à 19:42
-- Version du serveur :  5.5.41-MariaDB
-- Version de PHP :  5.5.24

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Base de données :  `tempeDB`
--

-- --------------------------------------------------------

--
-- Structure de la table `alertes`
--

CREATE TABLE IF NOT EXISTS `alertes` (
`id` int(11) NOT NULL,
  `capteur` varchar(25) NOT NULL COMMENT 'Capteur de temperature',
  `min_max` enum('MIN','MAX') NOT NULL COMMENT 'MIN ou MAX',
  `valeur` decimal(7,2) NOT NULL,
  `message` text NOT NULL COMMENT 'Message avec %s pour valeur',
  `contact` varchar(25) NOT NULL,
  `duree_repetition` int(11) NOT NULL DEFAULT '24' COMMENT 'Duree de la repetition, en heures',
  `date_envoie` datetime NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `capteurs`
--

CREATE TABLE IF NOT EXISTS `capteurs` (
  `id` char(4) NOT NULL COMMENT 'Identifiant du capteur : ex :''0010''',
  `nom` varchar(25) NOT NULL COMMENT 'Nom du capteur',
  `formule` text NOT NULL COMMENT 'Formule de calcul avec "valeur" comme valeur brute'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `circuit`
--

CREATE TABLE IF NOT EXISTS `circuit` (
  `nom` varchar(25) NOT NULL,
  `niveau` int(11) NOT NULL DEFAULT '0' COMMENT 'Niveau : 0 = Général, 1 = sous le Général, 2 = sous 1, ... (non utilisé!)',
  `parent` varchar(25) NOT NULL COMMENT 'circuit parent',
  `eclatable` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Le circuit est-il decrit et eclatable?',
  `puissance_maxi` int(11) NOT NULL COMMENT 'en Watts',
  `energie_maxi_jour` int(11) NOT NULL COMMENT 'en Wh'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `consos_electrique`
--

CREATE TABLE IF NOT EXISTS `consos_electrique` (
`Id` int(10) unsigned NOT NULL,
  `circuit` varchar(25) NOT NULL COMMENT 'Nom du circuit electrique',
  `date_debut` datetime NOT NULL COMMENT 'Date de début de la mesure',
  `date_fin` datetime NOT NULL COMMENT 'date de fin de la mesure',
  `energie` float NOT NULL COMMENT 'energie consommée',
  `puissance` float NOT NULL COMMENT 'puissance',
  `compteur` decimal(10,6) NOT NULL COMMENT 'compteur en kWh',
  `type_horaire` enum('HC','HP','','') DEFAULT NULL,
  `analyse` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB AUTO_INCREMENT=113764 DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `contacts`
--

CREATE TABLE IF NOT EXISTS `contacts` (
  `nom` varchar(25) NOT NULL COMMENT 'nom',
  `email` text NOT NULL COMMENT 'email'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `electric_device`
--

CREATE TABLE IF NOT EXISTS `electric_device` (
`id` int(11) NOT NULL,
  `nom` varchar(30) NOT NULL,
  `puissance_maxi` int(11) NOT NULL COMMENT 'en Watts',
  `energie_maxi_jour` int(11) NOT NULL COMMENT 'Energie en Wh maximum par jour',
  `puissance_typique` int(11) NOT NULL COMMENT 'en Watts',
  `parent` varchar(25) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `grandeur_mesuree`
--

CREATE TABLE IF NOT EXISTS `grandeur_mesuree` (
`id` int(11) NOT NULL,
  `nom` varchar(25) NOT NULL,
  `table_donnees` varchar(30) NOT NULL,
  `test_enregistrement` tinyint(1) NOT NULL,
  `duree` decimal(5,2) NOT NULL DEFAULT '0.25' COMMENT 'Durée sans enregistrement, en heure',
  `message` text NOT NULL,
  `contact` varchar(25) NOT NULL,
  `duree_repetition` int(11) NOT NULL DEFAULT '24',
  `date_envoie` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `groupe_prises`
--

CREATE TABLE IF NOT EXISTS `groupe_prises` (
  `groupe` varchar(30) NOT NULL,
  `nom_groupe` varchar(30) NOT NULL,
  `code_rf` char(5) NOT NULL COMMENT 'code radio freq ex :''00010'''
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `mesures`
--

CREATE TABLE IF NOT EXISTS `mesures` (
`Id` int(10) unsigned NOT NULL,
  `capteur` varchar(25) NOT NULL COMMENT 'Nom du capteur',
  `date` datetime NOT NULL,
  `temperature` decimal(7,2) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=117923 DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table `prises`
--

CREATE TABLE IF NOT EXISTS `prises` (
`Id` int(10) unsigned NOT NULL,
  `groupe` varchar(30) NOT NULL COMMENT 'Groupe de prises',
  `no_prise` int(10) unsigned NOT NULL COMMENT '1=prise A, 2=B, 3=C, 4=D',
  `nom` varchar(30) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

--
-- Index pour les tables exportées
--

--
-- Index pour la table `alertes`
--
ALTER TABLE `alertes`
 ADD PRIMARY KEY (`id`), ADD KEY `contact` (`contact`), ADD KEY `capteur` (`capteur`);

--
-- Index pour la table `capteurs`
--
ALTER TABLE `capteurs`
 ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `nom` (`nom`);

--
-- Index pour la table `circuit`
--
ALTER TABLE `circuit`
 ADD PRIMARY KEY (`nom`), ADD KEY `parent` (`parent`);

--
-- Index pour la table `consos_electrique`
--
ALTER TABLE `consos_electrique`
 ADD PRIMARY KEY (`Id`), ADD KEY `circuit` (`circuit`), ADD KEY `date_debut` (`date_debut`);

--
-- Index pour la table `contacts`
--
ALTER TABLE `contacts`
 ADD PRIMARY KEY (`nom`);

--
-- Index pour la table `electric_device`
--
ALTER TABLE `electric_device`
 ADD UNIQUE KEY `id` (`id`), ADD KEY `circuit` (`parent`);

--
-- Index pour la table `grandeur_mesuree`
--
ALTER TABLE `grandeur_mesuree`
 ADD PRIMARY KEY (`id`), ADD KEY `contact` (`contact`), ADD KEY `nom` (`nom`);

--
-- Index pour la table `groupe_prises`
--
ALTER TABLE `groupe_prises`
 ADD PRIMARY KEY (`groupe`);

--
-- Index pour la table `mesures`
--
ALTER TABLE `mesures`
 ADD PRIMARY KEY (`Id`), ADD KEY `capteur` (`capteur`,`date`), ADD KEY `date` (`date`);

--
-- Index pour la table `prises`
--
ALTER TABLE `prises`
 ADD PRIMARY KEY (`Id`), ADD KEY `groupe` (`groupe`);

--
-- AUTO_INCREMENT pour les tables exportées
--

--
-- AUTO_INCREMENT pour la table `alertes`
--
ALTER TABLE `alertes`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=15;
--
-- AUTO_INCREMENT pour la table `consos_electrique`
--
ALTER TABLE `consos_electrique`
MODIFY `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=113764;
--
-- AUTO_INCREMENT pour la table `electric_device`
--
ALTER TABLE `electric_device`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=4;
--
-- AUTO_INCREMENT pour la table `grandeur_mesuree`
--
ALTER TABLE `grandeur_mesuree`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT pour la table `mesures`
--
ALTER TABLE `mesures`
MODIFY `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=117923;
--
-- AUTO_INCREMENT pour la table `prises`
--
ALTER TABLE `prises`
MODIFY `Id` int(10) unsigned NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=5;
--
-- Contraintes pour les tables exportées
--

--
-- Contraintes pour la table `alertes`
--
ALTER TABLE `alertes`
ADD CONSTRAINT `alertes_ibfk_1` FOREIGN KEY (`capteur`) REFERENCES `capteurs` (`nom`) ON UPDATE CASCADE,
ADD CONSTRAINT `fk_nom` FOREIGN KEY (`contact`) REFERENCES `contacts` (`nom`);

--
-- Contraintes pour la table `capteurs`
--
ALTER TABLE `capteurs`
ADD CONSTRAINT `capteurs_ibfk_1` FOREIGN KEY (`nom`) REFERENCES `grandeur_mesuree` (`nom`);

--
-- Contraintes pour la table `circuit`
--
ALTER TABLE `circuit`
ADD CONSTRAINT `circuit_ibfk_1` FOREIGN KEY (`nom`) REFERENCES `grandeur_mesuree` (`nom`) ON UPDATE CASCADE;

--
-- Contraintes pour la table `electric_device`
--
ALTER TABLE `electric_device`
ADD CONSTRAINT `electric_device_ibfk_1` FOREIGN KEY (`parent`) REFERENCES `circuit` (`nom`) ON UPDATE CASCADE;

--
-- Contraintes pour la table `grandeur_mesuree`
--
ALTER TABLE `grandeur_mesuree`
ADD CONSTRAINT `grandeur_mesuree_ibfk_1` FOREIGN KEY (`contact`) REFERENCES `contacts` (`nom`) ON UPDATE CASCADE;

--
-- Contraintes pour la table `mesures`
--
ALTER TABLE `mesures`
ADD CONSTRAINT `mesures_ibfk_1` FOREIGN KEY (`capteur`) REFERENCES `capteurs` (`nom`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `prises`
--
ALTER TABLE `prises`
ADD CONSTRAINT `fk_groupe` FOREIGN KEY (`groupe`) REFERENCES `groupe_prises` (`groupe`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

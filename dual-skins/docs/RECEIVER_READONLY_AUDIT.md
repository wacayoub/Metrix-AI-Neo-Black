# Audit du récepteur

Statut : **NON EFFECTUÉ**.

Aucun connecteur SSH autorisé, hôte de récepteur ou session disponible n’a été
fourni. Aucun scan réseau, aucune tentative SSH, lecture distante ou commande sur
le Vu+ n’a été effectuée. Le projet partait d’un dossier local sans code existant.

Éléments à relever dans un seul audit ciblé ultérieur, si un accès est fourni :

- Image/build, architecture, version Python et Enigma2.
- Présence et signatures des API Menu, ServiceList, EventInfo, ePicLoad.
- Skins installés et conventions du sélecteur ; polices disponibles.
- Réglages de disposition des listes et picons, en minimisant les données lues.
- Versions des plugins utiles, sans lire mots de passe, bouquets ou URL IPTV.

Ne pas collecter `/etc/enigma2/settings` intégralement ni exporter des références
de services contenant des URL privées. EPGManager et IPToSatPro ne nécessitent
aucune lecture ou modification de leurs configurations pour le skin.

**NO_INSTALL / NO_RECEIVER_WRITE** demeure applicable. Ce document n’autorise ni
installation, ni copie distante, ni activation, ni redémarrage.

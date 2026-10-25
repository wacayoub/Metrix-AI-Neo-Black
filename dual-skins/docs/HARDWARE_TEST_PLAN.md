# Plan matériel futur — non exécuté

**Une autorisation explicite distincte est nécessaire avant toute écriture,
installation, activation ou relance sur le Vu+.** Aucune commande destructive ou
commande d’installation prête à exécuter n’est fournie dans cette livraison.

1. Audit en lecture seule unique : image/build, Python, API, ressources et
   dépendances. Décider si les modèles modernes sont présents. Si nécessaire,
   adapter le code local avant toute installation.
2. Conserver hors récepteur une sauvegarde sûre des réglages et du nom du skin
   actif ; ne pas publier ses secrets ou références de flux. Vérifier qu’une
   voie de récupération du skin MetrixHD original fonctionne.
3. Après accord écrit : installer uniquement le runtime et un premier skin.
   Vérifier les fichiers possédés par le paquet, sans toucher aux bouquets ou
   plugins tiers. Garder le helper désactivé pour ce premier contrôle.
4. Vérifier découverte séparée, FHD, marges, sélection, menus complets, retour,
   listes, EPG/timers, confirmations, clavier, audio/sous-titres, volume/mute.
5. Tester une chaîne SAT, une TNT si disponible et un flux IPTV, sans publier
   leurs références. Comparer signal au panneau natif ; IPTV sans SNR/AGC.
   Vérifier REC/timeshift et codecs connus en conditions réelles.
6. Tester FR/EN/AR, titres longs, shaping/RTL, picons XPICON/ZZZPicon variés,
   événements sans image/EPG/prochain, suppression du helper et mode hors ligne.
   À l’ouverture de la liste, vérifier l’image du premier événement sélectionné,
   puis les transitions image/texte et le ratio du picon. Vérifier la palette EPG
   avec les préférences graphiques existantes, sans les remplacer. Contrôler les
   15 lignes du contexte centré et la vidéo en cours dans les marges extérieures.
7. Mesurer zapping/sélection, CPU/mémoire et décodage d’images sur plusieurs
   minutes ; consigner la méthode et les valeurs observées, sans seuil inventé.
8. Tester le deuxième skin séparément, puis le helper si souhaité, météo avec
   consentement et catalogue licencié. Annuler une prévisualisation puis
   sauvegarder une préférence NEO ; vérifier l’absence de changement tiers.

Retour arrière : sélectionner le skin original conservé via l’interface native
si accessible, puis relancer seulement si l’utilisateur l’autorise. En cas
d’interface indisponible, établir une procédure de récupération adaptée au build
audité avant d’effectuer toute modification distante. Ne pas supprimer la
configuration Enigma2 globale et ne pas écraser MetrixHD.

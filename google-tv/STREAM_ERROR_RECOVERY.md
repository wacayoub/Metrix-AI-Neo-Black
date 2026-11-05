# Refus de streaming du Vu+ — 0.8.3

Le signalement utilisateur `ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED` a été reproduit sur Rai 1. OpenWebif répond, la référence native de la playlist correspond au service de son catalogue et l'adresse cible bien le port 8001 du récepteur. Cependant, ce serveur annonce HTTP 200 et `video/mpeg`, puis renvoie seulement 28 octets : `HTTP/1.0 400 Bad Request`, au lieu de paquets MPEG-TS.

Ce comportement est cohérent avec le [serveur de streaming Enigma2](https://github.com/openatv/enigma2/blob/master/lib/dvb/streamserver.cpp) : l'en-tête vidéo est envoyé avant la tentative d'ouverture, puis une erreur 400 peut suivre si le flux ne démarre pas. La cause précise côté récepteur reste à traiter ; changer de décodeur vidéo Android ne fournit pas les paquets absents.

Observations en lecture seule : Vu+ Zero4K, un tuner SI2166, indiqué en service sur « 75.0° E / 01 BBC ONE », SNR/AGC zéro, aucun enregistrement ou client de streaming actif, veille désactivée. Une mise en veille simple avec la télécommande du Vu+ est demandée à l'utilisateur pour vérifier si son tuner devient disponible. Aucun zap, changement de veille, redémarrage, SSH ou modification du récepteur n'a été effectué.

## Correctif Android

- Une source de données reconnaît le préfixe HTTP d'erreur sur la connexion existante au récepteur. Elle ne lance aucun second flux et ne journalise ni adresse ni contenu brut. Les paquets MPEG-TS et les flux Internet suivent leur chemin normal.
- Le refus du récepteur produit un message Vu+/tuner/service indisponible, plutôt qu'un faux diagnostic de conteneur vidéo. L'erreur explicite n'est pas soumise à une boucle automatique de relance.
- Après un échec, OK ou Lecture relance réellement la chaîne ; l'adresse en cache est invalidée pour obtenir une nouvelle playlist. Les erreurs de résolution affichent un texte fixe sans URL ni identifiants.
- La Mini TV, la transparence et les sorties existantes sont conservées.

## Vérification

27 tests JVM réussis, dont quatre nouveaux tests portant sur les erreurs HTTP encapsulées, les lectures fragmentées du préfixe, le passage des formats vidéo normaux et l'invalidation ciblée du cache. Lint release : zéro erreur, dix-sept avertissements. Signature, installation avec conservation des données, ART speed et empreinte de l'APK installée vérifiés.

Sur la Sony, le message HTTP 400 spécifique remplace l'erreur de conteneur. Une pression OK crée une nouvelle demande et une résolution `cached=false` en 46 ms. Le Vu+ refuse encore le flux : **aucune reprise des chaînes satellite n'est revendiquée** avant disponibilité du récepteur.

Un contrôle séparé de TF1 / PURE IPTV / FRANCE FHD, depuis le lecteur normal de Neo, donne un premier callback vidéo à 1 504 ms, état READY, lecture active, position 8 292 ms et 209 images rendues sans image abandonnée sur cet échantillon. Une transition ultérieure `playing=false` a aussi été observée ; ce contrôle court ne valide pas la stabilité prolongée. Les limites 4K/HDR et IPTV précédentes restent distinctes.

Preuves : `reports/sony-stream-recovery-2026-11-02.json`. Aucun pixel vidéo n'a été sondé. La demande de libération du tuner reste en attente ; la lecture satellite n'est pas considérée corrigée par le seul changement de message.

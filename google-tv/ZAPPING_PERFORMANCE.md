# Zapping — mesures sur Sony BRAVIA, 31 octobre 2026

Version livrée : 0.4.1-alpha (versionCode 5), APK debug signée et installée sur la Sony 192.168.11.188. Récepteur inchangé, OpenWebif GET uniquement.

## Changements
- Réutilisation du lecteur et de sa factory HTTP ; suppression du couple stop/clear avant chaque service.
- Commande de lecture sur Dispatchers.Main.immediate, indépendante du frame scheduler Compose.
- Le service déjà en lecture est repris sans reconstruction du flux.
- Cache des adresses M3U privées validées : 64 entrées, cinq minutes, lié à la connexion en mémoire. Préparation des deux adresses voisines après la première image, sans ouvrir de vidéo supplémentaire.
- EPG/picon du service différés après la première image ; deux requêtes de métadonnées au maximum.
- Tampons Media3 : minimum 3500 ms, maximum 12000 ms, seuil de démarrage 500 ms, reprise après rebuffer 1500 ms. La durée de démarrage réelle inclut le réseau, le tuner, les images clés et le décodage.
- Répétitions pendant une ouverture en cours regroupées sur 120 ms ; aucun délai volontaire sur le zap normal.
- Optimisation ART du seul paquet Android : `cmd package compile -m speed -f com.metrixneo.tv`, résultat Success. Elle a été appliquée après la dernière installation ; les résultats combinent les changements de code et cette compilation locale.

## Mesures
Horloge monotone Android. Départ : entrée dans play() ; arrivée : callback Player.Listener.onRenderedFirstFrame. Ce callback mesure la première image du lecteur, pas le début du son. Le buffer READY est journalisé séparément. Les journaux NeoZap ne contiennent ni URL ni identifiants.

Trois changements HD successifs mesurés sur Rai 1 / Rai 2 :

| Mesure | 0.4 avant optimisation | 0.4.1 finale |
|---|---:|---:|
| Première image, trois essais | 2711 / 2458 / 2119 ms | 1803 / 1494 / 2143 ms |
| Moyenne | 2429 ms | 1813 ms |
| Médiane | 2458 ms | 1803 ms |
| Résolution d'adresse | 623 / 359 / 389 ms | 6 / 4 / 4 ms, cache confirmé |

Sur cet échantillon limité : moyenne réduite d'environ 25 %, médiane d'environ 27 %. Les chaînes sont les mêmes, mais l'ordre des alternances et les conditions de diffusion ne constituent pas un protocole de laboratoire.

Le premier démarrage vidéo à froid reste plus lent : 4876 ms dans l'essai final, dont 1568 ms de résolution d'adresse. Il n'est pas inclus dans les trois changements après échauffement. Les premiers paquets TS du récepteur ont également été reçus côté PC en 456 ms dans une lecture de contrôle ; cela ne mesure pas un décodage TV.

Lancement à froid de l'activité : 7571 ms avant compilation ART locale, 2818 ms ensuite. Ce gain est distinct du temps d'arrivée de la vidéo et ne garantit pas la même valeur sur une autre TV.

## Validation
- assembleDebug, six tests JVM et lintDebug : succès ; lint 0 erreur, 14 avertissements non bloquants.
- Cache : réutilisation HTTP, expiration et éviction LRU vérifiées par tests.
- Série rapide CH+ / CH+ / CH− / CH− : requêtes intermédiaires abandonnées, dernier service sélectionné affiché ; aucune ouverture des deux demandes intermédiaires. Première image du service final en 2763 ms à partir de sa demande.
- Zap normal suivant : première image en 1505 ms, READY en 1793 ms.
- Aucun plantage AndroidRuntime observé. État final laissé sur Rai 1, AVC / AC3 / 1920×1080 ; picons et programmes réels conservés.
- L'image vidéo est absente des captures ADB de cette Sony ; les mesures reposent sur les callbacks du lecteur, et la confirmation antérieure de l'utilisateur établissait l'image et le son sur Rai 1.

Journaux locaux non suivis par Git : `.tools/zapping-baseline.log`, `.tools/zapping-final.log`, `.tools/zapping-final-rapid.log`. Les essais initiaux sur un service UHD sans première image ne sont pas utilisés dans la comparaison HD.

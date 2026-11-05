# Vérification TCL et Sony — 3 novembre 2026

Même APK 0.8.3-alpha / code 22 vérifiée par SHA-256 sur les deux TV :
`f08f0b0c343fb6ad2a300e93a47e8ad4eaaea4556c04271f2a60501bb9c6a1a7`.
Installation initiale et configuration chiffrée effectuées sur la TCL ; installation Sony conservée. Aucun changement du lecteur ou nouveau build Android pendant cette vérification.

| Contrôle matériel | Sony BRAVIA VU3 | TCL Smart TV / G13 |
| --- | --- | --- |
| Android / architecture | 14 / ARMv7 | 14 / ARMv7 |
| Modes d'affichage déclarés par Android | 3840 × 2160 | 1920 × 1080 |
| Navigation, pagination, Haut/Bas circulaire, EPG | 24/24 contrôles | 24/24 contrôles |
| Retour, appui maintenu, double EXIT, menus, retrait de la tâche | 16/16 contrôles | 16/16 contrôles |
| Bouquets imbriqués, Mini TV, transparence et lecture IPTV courte | 11/11 contrôles | 11/11 contrôles |
| TF1 / PURE IPTV / FRANCE FHD : premier callback vidéo | 1 006 ms | 1 511 ms |
| Dernière position observée TF1 | 68 886 ms | 68 064 ms |
| Compteur vidéo TF1, premier → dernier échantillon | 223 → 1 723 | 203 → 1 702 |
| Images perdues signalées sur ces échantillons | 0 | 0 |
| Erreur Media3 ou remise en tampon après READY, pendant cet essai | Aucune observée | Aucune observée |
| Rai 1, Rai 2, Rai 3 | Refus HTTP 400 du Vu+ | Refus HTTP 400 du Vu+ |

Les 51 contrôles réussis par appareil concernent les fonctions testées et ce court essai IPTV. Les trois chaînes satellite en échec sur chaque appareil sont consignées séparément, pas comptées comme des lectures réussies. Le catalogue parcouru comporte 10 436 services uniques, 42 groupes satellites et 156 dossiers racine. Les sous-dossiers PURE IPTV → FRANCE FHD ouvrent leurs chaînes sur les deux appareils.

Le Vu+ indique toujours son unique tuner sur « 75.0° E / 01 BBC ONE », signal nul, sans veille, enregistrement ni client de streaming actif. Aucun zap, commande de veille ou modification du récepteur n'a été effectué. La lecture satellite reste indisponible ; le correctif Android explique le refus mais ne le répare pas côté récepteur.

## Interruption conservée et portée des mesures

Le premier essai TCL a été interrompu après environ 48 secondes de lecture : Android indique `Asleep`, motif `power_button`. L'origine de cette commande n'est pas déterminée. La capture noire correspondante est conservée sous `reports/tcl-asleep-during-test-2026-11-03.png`. Le premier banc de mesure interrogeait aussi une fenêtre limitée de logcat : l'événement de première image avait disparu de cette fenêtre. Ses échecs ne constituent pas une preuve de panne du décodeur. Le rapport initial reste disponible ; la seconde tentative collecte les événements en continu et passe les onze contrôles.

Les captures ordinaires ADB vérifient la disposition de l'interface ; sur la Sony, le plan vidéo peut être noir dans ces captures. La capture TCL montre ici une image derrière la liste translucide. Aucun sondage de pixels vidéo ou PixelCopy n'est utilisé. Des compteurs croissants et zéro image perdue signalée ne certifient pas le mouvement final de la dalle ni le son audible.

Ces essais ne valident ni toutes les chaînes ni une séance prolongée. Les problèmes 4K/HDR précédemment signalés ne sont pas déclarés corrigés. La TCL testée déclare seulement un mode de sortie 1920 × 1080 : ce contrôle n'établit aucune restitution 4K. Android annonce les types HDR numériques `[2, 3]` sur les deux appareils ; cette annonce ne constitue pas un test HDR.

Double EXIT rejoint l'accueil suivi par la touche HOME physique : Google TV sur la TCL ; Gathin pendant le test Sony, où un service installé redirige HOME. Les deux appareils se trouvent finalement sur Google TV après les vérifications. Aucun réglage de lanceur ou service système n'a été modifié. La lecture IPTV est mise en pause avant de terminer et les essais sont successifs pour éviter deux sessions fournisseur concurrentes.

## Preuves et reproduction

- `reports/sony-check-2026-11-03-navigation.json`, `reports/tcl-check-2026-11-03-navigation.json`.
- `reports/sony-check-2026-11-03-exit.json`, `reports/tcl-check-2026-11-03-exit.json`.
- `reports/sony-compatibility-2026-11-03.json`, `reports/tcl-compatibility-2026-11-03.json`.
- `reports/tcl-compatibility-2026-11-03-first-attempt.json` : interruption et limite initiale du banc.
- `reports/sony-check-ui-2026-11-03.png`, `reports/tcl-check-ui-2026-11-03.png` : mise en page observée.

`tools/check-tv-compatibility.py --adb CHEMIN_ADB --serial IP:5555 --seconds 30 --output reports/compatibility.json` teste trois services satellite, les sous-dossiers et TF1 avec les deux aperçus, puis met le lecteur en pause. Les appareils doivent être déjà configurés et autorisés. La durée passée en Mini TV/transparence s'ajoute aux trente secondes finales. Le script ne lit ni ne journalise les URL fournisseur ou les identifiants.

`tools/test-tv-navigation.py --wrap-only` vérifie les 24 contrôles de navigation. `tools/test-tv-exit.py --ui-only` vérifie les 16 contrôles de sortie sans exiger un service satellite disponible et termine à l'accueil. Syntaxe Python des outils vérifiée ; aucun nouveau test de compilation APK n'est revendiqué ici.

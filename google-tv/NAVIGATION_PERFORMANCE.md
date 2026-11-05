# Navigation et télécommande — 0.7.0

La navigation précédente sur la Sony affichait de fortes lenteurs. Mesure du 31 octobre 2026 sur l'APK 0.6.3 debug / code 13, lecture TNT mise en pause et liste « Tous les services » ouverte : dix touches bas, dix haut, deux pages droite puis deux gauche, avec 100 ms entre les touches verticales.

Statistiques Android gfxinfo de ce parcours : 29 images d'interface, 29 hors délai, médiane 350 ms, P90 750 ms, P95 950 ms ; GPU médian 4 ms. Ce sont des durées de rendu d'interface, pas des mesures de latence physique de la télécommande ni de fluidité vidéo.

Changements :

- Index des bouquets, totaux et services uniques calculé une fois par liste reçue. Pages de vingt lignes obtenues par une vue de sous-liste, sans copier les milliers de chaînes restantes à chaque sélection.
- Ligne de chaîne composable séparée pour permettre à Compose de conserver les lignes dont les données et la sélection n'ont pas changé.
- EPG déjà en cours dédoublé ; requête de la chaîne sélectionnée prioritaire et bornée indépendamment des deux téléchargements EPG de fond. Les picons restent indépendants de l'affichage.
- Cache de huit listes de satellites ; réponses anciennes ignorées lorsque la sélection change.
- Horloge HH:mm actualisée à la frontière des minutes, sans recomposer chaque seconde.
- Répétition conservée pour flèches, pages et CH+/− ; OK/Menu/couleurs/retour ne déclenchent qu'une action lors d'un appui maintenu. CH+/− paginent le dossier ou la liste actuellement ouvert.
- Saisie jusqu'à six chiffres, dont les numéros de chaîne à cinq chiffres. Les numéros des satellites/bouquets et du menu commandent leur liste courante.
- Repères d'accessibilité et état « sélectionné » exposés pour le test automatique ; aucune capture des pixels vidéo.

La version locale optimisée utilise R8 et la réduction des ressources, sans mode débogage. Le décodeur GStreamer/JNI et ses classes appelées depuis le code natif sont conservés explicitement. La signature de développement locale garde l'identité de l'application déjà installée et ses données ; ce n'est pas une clé de publication. L'APK debug reste disponible pour le développement.

Android recommande de vérifier Compose en version release avec R8 : [documentation officielle](https://developer.android.com/develop/ui/compose/performance). La comparaison avant/après inclut à la fois les changements de code et le changement de configuration de compilation ; elle n'attribue pas un gain séparé à chaque optimisation.

Compilation :

```powershell
gradle :app:assembleRelease :app:testDebugUnitTest :app:lintRelease
```

Le parcours `tools/test-tv-navigation.py` utilise uniquement ADB, les nœuds d'accessibilité de Neo, des touches de télécommande et gfxinfo. Il vérifie les écrans et commandes implémentés, sans certifier le son ou l'image de la surface vidéo. Les plugins Enigma2, changements du Vu+, enregistrement et timeshift ne sont pas implémentés et ne sont pas présentés comme testés.

## Mesures après installation sur la Sony

APK 0.7.0-alpha, version release optimisée, même parcours et même télévision : 40 images d'interface, 26 hors délai, médiane **36 ms**, P90 **53 ms**, P95 **73 ms**. Le temps médian est environ dix fois plus court que les 350 ms précédentes. Des images restent hors délai : ce résultat ne promet pas une interface constante à 60 images/s. Un premier essai avait donné 36/65/69 ms pour médiane/P90/P95.

Un contrôle supplémentaire sur l'APK finale, après démarrage sans TNT en pause sous la liste, donne 45 images, 25 hors délai, médiane 30 ms, P90 61 ms et P95 73 ms. Son contexte de lecture diffère du premier comparatif ; il est conservé séparément dans le rapport du parcours fonctionnel.

Dix-sept tests JVM réussis, dont un test sur 100 000 éléments vérifiant qu'une page ne lit que vingt services. Lint release : zéro erreur, quinze avertissements. Les résultats des commandes et écrans réellement parcourus sont conservés dans `reports/sony-navigation-2026-10-31.json` ; les durées `check_seconds` incluent les lectures UIAutomator et ne mesurent pas la latence d'une touche.

Parcours de navigation/commande : **62 contrôles réussis, zéro échec**. Complément GStreamer : **quatre contrôles réussis**, démarrage IPTV, CH+ puis CH− avec callback de nouvelle image pour chaque service et rétablissement Media3 avec décodage. Rapport : `reports/sony-gstreamer-zapping-2026-10-31.json`. La sélection audio GStreamer est acceptée par le pipeline ; pause et reprise sont confirmées par ses états effectifs. Ces contrôles courts ne garantissent pas une lecture prolongée ; voir la limite ci-dessous.

APK du parcours principal : versionCode 15, 29 751 953 octets, SHA256 `870cc9d8784680b390ffb65b47c398fa0ceeb70dfd8ff6fec37a7be87b72aec1`. La dernière compilation ajoute uniquement la journalisation du domaine/code d'erreur natif, sans texte brut ni URL : 29 752 117 octets, SHA256 `465fb210f26975986181eeb451be1f5178ff1b84cd375de888431ece2c3bbaa3`. Signature et installation avec conservation des données vérifiées. Aucun changement du Vu+.

**Limite détectée par le contrôle prolongé :** TF1 FHD PURE atteint STATE_ENDED après environ 20 puis 26 s dans Media3. GStreamer rencontre également une erreur ; la dernière reproduction donne `gst-stream-error-quark / 7` (`GST_STREAM_ERROR_DECODE`) après environ 23 s. Cela ne prouve ni un défaut d'Internet ni une cause précise dans le firmware. Rapport séparé : `reports/sony-iptv-duration-2026-10-31.json`, résultat de stabilité **en échec**. Le démarrage et les commandes des lecteurs sont validés ; la stabilité prolongée de cette chaîne IPTV ne l'est pas. La lecture finale est rétablie sur Rai 1 avec Media3.

Le contrôle distingue les callbacks du décodeur et les états réels du lecteur des pixels affichés par la dalle. Les gels 4K/HDR signalés précédemment ne sont pas considérés comme résolus par cette optimisation de navigation.

## 0.8.1 — comparaison sur Sony, 2 novembre 2026

La version retient le surlignage des bouquets et satellites dans une couche graphique : déplacer le curseur met à jour son opacité et l'état d'accessibilité, sans recomposer les vingt libellés. Leur page est une valeur dérivée qui change aux frontières des vingt lignes. Les tuiles du menu isolent leur sélection et mémorisent leur fond ; les picons réutilisent leur conversion `ImageBitmap`. La sauvegarde chiffrée est observée par `snapshotFlow` avec le même délai de 500 ms et le même enregistrement immédiat au passage en arrière-plan.

La liste des chaînes conserve son rendu précédent et ses vingt emplacements lors des changements de page. Les détails EPG suivent immédiatement chaque sélection ; les noms complets et le défilement du texte sélectionné sont conservés.

Comparaison entre 0.8.0/code 19 et 0.8.1/code 20, toutes deux en release optimisée, ART speed, sur la même Sony BRAVIA_VU3 Android 14 :

| Écran | Médiane avant → après | P95 avant → après | Images hors délai avant → après |
| --- | --- | --- | --- |
| Bouquets natifs | 15 → **9 ms** | 23 → **16 ms** | 11/40 → **0/20** |
| Menu principal | 13 → 13 ms | 17 → 20 ms | 2/20 → 4/20 |
| Tous les services | 22 → 31 ms | 29 → 65 ms | 20/40 → 33/44 |

**Gain confirmé sur ce parcours de bouquets : 40 % de réduction du temps médian de rendu. Aucun gain démontré pour les chaînes ou le menu.** Le dernier relevé des chaînes est plus lent que la référence ; leur fluidité reste à améliorer. Ces échantillons courts utilisent des données EPG réelles, dont le contenu et l'activité système peuvent varier. Ils ne mesurent ni la latence physique d'une touche ni une cadence vidéo et ne garantissent pas 60 images/s.

Parcours : dix Bas puis dix Haut, avec une attente de 100 ms entre les touches verticales ; ajout de Droite, Droite, Gauche, Gauche pour les chaînes. Les boucles sont exécutées dans un seul shell ADB sur la TV, Rai 1 Media3 en pause sous la liste « Tous les services ». Les menus utilisent dix Droite puis dix Gauche ; les bouquets dix Bas puis dix Haut. La table utilise le deuxième passage des chaînes, avec lecture de gfxinfo immédiatement après le retour du shell, comme la référence. Un deuxième relevé après 500 ms est conservé : 45 images, médiane 31 ms, P95 65 ms. Les temps de traitement des événements Android s'ajoutent aux 100 ms explicites.

Mesures et identité de l'APK : `reports/sony-smooth-ui-2026-11-02.json`. La capture de l'interface est `reports/sony-smooth-ui-2026-11-02.png`. Les tests de navigation, reprise et sortie restent distincts des mesures de performance. Aucune capture des pixels de la surface vidéo, aucun changement du Vu+ et aucune nouvelle validation de stabilité IPTV/4K.

Référence technique : [bonnes pratiques de performance Compose](https://developer.android.com/develop/ui/compose/performance/bestpractices), notamment les lectures d'état différées et les valeurs dérivées.

Validation finale : **24 contrôles de navigation/EPG, 27 de reprise et 22 de sortie réussis**, plus 23 tests JVM. Lint release : zéro erreur, seize avertissements. Rapports `sony-smooth-wrap`, `sony-smooth-resume` et `sony-smooth-exit`, datés du 2 novembre 2026 dans `reports/`. Les tests vérifient les nœuds d'accessibilité, les états du lecteur et les nouveaux callbacks de décodage ; ils ne certifient pas les pixels vidéo ou le son.

Deux tentatives précédentes sont conservées séparément : une erreur de conteneur sur Rai 2, puis un défaut du test qui attendait un nouveau décodage alors que cette chaîne était déjà active. Le test établit maintenant une lecture fraîche de Rai 1 avant ses vérifications de redémarrage. Rai 1 et Rai 2 ont ensuite fourni de nouveaux callbacks vidéo et le parcours complet passe. La stabilité vidéo reste une limite distincte de ces contrôles d'interface.

APK finale : 29 905 554 octets, SHA256 `21b6423fee5ab942ec23df3dc7e0962de5fbac19124f2c4ced003f5e62832302`, version 0.8.1-alpha/code 20. La clé de développement existante conserve l'identité et les données de l'application ; aucune publication ni exécution CI distante n'est revendiquée.

Capture finale vérifiée : vingt lignes, picons, sélection Rai 1, EPG après les noms et horloge visibles. La météo est encore affichée « En attente… » sur ce démarrage ; cette vérification ne valide pas une nouvelle observation météo. L'empreinte de l'APK installée sur la Sony correspond au fichier compilé. Neo est laissé sur la liste, Rai 1 réellement en lecture derrière celle-ci.

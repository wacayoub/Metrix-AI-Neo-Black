# Metrix NEO AI — Google TV

Application native Android TV / Google TV. La version 0.4 remplace le tableau de bord alpha par le parcours MetrixNEO du Vu+ : menu principal, liste compacte de 20 chaînes, détails EPG, bouquets et infobar.

## Source de vérité
- `dual-skins/skins/MetrixNEO/`
- `dual-skins/docs/INFOBAR_FIDELITY.md`
- `dual-skins/previews/`
- Skin actif sur Vu+ (audit read-only si autorisé)

## Utilisation

Accès hors LAN en 4G/5G : proposition Tailscale avec passerelle domestique, sans installation sur le Vu+ ni exposition publique d'OpenWebif. Conserver l'adresse privée du récepteur dans Neo. Configuration et limites dans [REMOTE_ACCESS.md](REMOTE_ACCESS.md) ; aucun essai extérieur n'est revendiqué.

Contrôle matériel du 3 novembre : Neo 0.8.3 installé sur Sony et TCL, 51 contrôles de navigation/sortie/aperçus/IPTV court réussis par TV. Les trois services satellite testés restent refusés par le Vu+ ; la 4K/HDR n'est pas validée et la TCL déclare une sortie 1080p. Résultats détaillés : [TCL_SONY_CHECK.md](TCL_SONY_CHECK.md).

Version **0.8.3-alpha / code 22** : le lecteur reconnaît les erreurs HTTP envoyées par le Vu+ à l'intérieur d'une réponse annoncée comme vidéo. Le message distingue ce refus du serveur d'un format vidéo non reconnu. Après un échec, **OK** ou **Lecture** relance réellement le flux et renouvelle son adresse. Le Vu+ reste en lecture seule ; un tuner occupé ou un service indisponible doit être libéré côté récepteur. Diagnostic et limites dans [STREAM_ERROR_RECOVERY.md](STREAM_ERROR_RECOVERY.md).

Version **0.8.2-alpha / code 21** : Mini TV à droite de la liste, montrant la chaîne en cours pendant la consultation des autres services. La touche **jaune** alterne entre Mini TV et vidéo plein écran derrière une liste transparente ; le choix est mémorisé. OK ouvre la chaîne sélectionnée en plein écran. L'EPG, les noms complets, les picons et les vingt lignes sont conservés. Détails et vérifications dans [MINI_TV_AND_TRANSPARENCY.md](MINI_TV_AND_TRANSPARENCY.md).

Version **0.8.1-alpha / code 20** : surlignage des bouquets et satellites actualisé séparément, sauvegardes observées hors de la composition principale, conversion des picons réutilisée et fonds des tuiles mémorisés. Le rendu des chaînes conserve ses vingt emplacements lors des changements de page et l'EPG suit immédiatement la sélection. Les noms complets, le défilement du texte sélectionné et la reprise de session sont conservés. Comparaison sur Sony et limites dans [NAVIGATION_PERFORMANCE.md](NAVIGATION_PERFORMANCE.md).

Version **0.8.0-alpha / code 19** : reprise de la dernière chaîne et du contexte de liste (bouquet, sous-bouquet ou satellite), avec sélection mémorisée et sauvegarde chiffrée. Le retour HOME et la recréation du processus sont pris en charge. Une nouvelle icône TV/N et une bannière « METRIX NEO AI TV » remplacent les anciens visuels ; l'application est déclarée dans les catégories de lancement standard et TV. Détails, sources des images et preuves matérielles dans [RESUME_AND_LAUNCHER.md](RESUME_AND_LAUNCHER.md).

Version **0.7.3-alpha / code 18** : Haut depuis la première chaîne passe à la dernière chaîne et à sa page ; Bas depuis la dernière revient à la première. Même navigation circulaire dans les bouquets/sous-dossiers et les satellites. Les touches de pagination restent bornées et conservent les sauts de vingt lignes. Dans le guide, gauche/droite passent aussi d'une extrémité à l'autre de la liste des chaînes.

Version **0.7.2-alpha / code 17** : deux appuis EXIT/Retour dans les deux secondes quittent Neo et ouvrent l'accueil Google TV. Le premier conserve le retour habituel et affiche une indication discrète. Une autre touche, l'expiration du délai ou un retour dans l'application annule la confirmation ; un appui maintenu ne compte qu'une fois. La lecture est mise en pause avant le retour à l'accueil et la tâche Neo est retirée des applications récentes.

Sur la Sony testée, un service Gathin redirige l'accueil vers Gathin TV Home, y compris avec la touche HOME physique. Neo suit cet accueil configuré ; aucun service ni réglage système n'est désactivé. Contrôles matériels : `reports/sony-double-exit-2026-11-02.json`. Reproduction : `python tools/test-tv-exit.py --adb C:/chemin/platform-tools/adb.exe --serial IP_SONY:5555 --output reports/exit.json` ; le test termine sur l'accueil TV.

Version **0.7.1-alpha / code 16** : dans la liste, le nom complet de la chaîne est suivi de l'EPG dans un même texte, sans la colonne de 170 dp qui tronquait le nom. La ligne sélectionnée défile si l'ensemble dépasse la place disponible ; les autres restent fixes. Le panneau de détails affiche les noms et titres sur plusieurs lignes sans l'ancienne limite de deux/trois lignes. Dans le guide, le titre sélectionné peut également défiler.

Version **0.7.0-alpha / code 15** : navigation optimisée, pages et totaux mis en cache, priorité EPG à la sélection, cache des satellites, appuis maintenus corrigés et saisie jusqu'à six chiffres. Sur la Sony, le même parcours passe de 350 à 36 ms de rendu médian d'interface ; des images restent hors délai. APK locale optimisée : `app/build/outputs/apk/release/app-release.apk`, signée avec la clé de développement existante pour conserver les données. Détails et limites dans [NAVIGATION_PERFORMANCE.md](NAVIGATION_PERFORMANCE.md).

Soixante-six contrôles courts de navigation/commande passent. Le contrôle prolongé de TF1 FHD PURE révèle encore des interruptions avec Media3 et GStreamer ; les gels 4K/HDR restent non résolus. Les résultats de stabilité sont consignés séparément et ne sont pas présentés comme réussis. Retour final sur Rai 1 avec Media3.

Test autonome des fonctions implémentées, sans capture des pixels vidéo ni modification du Vu+ :

```powershell
python tools/test-tv-navigation.py --adb C:/chemin/platform-tools/adb.exe --serial IP_SONY:5555 --output reports/navigation.json --gfx-output reports/navigation-gfx.txt
```

Version 0.6.3 / code 13 : lecture restaurée sans les sondes expérimentales. Les essais des files synchrones, du lecteur privé Sony et du repli Android natif n'ont pas résolu les gels et ont été retirés. PixelCopy a déclenché un plantage du pilote graphique Sony ; aucun appel PixelCopy ne reste dans l'APK. Le contrôle ADB autonome est fourni dans `tools/check-sony-playback.py`, avec limites explicites : les statistiques Android ne certifient pas l'animation finale de la dalle. Diagnostic dans [SONY_COMPATIBILITY.md](SONY_COMPATIBILITY.md).

Version 0.6.1 : Media3 choisit automatiquement un profil de tampon selon les formats réellement sélectionnés. Pour la 4K (hauteur ≥ 2160) ou le HDR PQ/HLG : objectifs de chargement 12–35 s, seuil initial demandé 4 s, reprise après interruption 6 s. Pour les autres formats : profil précédent 3,5–12 s, démarrage 0,5 s et reprise 1,5 s. Les seuils configurés ne garantissent pas la réserve réellement disponible. Le démarrage UHD peut être plus lent. Les gels de TNT Ultimate restent confirmés sur la Sony après cette modification ; voir [le rapport matériel](Sony_KD-43X75K.md). Les journaux privés `NeoPlayback` relèvent toutes les dix secondes les images rendues/perdues, la position et le tampon, sans URL ni identifiant fournisseur.

Version 0.6 : Setup → Lecteur vidéo permet de choisir **Media3** ou **GStreamer**. Le choix est mémorisé séparément de la connexion au Vu+. Le même menu, les bouquets, les satellites, l'EPG, les picons, la météo et les touches de zapping sont conservés. GStreamer est intégré dans l'APK, sans application externe ; voir [GSTREAMER.md](GSTREAMER.md) pour la compilation native et les limites vérifiées.

Version 0.5.2 : les flux IPTV HTTP(S) des bouquets du Vu+ peuvent être lus directement sur la TV. L'adresse intégrée dans la référence Enigma2 est extraite sans le nom de chaîne parfois ajouté par le M3U OpenWebif ; les échappements des jetons sont conservés. Les identifiants OpenWebif sont réservés à l'hôte du récepteur et à ses ports Webif/8001/8002, pas aux fournisseurs IPTV. Les refus HTTP du serveur sont affichés sans publier l'adresse du flux.

Version 0.5.1 : la touche bleue parcourt maintenant les bouquets natifs niveau par niveau, par référence OpenWebif. OK ouvre un sous-dossier ; une fois arrivé aux chaînes, la liste NEO avec picons/EPG s'affiche. Retour remonte au dossier parent et restaure sa sélection. Les dossiers ne sont plus envoyés au lecteur comme des chaînes. Les noms identiques restent distincts grâce à leur référence ; les boucles de navigation sont refusées.

Version 0.5 : la touche verte ouvre les **satellites du Vu+**, puis OK charge les chaînes du satellite choisi. Bleu garde les bouquets et rouge revient à tous les services. Les dossiers techniques « New » sont écartés. Il s'agit des positions présentes dans la base du récepteur, pas d'une garantie de réception de toutes ces positions.

Les picons se chargent indépendamment des EPG et restent dans le cache privé de la TV : mémoire 8 Mio, disque 32 Mio / 512 entrées, validité sept jours ; les picons absents sont réessayés après une heure. Aucun téléchargement de picon n'est attendu pour afficher les lignes. Une copie locale des services (moins de 24 h, maximum 16 Mio) est affichée au démarrage pendant l'actualisation OpenWebif ; les données sont privées à la connexion du récepteur.

Le bandeau météo/horloge apparaît dans les listes, le menu principal et au-dessus de l'infobar. Le lieu et les coordonnées sont lus en GET depuis `/etc/enigma2/metrix-neo/MetrixNEO.json` par OpenWebif. La configuration constatée est Casablanca, 33.59 / −7.61. Données réelles [Open-Meteo](https://open-meteo.com/), attribution CC BY 4.0 affichée, actualisation toutes les 30 minutes ; aucune température fictive en absence de données. Date et horloge utilisent l'heure de la Sony.

Configurer OpenWebif dans Setup. Pour le récepteur de cette session : `192.168.11.2:82`, authentification requise. Saisir les identifiants sur la TV. L'adresse, le port et le bouquet sont mémorisés ; le mot de passe est chiffré en AES-GCM avec une clé AndroidKeyStore propre à la TV, liée à l'adresse/port/utilisateur. La connexion est rechargée après recréation du processus. Aucun identifiant en dur dans le code.

La liste garde les bouquets distincts, y compris une chaîne présente dans plusieurs bouquets. Rouge affiche tous les services uniques ; bleu ouvre les bouquets. Les EPG de fond et les picons ont chacun deux téléchargements simultanés au maximum, avec caches bornés. Une voie EPG supplémentaire est réservée à la chaîne sélectionnée ou en lecture, et les demandes identiques en cours sont dédoublées. Aucun programme ni picon fictif.

## Zapping 0.4.1
Le lecteur réutilise sa source HTTP, sans arrêt/vidage explicite avant chaque changement. La commande de lecture s'exécute sur le dispatcher Android principal, sans attendre le frame scheduler Compose. Valider le service déjà en lecture reprend immédiatement sa vidéo. Un tampon de démarrage de 500 ms est configuré, avec 3,5 à 12 secondes de réserve et 1,5 seconde après interruption ; ces paramètres ne constituent pas une promesse de première image en 500 ms.

Les adresses M3U validées sont gardées en mémoire (64 maximum, expiration après cinq minutes), pour la connexion active uniquement. Après la première image, les deux adresses voisines sont résolues en arrière-plan, sans ouvrir leurs vidéos ni réserver de tuners. L'EPG et le picon du service sont également différés après cette première image. Une attente de 120 ms regroupe les répétitions de télécommande pendant un changement encore en cours ; elle ne retarde pas le zapping normal.

Le journal local `NeoZap` mesure la résolution et la première image avec une horloge monotone, sans URL ni identifiants. Voir `ZAPPING_PERFORMANCE.md` pour les résultats et leurs limites.

| Télécommande | Télévision | Liste / menu |
|---|---|---|
| OK | Afficher / masquer l'infobar (6 secondes) | Valider / lire |
| Haut / bas | Ouvrir la liste sur la chaîne en cours | Déplacer la sélection |
| Gauche / droite | Zapper | Page de 20 chaînes / tuile de menu |
| CH+ / CH− | Zapper | Page précédente / suivante |
| MENU / Contents Menu | Menu principal | Fermer / ouvrir le menu |
| GUIDE | EPG de la chaîne sélectionnée | EPG |
| INFO | Description du programme | Guide |
| Bleu | Bouquets | Bouquets |
| Rouge | Tous les services | Tous les services / fermer le menu |
| 1–9 puis chiffres | Zapping numérique après 1,4 s, OK pour valider immédiatement | Idem, numéro dans la liste courante |
| 0 sans autre chiffre | Chaîne précédente | Idem pendant la lecture |
| Audio / sous-titres | Sélection des pistes Media3 disponibles | — |
| Retour / EXIT | Un appui : retour habituel ; deux en moins de 2 s : accueil Google TV | Un appui : revenir ; deux en moins de 2 s : accueil Google TV |

Les touches HOME, POWER, volume et les raccourcis capturés par Google TV restent gérés par la Sony. Leur interception par l'application n'est pas garantie. Sur la BRAVIA testée, GUIDE ouvre le guide Sony ; utiliser INFO depuis la liste pour accéder à l'EPG de Neo.

## Portage et limites
Les couleurs, géométries, icônes et police Raleway du grand nom de chaîne proviennent des sources NEO du dépôt. Le rendu est natif et se met à l'échelle depuis 1920×1080. Aucun aperçu contenant des données de démonstration n'est utilisé comme fond.

Le lecteur reste actif sous les menus et s'arrête en arrière-plan. L'infobar contient un seul programme suivant, sans horloge, et 14 emplacements techniques fixes ; les informations absentes restent neutralisées. Les formats vidéo/audio sont ceux du lecteur, pas des garanties HDR/Dolby.

La lecture des programmations OpenWebif est disponible depuis Timers. Les plugins Enigma2, les réglages système du Vu+, le classement fournisseurs, l'enregistrement et le timeshift ne sont pas portés. Les entrées concernées expliquent leurs limites. Aucune commande zap, veille, redémarrage, écriture ou installation n'est envoyée au Vu+.

Les assets procéduraux sont couverts par `dual-skins/LICENSES/MIT.txt`. La police inchangée est sous SIL OFL ; avis embarqués dans `app/src/main/assets/licenses/`. Le XML MetrixHD n'est pas embarqué dans l'APK.

## Construction et validation
JDK 17, Gradle 8.13, SDK Android 36 / build-tools 36.0.0 :

```sh
gradle --no-daemon :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
```

Depuis la version 0.6, installer également le NDK `25.2.9519653`, préparer le SDK GStreamer officiel avec Python 3.12+ et définir `GSTREAMER_ROOT_ANDROID` avant Gradle. Les commandes et l'empreinte du SDK sont dans [GSTREAMER.md](GSTREAMER.md). Le workflow CI réalise ces étapes ; son exécution distante n'a pas été déclenchée pendant cette session.

APK : `app/build/outputs/apk/debug/app-debug.apk`. Les douze tests JVM vérifient les bouquets imbriqués, le filtrage des marqueurs/services cachés, les satellites, le fallback API, les adresses IPTV sans nom de chaîne, la sélection des identifiants par hôte/port et le cache des adresses. Les tests matériels sont décrits dans `Sony_KD-43X75K.md`.

## Statut
- Branche de travail créée le 31 octobre 2026.
- La version 0.3 a été compilée, sa signature vérifiée et son accueil testé sur une Sony BRAVIA VU3 réelle sous Android 14.
- La version 0.4 est le portage du parcours Vu+ ; le détail des contrôles réalisés reste dans le rapport matériel. Une identité à 100 % avec le skin actif ne peut être certifiée sans comparaison à une capture réelle du Vu+.

Lire `CODEX_TASK.md` et `../AGENTS.md`.

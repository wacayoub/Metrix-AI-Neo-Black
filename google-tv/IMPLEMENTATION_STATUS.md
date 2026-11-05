# Statut 0.9.0 alpha — 5 novembre 2026

## Neo Connect intégré

Code 23 signé et installé sur Sony et TCL. Le moteur natif Android est réellement chargé sur la Sony. Association HTTPS épinglée, consentement VPN, échange WireGuard authentifié, réponse OpenWebif dans le tunnel, arrêt du service, profil chiffré persistant et double Retour vers Google TV : quinze contrôles Sony réussis. La TCL est devenue indisponible avant le test du tunnel ; aucune validation distante/vidéo/4K nouvelle n'est revendiquée.

Plugin 0.1.0 installé sur le Vu+ avec exception explicitement autorisée par l'utilisateur à la règle initiale de lecture seule. Moteur Go ARMv7 en espace utilisateur ; aucun module noyau, règle réseau hôte, réglage OpenWebif, autre paquet ou routeur modifié. Le contrôleur et le moteur installés fonctionnent dans le test réel ; leur écran graphique Enigma2 n'a pas été observé. Tunnel arrêté après l'essai.

34 tests JVM réussis ; lint release : zéro erreur, 21 avertissements ; quatre tests Go réussis ; seize tests Python réussis sur le Vu+ (quinze réussis et un ignoré sur Windows). IPK déterministe, sans scripts d'installation, permissions des clés vérifiées sur le récepteur. Orange / ZTE déclaré ; modèle précis, connectivité WAN, redirection et test 4G/5G restent à établir. Détails et preuves : [NEOCONNECT.md](NEOCONNECT.md) et [rapport](reports/neoconnect-2026-11-05.json).

## Historique 0.8.3 et versions antérieures

## Vérification TCL et Sony — 3 novembre 2026

Même APK code 22 installée et vérifiée par empreinte sur les deux TV Android 14 ARMv7. Chaque TV passe 24 contrôles de navigation, 16 de sortie et 11 contrôles des sous-bouquets, Mini TV/transparence et lecture TF1 IPTV courte. Dernières positions mesurées : 68,9 s Sony et 68,1 s TCL, compteurs vidéo croissants, zéro image perdue signalée et aucune erreur Media3 pendant ces essais. Rai 1, Rai 2 et Rai 3 restent refusées HTTP 400 par le Vu+ sur les deux appareils. Aucun contrôle du récepteur. La TCL déclare un mode d'affichage 1920 × 1080 ; la 4K/HDR et la stabilité prolongée ne sont pas validées. Essai TCL initial interrompu par une mise en veille `power_button`, conservé séparément. Détails et preuves dans [TCL_SONY_CHECK.md](TCL_SONY_CHECK.md).

## Version 0.8.3 : diagnostic du refus de streaming et relance

Le Vu+ renvoie HTTP 200 / `video/mpeg`, mais son corps contient seulement `HTTP/1.0 400 Bad Request` (28 octets). Le lecteur détecte désormais ce refus sur sa connexion existante et donne une indication Vu+/tuner/service indisponible. OK et Lecture relancent une chaîne en échec avec une adresse renouvelée. Aucun contrôle du Vu+ n'est ajouté.

27 tests JVM réussis, zéro erreur de lint et dix-sept avertissements ; code 22 signé, installé et vérifié par empreinte. Le refus HTTP 400 et la relance OK avec `cached=false` sont vérifiés sur la Sony. TF1 PURE IPTV fournit une nouvelle image en 1 504 ms et 209 images rendues pendant un test court. **La lecture satellite n'est pas déclarée rétablie** : le Vu+ indique toujours son tuner unique réservé à BBC ONE (75°E), signal zéro et absence de veille. Mise en veille simple demandée à l'utilisateur pour poursuivre le test. Détails dans `STREAM_ERROR_RECOVERY.md`.

## Version 0.8.2 : Mini TV et transparence

Mini TV 16:9 à droite de la liste, EPG en dessous, nom de la chaîne réellement en cours distinct de la sélection parcourue. Jaune alterne avec une vidéo plein écran derrière des panneaux translucides ; choix mémorisé dans les préférences. Un même lecteur et une même vue vidéo sont redimensionnés, sans nouvelle requête de lecture lors de la navigation ou du changement de présentation. Adaptation de la synchronisation des surfaces Media3 à Android 14 et cycle de surface GStreamer lié à l'attachement. Voir `MINI_TV_AND_TRANSPARENCY.md`.

Code 21 signé et installé sur la Sony. 23 tests JVM et 70 contrôles TV réussis (13 Mini TV Media3, 24 navigation, 11 GStreamer et 22 sortie), zéro erreur de lint et dix-sept avertissements. Les positions et compteurs vidéo Media3 avancent dans les deux modes ; GStreamer confirme ses états de pause/reprise et sa surface redimensionnée. Les captures ADB peuvent montrer le plan vidéo noir et ne valident pas les pixels de la dalle. Rapports et limites dans `MINI_TV_AND_TRANSPARENCY.md`.

## Version 0.8.1 : rendu de l'interface

Surlignage des bouquets/satellites modifiant uniquement les propriétés de leur couche graphique ; pages recalculées aux frontières des vingt lignes. Observation de la sauvegarde de session par `snapshotFlow`, picons convertis en `ImageBitmap` une seule fois par bitmap et fonds des tuiles mémorisés. Le rendu précédent des chaînes est conservé, avec ses vingt emplacements réutilisés et un panneau EPG immédiat. Aucun changement des lecteurs vidéo ; les limites IPTV/4K restent applicables. Voir `NAVIGATION_PERFORMANCE.md` pour les mesures et contrôles de cette version.

APK release code 20 installée avec conservation des données, signature vérifiée et ART speed réussi. 23 tests JVM réussis ; lint : zéro erreur et seize avertissements. **73 contrôles Sony réussis** : 24 de navigation/EPG, 27 de reprise de session et 22 de sortie. Le parcours des bouquets passe de 15 à 9 ms de rendu médian ; le menu reste à 13 ms et aucun gain n'est démontré pour les chaînes (31 ms contre 22 ms sur le relevé de référence). Rapport complet : `reports/sony-smooth-ui-2026-11-02.json`.

## Version 0.8.0 : dernière session et nouveaux visuels de lancement

Reprise de la dernière chaîne, du bouquet/sous-dossier/satellite et du curseur. Signet privé chiffré avec AndroidKeyStore, lié au récepteur ; enregistrement différé après la navigation et avant le passage en arrière-plan. Résolution par référence de service, curseur borné si la liste change, validation du récepteur avant lecture automatique et annulation de cette reprise en cas d'action utilisateur. L'actualisation ne remplace plus « Tous les services » par le premier bouquet et conserve la sélection par référence.

Nouveaux exports d'icône et de bannière NEO dans cinq densités, avec le nom intégré à la bannière ; catégories MAIN/LAUNCHER/LEANBACK_LAUNCHER et ressources explicites sur l'activité. Tuile réellement visible dans Gathin TV Home et lancée avec OK. Aucun réglage du lanceur ni changement du Vu+.

APK code 19 signée et installée, ART speed réussi, 23 tests JVM réussis. Lint release : zéro erreur, seize avertissements. 26 contrôles de reprise réussis, complétés par un lancement réel depuis la nouvelle tuile et la reprise de Rai 1 avec le curseur à la ligne 28. Rapports `reports/sony-resume-2026-11-02.json` et `reports/sony-launcher-icons-2026-11-02.json` ; détails dans `RESUME_AND_LAUNCHER.md`. Les limites IPTV/4K précédentes restent applicables.

## Version 0.7.3 : navigation première / dernière page

Haut depuis la première chaîne sélectionne la dernière chaîne et affiche automatiquement sa page. Bas depuis la dernière revient à la première. Navigation identique dans les bouquets/sous-dossiers et les satellites. La sélection chaîne par chaîne est circulaire ; les touches de pagination gardent leurs sauts bornés de vingt lignes. Les changements de chaîne gauche/droite depuis le guide sont également circulaires ; les déplacements entre programmes EPG restent inchangés.

APK release code 18 installée sur la Sony avec conservation des données, signature et ART speed vérifiés. Build et lint release réussis : zéro erreur, quinze avertissements. Dix-huit contrôles matériels ciblés passent : dernière chaîne et dernière page du catalogue réel, retour vers la première, déplacements voisins, continuité au franchissement de fin, pagination CH+/− et boucles des bouquets/satellites. Rapport `reports/sony-wrap-navigation-2026-11-02.json` ; reproduction avec `tools/test-tv-navigation.py --wrap-only` et les arguments ADB habituels. La TV est laissée sur la première ligne de la liste des chaînes. Aucun changement du Vu+ ni du double EXIT ou des lecteurs.

Un premier parcours de dix-huit contrôles passe également sur la liste de 100 services du bouquet mémorisé (`reports/sony-wrap-bouquet-2026-11-02.json`). Le parcours global vérifie explicitement l'en-tête « Tous les services » pour éviter de confondre ce bouquet avec le grand catalogue lorsque la synchronisation de démarrage restaure une sélection enregistrée.

## Version 0.7.2 : double EXIT vers l'accueil TV

L'ancien retour alternait indéfiniment entre lecteur, liste et menu. Deux appuis EXIT/Retour espacés de deux secondes au maximum ouvrent désormais l'accueil Android TV et terminent la tâche Neo. Le premier conserve la navigation précédente avec un Toast non bloquant. Les répétitions d'une touche maintenue sont ignorées ; une autre touche, l'expiration du délai ou un changement de cycle de vie annule la confirmation. BackHandler et les touches BACK/ESCAPE partagent le même traitement, sans compter deux fois un appui matériel. La lecture est mise en pause avant la sortie et libérée à la destruction de l'activité.

APK release code 17 installée avec conservation des données, signature vérifiée et compilation ART speed réussie. Build et lint release réussis : zéro erreur, quinze avertissements. Contrôles matériels détaillés dans `reports/sony-double-exit-2026-11-02.json` : appui simple, délai expiré, autre touche intercalée, appui maintenu, double Retour, double Escape depuis le menu, sortie depuis Setup, relance, décodage de la première chaîne réelle, pause de la lecture et suppression de la tâche des récents.

La Sony résout l'accueil Google TV `com.google.android.apps.tv.launcherx/.home.HomeActivity`, mais son service d'accessibilité `com.gathin.tvhome/.HomeKeyService` redirige ensuite vers Gathin TV Home. La touche HOME physique reproduit exactement cette redirection. Le test compare donc avec l'accueil effectivement ouvert par HOME et confirme Neo fermé ; aucun service, réglage système ou comportement global HOME n'a été modifié. La TV est laissée sur cet accueil. Aucun changement du Vu+ ni nouvelle validation des gels 4K/IPTV.

## Version 0.7.1 : noms complets avant l'EPG

Le nom de chaîne et le titre EPG partagent désormais un texte continu : nom complet, séparateur, programme. Suppression de la largeur fixe de 170 dp et des points de suspension dans cette ligne. Seule la ligne sélectionnée peut défiler si elle déborde. Les noms et titres du panneau de détails se replient sans l'ancienne limite de deux/trois lignes ; le titre sélectionné du guide peut aussi défiler.

APK release code 16 signée et installée sur la Sony en conservant la connexion ; ART speed réussi. Build et lint release : zéro erreur, quinze avertissements. Comparaison visuelle sur la TV : `SAN MARINO RTV HD` et `WEDOTV MOVIES` complets, EPG placé après le nom ; vingt lignes conservées et guide accessible. Sept contrôles ciblés réussis, consignés dans `reports/sony-full-names-2026-11-01.json`. Le défilement d'un cas extrême dépassant toute la ligne n'a pas été mesuré séparément. Aucun changement du Vu+ ni du comportement des lecteurs ; limites de stabilité 0.7.0 toujours applicables.

## Version 0.7.0 : manipulation et contrôle autonome

APK optimisée avec R8, réduction des ressources et signature de développement identique à l'installation existante. Index des services/bouquets calculé à réception, pages de vingt éléments sans copie de la liste entière, EPG dédoublé avec voie prioritaire pour la sélection, cache de huit satellites et horloge actualisée à la minute. Répétition des touches limitée aux déplacements ; numéros jusqu'à six chiffres et actions contextuelles dans les satellites, dossiers et menus.

Sur la Sony, même séquence de navigation : médiane de rendu 350 → 36 ms, P90 750 → 53 ms et P95 950 → 73 ms. La comparaison comprend le passage debug → release et ne mesure pas la latence physique de la télécommande. Des images restent hors délai. Dix-sept tests JVM réussis ; lint release zéro erreur, quinze avertissements. Détails dans `NAVIGATION_PERFORMANCE.md`.

Le test autonome `tools/test-tv-navigation.py` parcourt les vrais bouquets imbriqués, satellites, listes, EPG, menus, sélection numérique et commandes des lecteurs. Il contrôle les nœuds accessibles et les événements réels du lecteur, sans capture de la surface vidéo ni commande d'écriture du Vu+. Résultat détaillé dans `reports/sony-navigation-2026-10-31.json` ; il ne prétend pas vérifier chaque chaîne du catalogue, la qualité sonore ou la fluidité finale de la dalle.

Résultat du parcours de navigation/commande : 62 contrôles réussis, zéro échec. Quatre contrôles complémentaires de démarrage/zapping GStreamer et de restauration Media3 passent également (`reports/sony-gstreamer-zapping-2026-10-31.json`). Signature et conservation de la connexion vérifiées.

Le contrôle prolongé distinct révèle une limite réelle : TF1 FHD PURE termine après 20–26 s dans Media3 ; GStreamer produit aussi une erreur de décodage (`gst-stream-error-quark / 7`), reproduite après environ 23 s. La stabilité IPTV prolongée est donc **en échec**, sans cause racine établie. Rapport `reports/sony-iptv-duration-2026-10-31.json`. Une dernière compilation ajoute seulement le domaine/code aux journaux natifs ; les textes bruts et adresses ne sont pas journalisés. Retour final sur Rai 1 avec Media3. Les 66 contrôles courts ne sont pas présentés comme une validation globale de lecture.

Un blocage de démarrage/pause GStreamer découvert par ce test a conduit au passage `playbin` → `playbin3`, à la sélection de pistes par `SELECT_STREAMS` et à des événements basés sur l'état réel, plutôt que le seul remplissage du tampon. L'essai matériel TF1 FHD a reçu une image 1920 × 1080, puis les états PAUSED et PLAYING après les touches correspondantes. Aucun correctif visuel des gels 4K/HDR validé ; les fonctions Enigma2 non portées restent signalées.

## Version 0.6.2 : essai spécifique Sony
L'essai des files MediaCodec synchrones sur Sony BRAVIA VU3 / Android 14 n'a pas résolu les gels d'image, le son continue selon l'utilisateur. Il est retiré dans 0.6.3. Le diagnostic local, les essais du lecteur système et le refus de la bibliothèque privée Sony sont détaillés dans `SONY_COMPATIBILITY.md`.

APK d'essai code 11 installée, signature et ART vérifiés. Quatorze tests JVM, build et lint réussis (zéro erreur, quinze avertissements). Profil synchrone confirmé dans les journaux de la Sony ; TNT MAXOTT en profil 4K/HDR démarre, première image à 3812 ms. Les compteurs proches de 50 images/s ne reflètent pas tous les gels constatés à l'écran.

Version 0.6.3 : la sonde PixelCopy de développement (code 12) a déclenché un SIGSEGV dans `/vendor/lib/egl/libGLES.so`, `stream_unpack`, sur la Sony. Elle est retirée dans le code 13, sans nouvelle tentative de lecture des pixels matériels. Le script externe `tools/check-sony-playback.py` mesure les présentations SurfaceFlinger, les compteurs du lecteur et la survie du processus, sans modifier le récepteur ni affirmer que les pixels finaux de la dalle sont fluides. Les gels restent non résolus.

Code 13 restauré et ART vérifié ; absence des classes expérimentales confirmée dans les DEX de l'APK. Build, quatorze tests JVM et lint réussis (zéro erreur, quinze avertissements). Contrôle autonome réel de 90,11 s sur TNT MAXOTT, sans plantage ni interruption détectée dans les mesures disponibles ; le rapport `reports/sony-tnt-2026-10-31.json` conserve explicitement `visible_motion_verified=false`. Aucune correction visuelle des gels validée.

## Version 0.6.1 : réserve de lecture 4K/HDR
Media3 choisit un profil de chargement à partir des dimensions et du transfert colorimétrique des pistes. UHD ou HDR PQ/HLG : 12–35 s de réserve, démarrage demandé 4 s, reprise 6 s ; profil précédent conservé pour les autres formats. Compteurs réels des images rendues/perdues et du tampon toutes les dix secondes. Quatorze tests JVM, build et lint sans erreur bloquante. Une régression d'initialisation de LoadControl détectée à l'installation a été corrigée et couverte par deux tests ; validation matérielle et comparaison VLC dans `Sony_KD-43X75K.md`.

APK corrigée testée après rallumage : **gels 4K/HDR toujours confirmés par l'utilisateur**, avec KING365 et MAXOTT. JustPlayer en HLS ne résout pas les gels ; son tunneling provoque un plantage natif du système Sony, mode ensuite désactivé. Les gels se reproduisent dans un extrait stocké sur la TV ; l'analyse indépendante des 1643 images ne détecte ni longue répétition exacte ni trou d'horodatage. Vérification des capacités du décodeur Realtek et essai optionnel du moteur fourni par le firmware décrits dans `Sony_KD-43X75K.md`. Aucune fluidité déduite des seuls compteurs.


## Version 0.6 : GStreamer intégré
Contrôle 4K ultérieur sur la Sony : quatre flux 3840 × 2160 / HEVC vérifiés (TF1, France 2, Love Nature de PURE ; TRT de MAXOTT). Image TRT visible dans la capture, quelques transitions de tampon. Love Nature nommé 4K chez STRONG8K : flux reçu en 1920 × 1080 / AVC avec Media3, échec avec GStreamer sur deux essais. Résultats et limites de fluidité/son dans `Sony_KD-43X75K.md` ; aucune compatibilité générale de tous les flux 4K affirmée.

Choix Media3 / GStreamer mémorisé dans Setup, utilisable au D-pad avec focus visible. SDK GStreamer Android 1.28.8 officiel vérifié par SHA256, JNI C `playbin` / GL / OpenSL ES, contrôle sérialisé sur un thread dédié. Mêmes listes, bouquets, satellites et commandes ; pistes natives numérotées. Décodage automatique avec les plugins Android MediaCodec et libav.

APK code 9 installée sur la Sony ARMv7. Lecture SD visible dans une capture et retour sur TF1 SD avec callback vidéo en 1578 ms. TF1 FHD PURE : image et son confirmés par l'utilisateur sur la TV ; la capture ADB et les métadonnées de la surface matérielle ne suffisent pas à contrôler son rendu. Build, douze tests JVM et lint (zéro erreur, quinze avertissements) réussis. Le détail, les sources et la préparation du SDK sont dans `GSTREAMER.md` et `Sony_KD-43X75K.md`. La prise en charge de tous les codecs, l'affichage effectif des sous-titres, les flux HTTPS/HLS et l'ABI arm64 n'ont pas fait l'objet d'une validation matérielle exhaustive.

## Correctif 0.5.2 : lecture IPTV
Suppression du refus systématique des flux publics, tout en gardant OpenWebif sur le LAN. Extraction de l'URL au champ 10 de la référence Enigma2, sans le nom de service ajouté par certains M3U OpenWebif, et conservation des échappements de jetons. Sources Media3 distinctes pour le récepteur authentifié et les fournisseurs externes. Erreurs HTTP 401/403/404 explicites, sans adresse ni identifiant dans les journaux applicatifs. APK code 8 signée, installée et compilée ART sur Sony ; douze tests JVM passés et lint : zéro erreur, quatorze avertissements.

Lecture réelle contrôlée : KING365 TF1 SD, image visible dans la capture ADB, premier frame en 2012 ms. PURE IPTV TF1 FHD : callback premier frame en 1788 ms, lecteur prêt en 1825 ms, formats AVC 1920 × 1080 et audio MP4A-LATM ; la capture ADB ne restitue pas sa vidéo. Le refus HTTP 401 constaté depuis le PC ne se reproduit pas dans cet essai sur la Sony. La confirmation visuelle/sonore de PURE sur la TV reste distincte du contrôle du décodeur Media3.

## Correctif 0.5.1 : sous-bouquets
Parcours natif GET `/api/getservices?sRef=…`, sans aplatir la hiérarchie pour la navigation bleue. Types directory/group distingués des services jouables. Pile de retour avec restauration de sélection, cache mémoire de 32 dossiers, annulation des réponses de navigation périmées. Les dossiers finaux contenant des chaînes réutilisent la liste NEO, les picons, l'EPG et le lecteur existants. Deux tests de régression supplémentaires couvrent plusieurs niveaux et les types de référence.

## Satellites, caches et météo
La touche verte ouvre les satellites natifs du récepteur. Test matériel : 42 entrées ; sélection Hotbird 13°E, 1359 services jouables affichés avec leurs données réelles. Les picons ont désormais un cache mémoire/disque indépendant de l'EPG. La liste complète est également copiée dans le cache privé pour l'ouverture hors attente du réseau.

Météo réelle et trois prévisions quotidiennes affichées avec date/horloge, lieu repris de la configuration NEO du Vu+ : Casablanca, 33.59 / −7.61. Aucune configuration du récepteur n'a été modifiée. Les captures réelles et le contrôle du cache sont décrits dans `Sony_KD-43X75K.md`.

## Correctif 0.4.1 : zapping
APK installée sur la Sony : buffer de démarrage réduit, source HTTP réutilisée, adresses de flux en cache et préparées pour les chaînes voisines, métadonnées différées, contrôle de lecture hors du frame scheduler Compose. Optimisation ART du paquet effectuée sur la TV. Six tests JVM, build et lint réussis. Trois essais HD : première image entre 1,49 et 2,14 secondes, moyenne réduite d'environ 25 % ; première ouverture à froid encore plus lente. Mesures détaillées et limites dans `ZAPPING_PERFORMANCE.md`.

- Portage Android du parcours MetrixNEO : menu principal avec icônes du skin, liste de 20 chaînes par page, panneau de détails, bouquets distincts, EPG par service, picons OpenWebif et grand nom de chaîne Raleway.
- Commandes ajoutées : MENU, INFO, GUIDE, couleurs, navigation/page, CH+/−, saisie numérique, rappel de la chaîne précédente, audio et sous-titres Media3. Les touches réservées par Google TV restent gérées par le système.
- Lecteur conservé sous les menus, pause en arrière-plan, erreurs et buffering explicites. Infobar masquable après six secondes, un programme suivant, 14 cases fixes avec valeurs inconnues neutralisées.
- Adresse/port/utilisateur/bouquet mémorisés ; mot de passe chiffré AES-GCM, clé AndroidKeyStore propre à la TV, sans secret en dur. Lectures GET OpenWebif uniquement ; aucun zap du récepteur, redémarrage, plugin ni écriture.
- Vérifiés : build local, 3 tests JVM API/parser, lint sans erreur, installation/signature, affichage/menu/Setup, connexion authentifiée, bouquets, picons/EPG et zapping Rai 1 → Rai 2 sur Sony réelle. L'utilisateur a confirmé l'image et le son sur Rai 1. Voir `Sony_KD-43X75K.md` pour les limites du test matériel.
- Non portés : plugins Enigma2, réglages système Vu+, enregistrement/timeshift, EPG graphique multi-chaînes, IPToSat Pro, IPAudio, IA et affiches. Les entrées concernées indiquent leurs limites.
- L'interface repose sur les sources du dépôt. La fidélité à 100 % au skin actif et la parité complète Enigma2 ne sont pas certifiées.
- Changements locaux non publiés ; aucune exécution CI distante affirmée.

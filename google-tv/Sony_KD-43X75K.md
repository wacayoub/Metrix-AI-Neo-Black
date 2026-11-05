# Sony BRAVIA KD-43X75K — Android TV 14

## Navigation 0.7.0 / code 15

Installation locale optimisée avec conservation des données. Le parcours comparable de dix touches bas, dix haut et quatre changements de page passe de 350 ms de rendu médian (debug code 13) à 36 ms (release optimisée) ; P90 53 ms, P95 73 ms, 26 images hors délai sur 40. Il reste donc des ralentissements, malgré un temps médian environ dix fois plus court. Ce résultat décrit le rendu des menus, pas la vidéo ni la latence physique de la télécommande.

Dix-sept tests JVM passent ; lint release sans erreur et quinze avertissements. Le parcours matériel autonome couvre les écrans et commandes implémentés : `reports/sony-navigation-2026-10-31.json`, avec limites explicites sur ce qui peut être observé. Les sous-dossiers PURE IPTV → FRANCE FHD et les chaînes Hotbird sont parcourus sur les données réelles du récepteur ; météo Casablanca et horloge présentes.

Parcours de navigation/commande : 62 contrôles réussis, zéro échec. Complément GStreamer : démarrage, CH+ et CH− avec nouvelle image décodée, puis restauration Media3, quatre contrôles réussis. La sélection de piste audio GStreamer est acceptée ; la pause/reprise atteint les états réels du pipeline. Signature vérifiée, connexion conservée. Le contrôle supplémentaire de rendu après démarrage donne une médiane de 30 ms (45 images, 25 hors délai), dans un contexte sans TNT en pause sous la liste.

**Contrôle prolongé : stabilité TF1 FHD non validée.** Après le parcours court, Media3 atteint STATE_ENDED à 20,244 puis 26,051 s. GStreamer rencontre une erreur à environ 13,5 s ; une compilation ajoutant uniquement la journalisation du domaine/code reproduit `gst-stream-error-quark / 7` (`GST_STREAM_ERROR_DECODE`) à environ 23,1 s. Le code signale un échec de décodage, sans identifier à lui seul sa cause ([référence GStreamer](https://gstreamer.freedesktop.org/documentation/gstreamer/gsterror.html)). Rapport `reports/sony-iptv-duration-2026-10-31.json`, résultat en échec. Aucun défaut d'Internet déduit. La TV est rétablie sur Rai 1 / Media3 ; les gels 4K/HDR restent eux aussi non résolus.

L'ancien pipeline GStreamer restait READY avec PLAYING en attente sur TF1 FHD, malgré un événement de tampon rempli. Avec `playbin3`, l'essai reçoit un callback vidéo 1920 × 1080 après 2276 ms, et confirme effectivement PAUSED puis PLAYING lors de la pause/reprise. Les états sont lus sans attente bloquante ; la sélection de pistes est adaptée à l'API de playbin3. Cela ne prouve pas que les gels 4K/HDR du firmware sont corrigés.

## Restauration 0.6.3 / code 13

APK sans PixelCopy, sans profil synchrone forcé et sans bibliothèque privée Sony, vérifiée par signature et inspection des DEX : aucune des classes de sonde/lecteur expérimental ne reste embarquée. Installation avec conservation des données et ART speed réussis. Quatorze tests JVM passent ; build et lint réussis, zéro erreur et quinze avertissements. Media3 est rétabli sur TNT MAXOTT 4K HDR. Le gel visible reste non résolu ; les contrôles autonomes suivants ne le présentent pas comme corrigé.

## Essai 0.6.2 — files de décodage synchrones

APK d'essai code 11 / 0.6.2-alpha signée, installée avec conservation des données, puis ART speed réussi. Build, quatorze tests JVM et lint : zéro erreur, quinze avertissements. L'option native provisoire et la dépendance propriétaire ont été retirées de cette APK.

Sur la Sony réelle, le processus confirme `profile=vu3_android14 codec_queue=synchronous`. MAXOTT → VIP 4K CHANNELS → ligne 20, TNT SPORT ULTIMATE 4K : profil `4k_hdr`, première image à 3812 ms, READY à 6566 ms. Premier relevé : 246 images rendues, zéro perdue, position 4901 ms, tampon 7624 ms. **L'utilisateur confirme que l'image gèle toujours pendant que le son continue.** Les compteurs restent proches de 50 images/s sans pertes Media3 ; ils ne reflètent donc pas tous les gels visibles. Le forçage synchrone est retiré dans 0.6.3. Pas de modification de résolution, HDR, cadence système ni du Vu+.

## Mesures autonomes de présentation et de contenu

À la demande de l'utilisateur, les vérifications suivantes ne demandent plus de confirmations répétées. Un relevé SurfaceFlinger de 46,52 s sur Neo 0.6.2 obtient 2349 horodatages distincts de présentation, 31 clés distinctes du compositeur vidéo matériel, intervalle maximal 50,649 ms, aucun intervalle supérieur à 500 ms. Ce relevé confirme l'activité des couches mais ne prouve pas l'animation finale visible sur la dalle.

Le rapport MediaCodec du lecteur système, daté 22:17:43.998, UID média 1013 et HEVC 3840 × 2160/HDR10, donne sur l'extrait MP4 de 32 s : 1643 images libérées, 1075 rendues, 558 perdues, 137 événements `freeze-count`, durée maximale d'événement 133 ms et 797 événements judder. Ces événements mesurés ne sont pas assimilés à des arrêts de plusieurs secondes. À l'inverse, le rapport JustPlayer MP4 du même extrait indique seulement trois pertes et un maximum freeze de 40 ms malgré les gels rapportés humainement. Aucun verdict de fluidité à partir des seuls compteurs.

La sonde de développement 0.6.3 / code 12 a tenté PixelCopy sur notre SurfaceView. À 22:34:01, première tentative pendant la lecture HDR : SIGSEGV dans `/vendor/lib/egl/libGLES.so` (`stream_unpack+5076`), RenderThread du processus Neo 1493. Exit-info confirme APP CRASH(NATIVE), status 11. Aucune miniature ni mesure de pixels exploitable n'a été produite. La sonde a été retirée dans le code 13 ; ce plantage induit par le test est distinct des gels antérieurs et n'est pas présenté comme leur cause prouvée.

Le contrôle conservé est le script ADB externe `tools/check-sony-playback.py`, sans lecture directe des pixels ni modification de la TV. Après restauration code 13 sur TNT MAXOTT : contrôle autonome de 90,11 s, processus conservé, neuf relevés du lecteur, 4424 horodatages distincts de présentation ; intervalle maximal 34,076 ms, aucune interruption de présentation supérieure à 500 ms, aucun compteur/position bloqué et aucune erreur ADB pendant cette fenêtre. Le rapport garde `visible_motion_verified=false` : ces mesures ne certifient pas l'absence de gel sur la dalle. Rapport sans URL ni identifiant fournisseur : `reports/sony-tnt-2026-10-31.json`.

## Gel de TNT Sports Ultimate HDR — version 0.6.1

La chaîne courante du signalement était KING365 → ANGLAISES (UK) → `TNT SPORTS ULITMATE HDR 4K`, ligne 83. Elle se distingue de TRT 4K testée précédemment. Source et adresse identiques lors de la comparaison des lecteurs.

- GStreamer 0.6 : gel signalé par l'utilisateur après le démarrage 3840 × 2160. Un callback de première image ne prouvait pas la stabilité de la lecture prolongée.
- Media3 0.6 : première image en 1245 ms, prêt en 1370 ms ; remise en tampon entre 83547 et 87818 ms après la demande, soit environ 4,27 s. Formats lus : HEVC 3840 × 2160, HDR signalé dans ColorInfo, audio EAC3-JOC.
- VLC 3.7.2, déjà installé : lecture du même URI dans l'application VLC, avec Neo arrêté pour éviter deux connexions fournisseur. Session Android en PLAYING, mais nombreux avertissements d'images en retard, dont un retard d'environ 9580 ms. Ce test ne permet pas de le recommander comme plus stable sur ce flux. Lecture VLC ensuite fermée normalement, session STOPPED et inactive.
- La Sony expose les types HDR Android 2 et 3 : HDR10 et HLG. Une surface du flux indiquait BT2020 / SMPTE 2084. Le Wi-Fi relevé était à 2462 MHz, RSSI −55 dBm, liaison annoncée 144–156 Mb/s ; le débit utile et la congestion ne sont pas déduits de cette vitesse de liaison.

Le correctif Media3 0.6.1 sélectionne la politique de chargement d'après les formats des pistes, et non le nom de la chaîne : hauteur ≥ 2160 ou transfert HDR PQ/HLG → minimum 12 s, maximum 35 s, seuil de démarrage demandé 4 s, reprise 6 s. Les autres formats gardent 3,5/12/0,5/1,5 s. Allocation partagée entre les politiques ; journaux `NeoBuffer` et compteurs `NeoPlayback` sans URI, pour distinguer READY et images effectivement rendues.

Build et quatorze tests JVM réussis, dont deux régressions de construction/cycle de vie de LoadControl. Une première installation de développement a révélé `getBackBufferDurationUs not implemented` : les méthodes par défaut Java n'étaient pas transmises par la délégation Kotlin. Le contrôleur corrigé implémente explicitement les méthodes de l'interface ; le test reproduit les appels qui provoquaient le plantage. Cette erreur est distincte du gel vidéo signalé avant le correctif. Installation corrigée, signature et ART réussis ; contrôle matériel prolongé décrit ci-dessous.

**Contrôle effectué après rallumage : gels non résolus.** Media3 0.6.1 a sélectionné `normal` sur TNT FHD et `4k_hdr` sur TNT UHD. KING365 : première image 1401 ms, prêt 3010 ms ; environ deux minutes avec 14–17 s de tampon et quasiment aucune image perdue, puis recul d'horodatage, pertes et fin du flux à environ 201 s. L'utilisateur a confirmé des arrêts de plusieurs secondes. Source alternative MAXOTT → VIP 4K CHANNELS → ligne 20 : HEVC 3840 × 2160/HDR, audio AAC, première image 1083 ms, prêt 2765 ms, tampon observé autour de 5–6 s. L'utilisateur constate également les gels, malgré des compteurs proches de 50 images/s. Les seuils du contrôleur sont des objectifs de chargement, pas une réserve garantie ; READY et les compteurs ne prouvent pas la fluidité à l'écran.

JustPlayer officiel 0.217 a été installé et testé séparément, Neo arrêté pour éviter deux connexions fournisseur. Son mode tunneling a provoqué trois plantages natifs : SIGABRT, `ubsan: sub-overflow`, dans `libstagefright.so` / `VideoRenderQualityTracker::processMetricsForRenderedFrame` du système Sony. Tunneling désactivé ensuite. Le même service MAXOTT en HLS fonctionne sans ce plantage, mais l'utilisateur confirme toujours les arrêts. Ce changement de lecteur/conteneur ne constitue donc pas une solution validée.

Comparaison locale : 8 segments HLS du même programme, 48 800 852 octets, 32,86 s, téléchargés avant lecture puis copiés dans la mémoire de la Sony. JustPlayer, tunneling désactivé : l'utilisateur confirme encore des gels pendant l'extrait. Analyse logicielle indépendante : HEVC Main 10, 3840 × 2160, yuv420p10le, 50 images/s ; 1643 images décodées sur 32,84 s, aucun intervalle d'horodatage supérieur à 100 ms ni répétition exacte du plan de luminance pendant au moins 500 ms. Ce test écarte l'accès Internet pendant cette lecture et oriente l'investigation vers le décodage/affichage sur la TV ; il ne certifie pas à lui seul la cause dans le firmware.

Sonde Android en lecture seule : SoC RTD2873A / Realtek ; `OMX.realtek.video.decoder` matériel, HEVC Main/Main10/HDR10, niveaux jusqu'à High Tier 5.1, capacités annoncées 3840 × 2160 à 50/60 images/s, PerformancePoint 2160p60, débit jusqu'à 80 Mbit/s. Les décodeurs HEVC logiciels exposés sont limités à 2048 × 2048 et ne fournissent pas de solution 4K. Android n'expose qu'un mode d'affichage 3840 × 2160 à 60 Hz, HDR10/HLG. Les modes HDMI 50 Hz de la fiche Sony ne prouvent pas qu'une application peut commuter sa surface à 50 Hz.

Le lecteur système `com.realtek.tvmediaplay` utilise `rtk-mediaplayer`, notamment `com.realtek.media.RtkMediaPlayerWrap`. Son initialisation dans Neo a été refusée par une SecurityException du système. Le repli Android MediaPlayer n'a produit aucune dimension ni première image sur le flux TS, puis a terminé vers 25 s. Cette option expérimentale et la dépendance propriétaire ont été retirées. Le même extrait local remuxé en MP4 présente encore des gels selon l'utilisateur, avec JustPlayer puis le lecteur système `com.android.gallery3d/.app.MovieActivity`. Aucun réglage Wi-Fi, firmware ou service du Vu+ modifié. Le profil Media3 synchrone de l'essai final 0.6.2 est décrit dans `SONY_COMPATIBILITY.md` ; résultat matériel à confirmer.

## Contrôle 4K — 31 octobre 2026, après installation 0.6

Échantillon de cinq chaînes, testées sur cette Sony avec l'APK 0.6.0-alpha / code 9. Le nom commercial 4K n'est pas utilisé comme preuve de résolution. Mesures provenant des rapports MediaCodec Android de l'UID de l'application, après libération du flux précédent, et du lecteur. Aucun changement d'APK ni du Vu+ pendant ce contrôle.

| Chaîne et bouquet | Résolution / codec reçus | Résultat du test |
| --- | --- | --- |
| TF1 4K — PURE IPTV | 3840 × 2160, HEVC, OMX.realtek.video.decoder | GStreamer : prêt en 2400 ms, environ 90 s observées sans erreur applicative. Vidéo absente de la capture ADB ; fluidité/son non confirmés humainement pour cet essai 4K. |
| France 2 UHD — PURE IPTV | 3840 × 2160, HEVC, OMX.realtek.video.decoder | GStreamer : prêt en 3447 ms, environ 46 s observées sans erreur applicative. |
| Love Nature 4K (VO) — PURE IPTV | 3840 × 2160, HEVC, OMX.realtek.video.decoder | GStreamer : prêt en 3846 ms, environ 45 s observées sans erreur applicative. |
| TRT 4K — MAXOTT / VIP 4K CHANNELS | 3840 × 2160, HEVC, OMX.realtek.video.decoder | GStreamer : callback GL vidéo en 1341 ms, prêt en 3153 ms ; image visible dans la capture avec infobar 4K / 3840 × 2160. Environ 83 s observées. Trois transitions de tampon immédiatement suivies de l'état prêt, sans erreur ni plantage. |
| Love Nature UHD 3840P — STRONG8K / 4K UHD 3840P | **1920 × 1080, AVC**, confirmé par Media3 et MediaCodec | GStreamer : échec d'accès au flux sur deux essais, cause précise non établie. Media3 : première image signalée en 4572 ms, prêt en 4706 ms, puis une remise en tampon d'environ 4,9 s. Le flux reçu pendant le contrôle est FHD malgré son intitulé. |

« Prêt » désigne l'état du lecteur/tampon et ne remplace pas une confirmation de fluidité à l'écran. Les durées d'observation ci-dessus viennent de l'horodatage des changements de chaîne ; `lifetime_millis` de MediaMetrics est arrondi et n'est pas traité comme une mesure exacte. La valeur codec `error_code=-1` n'est pas interprétée comme un code de succès ou d'échec. Aucun HDR, FPS précis ni audio Dolby certifié par ces mesures. Aucun test exhaustif de tous les bouquets.

Les contrôles n'ont pas reproduit de plantage de l'application ; les dernières sorties de processus correspondent aux mises à jour d'APK antérieures. Retour à GStreamer après la comparaison Media3. Captures privées locales : `sony-4k-trt-gst.png`, `sony-4k-strong-format.png`, `sony-4k-final.png` ; rapports Android bruts et références fournisseurs conservés uniquement dans le dossier local ignoré, sans URL ni secret dans ce document.

## Version 0.6 — GStreamer
31 octobre 2026 : GStreamer 1.28.8 intégré dans l'APK code 9, ABI armeabi-v7a confirmée sur cette Sony. Bibliothèques natives et runtime C++ présents, certificats/polices/notices du SDK empaquetés. Signature vérifiée, installation avec conservation des données et compilation ART speed réussies. Build, douze tests JVM et lint : zéro erreur, quinze avertissements.

Contrôles matériels effectués :
- Setup : sélection Media3 puis GStreamer uniquement au D-pad/OK ; coche et contour de focus sur GStreamer confirmés. Choix conservé entre installations et relances.
- KING365 TF1 SD : image visible dans la capture, dimensions remontées 1024 × 576, une piste audio. Initialisation native puis frame en 3553 ms ; retour vers cette chaîne après un autre essai : frame en 1578 ms. La chaîne suivante n'a pas fourni de frame pendant la fenêtre de neuf secondes ; aucune compatibilité exhaustive du bouquet n'est affirmée.
- PURE IPTV TF1 FHD : le 31 octobre 2026, l'utilisateur a confirmé **image et son OK sur la TV avec GStreamer**. La capture ADB était noire et le callback GL ne remontait pas la première image. Le message OMX Realtek `DynamicANWBuffer` ne permettait donc pas de conclure à une panne. L'essai de priorité logicielle AVC a été retiré ; la version retenue garde le décodage automatique confirmé par l'utilisateur.
- Commandes pause, reprise, ouverture des pistes puis retour au lecteur envoyées par ADB. Aucun plantage observé. Leur effet visuel instantané n'est pas certifié par la seule capture de la surface matérielle.

La transition vers une autre URI utilise READY pour conserver la fenêtre vidéo, et les commandes sont traitées hors du thread UI. Les compteurs de pistes sont indépendants de la disponibilité des dimensions vidéo. Les valeurs techniques non remontées restent inconnues dans l'infobar. Sous-titres effectivement rendus, HDR, HTTPS/HLS, arrêt réseau et matériel arm64 non validés pendant cette session. Le contrôle 4K ultérieur figure en tête de ce rapport.

Dernière installation vérifiée : 0.6.0-alpha / code 9, signature et ART réussis ; application laissée sur TF1 FHD PURE avec GStreamer. Sur ce flux, la Sony ne remonte toujours ni dimensions ni nombre de pistes via playbin au moment du contrôle : la page Pistes ne propose donc que la désactivation des sous-titres. La lecture automatique image/son est confirmée par l'utilisateur, mais la sélection audio manuelle de ce flux reste une limite connue. Capture : `sony-neo-gst-audio.png`.

Captures privées locales : `sony-neo-gst-king.png`, `sony-neo-gst-selector-final.png`, `sony-neo-gst-final.png`, `sony-neo-gst-tracks-final.png`. Aucun flux ni identifiant fournisseur dans ces rapports. Aucun changement ni commande zap sur le Vu+.

## Correctif 0.5.2 — flux IPTV
31 octobre 2026 : APK code 8 / 0.5.2-alpha signée, installée avec conservation de la connexion et des caches, puis compilation ART speed réussie. Build, douze tests JVM et lint (zéro erreur, quatorze avertissements) réussis.

Tests de lecture sur la Sony, via les dossiers natifs :
- KING365 → FR TV SD (FRANCE) → TF1 SD : première image signalée par Media3 en 2012 ms, prêt en 2037 ms ; capture ADB avec image vidéo visible, format AVC 1024 × 576. Pas de confirmation sonore humaine pour cet essai.
- PURE IPTV → FRANCE FHD → TF1 FHD : première image signalée en 1788 ms, prêt en 1825 ms ; AVC 1920 × 1080, audio MP4A-LATM, langue FR. La vidéo est noire dans la capture ADB : cette capture seule ne permet pas de confirmer ce que voit l'utilisateur. Pas d'erreur HTTP sur la Sony malgré un 401 depuis le PC sur l'adresse corrigée.

Captures locales privées : `sony-neo-iptv-king.png`, `sony-neo-iptv-pure.png`, `sony-neo-iptv-pure-info.png`. Aucun URL fournisseur ni identifiant sauvegardé dans cette documentation. Pas de modification, zap ou installation sur le Vu+.

## Correctif 0.5.1 — bouquets imbriqués
APK code 7 installée après vérification de signature, compilation ART Success. Neuf tests JVM et lint sans erreur bloquante. Parcours matériel vérifié par touches ADB : bleu → racine (156 dossiers) → PURE IPTV (50 sous-dossiers) → FRANCE FHD (278 entrées, liste NEO). Retour remonte à PURE IPTV avec FRANCE FHD sélectionné ; Retour suivant restaure PURE IPTV dans la racine. Réouverture du même chemin vérifiée. Aucun plantage observé ; aucun flux IPTV testé pendant ce contrôle de navigation.

Captures locales : `sony-neo-subfolders.png`, `sony-neo-subfolder-channels.png`, `sony-neo-subfolder-back.png`, `sony-neo-root-back.png`. Application laissée sur la liste FRANCE FHD.

TV IP confirmée par l'utilisateur : 192.168.11.188 (réseau LAN).
Vu+ Zero 4K OpenATV 8.0.1 : `192.168.11.2:82`, adresse et port confirmés par l'utilisateur le 31 octobre 2026. OpenWebif répond HTTP 401 sans authentification.

## App
- minSdk 26, Android TV leanback launcher, D-pad, 1080p UI, rendu adapté à la TV 4K.
- L'adresse de la TV est une cible d'installation et ne doit jamais remplacer l'adresse du Vu+ dans OpenWebif.
- L'APK ne contrôle aucun menu de la TV avant ADB autorisé.
- ADB TCP 5555 activé et autorisé par l'utilisateur pendant la session du 31 octobre 2026. Ne pas contourner une future révocation. Le débogage sans fil peut nécessiter une nouvelle association.
- Installation ADB seulement après validation de la signature de l'APK.
- Ne jamais installer ou modifier de plugins, skin ou configurations sur le Vu+.

## Statut
## Contrôles du 31 octobre 2026
- Appareil observé via ADB : fabricant Sony, modèle BRAVIA VU3, API 34 (Android 14).
- APK 0.3 puis 0.4 compilés localement ; signature APK v2 vérifiée avant installation `adb install -r` (Success).
- 0.4 démarrée à froid, activité visible et processus vivant. Aucun plantage applicatif observé dans AndroidRuntime.
- Captures réelles en 1920×1080 : structure liste/panneau de détails, menu principal NEO, écran Setup lisibles, sans débordement observé.
- Injection de touches ADB : MENU ouvre le menu, droite sélectionne Setup, OK ouvre la configuration avec le port 82. Ce contrôle ne certifie pas toutes les touches physiques de la télécommande Sony.
- Compilation, 3 tests JVM et lint Android réussis ; lint : 0 erreur, 13 avertissements non bloquants. CI mise à jour, exécution distante non déclenchée.
- Connexion authentifiée réussie. API : 156 entrées bouquets, 108 services bruts dans Top Italia (100 services jouables après filtrage des marqueurs) ; EPG réel disponible.
- Captures réelles : liste de 20 lignes, picons et EPG de Rai 1, page 21–40, sélection des bouquets, infobars Rai 1 puis Rai 2 après CH+. Les informations de programmes proviennent du récepteur.
- Rai 1 : l'utilisateur confirme « Image et son OK ». Le lecteur expose AVC / AC3 / 1920×1080 ; la capture ADB ne récupère pas l'image vidéo sur cette Sony. Aucune promesse HDR/Dolby ajoutée.
- La touche GUIDE est interceptée par le système et ouvre `com.android.tv`. INFO, reçu dans Neo, ouvre son écran EPG. La parité de toutes les touches physiques n'est pas certifiée.
- La mise en arrière-plan peut recréer le processus. La connexion chiffrée AndroidKeyStore a été ajoutée pour permettre la reconnexion sans nouvelle saisie.
- Reconnexion vérifiée après `am force-stop` et lancement à froid : 11 917 services uniques rechargés sans saisir de nouveau les identifiants. Présence d'un mot de passe chiffré vérifiée sans afficher sa valeur.
- EPG Rai 1 ouvert avec INFO et Retour vers la liste vérifiés. Saisie numérique 3 + OK sélectionne Rai 3 ; 0 rappelle Rai 1. La sélection suit le rappel de chaîne.
- État de livraison : application 0.4 au premier plan sur la Sony, Rai 1 en lecture. Compilation, 3 tests JVM et lint relancés et réussis après la dernière correction.
- Le Vu+ n'a reçu que des requêtes HTTP GET de consultation ; aucune installation ni modification système.

Les captures de travail sont locales dans `.tools/sony-neo-*.png`, hors suivi Git. Une lecture authentifiée de `config.skin.primary_skin` confirme `MetrixNEO/skin.xml` sur le Vu+. `/grab` a retourné un OSD sans menu exploitable ; aucune comparaison pixel à pixel au menu réellement actif n'est affirmée.

## Mise à jour 0.4.1 — zapping
Installation après vérification de signature, puis compilation ART du paquet en mode speed : Success. Lancement à froid de l'activité en 2818 ms. Cache d'adresses confirmé dans les journaux ; trois changements HD en 1803, 1494 et 2143 ms jusqu'à la première image. Tests de répétitions rapides et zap normal suivant réalisés ; aucun plantage observé. Six tests JVM et lint 0 erreur. Voir `ZAPPING_PERFORMANCE.md` pour la comparaison, le coût de démarrage vidéo à froid et les limites de mesure.

## Mise à jour 0.5 — satellites / météo / cache
- Lecture GET de la configuration NEO : Casablanca, latitude 33.59, longitude −7.61. Température, conditions et trois jours de prévision Open-Meteo visibles sur la Sony, avec date et horloge.
- 42 groupes satellites natifs retournés par OpenWebif, sans les dossiers « New ». Navigation verte/OK vérifiée ; Hotbird 13F/13G à 13°E ouvre 1359 services jouables. Picons et EPG réels affichés.
- Cache privé : 40 entrées picon constatées après visite des deux listes. Après arrêt et relancement de l'application, noms/tailles/dates de ces fichiers identiques : aucun remplacement de ces picons lors de la recharge observée. La capture `sony-neo-cache-loaded.png` montre les vingt logos de Top Italia réaffichés.
- Le journal NeoLists confirme `cached_list services=15308` avant la mise à jour réseau (11917 références uniques). Le cache conserve les appartenances multiples aux bouquets.
- APK 0.5 (code 6) signée, installée et compilée ART. Sept tests JVM passés, dont sélection satellite et exclusion des marqueurs ; lint sans erreur bloquante.
- Captures locales hors Git : `sony-neo-satellites.png`, `sony-neo-hotbird.png`, `sony-neo-weather-list.png`, `sony-neo-cache-loaded.png`.
- Vérification finale après réinstallation : liste locale 15308 entrées rechargée ; lecture de 2M MONDE HD depuis Hotbird, callback première image puis READY, format AVC 1920×1080. Capture `sony-neo-weather-player.png` : météo/horloge en haut et infobar en bas, textes arabes correctement affichés. Aucun plantage observé. État final : liste des satellites ouverte sur la Sony.

# Mini TV et transparence — 0.8.2

La liste dispose de deux présentations mémorisées, accessibles avec la touche jaune :

- **Mini TV**, par défaut : vidéo 16:9 de 640 × 360 dans le repère NEO 1920 × 1080, à droite, avec le nom de la chaîne en cours. Les détails EPG de la sélection restent sous la vidéo.
- **TV en fond** : vidéo plein écran, liste et panneau EPG translucides. Le fond général a une opacité de 48 %, la liste ajoute un panneau de 40 % et le panneau EPG une opacité de 78 % pour garder le texte lisible.

Les flèches parcourent les chaînes et changent leurs détails EPG ; la vidéo reste celle de la chaîne en cours. OK ouvre la sélection en plein écran. Jaune est aussi accessible par le bouton de pied de page. Un appui maintenu ne bascule qu'une fois. Le choix de présentation survit à la fermeture du processus et au retour dans l'application.

Un seul lecteur et une seule surface vidéo restent présents. La vue change de position et de taille lors de l'ouverture de la liste, de la bascule jaune et du retour plein écran. Parcourir les services et changer de présentation ne lance pas une seconde lecture. En l'absence de chaîne ouverte, le cadre indique « OK : lancer une chaîne » ; aucun flux de démonstration n'est utilisé.

Media3 conserve `SurfaceView`, notamment pour les capacités de sortie HDR. Son option `setEnableComposeSurfaceSyncWorkaround(true)` traite le problème de dimensionnement d'`AndroidView` sur Android 14 décrit dans la [documentation officielle des surfaces](https://developer.android.com/media/media3/ui/surface). La surface GStreamer utilise, à partir d'Android 14, un cycle lié à son attachement ; le pipeline natif conserve la fenêtre lorsque celle-ci ne change pas.

Le test `tools/test-tv-preview.py` vérifie les cadres réels via l'accessibilité et SurfaceFlinger, la progression des compteurs de décodage et de position dans chaque présentation, l'absence de nouvelle demande de flux lors des bascules, le retour plein écran et la mémorisation des deux choix. Il ne lit aucun pixel vidéo et n'utilise pas PixelCopy. Les captures ADB de cette Sony peuvent afficher le plan vidéo noir alors que le compositeur reçoit une vidéo et que les compteurs avancent : elles servent à vérifier les panneaux, sans certifier les pixels affichés par la dalle ni le son.

La stabilité 4K/HDR et les interruptions IPTV déjà documentées restent des limites distinctes. Aucun changement du Vu+.

## Vérification sur la Sony

APK 0.8.2-alpha/code 21 signée et installée avec conservation des données ; compilation ART speed réussie. 23 tests JVM réussis, zéro erreur de lint et dix-sept avertissements, dont la suggestion de style KTX pour la nouvelle préférence.

**70 contrôles TV réussis :**

- 13 contrôles Mini TV/transparence Media3, dont la taille réelle 640 × 360, le maintien de Rai 1 pendant la sélection de Rai 2, la bascule sans nouvelle demande de flux et la mémorisation des deux vues après fermeture du processus.
- 24 contrôles de navigation : vingt lignes, pagination, passage première/dernière chaîne, bouquets/satellites, appuis maintenus et cohérence du panneau EPG.
- 11 contrôles GStreamer : premier callback vidéo réel, surface Mini TV puis plein écran, états PAUSED/PLAYING réellement confirmés dans les deux vues, absence de retune/erreur lors des bascules, puis restauration de Media3 et nouveau décodage.
- 22 contrôles de sortie : simple/double Retour, délai, autres touches, appui maintenu, sortie depuis Setup et lecture, pause et suppression de la tâche.

Pendant le contrôle Media3, la position passe de 17 512 à 27 508 ms et le compteur d'images rendues de 393 à 642 dans la Mini TV. Dans la liste transparente, la position passe de 37 508 à 47 516 ms et le compteur de 892 à 1 143. Aucun saut de séquence de lecture pendant la navigation ou les bascules. Ces compteurs confirment la progression du décodeur, sans certifier la fluidité physique de la dalle.

Rapports dans `reports/` : `sony-preview-2026-11-02.json`, `sony-preview-navigation-2026-11-02.json`, `sony-gst-preview-2026-11-02.json` et `sony-preview-exit-2026-11-02.json`. Captures de disposition : `sony-mini-tv-2026-11-02.png` et `sony-transparent-list-2026-11-02.png`.

APK : 29 905 554 octets, SHA256 `e4c0588a3ad9b43181d199f305424c93a038cb29baed790bb82d1c8bfeb62131`. Les tests portent sur l'installation locale, sans exécution CI distante revendiquée.

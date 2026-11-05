# Compatibilité 4K HDR — Sony BRAVIA VU3

L'essai 0.6.2 a comparé les files MediaCodec synchrones sur Sony / carte `BRAVIA_VU3_4K` / Android 14. L'utilisateur confirme encore des gels d'image avec son continu. Ce forçage est retiré dans 0.6.3 ; Media3 reprend son mode par défaut. Résolution, données HDR, flux et profil de tampon conservés. Tunneling reste désactivé.

La comparaison utilise les API officielles [de personnalisation Media3](https://developer.android.com/media/media3/exoplayer/customization) et [DefaultRenderersFactory](https://developer.android.com/reference/androidx/media3/exoplayer/DefaultRenderersFactory). Le résultat ne justifie pas de conserver un profil présenté comme correctif.

Contrôles effectués avant cet essai :

- Le SoC réel annonce RTD2873A / Realtek ; `OMX.realtek.video.decoder` est matériel, avec HEVC Main 10/HDR10 et PerformancePoint 3840 × 2160 à 60 images/s. Les décodeurs logiciels exposés ne permettent pas la 4K.
- Le même extrait TNT enregistré dans la mémoire de la TV présente encore des gels selon l'utilisateur, dans JustPlayer en TS puis en MP4 sans réencodage, ainsi que dans le lecteur système `com.android.gallery3d/.app.MovieActivity` en MP4. Internet n'intervient pas pendant ces lectures.
- Analyse logicielle du fichier : 1643 images HEVC Main 10 / 3840 × 2160 / 50 images/s ; aucun intervalle d'horodatage supérieur à 100 ms ni répétition exacte de luminance durant au moins 500 ms. Ce résultat oriente le diagnostic vers le décodage/affichage de ce flux sur la TV sans prouver à lui seul une panne du firmware.
- JustPlayer en tunneling a provoqué trois plantages dans `libstagefright.so` du système Sony, avec `ubsan: sub-overflow`. Ce mode a été désactivé.
- Le lecteur privé Sony/Realtek utilise `rtk-mediaplayer`. Un essai de `RtkMediaPlayerWrap` dans Neo échoue avant lecture : InvocationTargetException → ExceptionInInitializerError → SecurityException → RemoteException. Aucun privilège système n'a été ajouté pour contourner ce refus.
- Le repli public Android MediaPlayer sur le flux TS a préparé une piste audio, aucune dimension vidéo, puis terminé vers 25 s sans première image. Ce lecteur expérimental a donc été retiré de l'interface et de l'APK finale, avec toute dépendance à la bibliothèque propriétaire.
- Android n'expose qu'un mode d'affichage 2160p60 sur cette TV, HDR10/HLG. Les modes HDMI 50 Hz de la fiche Sony ne prouvent pas qu'une application peut commuter sa surface à 50 Hz. Aucun mode système forcé.

Sony indique HDR10/HLG et HEVC dans les [caractéristiques X75K](https://www.sony-mea.com/en/electronics/televisions/x75k-series/specifications). L'incrément de firmware relevé est `386-60842` ; le support Sony publie [v60842000 pour ce modèle](https://www.sony-mea.com/en/electronics/support/lcd-tvs-android-x74k_x75k-series/kd-43x75k/downloads). Cela correspond à la même série de version, sans certifier la comparaison de chaque variante régionale. Aucun firmware téléchargé ni installé.

La sonde de développement 0.6.3 / code 12 a essayé [PixelCopy](https://developer.android.com/reference/android/view/PixelCopy) sur notre propre SurfaceView pour observer les pixels. La première tentative a déclenché un SIGSEGV dans `/vendor/lib/egl/libGLES.so` / `stream_unpack` du firmware Sony, à 22:34:01, processus Neo 1493 / RenderThread. C'est un plantage induit par ce test, distinct des gels signalés avant l'essai. Le code 13 retire complètement la sonde, sans nouvelle tentative ni accès privilégié au GPU. Cette erreur ne prouve pas à elle seule la cause des gels de lecture.

Le contrôle autonome sûr est externe : `tools/check-sony-playback.py`. Il lit la présentation SurfaceFlinger et les journaux structurés de Neo, relève les interruptions mesurables et vérifie la présence du processus. Il n'effectue aucune capture de pixels, aucune commande du Vu+ et aucune écriture sur la TV. Les mesures peuvent ne pas exposer un gel situé après leur point de collecte : `visible_motion_verified` reste explicitement faux.

Exemple, une chaîne déjà ouverte dans Neo :

```powershell
python tools/check-sony-playback.py --adb C:/outils/adb.exe --serial 192.168.11.188:5555 --seconds 90 --output reports/sony-current.json
```

Code de sortie 0 : aucune interruption détectée dans les mesures disponibles, sans certification visuelle ; 2 : interruption/erreur relevée ; 3 : observations insuffisantes. Le rapport ne contient ni URL de flux ni identifiant fournisseur. Une interruption de collecte ADB peut également créer un trou d'observation ; elle n'est pas assimilée à une preuve de gel de la dalle.

Résultats et limites dans [Sony_KD-43X75K.md](Sony_KD-43X75K.md). Les journaux de diagnostic applicatifs ne contiennent pas d'URI ; les fichiers de test restent dans les dossiers locaux ignorés.

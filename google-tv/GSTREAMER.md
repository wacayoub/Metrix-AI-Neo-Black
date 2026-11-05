# Lecteur GStreamer Android

L'APK 0.6.1-alpha (code 10) intègre GStreamer 1.28.8 en plus de Media3. Setup → Lecteur vidéo → GStreamer sélectionne le moteur et mémorise le choix. Un changement de moteur relance la chaîne courante ; les menus et la télécommande restent natifs à l'application. Media3 reste disponible dans Setup, avec un profil de tampon adapté aux formats 4K/HDR depuis la version 0.6.1.

## Correction 0.7.0

Le parcours autonome a révélé un démarrage bloqué dans l'ancien `playbin` : pipeline READY, transition PLAYING en attente, malgré un événement de tampon plein. Cet événement ne doit pas être traité comme une preuve de lecture. Le passage à `playbin3` permet sur la Sony d'atteindre réellement PLAYING, de recevoir une image 1920 × 1080 de TF1 FHD, puis de confirmer les états PAUSED et PLAYING lors des commandes de pause/reprise.

Le bus est lu par lots bornés ; les dimensions viennent des caps du callback GL et les pistes des messages `STREAM_COLLECTION`, sans requête de pad susceptible de bloquer le thread de contrôle. Les sources GLib sont traitées sans attente bloquante. Les transitions de tampon ne forcent plus une mise en pause pendant le démarrage live. Les événements « prêt » et « pause » proviennent de l'état effectif du pipeline. Aucune lecture des pixels ni sonde du pilote Sony n'est ajoutée.

La sélection des pistes utilise les identifiants de la collection avec `SELECT_STREAMS`, l'API de [playbin3](https://gstreamer.freedesktop.org/documentation/playback/playbin3.html). Les propriétés `current-audio/current-text` de playbin2 ne sont plus utilisées. Les noms des langues et les métadonnées HDR restent indisponibles dans l'infobar GStreamer. Cette correction de démarrage et de commande ne constitue pas une correction validée des gels 4K/HDR.

Le contrôle prolongé de TF1 FHD PURE échoue encore après le démarrage : erreur `gst-stream-error-quark / 7`, soit `GST_STREAM_ERROR_DECODE`, reproduite vers 23 s. Media3 termine également ce flux après 20–26 s. Le domaine et le code sont journalisés sans message brut ni URI ; ils ne suffisent pas à établir la cause racine. Les tests courts de pause, reprise, sélection audio et zapping passent, mais la stabilité de ce flux n'est pas validée. Rapport : `reports/sony-iptv-duration-2026-10-31.json`.

## Intégration

- SDK Android officiel, JNI C avec `playbin3`, `glimagesink` sur SurfaceView et audio OpenSL ES. Plugins Android MediaCodec et libav inclus ; leur inclusion ne certifie pas chaque codec ni l'accélération matérielle de chaque flux.
- Un thread de contrôle sérialise les opérations JNI et le bus GStreamer, sans arrêt de pipeline sur le thread UI. Les demandes de zap périmées sont écartées. Les callbacks sont ramenés au thread principal et associés au numéro de la demande active.
- Adresses issues des références Enigma2 ou du M3U OpenWebif. Identifiants du récepteur transmis uniquement pour son hôte/port autorisé ; redirections automatiques désactivées pour une source authentifiée. Sources externes sans ces identifiants. TLS avec OpenSSL et certificats du SDK, sans désactivation de la validation.
- Lecture/pause et liste de pistes reliées au même parcours télécommande. Les pistes GStreamer sont numérotées ; le nom des langues/codecs, les métadonnées HDR et la fréquence d'image ne sont pas encore remontés dans l'infobar de ce moteur. Les valeurs inconnues restent neutralisées.
- Sur l'ancienne version, l'utilisateur avait confirmé image et son de TF1 FHD PURE mais le compteur de pistes restait indisponible. Le contrôle 0.7.0 reçoit une piste audio et les dimensions 1920 × 1080 ; la validation automatique des états ne certifie pas l'animation finale de la dalle ni le son.
- Pause à la sortie de l'activité ; libération du moteur à sa destruction. Les chaînes audio seules ne produisent pas de callback de frame vidéo.
- Aucun texte d'erreur brut GStreamer, URI ou jeton fournisseur dans les journaux applicatifs. Les erreurs du lecteur sont présentées sans adresse.

## Reproduire la compilation

JDK 17, Gradle 8.13, SDK Android 36 / build-tools 36.0.0, NDK r25c (`25.2.9519653`) et Python 3.12+.

Depuis `google-tv/`, préparer le SDK dans un dossier local hors des sources :

```powershell
python tools/prepare-gstreamer.py C:/chemin/outils/gstreamer
$env:GSTREAMER_ROOT_ANDROID = 'C:/chemin/outils/gstreamer'
gradle --no-daemon :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
```

Le script télécharge le [SDK officiel Android 1.28.8](https://gstreamer.freedesktop.org/data/pkg/android/1.28.8/), vérifie son SHA256 avant extraction et copie les cibles des liens pour fonctionner aussi sur Windows sans droits administrateur. Archive d'environ 1 Go ; prévoir l'espace pour l'archive, le SDK extrait et le NDK. Empreinte épinglée :

```text
f19c6f971a956675402452fce0fe772d66dbd0d28d70999618355813ea593a99
```

L'ABI construite par défaut est `armeabi-v7a`, correspondant à la Sony de cette session (`armeabi-v7a,armeabi`). Le chemin arm64 existe dans Android.mk mais aucun résultat matériel arm64 n'est revendiqué. Le helper, la configuration CI et la préparation Java/assets ciblent actuellement ARMv7. L'APK a donc vocation à l'installation directe sur cette Sony ; aucune publication Play Store n'a été effectuée.

Le build génère la classe d'initialisation officielle, le support AndroidMedia, les polices et le magasin de certificats avant la compilation Kotlin/assets. Le moteur partagé est compilé avec les archives statiques du SDK et empaqueté avec son runtime C++. Aucun binaire du SDK n'est ajouté aux sources Git.

## Sources et notices tierces

Les notices du SDK sont incluses dans `assets/gstreamer/licenses/` à la compilation. Le fichier `GSTREAMER_NOTICE.txt` dans les assets identifie la distribution et les sources. Sources du moteur et des plugins : [GStreamer](https://gstreamer.freedesktop.org/src/) ; recettes et versions des dépendances : [Cerbero](https://gitlab.freedesktop.org/gstreamer/cerbero/-/tree/1.28.8). Pour reconstruire avec un SDK adapté, conserver la structure `armv7/`, définir `GSTREAMER_ROOT_ANDROID` sur ce SDK et relancer Gradle. Le JNI applicatif et la liste des plugins sont dans `app/src/main/jni/`.

Les vérifications sur la Sony sont consignées dans [Sony_KD-43X75K.md](Sony_KD-43X75K.md). Le succès des tests JVM OpenWebif ne constitue pas un test des codecs natifs.

Un échantillon 4K a ensuite été testé : quatre flux HEVC 3840 × 2160 vérifiés sur Sony, dont TRT 4K avec image visible dans la capture. Un flux Love Nature STRONG8K intitulé 4K arrive en FHD avec Media3 et échoue avec GStreamer ; cet écart reste à diagnostiquer. Voir le tableau matériel pour les durées d'observation et les limites de confirmation du son/de la fluidité.

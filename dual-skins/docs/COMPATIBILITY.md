# Compatibilité : preuves et portée

État : **CANDIDAT HORS APPAREIL**, pas une version certifiée OpenATV 8.0.1.

## Source technique

Sources publiques consultées et clonées en lecture seule dans `.upstream/`,
exclu de Git et de l’archive. SHA exacts dans `sources.lock.json`.

- MetrixHD : conventions des écrans, infobar, EPG, templates et avis de licence.
- Enigma2 `8.0` : `Screens/Menu.py`, `Screens/ChannelSelection.py`,
  `Screens/EpgSelection.py`, `Screens/EventView.py`, `Screens/AudioSelection.py`,
  `Screens/Setup.py`, `Screens/SkinSelection.py`, `Screens/SessionGlobals.py`.
- Composants : ServiceList/ServiceListLegacy, Source.List, FrontendStatus,
  Picon, ChoiceList, EventInfo, ePicLoad et points d’extension skin applet.
- Documentation : https://openatv.github.io/enigma2-doku/en/developers/skinning/api/xml/

Le nom commercial `8.0.1` ne permet pas de connaître les API effectivement présentes.
La branche `8.0` examinée contient des évolutions récentes. Aucun widget moderne
ne doit être présenté comme prouvé sur le build personnel sans audit matériel.

## Points établis hors appareil

- Deux répertoires distincts avec `skin.xml` et `prev.png`, convention observée
  dans SkinSelection. La découverte sur Vu+ n’a pas été exécutée.
- Styles FHD et géométrie statique dans 1920 × 1080.
- Applets `onLayoutFinish` présentes dans le moteur skin étudié ; elles lient
  uniquement l’instance de Menu/ChannelSelection, sans monkeypatch global.
- Aucun import obligatoire du helper dans les fichiers XML.
- Mesures SNR/AGC depuis FrontendStatus brut. Le sentinel 65536 est inconnu.
  Aucune AGC estimée à partir du SNR.
- Picon rendu selon son ratio natif ; résolution existante de Picon réutilisée.
- Panneau de chaînes réorganisé sans image ; picon réancré et synopsis agrandi
  sans déplacement des prochains événements. Géométrie commune au simulateur.
- Polices et états EPG définis avec les attributs exacts EPGList.applySkin ;
  23 ressources graphiques natives propres à chaque skin pour le mode graphique.
- Données vidéo depuis iServiceInformation, sans utilisation de la résolution
  de sortie HDMI comme qualité supposée de l’émission.

## Points à vérifier sur cible

1. Version Python, image/build exact, disponibilité des modèles XML Menu et ServiceList.
2. Le mode ServiceListLegacy dépend des préférences existantes : il ne garantit
   pas les 20 lignes demandées ni la suppression de tous les badges. Aucune préférence
   globale de liste n’est modifiée pour le forcer.
3. Compatibilité de la forme Menu.setMenuList et indexNames, navigation en grille.
4. Couverture réelle FR/EN/AR, shaping/RTL, troncatures, polices système présentes.
5. Conventions de scale, fonts et géométrie interne des listes de plugins,
   claviers, timers et ChoiceList : les coordonnées statiques seules ne les prouvent pas.
6. Références IPTV de lecteurs tiers, exactitude des métadonnées codecs/HDR/FPS.
7. Affichage REC/timeshift, réactions au zapping et absence de ressources retenues.
8. Dépendances opkg réellement disponibles dans le feed et paquetage accepté.
9. Interaction avec plugins additionnels et configurations de menu triées/masquées.

Python local : 3.13.2, Pillow 13.0.0. Les tests n’importent pas les bindings C++
Enigma2. Un faux environnement de Menu couvre les callbacks, pas le dessin natif.
Pillow local est sans RAQM : aucune validation visuelle du shaping arabe.

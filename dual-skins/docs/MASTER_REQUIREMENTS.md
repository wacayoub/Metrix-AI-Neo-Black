# PROMPT MAÎTRE POUR CODEX — METRIX NEO + METRIX NEO ADVANCED

## Mission et mode opératoire

Tu es Codex, ingénieur senior Enigma2/OpenATV, concepteur de skins FHD 1920×1080, développeur Python 3 et mainteneur de paquets .ipk. Réalise un seul projet cohérent comportant **DEUX SKINS COMPLETS, DISTINCTS, SÉLECTIONNABLES SÉPARÉMENT** dans le sélecteur OpenATV :

1. **Metrix NEO** — style MetrixHD, minimaliste et moderne.
2. **Metrix NEO Advanced** — version premium/intelligente, mais toujours sobre et fluide.

**Matériel cible** : Vu+ Zero 4K, image OpenATV 8.0.1, Python 3 (la version exacte doit être vérifiée sur la machine plutôt que supposée), OSD natif FHD 1920×1080. Fuseau horaire Africa/Casablanca. C'est un travail de développement avec GitHub, pas une demande d'installation immédiate.

**CONTRAINTE BLOQUANTE** : état `NO_INSTALL / NO_RECEIVER_WRITE`. Tu peux créer un dépôt, développer et tester hors du récepteur, analyser en lecture seule les fichiers du Vu+ SI le connecteur SSH est déjà disponible et autorisé. **Ne modifie, n'installe, n'active, ne redémarre rien sur le Vu+ sans autorisation explicite ultérieure de l'utilisateur.** N'écris ni dans `/etc/enigma2`, ni dans `/usr/share/enigma2`, ni dans `/usr/lib/enigma2/python/Plugins` sur le récepteur. Ne modifie pas les listes de chaînes, bouquets, mappings, EPG, favoris, paramètres d'EPGManager ou d'IPToSatPro. Ne redemande pas des informations déjà fournies et ne promet pas un accès SSH si celui-ci n'existe pas. N'inclus aucun mot de passe dans le dépôt ou dans les logs.

Lis **tous les documents et images** du ZIP `METRIX_NEO_CODEX_MASTER_PACK.zip`, particulièrement `references/APPROUVEES/`, et applique l'ordre de priorité défini par `README_REFERENCES.md`. Les photos sont des **références graphiques**, pas des fonds destinés à être embarqués au runtime. Les captures approuvées prévalent sur toute ancienne exploration contradictoire.

## 1. Sources et compatibilité

- Référence technique upstream : https://github.com/openatv/MetrixHD
- OpenATV Enigma2 : https://github.com/openatv/enigma2
- Documentation skin XML : https://openatv.github.io/enigma2-doku/en/developers/skinning/api/xml/
- Documentation Enigma2 skins : https://github.com/openatv/enigma2/blob/master/doc/SKINS
- Examine la branche et les fichiers réellement installés sur OpenATV 8.0.1 avant de fixer les noms de screen, renderer, converter, composant Listbox/ServiceList et sources. Ne copie pas des noms périmés. Vérifie la licence de MetrixHD et des ressources avant réutilisation ; préserve les avis de licence/attribution obligatoires. N'embarque pas d'images, posters, logos ou typographies sans droits adéquats.
- Un fichier XML de skin ne crée pas une nouvelle logique applicative. Pour les données Smart EPG, posters, logos de clubs et diagnostics, utilise un **plugin d'accompagnement facultatif** et les points d'extension réellement supportés, avec repli élégant si indisponible.
- Dans OpenATV, des dossiers distincts de skins avec un `skin.xml` correct doivent être reconnus séparément. Proposer des identités indépendantes telles que `MetrixNEO/skin.xml` et `MetrixNEOAdvanced/skin.xml`, tout en conservant `MetrixHD` d'origine. Vérifier la découverte réelle sur OpenATV cible.
- Deux thèmes seulement : ne confonds jamais deux « infobars sélectionnables dans un seul skin » avec les DEUX skins complets demandés.

## 2. Design system — impératif

Inspiration exacte : capture **EPGManager** du pack. Style **plat, sobre, sombre et technique**, PAS de Windows, PAS de néon exagéré, PAS de grandes cartes multicolores. Palette de départ à calibrer visuellement contre la vraie capture :
- Fond OSD `#090F17` / noir bleu nuit ; fond des cartes `#162231` ; panneau secondaire `#1B2A3A` ; sélection bleu ardoise/turquoise mat `#254C5C` ; accent cyan discret `#29A9BE` ; texte `#E7EBF0` ; secondaires `#98A8B8`.
- Jaune uniquement pour avertissement ou qualité vidéo pertinente, rouge **REC actif / erreur**, vert **état sain**. Les touches rouge/vert/jaune/bleu restent conformes à Enigma2.
- Trait de séparation très fin (1–2 px), aucune ombre ou glow intensif, pas de fond photographique imposé à tous les écrans. Angles peu arrondis. Petites icônes duotone/blanches uniformes.
- Interface FHD 1920×1080, textes lisibles à 2–3 mètres, prise en charge des titres FR/EN/AR (UTF-8, RTL si nécessaire, troncature intelligente). Ne remplace jamais des caractères arabes par des symboles, et ne change pas la langue d'une émission.
- **Widget météo en haut à gauche**, 3 jours, icônes **« Classique moderne » approuvées** ; **horloge/date en haut à droite**. Météo non bloquante, cache, mode hors ligne ; aucune prévision fictive affichée comme réelle.
- Picons ZZZPicon/XPICON conservés avec leur ratio réel : jamais étirer, remplacer, ni redimensionner le fichier source ; adapter uniquement le cadre de rendu.
- Performance prioritaire sur Vu+ Zero 4K : pas d'animations lourdes, décodages d'images en arrière-plan, pas d'appels réseau pendant le zapping ou les déplacements de sélection. Les cibles de performance seront mesurées sur appareil et les widgets coûteux pourront être désactivés.

## 3. Définition du SKIN « Metrix NEO » — classique moderne

**Visuel de menu approuvé** `01_MENU_NEO_5_TUILES.png` : 5 tuiles structurées comme la photo de l'utilisateur : Plugin Browser, Setup, Timers, Standby/Restart, Information ; météo+horloge en haut ; touches de couleur en bas. Reproduire l'organisation et non une grille différente. Chaque tuile déclenche la fonction native réellement disponible ; pas d'entrée cassée ni doublon artificiel.

**Visuel Channel List approuvé** `03_CHANNEL_NEO_DENSE.png` : liste dense d'environ 20 chaînes visibles avec petite marge sur les 4 côtés, picon d'origine, **titre EPG sur la même ligne que le nom de la chaîne**, barre de progression courte, **aucun horaire EPG et aucun badge HD/SD dans les lignes**. Le panneau droit affiche une image fixe du programme si vérifiée, titre, synopsis et **deux programmes suivants** si l'EPG fournit les données. **Jamais de mini-TV / PiG**. Mode sans image confortable : le picon, le titre et le synopsis occupent l'espace sans trou. La photographie ne s'affiche pas en fond de toute la liste.

**Infobar approuvée** : bas de l'écran, **marge inférieure = 0 pixel**, taille proche de MetrixHD, 2 lignes d'informations compactes, météo et heure en haut, picon au ratio correct, émission actuelle/suivante, barres de progression, REC/timeshift, SAT ou IPTV, qualité image/son réelle. Les barres SNR et AGC suivent l'orientation précédemment validée : remplir de droite vers gauche, avec le pourcentage lisible. Pour IPTV, masquer SNR/AGC non pertinents au lieu d'afficher 0 % inventé. Aucune affiche du programme dans l'infobar.

**Guide EPG** : grille chronologique proche de la capture MetrixHD d'origine avec chaînes/picons et échelle horaire, sélection bleu ardoise, description dans la zone haute ou panneau secondaire, raccourcis programmations/timer/EPG respectés. Les horaires restent visibles dans la **grille EPG** ; la suppression des horaires vise uniquement les **lignes de Channel List**.

**Menu contextuel** : grande icône monochrome à gauche, liste verticale native à droite, sélection mate, même logique que le Metrix actuel. Ne masque aucune opération existante.

**Paramètres** : liste simple des options par catégories, réglages usuels en lecture/écriture uniquement si l'utilisateur les valide dans l'interface ; prévisualisation non destructive et bouton retour/annuler.

## 4. Définition du SKIN « Metrix NEO Advanced » — premium maîtrisé

**Visuel menu approuvé** `02_MENU_ADVANCED_12_TUILES.png` : panneau à gauche avec grande photographie de salon/TV du concept validé (remplaçable par image décorative libre/licenciée, sans dépendance réseau), **12 tuiles à droite en 4 lignes × 3 colonnes** ; exactement le type d'organisation de l'image jointe. Rubriques : Plugin Browser, Setup, Éditeur de chaînes, Timers, Gestionnaire de fichiers, Enregistrements, Gestionnaire de logiciels, Réseau, Standby/Redémarrer, Information, Thème & Skin, Outils. Les noms doivent correspondre aux fonctions présentes réellement ; si un plugin de fichiers manque, griser/masquer plutôt que simuler son existence.

**Channel List** `04_CHANNEL_ADVANCED_AEREE.png` : disposition plus aérée (~13 lignes visibles), même principe « numéro | picon | chaîne + programme adjacent | barre EPG », aucun horaire dans les lignes, pas de badge HD/SD dans les lignes, marges suffisantes, panneau droit avec image du programme, synopsis, **2 programmes suivants**, catégorie fiable, métadonnées et logos sportifs uniquement si identification confirmée. **Toujours pas de mini-TV**. `05_CHANNEL_COMPACT_OPTION.png` peut servir de disposition compacte alternative dans les paramètres Advanced, sans créer de troisième skin.

**Infobar Advanced** : se référer à `06_INFOBAR_AI_APPROUVEE.png` (et aux infobars d'exploration marquées pour indication). Conserver météo Classique moderne, heure, picon compact, EPG actuel/suivant, REC et timeshift conditionnels, logos de clubs pour un événement identifié avec confiance, icônes métiers discrètes pour autres genres (film, série, documentaire, actualités, enfant, musique). Qualité réelle : SD/HD/FHD/4K, HDR/HLG si détecté, HEVC/H.264, FPS, audio AAC/AC3/DD+/DTS suivant piste disponible, langue, DVB-S/T/IPTV, signal applicable. Pas d'icône Wi‑Fi trompeuse pour « Smart Match ». Indicateur IA facultatif et discret, absent quand aucune donnée enrichie.

**EPG Advanced** : vue détaillée avec bandeau d'émission, image fixe si disponible, synopsis, dates, série SxxExx si confirmée, + deux prochains événements avec heures valides. Offrir un guide timeline utilisable pour naviguer entre les chaînes et les périodes, sans sacrifier la lisibilité. Toutes les opérations EPG natives (navigation, programmation, timer, auto timer si plugin présent) doivent rester accessibles.

**Menu contextuel Advanced** : aperçu d'informations de la chaîne/programme à gauche (image fixe si disponible), vraie liste d'actions native à droite, petites icônes et description contextuelle. Ne pas supprimer les outils de bouquets, recherche, rename/move, audio/subtitles, service info, etc. ; respecter les permissions et les commandes existantes.

**Settings Advanced** : navigation par catégories à gauche, détails des options à droite avec prévisualisation, météo, polices, couleurs, transparence, présentation de l'EPG, affichages par écran, caches, modules intelligents, performance, restauration de valeurs de skin uniquement. Aucune prévisualisation ne doit écrire de configuration système ou redémarrer.

## 5. Fonctions communes validées : activer les cinq

A) **Météo Classique moderne** : icônes soleil, nuages, ciel dégagé nuit, pluie, orage, neige, brouillard, vent ; 3 jours ; fond sombre ; option masquer ; cache local et timeout ; service météo libre/autorisable.

B) **Images des programmes** : mini-module optionnel de récupération de métadonnées et images de films/séries/documentaires/émissions via sources à API/licences conformes. Priorité aux métadonnées déjà disponibles localement dans EPG/Enigma2, puis fournisseur autorisé configuré ; ne pas scraper abusivement ; recherche hors du chemin de navigation ; cache limité et configurable, TTL/éviction ; pas d'image trouvée = panneau texte/picon, pas d'image inventée. Les maquettes avec personnages ou logos commerciaux sont des **illustrations**, pas des images à fournir légalement dans l'application.

C) **Smart EPG Advanced** : extraction sûre et configurable des genres, saisons/épisodes, équipes sportives depuis titre/descriptions EPGManager en lecture seule ou EPG natif ; désambiguïsation AR/FR/EN ; événements prochains x2 ; logos sportifs seulement si droits et correspondance fiables ; indicateur de confiance/aucune donnée plutôt qu'une déduction inventée. Aucune IA distante obligatoire, fonctionne en mode local ; les appels IA réels nécessitent clé utilisateur et consentement.

D) **Diagnostics intelligents** : indicateurs contextuels de source, signal, codec, audio absent, EPG manquant, enregistrement/timeshift ; texte court et exact ; ne pas polluer la vidéo par des notifications permanentes ; aucune connexion/contrôle IPToSatPro sans API publique. Lecture seule des états utiles.

E) **Prévisualisation des réglages** : modifier temporairement les styles dans un écran prévisualisation, annuler sans effet de bord, confirmer pour sauvegarder uniquement la configuration NEO ; sauvegardes lisibles et restauration sans supprimer les paramètres tiers.

## 6. Priorités fonctionnelles et vrais états Enigma2

- Picons : ZZZPicon et XPICON, gestion service reference, chemins existants; ratio conservé. En cas d'absence, placeholder sobre.
- EPG : lire l'EPG Enigma2 qui peut être alimenté par EPGManager ; **ne pas toucher** à l'EPGManager, ses sources, mappings, déclenchements ou cache. Titre et description dans leur langue d'origine ; RTL arabe fiable.
- REC : rouge seulement si enregistrement effectivement actif, indicateur temps/titre seulement si réel.
- Timeshift : icône et décalage seulement si actif ; ne pas afficher arbitrairement « +116 min » ni reculer de 30 s si ces commandes ne sont pas opérationnelles.
- Réception SAT/TNT : SNR, AGC, BER si fournies ; barre orientée comme la validation visuelle (de droite vers la gauche), mais valeurs exactes/invalides distinguées. Réception IPTV : pas de fausse valeur SNR/AGC, afficher type de flux/lecteur lorsqu'il est exposé.
- Audio : afficher le codec de la piste sélectionnée et sa langue ; ne pas afficher Dolby Atmos/DD+ parce que la vidéo est 4K. Afficher HDR uniquement avec preuve de signalisation réelle ; fallback sobre.
- Logos de clubs : facultatifs, cache local, pas de logo pour un match ambigu ; pour films/séries/info pas de logos de clubs, icône monochrome au besoin.
- Fonctionnalités natives OpenATV : timers, autotimer si présent, sous-titres, pistes audio, clavier, notifications, demandes de confirmation, volume et mute, recording, recherche bouquets/services, contexte et paramètres préservés.
- Les deux skins doivent respecter les mêmes règles de style pour les fenêtres secondaires, avec **NEO simple et Advanced plus explicatif**, surtout pour réseaux/audio vidéo/extensibilité.

## 7. Architecture logicielle attendue

Proposer une arborescence claire du type :
```
metrix-neo/
  skins/MetrixNEO/skin.xml
  skins/MetrixNEOAdvanced/skin.xml
  skins/shared-assets/           # icônes et modules réutilisables sourcés/licenciés
  plugin/MetrixNEOHelper/        # OPTIONNEL : posters, cache, météo, smart EPG, diagnostics
  docs/SCREEN_MATRIX.md
  docs/DESIGN_TOKENS.md
  docs/IMAGE_LICENSES.md
  docs/COMPATIBILITY.md
  docs/RECEIVER_READONLY_AUDIT.md
  tools/                       # compilation, vérification XML et tests hors appareil
  packaging/                   # .ipk séparés par skin, helper indépendant si utile
  tests/
  README.md
```
Le nom des modules, composants et skinparts doit être ajusté aux véritables contraintes de la version cible. Évite la duplication : partager le code/configuration, mais garder **deux identités de skins indépendantes** et deux réglages propres. Packager deux paquets installables indépendamment, avec `skin.xml`, icônes, prévisualisation du sélecteur, version, changelog et licences ; helper en dépendance optionnelle ou offre un repli sûr.

## 8. Déroulement demandé (minimiser temps et crédits)

1. Lire ce cahier des charges et les photos. Remplir une matrice : écran OpenATV existant, skin cible, sources supportées, widgets natifs et fallback.
2. Faire **un seul audit ciblé** des répertoires/runtimes si un accès SSH déjà approuvé est disponible ; lecture seule uniquement, pas de scan intrusif ni de mise à jour automatique ; ne pas exposer secrets ou URL IPTV dans les comptes rendus.
3. Créer le dépôt GitHub ou l'arborescence locale de travail autorisée ; vérifier licences et ressources, puis intégrer le design XML des écrans les plus importants.
4. Implémenter les **deux skins et toutes leurs fenêtres listées** en un cycle de développement concentré ; créer les helpers facultatifs après vérification des APIs réellement présentes.
5. Vérifier syntaxe XML, existence des pixmaps, layout FHD, règles de fallback, arabisations/RTL, no fake metrics, pas de régression, absence de chemins absolus, génération de prévisualisations statiques et paquetage `.ipk` local.
6. Produire deux captures/simulations par écran important, une par skin, lorsque possible et les comparer au pack approuvé. Les simulations ne prouvent pas la compatibilité sur matériel.
7. Me rendre un rapport bref : fonctionnalités réellement développées, différences NEO vs Advanced, limites, tests réussis/échoués, contenu et chemins des paquets et statut `NOT_INSTALLED`.

**N'effectue aucune installation à l'étape 7.** Le test réel sur Vu+ (OSD, zapping, fluidité, signal, audio, EPG, sauvegarde/activation et éventuel redémarrage d'Enigma2) fera l'objet d'une autorisation distincte, après revue des artefacts. Préparer un plan sûr de sauvegarde/test et un retour au skin original, sans exécuter ces actions maintenant. Ne dis jamais qu'une fonction est « 100 % validée » sans test hardware.

## 9. Critères d'acceptation

- Deux skins identifiables indépendamment dans le sélecteur de skins OpenATV, sous réserve du test final sur boîtier.
- `MetrixHD` officiel préservé et aucun impact sur bouquets, Enigma2 config, IPToSatPro, EPGManager.
- Chaque skin couvre Menu, Infobar, SecondInfoBar, ChannelSelection, EventView, EPGSelection/grille, menu contextuel, Settings, audio/subtitles, REC/timeshift et dialogues/fenêtres de base ; ne laisse pas de texte coupé ou d'icône géante.
- NEO : menu cinq tuiles / Channel List dense ~20 / grille EPG classique / menu contextuel simple.
- Advanced : menu panneau gauche + 12 tuiles / Channel List aérée ~13 avec image + EPG x2 / EPG enrichi / contextuel enrichi / Settings avec aperçu.
- Les deux : weather 3j classique moderne, horloge, couleur EPGManager sans excès, picons XPICON/ZZZPicon ratio conservé, info vidéo/audio réelle, REC/timeshift conditionnel, signal dans orientation choisie, texte FR/AR/EN.
- Deux programmes suivants lorsqu'ils existent, sans inventer d'horaires. Aucune mini-TV dans ChannelList.
- Pas d'accélération ou d'IA mensongères, pas de métriques simulées, pas d'appel réseau bloquant, pas d'obligation de service payant.
- Les prévisualisations de Settings doivent être annulables ; suppression/absence du helper ne casse pas les écrans natifs.
- Test statique et build .ipk réussis hors appareil ; tests matériels signalés comme **non effectués** tant que pas autorisés.

## 10. Références visuelles — ordre de priorité

1. `references/APPROUVEES/00_PALETTE_EPGMANAGER.jpg` — référence **absolue** pour couleurs, densité et typographie.
2. `references/APPROUVEES/01_MENU_NEO_5_TUILES.png` et `02_MENU_ADVANCED_12_TUILES.png` — **les deux menus validés** par l'utilisateur (ne pas les réinventer).
3. `references/APPROUVEES/03_CHANNEL_NEO_DENSE.png`, `04_CHANNEL_ADVANCED_AEREE.png`, `05_CHANNEL_COMPACT_OPTION.png` — listes de chaînes validées/variante.
4. `references/APPROUVEES/06_INFOBAR_AI_APPROUVEE.png`, `07_INFOBAR_GROUPE.png` — infobar validée et exemple multi-types.
5. `references/APPROUVEES/08_FINAL_SCREENS_NEO_VS_ADVANCED.png`, `09_APPROBATION_DETAIL_EP G_MENU_CONTEXT_SETTINGS.png` (corriger l'espace dans le nom : voir README) — guide EPG, menus contextuels, réglages validés.
6. `references/APPROUVEES/10_METRIX_ORIGINAL_INFOBAR.jpg`, `11_METRIX_ORIGINAL_MAIN_MENU.jpg`, `12_METRIX_ORIGINAL_EPG.jpg`, `13_METRIX_ORIGINAL_CONTEXT.jpg`, `14_METRIX_ORIGINAL_SETTINGS.jpg` — structure, ratio, conventions natives Metrix à conserver.
7. `references/EXPLORATIONS/` — variations historiques pour inspiration SEULEMENT ; certaines ont été **explicitement rejetées** (glow excessif, mini-TV, surabondance de couleurs, grand menu Windows, infobar flottante) : ne jamais les prendre pour choix définitifs.

## LIVRABLES

Fournis le repo de travail, les deux dossiers de skin complets, les modules optionnels, les assets sous licences valides, scripts de vérification/test, maquettes de vérification, un README clair, une matrice de compatibilité, les paquets .ipk séparés si build possible et un bref état d'avancement réel. **Aucune installation sur mon Vu+ avant accord écrit distinct.** Avance autonomement sans multiplier les audits, versions bêta ou demandes d'approbation intermédiaires.

# Modules facultatifs et configurations propres

Le runtime commun est nécessaire aux skins. Le paquet MetrixNEOHelper est
facultatif et n’est pas une dépendance des skins.

## Préférences

Les deux skins exposent leurs préférences via MENU dans le menu principal,
puis « Metrix NEO · Préférences », même sans le plugin facultatif. Advanced
conserve aussi sa tuile « Thème & Skin ». Aucun ajout au menu système global.

Fichiers propres après une sauvegarde explicite dans l’interface :

- `/etc/enigma2/metrix-neo/MetrixNEO.json`
- `/etc/enigma2/metrix-neo/MetrixNEOAdvanced.json`

Chaque sauvegarde conserve un `.json.bak` lisible. Annuler et prévisualiser ne
créent pas de fichier. Aucun `configfile.save()` global, activation de skin ou
redémarrage. Les changements de présentation sont pris en compte à la réouverture
des écrans ; aucun changement du skin actif n’est demandé.

L’aperçu permet de constater la taille de police sur un texte local. L’option
de texte agrandi ne remplace pas encore les polices de tous les écrans. MENU ouvre le choix natif des catégories à gauche ; les changements restent
temporaires entre catégories. Couleurs/transparence par écran et restauration graphique complète
restent à développer après confrontation aux maquettes.

## Météo

Activation météo + coordonnées + consentement réseau requis. Source Open-Meteo,
fuseau Africa/Casablanca, quatre jours en cache pour trois prévisions affichées, timeout 5 s, réponse limitée à 128 Kio.
Travail via `twisted.internet.threads.deferToThread`. Aucune requête au zapping.
Le timer vérifie toutes les 15 minutes ; TTL par défaut d’une heure. Cache JSON
dédié et borné sous `/tmp/metrix-neo-cache/<profil>`, volatil au redémarrage.
L’interface signale « cache » pour les prévisions expirées encore datées du jour
ou ultérieures. Aucune prévision fictive et aucun géocodage automatique.

Le fournisseur est attribué dans la documentation et les préférences. Les données
actuelles (température, condition, jour/nuit) sont séparées des prévisions
quotidiennes. Le libellé du lieu est saisi volontairement ; aucune ville n’est
déduite du fuseau horaire. Sans mesure actuelle, température et icône restent
masquées. Le pictogramme de nuit dépend de is_day, jamais de l’heure affichée.

## Images de programmes

L’import utilise en lecture seule `/media/hdd/metrix-neo/artwork/metadata.json`.
Ce répertoire n’est pas créé automatiquement. Exemple de format documentaire,
à ne pas confondre avec une émission réelle :

```json
[
  {
    "title": "Titre exact présent dans votre EPG",
    "start": 1234567890,
    "image": "image-autorisee.jpg",
    "license": "Licence ou autorisation réelle",
    "source": "Source réelle du visuel"
  }
]
```

Le titre et l’instant de début doivent correspondre exactement à l’événement.
L’image suit la sélection EPG : une nouvelle émission déclenche sa propre
recherche, puis un décodage asynchrone. L’ancienne image est masquée immédiatement ;
un résultat arrivé après un changement de sélection ne peut pas la remplacer.
La scène de téléphone visible dans les aperçus illustre uniquement un événement
d’exemple et n’est pas une image fixe chargée par le skin.
Chemins confinés au catalogue ; signatures PNG/JPEG, poids maximum 4 Mio,
catalogue maximum 1 Mio et 2 000 entrées. Décodage asynchrone par ePicLoad.
Sans image, le picon, le titre et le synopsis remontent dans le panneau de
ChannelSelection ; le synopsis s’agrandit et les deux prochains programmes
restent à leur place. Aucun cadre d’affiche vide ni deuxième picon n’est réservé.
Les deux listes restent sur fond bleu nuit uni, selon le choix explicite de l’utilisateur.
Les fichiers sources ne sont ni redimensionnés, ni évincés.

Le budget cache/TTL concerne actuellement la météo. `poster_ttl` est réservé à
un futur fournisseur distant ; il ne gère pas le catalogue utilisateur. Aucun
téléchargement TMDb, scraper ou accès IA distant n’est implémenté.

## Smart et diagnostics

Reconnaissance stricte de SxxExx, Season/Episode, Saison/Épisode et الموسم/الحلقة,
sans changer le titre d’origine. Les prochaines émissions x2 proviennent de
l’EPG natif, triées et filtrées ; aucune émission n’est dupliquée pour combler
un manque. Diagnostics : piste audio absente et EPG absent seulement si les
états sont exposés. Les mesures inconnues restent invisibles.

La fonction pure de diagnostics supporte aussi REC/timeshift/signal ; les
indicateurs d’infobar utilisent directement les états natifs. Aucun contrôle
IPToSatPro, aucun accès privé EPGManager et aucune analyse de bouquets.

Restent hors livraison : catégories avancées multilingues, posters distants
et IA distante. Les logos automatiques de football sont décrits ci-dessous.

## Écussons locaux des infobars

Le même metadata.json accepte des lignes supplémentaires avec `"role": "home"`
et `"role": "away"`. Chaque ligne porte titre, début Unix, image relative,
licence et source, comme les affiches. Les deux rôles doivent correspondre au
même titre et au même début d’événement. Sans paire complète correspondante,
aucun écusson ni VS ne s’affiche. Une ligne sans rôle reste une affiche
(`poster`). Aucun fichier de club n’est livré avec le skin.

## Logos automatiques de football

Une option distincte peut identifier les deux noms explicitement séparés dans
l’EPG et demander leurs écussons à TheSportsDB. Les résultats doivent correspondre
exactement aux noms/alias disponibles, avec deux identifiants distincts et deux
PNG valides. Les demandes sont dédupliquées et les réponses tardives ne remplacent
jamais les logos du programme en cours. Réseau désactivé par défaut, autorisation
indépendante de la météo, cache hors ligne et API key masquée.
Voir [TEAM_LOGOS.md](TEAM_LOGOS.md) pour la configuration, les droits et les
limites de validation de cette nouvelle source facultative.

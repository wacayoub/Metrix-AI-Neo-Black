# Metrix NEO et Metrix NEO Advanced 0.1.0

Deux skins Full HD distincts pour OpenATV : Metrix NEO compact et Metrix NEO
Advanced avec panneau enrichi. Tous les menus des deux thèmes sont validés
visuellement par l’utilisateur le 25 octobre 2026 sur les aperçus présentés.

- Menus à icônes, dégradés bleu nuit/cyan, deux listes de chaînes à vingt lignes,
  infobars distinctes et fréquence satellite conservée.
- Contexte centré avec quinze lignes et vidéo courante autour ; images EPG
  liées au programme sélectionné et repli sans image.
- Guides EPG, préférences, audio, sous-titres, programmations, enregistrements,
  plugins, saisie et dialogues harmonisés. Actions natives conservées.
- Runtime commun nécessaire, helper facultatif. Météo et logos de football
  automatiques sur consentement distinct ; images de programmes locales.
- Licences MetrixHD réservées à OpenATV, code original MIT et Raleway Light OFL
  incluses. Aucun logo commercial de club embarqué.

Validation locale : 152 tests Python, contrôles XML/ressources/géométrie et
inspection de quatre IPK sans scripts de maintenance. IPK et ZIP sources
reproductibles avec les mêmes entrées. Sources techniques épinglées dans
`sources.lock.json`. Rapports détaillés joints à la livraison.

Les paquets restent non testés sur le Vu+ Zero 4K personnel sous OpenATV 8.0.1.
L’aperçu est une simulation XML ; il ne certifie pas le rendu natif, le zapping,
les performances ou la résolution des dépendances opkg. Les fenêtres propres à
certains plugins tiers utilisent leur repli natif. Le Smart reste local et
limité aux données disponibles ; aucun service d’IA ni fournisseur distant de
posters n’est inclus.

Aucun accès, installation, activation ou redémarrage du Vu+. Aucun changement
d’EPGManager, IPToSatPro, bouquets, mappings ou configurations existantes.
GitHub est préparé localement ; aucune release publiée ni CI distante exécutée.

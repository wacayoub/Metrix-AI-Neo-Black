# Metrix NEO et Metrix NEO Advanced

Deux skins FHD distincts pour **OpenATV**, destinés au Vu+ Zero 4K sous OpenATV
8.0.1. Livraison locale de développement `0.1.0` : **NOT_INSTALLED**.
Tous les menus des deux thèmes sont validés visuellement par l’utilisateur le
25 octobre 2026. La compatibilité et le rendu natif sur votre appareil restent
à vérifier. Aucun accès ni changement du Vu+ n’a été effectué.

| | Metrix NEO | Metrix NEO Advanced |
|---|---|---|
| Identité | `MetrixNEO/skin.xml` | `MetrixNEOAdvanced/skin.xml` |
| Menu principal | 5 tuiles illustrées | Photo gauche + 12 tuiles, 4 colonnes × 3 lignes |
| Liste par modèle | 20 lignes, programme adjacent, fond bleu nuit uni | 20 lignes avec marges, fond bleu nuit uni, option compacte |
| EPG | Timeline native, description haute | Timeline et panneau de détail |
| Contexte | Fenêtre centrée, 15 lignes, vidéo en cours autour | Idem, image EPG et aide de l’action |
| Enrichissements | Images, météo et logos EPG facultatifs | Images, logos EPG, épisode explicite et diagnostics |
| Réglages | Fichier NEO propre | Fichier Advanced propre |

Le ZIP annoncé n’a pas été reçu. **Six images ont depuis été fournies** et
servent maintenant de références aux menus, listes, contextes et infobars. Le dashboard
Advanced suit la dernière image agrandie : 4 colonnes × 3 lignes. Les deux listes
reprennent les 20 lignes des captures les plus récentes. Les aperçus sont des
simulations issues des XML, avec des données d’exemple explicitement indiquées.
La galerie contient 28 simulations, dont les deux listes sans image EPG et les
catégories réelles des préférences. Des liens directs permettent de retrouver
les listes de chaînes, les infobars et les paramètres. Leur
panneau se réorganise réellement au runtime ; l’image du programme ne reste
jamais figée. Les guides sont harmonisés dans leurs modes couleur et graphique.

- [Galerie comparative locale](previews/index.html)
- [Listes de chaînes des deux skins](previews/index.html#listes-chaines)
- [Infobars des deux skins](previews/index.html#infobars)
- [Préférences et commandes réelles](docs/PREFERENCES.md)
- [Pictogrammes et fidélité des infobars](docs/INFOBAR_FIDELITY.md)
- [Planche des 48 pictogrammes](assets/source/infobar-icons-guide.png)
- [Logos automatiques et fréquence satellite](docs/TEAM_LOGOS.md)
- [Rapport de livraison et limites](docs/DELIVERY_REPORT.md)
- [Préparation GitHub](docs/GITHUB_PREPARATION.md)
- [Notes de version 0.1.0](docs/RELEASE_NOTES_0.1.0.md)
- [Matrice des écrans](docs/SCREEN_MATRIX.md)
- [Compatibilité et API examinées](docs/COMPATIBILITY.md)
- [Paquetage](packaging/README.md)
- [Plan de test futur, à autoriser séparément](docs/HARDWARE_TEST_PLAN.md)

## Contenu

```
skins/MetrixNEO/             skin.xml, skinTemplates.xml, prev.png, assets/
skins/MetrixNEOAdvanced/     skin.xml, skinTemplates.xml, prev.png, assets/
runtime/Components/         adaptateurs et rendu communs nécessaires
plugin/MetrixNEOHelper/     météo, images et logos EPG facultatifs
tools/                      génération, vérification, simulations et IPK
tests/                      tests sans récepteur ni accès réseau réel
docs/                       décisions, limites, audit et plan matériel
LICENSES/                   avis MetrixHD, licence du code original, tiers
.github/                    CI de validation et préparation des artefacts
dist/                       4 IPK, ZIP sources, manifeste, SHA256SUMS
```

## Reproduire hors récepteur

Python 3.10 minimum pour le code original ; tests locaux sous Python 3.13.2.
Le runtime utilise les bindings Enigma2 de la cible ; il ne peut pas être exécuté
comme une application Windows. Pillow sert uniquement aux simulations.

```console
python -m pip install -r requirements-dev.txt
python tools/fetch_pinned_sources.py
python tools/release_check.py
```

La première commande récupère uniquement les sources publiques aux commits
épinglés ; `--check` vérifie les clones existants sans réseau. Le cycle de
livraison refuse des sources absentes ou modifiées afin de ne pas sauter les
tests natifs. Les générations opèrent uniquement dans le dépôt local. Aucun outil de déploiement
ou commande SSH/opkg d’installation n’est inclus. Les paquets ne contiennent pas
de scripts postinst/prerm et n’activent aucun skin.

## Architecture et replis

Les skins sont indépendants et peuvent être empaquetés séparément. Ils dépendent
d’un petit paquet commun de rendu, **pas du helper Smart**. Retirer le helper
masque les enrichissements ; les widgets natifs et leurs actions demeurent.
Le runtime conserve un seul code commun pour les deux identités.

Les menus utilisent les données et callbacks natifs. Le bouton MENU du menu
principal ouvre toutes les fonctions natives et ajouts de plugins. Les fonctions
propres NEO restent également accessibles par ce menu, sans imposer le helper.
Les fonctions
absentes sont indiquées indisponibles ; aucune installation n’est déclenchée.
Les appels d’enrichissement ne remplacent ni l’EPG natif, ni EPGManager, ni
IPToSatPro. Aucune donnée de bouquet ou de mapping n’est modifiée.

La météo nécessite le helper, des coordonnées saisies volontairement et le
consentement réseau. La météo absente reste masquée ; un cache expiré est signalé.
Open-Meteo.com, données CC BY 4.0, API gratuite à usage non commercial.
Voir [conditions](https://open-meteo.com/en/terms).

Les images sont lues dans un catalogue local sous licence et décodées via
`ePicLoad`. Aucun poster, logo sportif ou résultat distant supposé n’est inventé.
Voir [format du catalogue](docs/OPTIONAL_MODULES.md).

## GitHub

Arborescence, exclusions, CI et modèle de ticket prêts. Dépôt Git local initialisé.
Le projet existant [wacayoub/Metrix-AI-Neo-Black](https://github.com/wacayoub/Metrix-AI-Neo-Black)
a été retrouvé et audité en lecture seule. Un patch d’intégration place ce
nouveau projet dans `dual-skins/` en conservant les anciens scripts, le README et
les manifestes de mise à jour. Aucune publication distante n’a été effectuée.
Voir [préparation GitHub](docs/GITHUB_PREPARATION.md).

## Licence

Base technique étudiée : [MetrixHD officiel](https://github.com/openatv/MetrixHD),
créé par iMaxxx et maintenu par l’équipe OpenATV. Avis particulier conservé,
usage des skins limité à OpenATV. Code Python et assets procéduraux originaux :
MIT. Les polices système sont référencées sans redistribution. Le grand nom de
chaîne NEO et les titres/horloges du sélecteur audio des deux skins utilisent
Raleway Light embarquée, inchangée, sous SIL OFL 1.1.
Voir [avis et attribution](LICENSES/MetrixHD.txt).

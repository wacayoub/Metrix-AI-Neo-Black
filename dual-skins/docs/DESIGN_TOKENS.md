# Design system après réception des références

Les quatre dernières images utilisateur guident la palette et les proportions.

| Usage | RGB |
|---|---|
| Fond | #031323 |
| Panneau | #031523 |
| Haut des tuiles | #0B3154 |
| Milieu des tuiles | #082641 |
| Bas des tuiles | #072039 |
| Sélection haute | #0046AE |
| Sélection médiane | #00368F |
| Sélection basse | #0052B2 |
| Lueur latérale de sélection | #008EEB |
| Contour fin | #123E5A |
| Accent / progression | #11B8EF |
| Texte | #E9F0F8 |
| Texte secondaire | #A7B6C8 |
| Titre EPG adjacent | #48A6CC |

Enigma2 utilise une transparence inverse dans #AARRGGBB : 00 opaque, FF transparent.
Les sélections ont trois arrêts de couleur natifs, des liserés et un éclairage
latéral statique. Le contour reste limité à 2 px. Aucun flou ni effet animé au
runtime. Les couleurs ont été ajustées après lecture de pixels hors texte dans
la référence du dashboard ; ce relevé ne constitue pas un score de fidélité.

NEO : menu cinq tuiles, icônes monochromes et légendes. Advanced : photo originale
à gauche et grille 4 colonnes × 3 lignes. Les deux listes présentent 20 lignes
selon les nouvelles références, sans horaire ni badge de résolution dans les lignes.
NEO : corps 1218 × 900, lignes de 45 px. Advanced : corps 914 × 760, lignes de
38 px et marges. Les deux listes ont un fond bleu nuit uni #031323, sans photo
ni vidéo derrière leurs panneaux. Le dashboard Advanced utilise des cellules
de 340 × 140 et un cadre de 1872 × 633 ; les cinq tuiles NEO utilisent des
cellules de 362 × 306 et un cadre de 1872 × 516. Les bandeaux de titres/options
du montage de référence ne sont pas comptés dans la hauteur de l’interface.

La police Regular est désormais LiberationSans-Regular.ttf, présente dans la
liste commune d’installation des polices du code Enigma2 audité. Le simulateur
lit le même fichier depuis ce clone lorsque disponible ; la police n’est pas
redistribuée. Les replis du simulateur sont signalés dans le rapport visuel.
Les icônes ont des empreintes ajustées par pictogramme et par skin : puzzle plus
présent, roue/horloge/information plus petits dans NEO ; pictogrammes Advanced
contenus dans 64 × 64 avec un espace transparent propre à chaque symbole. Elles
sont anticrénelées à la construction. La photo du salon utilise le cadrage natif `scale="fill"`, sans
étirement du ratio et sans modification du fichier source.

L’image du programme se situe en haut du panneau droit, avant le picon/service,
le titre, la progression, le synopsis et les deux événements suivants. Les faits
de décodeur ne sont affichés que si le service sélectionné est celui réellement
en lecture ; les informations inconnues restent masquées. Trois colonnes séparent
résolution/codec, ratio/source et audio. Le ratio provient de sAspect, jamais du
seul rapport largeur/hauteur de la vidéo.

Les boutons et listes restent natifs. Le rendu des polices, l’anticrénelage et
les dimensions internes doivent encore être comparés sur le Vu+.

## Affinage après comparaison côte à côte

Le menu NEO utilise désormais ses propres dégradés : tuiles #0C2B47 / #09243D /
#091E31 et sélection #003389 / #002E7C / #002E6D. Le relevé visuel du menu NEO
montrait une sélection plus sombre que celle du dashboard Advanced.

Les colonnes des listes sont fixées indépendamment, sans réduction proportionnelle
de toute la ligne Advanced. Coordonnées absolues FHD des ancres :

| Ancre | NEO | Advanced |
|---|---:|---:|
| Boîte de picon, début | 118 | 334 |
| Nom de chaîne, début | 234 | 426 |
| Séparateur vertical | 396 | 560 |
| Programme, début | 426 | 590 |
| Progression, début | 1092 | 1044 |

Les relevés manuels des références restent approximatifs. Les noms longs peuvent
être tronqués dans la colonne native ; l’aperçu ne les réduit pas artificiellement.
La sélection des lignes utilise un liseré de 1 px, puis un dégradé intérieur.
La progression sélectionnée est blanche dans le XML lui-même. Le simulateur lit
ces mêmes rectangles/couleurs et respecte maintenant l’alignement des numéros
et le centrage vertical des textes des lignes.

## Recalage final des menus et des listes

Les titres de tuiles utilisent l’alias natif `MenuTitle` vers
`LiberationSans-Bold.ttf`, présent dans le Makefile commun des polices Enigma2
audité. Les autres textes conservent la police Regular. Le simulateur utilise
la même graisse lorsqu’elle est disponible, sans redistribuer de police.

| Élément | NEO | Advanced |
|---|---|---|
| Titre de tuile | 32 px gras | 23 px gras, boîte de 56 px permettant deux lignes |
| Description de tuile | 24 px | 19 px |
| Nom / programme de chaîne | 23 / 24 px | 20 / 21 px |
| Marge latérale dans la sélection de chaîne | 4 px | 2 px |
| Dégradé de tuile sélectionnée, haut / milieu / bas | #003389 / #003080 / #002B73 | #003EA0 / #00358F / #0048A9 |
| Dégradé de ligne sélectionnée, haut / milieu / bas | #003F9F / #00358D / #0241AC | #0348B6 / #023289 / #0052BC |

Le liseré de ligne est #1A7BCB et son trait supérieur #2084D9. Ces palettes
spécifiques remplacent les anciens arrêts communs dans les menus et les listes.
Les relevés hors texte servent à guider les couleurs, sans mesurer une fidélité
globale ni prouver le rendu Enigma2 sur matériel. La roue dentée est redessinée
avec huit dents plates et les empreintes des pictogrammes sont ajustées par skin.

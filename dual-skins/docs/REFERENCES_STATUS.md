# Références reçues et décisions appliquées

Le prompt maître initial est conservé dans MASTER_REQUIREMENTS.md. Le ZIP complet
n’a pas été reçu. Six images ont ensuite été fournies directement :

| Image | Fichier | Application |
|---|---|---|
| 1 | 1000514993.png | Comparatif NEO/Advanced : NEO option 2 à cinq tuiles, icônes et style des contextes |
| 2 | 1000514994.png | Dashboard Advanced agrandi : photo gauche, 4 colonnes × 3 lignes |
| 3 | 1000514982.png | Liste Advanced avec marges, 20 lignes et détail droit ; la ville représente un exemple de contenu, pas un fond à embarquer |
| 4 | 1000514981.png | Liste NEO plein écran, 20 lignes, image programme au-dessus des informations |
| 5 | 1000515121.png | Infobar NEO : numéro puis picon, émission, clubs et suivant, statuts bas, météo gauche et horloge droite |
| 6 | 1000515120.jpg | Infobar Advanced : picon puis numéro/chaîne, clubs, émission, progression longue et détails de réception |

Ces dernières images et la demande de fidélité prévalent sur les premières
simulations et les anciennes indications contradictoires de densité/grille.
Les légendes de variantes du collage ne sont pas intégrées à l’OSD.

La structure est codée dans tools/reference_design.py. Les aperçus des menus et
listes lisent les coordonnées des XML générés et leurs templates. Les captures
ne sont jamais utilisées comme interface de fond : titres, actions, listes,
progression et météo restent des widgets natifs.

Les photos décoratives originales générées pour le projet sont distinctes des
captures. L’image programme fictive n’est utilisée que pour les aperçus et n’est
pas distribuée dans les IPK. Les picons typographiques des aperçus illustrent
l’emplacement des vrais picons existants sur l’appareil.

La fidélité visuelle a été revue localement. Une identité pixel à pixel ne peut
être attestée sans rendu réel Enigma2, polices de la cible et comparaison sur
appareil. Les images ont des ratios/cadrages différents ; leurs données météo
et programmes ne doivent pas être figés au runtime. Aucun test Vu+ n’a eu lieu.

La correction suivante porte spécifiquement sur les proportions : suppression
de la hauteur ajoutée par les bandeaux de montage, cellules Advanced plus basses,
tuiles NEO moins hautes, bandeau météo sur trois colonnes verticales, polices
régulières, icônes aux empreintes comparables et dégradés plus proches des zones
bleues relevées. Les fenêtres contextuelles retrouvent également un cadre compact.
Leurs actions restent celles du menu natif ; la légende EXIT correspond à sa
fermeture. Les raccourcis colorés du montage ne sont pas affichés comme s’ils
étaient disponibles lorsqu’ils ne sont pas raccordés au menu natif.

La clarification suivante de l’utilisateur prévaut sur l’interprétation initiale :
la scène de téléphone est un exemple d’image du programme EPG sélectionné, et
la ville un exemple de contenu de chaîne. Elles ne doivent jamais devenir un
fond permanent. Choix confirmé pour les deux listes : fond bleu nuit uni.
Le renderer EPG suit l’événement, masque l’ancienne image pendant un changement,
et ignore les décodages obsolètes. Sans image correspondante, le picon sert de
repli. Le catalogue local reste la seule source implémentée à ce stade.

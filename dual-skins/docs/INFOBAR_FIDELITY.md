# Pictogrammes et fidélité des infobars

Les deux photos de référence sont 1000515121.png pour NEO et 1000515120.jpg
pour Advanced. Elles restent privées et ne deviennent jamais un fond du skin.
La vidéo derrière l’OSD reste la chaîne en cours.

Dans NEO, la dernière capture utilisateur remplace le petit nom au-dessus du
picon par un grand titre en bas à gauche de la vidéo, juste au-dessus du bandeau.
Le nom réel est affiché sur une seule ligne en Raleway Light 112, dans la zone
80,706 / 1760 × 124. Il provient de session.CurrentService via ServiceName/Name
et suit les changements de chaîne ; aucun nom n’est figé. Les noms très longs
restent bornés à cette zone sans retour à la ligne. Le picon et les autres blocs
du bandeau gardent leurs positions. Le panneau de description de la seconde
infobar NEO s’arrête avant cette nouvelle zone afin d’éviter une superposition.
La police fine est copiée sans modification depuis la base MetrixHD auditée,
avec sa licence SIL OFL 1.1 dans LICENSES/Raleway-Light-OFL.txt. Le même TTF
est utilisé dans les simulations et inclus dans l’IPK NEO.

Les deux compositions conservent le bandeau de 248 px au bord inférieur.
Les badges techniques sont désormais de vrais PNG transparents, dessinés par
le code avec anticrénelage : 24 ressources par profil, soit 48 au total. NEO
utilise les cadres or pour 4K/HDR et REC circulaire.
Advanced utilise le HDR blanc, le point REC et la parabole SAT. Les formats
audio ont leurs pictogrammes propres ; AAC/DTS n’utilisent pas le double D.

La dernière correction remplace le texte technique concaténé par six colonnes
fixes dans NEO et sept dans Advanced. Résolution, FPS, aspect, audio et langue
partagent une seule ligne ; Advanced ajoute position orbitale et accord satellite
sur cette même ligne. NEO conserve aussi la fréquence, polarisation et débit
symbole entre REC et TIMESHIFT. Toutes les étiquettes sont centrées verticalement et ne
reviennent pas à la ligne. Une valeur inconnue reste vide, sans déplacer les autres.
Les FPS sont arrondis à deux décimales au maximum (59.94 fps, par exemple).
L’absence d’API audio ne masque plus les informations vidéo ou satellite valides.

La parabole SAT est redessinée dans les deux profils avec coupelle inclinée,
tête de réception, pied et ondes. Les cadres sont affinés et les couleurs de
l’infobar utilisent un blanc doux, gris bleuté, cyan et or dédiés. Le titre et
l’horloge NEO passent de Bold à Regular. La police est Liberation Sans Regular,
présente dans les fichiers installés par Enigma2 : aucun fichier Light fictif
ni Myriad Pro conditionnel à d’autres modèles n’est référencé sur le Zero 4K.
L’aspect plus léger vient de la graisse Regular et des couleurs, sans police
supplémentaire à installer. Les menus et listes déjà approuvés gardent leurs styles.

Sources : tools/infobar_assets.py et vocabulaire runtime infobar_icons.py.
La planche complète est assets/source/infobar-icons-guide.png. Les glyphes des
icônes sont rasterisés à la construction ; leur police reste native. Raleway
Light est embarquée uniquement pour le grand nom de chaîne de NEO.
Le renderer natif mémorise le dernier pictogramme et masque une valeur inconnue
ou une ressource absente. Aucun téléchargement, polling supplémentaire ou
appel réseau n’a lieu lors de l’affichage des badges.

NEO affiche les trois jours suivants, et Advanced présente aussi le bloc
Aujourd’hui. Le fournisseur met en cache quatre jours pour ces présentations ;
les autres écrans gardent trois prévisions visibles. Les conditions météo et
le jour/nuit proviennent des données disponibles, sans ville ou date figée.

Atmos nécessite cette mention explicite dans la piste audio sélectionnée.
La 4K, le HDR ou E-AC-3 seuls ne l’impliquent pas. Le retard du timeshift
Advanced est calculé uniquement avec les longueurs et positions PTS natives,
à 90 000 unités/seconde, lorsque le timeshift est actif et que ces valeurs
sont valides. Sinon, seul l’état TIMESHIFT actif peut être indiqué.

Les icônes seekback/seekforward ont été créées comme ressources. Elles ne sont
pas affichées comme des commandes ±30 s : aucun raccourci de télécommande ni
comportement Enigma2 existant n’est remplacé. La mention IA ou Smart Match
de la maquette n’est pas présentée comme une inférence ou une connexion réelle.

Les picons existants et les écussons locaux sous licence sont chargés par leurs
renderers. Le helper peut aussi rechercher les deux noms explicites du match
dans l’EPG auprès de TheSportsDB, sur consentement séparé et avec cache borné.
Les détails et limites sont dans TEAM_LOGOS.md. Les initiales RM/FCB et le picon typographique des simulations servent
à comparer les emplacements ; aucun écusson de club commercial n’est embarqué.
Les chiffres, Atmos/DD+, retard et programmes des aperçus sont des données de
démonstration, jamais les mesures du récepteur personnel.

La ressemblance à 100 % n’est pas certifiée : les photos AI combinent des états
et contrôles qui ne sont pas tous disponibles, et aucun rendu réel sur le build
OpenATV 8.0.1 de l’utilisateur n’a été autorisé. Les comparaisons locales portent
sur les géométries et assets réellement intégrés aux XML, sans capture du Vu+.

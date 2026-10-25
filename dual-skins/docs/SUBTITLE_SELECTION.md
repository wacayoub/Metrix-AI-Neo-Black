# Sous-titres — revue visuelle

Validé visuellement par l’utilisateur pour les deux thèmes le 25 octobre 2026.
Cette validation ne donne aucune autorisation d’installation ou d’accès au Vu+.

Le menu audio des deux thèmes est validé visuellement par l’utilisateur le
25 octobre 2026. Cette validation ne porte pas sur le récepteur et ne donne
aucune autorisation d’installation.

OpenATV branch8.0 ouvre `SubtitleSelection`, qui hérite d’`AudioSelection` et
utilise explicitement son skin. Le sélecteur conserve donc la disposition audio
approuvée, le bleu nuit translucide, les dégradés NEO/Advanced, les accents cyan
et la vidéo courante en arrière-plan. Le nouveau pictogramme CC remplace le
haut-parleur seulement lorsque `settings.menupage.value == 'subtitles'`.
L’icône suit le mode natif, indépendamment de la langue du titre. Son écouteur
est retiré à la destruction de la fenêtre ; aucun réglage n’est changé.

Les pistes, formats, langues et marques X sont fournis par OpenATV. Les pistes
DVB et télétexte des aperçus sont des exemples. Aucun faux bouton « Désactiver »
n’est ajouté : dans le code audité, OK sur la piste active désactive celle-ci ;
OK sur une autre piste la sélectionne. Le menu rapide apparaît seulement si une
piste est active et si le contexte natif le permet. MENU conserve les réglages
automatiques de langue ; EXIT ferme la fenêtre. Les raccourcis couleur restent
conditionnés par les options natives disponibles. Le menu rapide lui-même
conserve son affichage natif et n’est pas présenté comme redessiné ici.

Les aperçus comprennent : piste active avec X, aucune piste active, aucune piste
disponible et focus sur le menu rapide. Le cas vide conserve la liste native
vide. Le texte explicatif est dans la légende de revue, sans message inventé
dans le produit. La vidéo est illustrative, jamais embarquée dans les IPK.

Le screen historique `Subtitles` (repli de configuration) reste distinct du
sélecteur réellement utilisé par la branche OpenATV auditée. La galerie propose
une entrée « Sous-titres · sélection native » basée sur `AudioSelection`.
Le rendu sur le build exact du Vu+ reste à vérifier avec autorisation explicite.

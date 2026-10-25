# Préférences réelles des deux skins

Accès futur dans Enigma2 : MENU du menu principal → menu natif complet →
« Metrix NEO · Préférences ». Le helper facultatif propose aussi cette entrée
dans le navigateur de plugins lorsqu’il est présent. Aucun accès au récepteur
n’a été effectué pour préparer ces écrans.

## Touches

| Touche | Libellé | Action réelle |
|---|---|---|
| Rouge ou EXIT | Annuler | Ferme sans sauvegarder les modifications temporaires |
| Verte | Enregistrer | Valide les valeurs puis sauvegarde seulement le profil NEO courant et ferme |
| Jaune | Défauts NEO | Rétablit les valeurs par défaut de ce profil dans l’éditeur, sans les sauvegarder |
| Bleue | Actualiser | Demande au helper une actualisation avec les valeurs déjà enregistrées ; ne sauvegarde pas l’éditeur |
| MENU | Catégorie | Ouvre le choix natif des catégories ; OK sélectionne, EXIT conserve la catégorie |
| Haut / bas | — | Déplace la sélection dans les options |
| Gauche / droite, OK | — | Édition native : valeur, bascule ou clavier selon le type |

Le choix d’une catégorie conserve les modifications des autres catégories.
Après Jaune, Rouge annule la restauration ; Vert la confirme. Une coordonnée
invalide empêche la sauvegarde et laisse l’écran ouvert. Bleu sans helper
explique son absence. La météo nécessite toujours coordonnées et consentement.

## Catégories proposées

- Présentation : texte de l’exemple à droite ; disposition compacte uniquement
  dans Advanced, appliquée lors d’une prochaine ouverture de la liste à modèles.
- Météo : affichage, latitude, longitude, nom du lieu et autorisation réseau.
- Images EPG : catalogue local sous licence, logos d’équipes automatiques,
  consentement réseau TheSportsDB distinct de la météo et clé API masquée.
- Smart EPG, uniquement Advanced : saisons/épisodes explicitement présents.
- Diagnostics, uniquement Advanced : informations conditionnelles de la seconde
  infobar, jamais des valeurs ou alertes inventées.
- Cache : limite du cache du helper, de 1 à 128 Mo ; aucun nettoyage des données
  Enigma2 ou des autres plugins.

Les libellés, descriptions et touches des aperçus proviennent du même module
`preferences.py` que l’écran réel. La galerie expose toutes les catégories via
un sélecteur pour chaque skin. Ses valeurs sont les valeurs NEO par défaut,
sans lire ni écrire un fichier de réglages du récepteur.

Les paramètres système OpenATV restent gérés par leur écran natif `Setup` :
le skin reprend ses sources de touches et masque les touches absentes.
L’aperçu illustre un extrait des paramètres audio de la branche 8.0 étudiée,
avec des valeurs de démonstration. Les trois libellés non traduits dans le PO
français étudié restent en anglais, comme le repli natif.

La personnalisation générale des couleurs, de la transparence et de toutes les
polices n’est pas implémentée ; aucun réglage factice ne la prétend disponible.
L’identité visuelle sur appareil, la disposition interne du ConfigList et le
comportement sur le build OpenATV 8.0.1 exact attendent un test autorisé.

Les logos automatiques fonctionnent aussi lorsque les images de programmes
sont désactivées. Vert demande au helper de relire les valeurs sauvegardées ;
les emplacements peuvent se mettre à jour sans redémarrage Enigma2.
Voir [source, cache et limites](TEAM_LOGOS.md).

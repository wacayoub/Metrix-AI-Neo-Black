# Revue visuelle des menus

État : tous les menus des deux thèmes validés visuellement par l’utilisateur le 25 octobre 2026. Aucune validation matérielle effectuée.

Ouvrir `previews/validation-menus.html` depuis le lien « Revue finale de tous les menus » de la galerie principale. Chaque famille propose un sélecteur et les deux skins côte à côte. Les images ouvrent leur version 1920 × 1080.

| Famille | Écrans couverts | Validation utilisateur |
| --- | --- | --- |
| Menus et plugins | Principal, menu natif, plugins en liste et grille | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Contextes et confirmations | Contexte à 15 lignes, choix, message | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Paramètres et préférences | Système, présentation, météo, images, Smart, diagnostics, cache | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Programmations | Général, enregistrement, planification, conflit · NEO et Advanced | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Enregistrements | Films et fichiers enregistrés | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Audio | Sélecteur des pistes audio · NEO et Advanced | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Sous-titres | Sélecteur natif des sous-titres · NEO et Advanced | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Saisie et utilitaires | Repli paramètres, saisie, clavier, console, volume, muet | Validé visuellement par l’utilisateur le 25 octobre 2026 |
| Télévision | Deux listes, deux infobars, EPG graphique, EPG liste, programme | Validé visuellement par l’utilisateur le 25 octobre 2026 |

La revue couvre les 40 identités de fenêtres définies dans chaque XML, regroupées en 34 vues, y compris les alias et le mode sous-titres du sélecteur natif AudioSelection. Smart et diagnostics sont réservés à Advanced.

Les contextes illustrant la vidéo autour de la fenêtre sont réduits à 960 × 540 dans la conversation pour respecter la taille maximale d’affichage. Leurs originaux 1920 × 1080 restent accessibles dans la galerie locale ; les autres comparaisons intégrées conservent tous leurs pixels.

Les menus déjà présentés conservent leurs PNG existants. Les nouveaux aperçus secondaires reprennent les rectangles, couleurs, ressources et textes des XML ; leurs rangées natives et leur clavier restent illustratifs. Ils ne reproduisent pas le moteur Enigma2. Les exemples de touches viennent du code OpenATV branch8.0 audité ; les touches réelles dépendent de l’état, des capacités et de la configuration. Les boutons films sont les affectations par défaut modifiables.

Les programmations, fichiers, plugins installés, mesures, programmes et pistes ne proviennent pas du Vu+. Le fond neutre des petites boîtes représente le contenu sous-jacent ; sur le récepteur, celui-ci dépend de la fenêtre ou de la chaîne courante. Les fenêtres AutoTimer, NetworkOverview et plugins tiers qui utilisent un repli natif ne sont pas toutes redessinées ici.

Aucun accès, installation, activation ou redémarrage du récepteur. La revue ne donne pas d’autorisation pour ces opérations. Les générateurs d’aperçus ne modifient pas les XML runtime. La mise à jour distincte du sélecteur audio et des IPK est décrite dans `AUDIO_SELECTION.md`.

Reproduction locale : `python -X utf8 tools/menu_review.py`, puis `python -X utf8 tools/build_menu_validation.py --no-inline`. Sans cette option, les comparaisons sont générées dans `build/conversation-previews/`, ou dans le dossier fourni par `--visual-dir`. Les rapports de couverture et d’intégrité des PNG sont `reports/menu-validation.json` et `reports/menu-validation-images.json`.

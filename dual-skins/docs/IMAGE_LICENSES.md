# Inventaire des images

| Ressource | Origine / droits | Runtime |
|---|---|---|
| assets/context.png | Filmstrip original par tools/reference_assets.py, MIT | Oui |
| assets/question/info/warning/error.png | Dessins originaux par tools/render_previews.py, MIT | Oui |
| assets/weather-{sun,cloud,moon,rain,storm,snow,fog,wind}.png | Dessins originaux procéduraux par tools/reference_assets.py, MIT | Oui, si météo disponible |
| assets/lounge-reference.png | Photo de salon originale générée pour le projet | Menu Advanced |
| assets/source/scenic-reference-generated.png | Source historique et illustration de vidéo en cours dans les aperçus contextuels uniquement, marquée comme exemple | Non, aucune photo fixe autour du menu natif |
| assets/menu-*.png | Pictogrammes monochromes dessinés par le code original | Menus et contextes |
| assets/*-frame.png, selection-row.png, progress.png | Chrome original généré à partir des tokens | Oui |
| assets/timeline.png | Barre unie originale, MIT | EPG |
| epg/*.png | 23 ressources originales procédurales par tools/reference_assets.py, MIT | Mode graphique EPG natif, palette cohérente avec le mode couleur |
| prev.png | Simulation locale des XML, pas une capture Vu+ | Sélecteur |
| previews/*.png | Simulations avec données d’exemple, MIT | Non |
| Picons utilisateur | Fichiers existants ; droits de leur fournisseur | Lus sur cible, jamais modifiés ni embarqués |
| Affiches de programmes | Catalogue local, licence et source exigées | Optionnel, aucune fournie |
| Logos de clubs | Catalogue local sous licence ou API TheSportsDB facultative ; droits des tiers conservés | Optionnels, aucun fichier de club embarqué |
| Six captures utilisateur | Reçues en références de conception | Jamais embarquées comme interface |
| previews/fixtures/programme-demo-generated.png | Image fictive générée, réservée aux simulations | Jamais dans les IPK |
| fonts/Raleway-Light.ttf | Copie inchangée du MetrixHD audité ; Matt McInerney, Pablo Impallari, Rodrigo Fuenzalida ; SIL OFL 1.1 | Grand nom de chaîne NEO ; titre et horloge audio des deux skins |

Aucune photographie commerciale n’est redistribuée.
Les aperçus locaux utilisent, lorsque disponible, LiberationSans-Regular.ttf du
clone technique audité ; les skins référencent les polices Regular et Bold déjà
fournies par Enigma2, sans les embarquer. Exception : Raleway Light est incluse
dans chaque skin pour le sélecteur audio, et dans NEO pour le grand nom de chaîne,
avec sa notice SIL OFL 1.1, sans modification.
SHA-256 : 3cf1d8bf160d93b4a2ec30dbfc177bfb9d14358fe4232b51df39a1c677695bf5.
Les trois prompts et destinations des assets générés sont conservés dans
assets/source/IMAGEGEN_PROMPTS.md. Les images utilisateur restent privées dans
les pièces jointes et sont exclues de Git ainsi que de l’archive source.
Le contrôle technique du catalogue exige une mention de licence/source mais ne
constitue pas une vérification juridique de son contenu fourni par l’utilisateur.

Les assets infobar-* sont des dessins et dégradés originaux. Les initiales RM/FCB
des simulations ne sont pas des écussons fournis au runtime. Les deux photos
sportives utilisateur servent exclusivement de références locales privées.

Les infobar-icon-* et leur planche sont générés par tools/infobar_assets.py,
sans découpe des photos utilisateur ni copie des PNG MetrixHD. Les noms des
formats audio/vidéo décrivent leurs états techniques ; aucune certification du
matériel n’est déclarée par la présence d’un pictogramme dans le code source.

L’adaptateur TheSportsDB référence ses API officielles et conserve l’attribution.
Les téléchargements futurs restent dans le cache local de l’utilisateur ; aucun
logo commercial ni résultat API n’est redistribué avec le projet. Les conditions
et limites figurent dans TEAM_LOGOS.md.

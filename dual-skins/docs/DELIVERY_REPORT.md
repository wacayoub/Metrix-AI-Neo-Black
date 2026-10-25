# Livraison 0.1.0 — 25 octobre 2026

**Tous les menus des deux thèmes sont validés visuellement par l’utilisateur.**
Preuve : « Super, on valide tous les menus pour les deux thèmes. »
Cette validation porte sur les aperçus ; aucun test matériel n’a été effectué.
Statut : **NOT_INSTALLED / NO_RECEIVER_WRITE**.

## Contenu finalisé

Deux identités Full HD indépendantes : `MetrixNEO/skin.xml` et
`MetrixNEOAdvanced/skin.xml`, avec leurs fichiers et paquets propres.
Menus à icônes, dégradés bleu nuit/cyan, deux listes à vingt lignes et fond uni,
infobars distinctes avec fréquence satellite, guides EPG, contexte centré de
1 480 × 850 avec quinze lignes, paramètres, audio, sous-titres, programmations,
plugins, enregistrements, saisie, clavier et dialogues.

Les images EPG suivent le programme sélectionné ; le panneau se réorganise
sans image. Les photos de chaîne des références ne sont pas des papiers peints.
La vidéo courante reste visible autour des fenêtres prévues pour cela.
Les callbacks natifs, les touches disponibles et les configurations existantes
sont respectés. Les exemples de touches des films correspondent aux valeurs
natives par défaut, configurables par l’utilisateur.

La revue couvre 40 identités de fenêtres dans chaque skin, regroupées en
34 vues. La galerie `previews/validation-menus.html` conserve les deux thèmes
côte à côte ; `previews/index.html` donne accès aux listes et infobars.
`reports/visual-validation.json` consigne l’approbation. Les aperçus sont issus
des XML avec des données d’exemple, sans exécution du moteur Enigma2.

## Paquets et sources

| Fichier dans dist/ | Usage |
| --- | --- |
| enigma2-plugin-skins-metrixneo_0.1.0_all.ipk | Skin classique Metrix NEO |
| enigma2-plugin-skins-metrixneo-advanced_0.1.0_all.ipk | Skin premium Metrix NEO Advanced |
| enigma2-plugin-skincomponents-metrixneo-runtime_0.1.0_all.ipk | Dépendance nécessaire à chaque skin |
| enigma2-plugin-extensions-metrixneohelper_0.1.0_all.ipk | Helper facultatif : météo, images, logos |
| metrix-neo-0.1.0-source.zip | Code, ressources, tests, documentation, aperçus |
| metrix-neo-dual-skins.patch | Intégration additive au dépôt GitHub existant |
| metrix-neo-0.1.0-github-delivery.zip | Dossier complet de livraison avec rapports et empreintes |

Les quatre IPK sont `Architecture: all`, sans bytecode Windows ni scripts de
maintenance. Ils n’activent pas de skin. `manifest.json` et `SHA256SUMS`
identifient les quatre paquets et le ZIP source ; `DELIVERY_SHA256SUMS`
identifie le dossier complet. Ce dernier contient aussi ses empreintes internes.

## Résultats des tests hors appareil

| Vérification | Résultat et preuve |
| --- | --- |
| Tests Python | 152 réussis ; reports/tests.txt |
| XML, géométrie FHD, ressources, polices et raccordements | PASS ; reports/static-report.json |
| Intégrité ar/gzip/tar, droits, MD5, chemins disjoints | PASS, quatre IPK, 296 fichiers détenus ; reports/ipk-report.json |
| Scripts de maintenance et opérations récepteur | Zéro ; aucun opkg d’installation exécuté |
| Reconstruction à entrées fixes | IPK et ZIP source identiques ; dist/BUILD_REPORT.json |
| Sources techniques | Commits MetrixHD et OpenATV vérifiés ; sources.lock.json |
| Dispositions audio, sous-titres, timers, autres menus | PASS ; reports/audio-layout.json, subtitle-layout.json, timer-layout.json, remaining-menus.json |
| API TheSportsDB depuis le PC, lors du développement | Deux identités et PNG vérifiés en mémoire ; reports/team-provider-live.json |
| Patch GitHub | Contrôle d’application avant/arrière, ajouts seulement ; dist/GITHUB_PREPARATION.json |
| Appareil personnel, opkg, activation et zapping | NON EFFECTUÉS |
| CI distante GitHub | NON EXÉCUTÉE ; préparation locale uniquement |

Les tests natifs des programmations et du clavier utilisent les fonctions de
dessin des sources OpenATV épinglées avec des bindings simulés. Le cycle final
refuse des sources absentes ou modifiées, afin de ne pas omettre ces tests.
La reproductibilité constatée porte sur deux constructions locales avec les
mêmes entrées et dépendances ; elle ne constitue pas une comparaison entre OS.

## GitHub

Cible : https://github.com/wacayoub/Metrix-AI-Neo-Black.
Le HEAD de `main` a été revérifié en lecture seule le 25 octobre 2026 :
`18ec2cfd3d9e97fc41fb889d81bc695961a5e6eb`.
L’intégration ajoute `dual-skins/` et une CI racine dédiée. Aucun ancien fichier,
manifest, feed ou plugin n’est modifié. Le patch inclut les ressources binaires.
Le vrai index Git local reste inchangé ; les index et objets de préparation
sont isolés sous `build/`.

La CI prépare les dépendances et récupère les deux sources publiques aux
commits épinglés, puis vérifie tests, XML, IPK et reproductibilité. Les uploads
excluent les caches Git et le répertoire privé de travail. Description de PR,
notes de version et procédure sont dans `GITHUB_PR_BODY.md`,
`RELEASE_NOTES_0.1.0.md` et `GITHUB_PREPARATION.md`.
Aucune branche distante, PR, release ou publication n’a été créée.

## Limites restantes

1. Le build personnel OpenATV 8.0.1 et ses bindings Python/Enigma2 n’ont pas été
   audités. Les sources officielles branch8.0 épinglées constituent une base
   technique, pas une certification du Vu+ Zero 4K. Découverte des skins,
   dépendances opkg, activation, zapping, rendu, overscan, mémoire et rapidité
   restent à tester sur matériel avec autorisation distincte.
2. Les aperçus sont validés visuellement ; une identité de rendu à 100 % dans
   Enigma2 ne peut pas être attestée hors appareil. Le ZIP maître annoncé et
   ses deux documents d’introduction n’ont pas été reçus. Le prompt disponible,
   les photos reçues ensuite et les corrections/validations de l’utilisateur
   ont guidé le travail. Les photos privées sont exclues des livrables.
3. Les fenêtres de certains plugins tiers utilisent leurs replis natifs et ne
   sont pas toutes redessinées. Le mode Legacy respecte les préférences
   existantes ; sa densité ne peut pas être imposée entièrement par le skin.
   Le dessin natif du clavier dépend des paramètres reconnus par le build.
4. Le Smart reste local et conservateur. Aucun service d’IA distante,
   fournisseur de posters distant ou diagnostic approfondi de flux n’est
   inclus. La personnalisation libre des couleurs/transparences reste limitée.
5. Les images de programmes proviennent d’un catalogue local sous licence.
   Les logos automatiques nécessitent deux noms explicites et reconnus dans
   l’EPG, le helper et un consentement TheSportsDB séparé. Couverture et
   disponibilité du fournisseur ne sont pas garanties. Aucun logo commercial
   de club n’est embarqué. La météo exige coordonnées et consentement réseau.
6. Les champs techniques absents restent vides ou masqués : aucun débit,
   Atmos, retard timeshift ou état LIVE n’est inventé. Les données réelles
   dépendent du service, du tuner, du flux et des API du build.
7. Aucun shaping arabe ni performance sur récepteur n’est vérifié. Pillow
   local est sans RAQM. La CI distante est préparée mais n’a pas été exécutée.

Licences : avis MetrixHD réservé à OpenATV conservé, code original MIT et
Raleway Light inchangée sous SIL OFL 1.1. Voir `LICENSES/` et THIRD_PARTY.md.
Aucun accès, installation, activation ou redémarrage du Vu+. Aucune modification
d’EPGManager, IPToSatPro, bouquets, mappings ou configurations existantes.

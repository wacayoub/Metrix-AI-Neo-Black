# Préparation du projet GitHub existant

Dépôt retrouvé via les dépôts connectés :
https://github.com/wacayoub/Metrix-AI-Neo-Black

Commit audité et HEAD de main confirmé à nouveau en lecture seule le 25 octobre 2026 : `18ec2cfd3d9e97fc41fb889d81bc695961a5e6eb` (`main`).
La recherche sur l’autre compte connecté n’a renvoyé aucun dépôt Metrix.

## Audit ciblé

Le dépôt existant contient un updater de palettes V3 et un plugin Metrix Neo AI
0.4.0. Ils appliquent des profils à l’apparence générée par MyMetrixLite ; ils ne
fournissent pas deux dossiers de skins indépendants. Aucun `AGENTS.md`, ZIP de
références ni XML de skin complet n’est présent dans l’arbre audité.

Fichiers examinés : README racine, install.sh, latest.json, metrix_neo_updater.py,
neo-plugin/README.md, manifest.json, neo_engine.py, plugin.py et tests existants.
Les anciens scripts contiennent des opérations d’application/restauration et
des mécanismes automatiques : **aucun n’a été exécuté**.

## Intégration préparée

`dist/metrix-neo-dual-skins.patch` ajoute le projet courant dans `dual-skins/`
et une CI racine `.github/workflows/metrix-neo-dual-skins.yml` avec répertoire de
travail `dual-skins`. Le patch ne modifie aucun fichier existant du commit audité.
Il contient les images via le format Git binary patch.

Les fichiers `latest.json`, `install.sh`, `metrix_neo_updater.py`, `releases/`,
`neo-plugin/manifest.json` et les anciens plugins ne sont pas des cibles du patch.
Cette préparation ne rend donc pas les nouveaux skins disponibles aux anciens
updaters. Le numéro 0.1.0 appartient au nouveau projet, distinct du plugin 0.4.0.

Le patch est construit et vérifié contre le commit audité à l’aide d’un index Git
temporaire local ; aucune commande d’application des thèmes ou d’installation
récepteur n’est lancée. `dist/GITHUB_PREPARATION.json` fournit le résultat et
l’empreinte SHA-256. Le patch peut devenir périmé si le dépôt distant évolue ;
refaire la vérification sur son nouveau HEAD avant toute intégration.

Le générateur relit les fichiers de travail suivis et les nouveaux fichiers non
ignorés. Il utilise désormais deux index et un magasin d’objets dans `build/`,
avec lecture des objets du dépôt principal. Il ne modifie donc pas `.git`,
ne dépend pas d’un `git add` préalable et inclut les dernières corrections locales.

Un dépôt Git local et son index de revue sont prêts, sans commit d’auteur inventé.
Aucune branche, PR, release, modification de feed ou publication distante n’a
été créée. Cette livraison répond à la préparation GitHub et conserve une revue
possible avant publication des candidats non validés sur matériel.


## Livraison prête pour revue

`dist/metrix-neo-0.1.0-github-delivery.zip` réunit les quatre IPK, le ZIP source,
le patch binaire, les rapports, licences et empreintes. `GITHUB_PR_BODY.md` et
`RELEASE_NOTES_0.1.0.md` fournissent les textes de publication préparés.
Tous les menus des deux thèmes sont validés visuellement ; les tests matériels
restent distincts de cette validation.

Reproduction depuis les sources :

```console
python -m pip install -r requirements-dev.txt
python tools/fetch_pinned_sources.py
python tools/release_check.py
```

La récupération concerne seulement MetrixHD et Enigma2 publics aux commits
épinglés. Un clone existant divergent est refusé sans reset. Le mode `--check`
est entièrement hors réseau. La CI réalise cette préparation avant les tests.
Aucun fichier de cache Git ou dossier privé `build/` n’est téléversé en artefact.

Pour préparer à nouveau le patch dans ce checkout de travail et son dépôt
legacy audité, puis le dossier complet :

```console
python tools/prepare_legacy_patch.py
python tools/build_delivery.py
```

Le générateur du patch nécessite les objets du commit legacy audité ; le ZIP
source seul n’embarque pas ce dépôt ni son historique. Les paquets peuvent être
reconstruits indépendamment. Avant une intégration future, vérifier à nouveau
le HEAD distant et l’absence du chemin dual-skins/. Puis, dans un checkout
séparé du dépôt cible à la base auditée :

```console
git switch -c codex/metrix-neo-dual-skins
git apply --check /chemin/vers/metrix-neo-dual-skins.patch
git apply /chemin/vers/metrix-neo-dual-skins.patch
```

Ces commandes sont une procédure de revue à exécuter sur le PC, pas sur le
récepteur. Aucun push ni lancement distant de CI n’a été effectué ici.

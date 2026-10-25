# Paquetage local uniquement

`python tools/build_ipk.py` génère quatre paquets IPK ar/debian-binary 2.0 :

| Paquet | Rôle |
|---|---|
| enigma2-plugin-skins-metrixneo | Identité /usr/share/enigma2/MetrixNEO |
| enigma2-plugin-skins-metrixneo-advanced | Identité /usr/share/enigma2/MetrixNEOAdvanced |
| enigma2-plugin-skincomponents-metrixneo-runtime | Composants nécessaires partagés ; dépendance des deux skins |
| enigma2-plugin-extensions-metrixneohelper | Enrichissements facultatifs ; aucun skin n’en dépend |

Tous utilisent `Architecture: all` : uniquement XML, images PNG et Python source,
sans compilation croisée ni bytecode Windows. Cela ne prouve pas la compatibilité
des API Enigma2 du récepteur. La résolution des dépendances opkg reste à vérifier.

Aucun hook postinst, activation de skin, déploiement SSH, effacement tiers ou
redémarrage. Les chemins appartenant aux paquets sont contrôlés et disjoints.
Les scripts de construction et inspection ne contiennent aucune commande d’installation.

`dist/manifest.json` et `SHA256SUMS` décrivent les fichiers livrés.
L’archive ZIP fournit les sources, tests, documentation et simulations.

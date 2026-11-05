# Neo Connect pour Vu+ Zero 4K — 0.1.0 alpha

Plugin Enigma2 Python accompagné d'un moteur WireGuard Go statique Linux ARMv7. Cible du paquet : **vuzero4k**, vérifiée sur le récepteur de cette session. Aucun support universel Enigma2 n'est revendiqué.

Voir [le guide complet](../NEOCONNECT.md) pour l'association, la révocation, les exigences Orange/Internet et les limites des essais. Le réseau mobile n'a pas encore été testé.

## Construire sans contacter le récepteur

Prérequis : Python 3.11+ pour les outils de construction, Go 1.27.3 comme déclaré dans `endpoint/go.mod`, accès aux modules épinglés dans `go.sum`.

```sh
go -C google-tv/receiver-plugin/endpoint test -v -timeout 60s ./...
python -m unittest discover -s google-tv/receiver-plugin/tests -v
python google-tv/receiver-plugin/build_endpoint.py
python google-tv/receiver-plugin/build_ipk.py
```

Le moteur est compilé avec `CGO_ENABLED=0`, Linux/ARMv7, sans bibliothèque système dynamique. `build_endpoint.py --go CHEMIN` permet de choisir l'exécutable Go. Les licences des dépendances et leur manifeste sont ajoutés au paquet. `dist/` est exclu de Git ; la CI publie l'IPK et son empreinte.

## Installer et utiliser

L'installation sur le Vu+ exige l'autorisation explicite du propriétaire : la règle du dépôt reste lecture seule par défaut. Cette session a reçu une exception limitée à Neo Connect, son installation et ses tests locaux.

Vérifier le SHA-256 fourni, transférer le paquet puis installer avec `opkg install /tmp/NOM_DU_PAQUET.ipk`. Vérifier d'abord les dépendances existantes et le résultat de `opkg --noaction install` ; ne pas accepter implicitement une mise à jour de l'image ou du noyau. Le paquet ne contient aucun script de post-installation ou de suppression. Il installe seulement ses fichiers sous `Plugins/Extensions/NeoConnect` et ses notices sous `/usr/share/doc/neoconnect`.

Il ne redémarre pas Enigma2. Après détection du plugin par le menu Extensions : VERT active après confirmation ou renouvelle le code, ROUGE arrête, JAUNE propose de révoquer un appareil, EXIT ferme l'écran. Aucun démarrage automatique du tunnel. Arrêter le plugin avant une désinstallation avec `opkg remove enigma2-plugin-extensions-neoconnect` ; les identités privées sous `/etc/enigma2/neoconnect` sont conservées. Ne les supprimer qu'en connaissance de cause : une nouvelle identité oblige à refaire les associations.

Le moteur n'est piloté que par son processus parent via des pipes privés et s'arrête à leur fermeture. Aucun serveur de commande générique, script shell distant ou API de contrôle OpenWebif n'est ajouté. État et clés privés : dossier 0700 et fichiers 0600. Le code d'association n'est pas enregistré sur disque par le plugin.

## Validation

Quatre tests Go comprennent de vrais échanges WireGuard chiffrés avec serveur HTTP local, restriction des ports, ajout de pair sans interrompre l'existant et révocation. Les seize tests Python couvrent politique réseau, transactions, association HTTPS réelle, concurrence et permissions POSIX (un test ignoré sous Windows). Le moteur et le contrôleur installés ont aussi servi à l'association réelle Sony → Vu+ et à une lecture d'API OpenWebif via le tunnel. Le menu graphique Enigma2 n'a pas été observé sur écran pendant ce test ; aucune vidéo distante n'est certifiée.

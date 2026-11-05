# Neo hors du LAN, en 4G/5G

Solution désormais développée à la demande de l'utilisateur : **[Neo Connect intégré](NEOCONNECT.md)**, sans application VPN séparée ni relais cloud. Plugin installé avec autorisation explicite, tunnel Sony → Vu+ vérifié sur le LAN ; accès 4G/5G et réglage du routeur Orange / ZTE restant à valider. Aucune ouverture de port Internet n'a été réalisée.

Le texte ci-dessous conserve la proposition initiale **Tailscale avec une passerelle à la maison**, non retenue et non installée. Ses mentions d'absence de modification du Vu+ décrivent uniquement cette proposition initiale, antérieure à l'exception autorisant Neo Connect.

```text
Sony/TCL ailleurs, connectée au partage 4G/5G du téléphone
    → Tailscale sur cette TV
    → tunnel privé
    → PC/NAS/routeur compatible, allumé à la maison
    → Vu+ 192.168.11.2
```

La passerelle Tailscale, appelée « subnet router », permet d'atteindre un appareil qui n'exécute pas Tailscale. Le Vu+ conserve son installation actuelle. Le PC de cette session ne dispose pas de Tailscale au moment du contrôle. Choisir une passerelle qui restera allumée et connectée au même LAN que le Vu+. [Documentation officielle des subnet routers](https://tailscale.com/docs/features/subnet-routers).

## Configuration à réaliser

1. Installer Tailscale sur la passerelle domestique et sur l'appareil distant, puis les connecter au compte personnel choisi. Sur Android TV, l'association peut se faire par QR code ou code affiché. Si la TV utilise le partage 4G/5G du téléphone, installer le client VPN sur la TV elle-même. [Installation officielle Android/Android TV](https://tailscale.com/docs/install/android).
2. Sur la passerelle, activer le routage IP selon son système et annoncer uniquement la route du Vu+ : `192.168.11.2/32`. La commande Tailscale correspondante est `tailscale set --advertise-routes=192.168.11.2/32`. Sur Windows, l'activation du routage IP est une étape distincte ; cette commande seule ne remplace pas cette configuration.
3. Approuver cette route dans la console Tailscale. Limiter les règles d'accès aux appareils/personnes autorisés et aux ports TCP nécessaires : **82** pour OpenWebif, **8001** pour le flux natif ; **8002** seulement si un service existant l'utilise. L'approbation de route et les règles d'accès sont deux opérations distinctes. Conserver le SNAT par défaut évite de devoir ajouter une route de retour sur le Vu+.
4. Dans Neo, conserver **192.168.11.2**, port **82**, avec les identifiants saisis localement. Les M3U satellite qui ciblent cette même adresse deviennent routables par le tunnel. Ne pas remplacer cette adresse par l'IP Tailscale de la passerelle : celle-ci ne fournit pas elle-même OpenWebif.

Android prend automatiquement en compte les routes de sous-réseau approuvées. Cette proposition correspond au contrôle actuel de Neo, qui accepte les adresses privées pour OpenWebif ; aucun contournement de ce contrôle n'est nécessaire. [Routage et approbation des routes](https://tailscale.com/docs/features/subnet-routers).

## Vérification extérieure à effectuer

Depuis une vraie connexion 4G/5G, VPN actif : vérifier l'accès à `http://192.168.11.2:82`, charger les bouquets, puis observer plusieurs minutes de lecture dans Neo. Vérifier ensuite que l'accès privé disparaît lorsque le VPN est arrêté. Ce test n'a pas été réalisé pendant la préparation de ce guide.

Les connexions Tailscale directes sont préférables pour le débit vidéo ; un relais peut être utilisé lorsque le réseau empêche la liaison directe. Examiner `tailscale status` ou `tailscale ping` depuis un client approprié pour identifier le chemin. Le débit montant de la maison et le débit mobile doivent suffire au flux ; Neo n'ajoute pas de transcodage distant. [Types de connexions et diagnostic officiels](https://tailscale.com/docs/reference/connection-types).

Les refus HTTP 400 du Vu+ déjà observés en LAN doivent aussi être résolus côté récepteur : le VPN transporte les connexions mais ne libère pas un tuner occupé. La 4K/HDR hors LAN n'est pas validée. Pour les IPTV qui pointent directement vers Internet, le routage limité au Vu+ ne change pas leur accès fournisseur.

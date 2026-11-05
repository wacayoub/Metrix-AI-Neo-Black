# Neo Connect — 0.9.0 alpha

Neo Connect relie Neo Android au Vu+ avec WireGuard intégré aux deux extrémités. Il ne nécessite ni application VPN séparée, ni Tailscale, ni compte ou relais cloud. WireGuard reste une dépendance libre, pas un protocole cryptographique maison.

## Ce qui a réellement été vérifié le 5 novembre 2026

Le paquet 0.1.0 a été installé sur le Vu+ Zero 4K après autorisation explicite de l'utilisateur, en exception à la règle de lecture seule. Aucun autre paquet, module noyau, réglage OpenWebif, image ou réglage du routeur n'a été changé. Le binaire ARM fonctionne sur son noyau 4.1.20-1.9 et son Python 3.14.7. Les fichiers privés sont en 0600, leur dossier en 0700.

Sur la Sony Android 14, la véritable interface Android a effectué l'association HTTPS avec comparaison de l'empreinte reçue par SSH de confiance, l'autorisation VPN Android, un échange WireGuard authentifié et une requête OpenWebif réussie dans le tunnel. Déconnexion, arrêt du service, persistance du profil chiffré, retour simple et double Retour vers Google TV ont réussi. [Rapport matériel](reports/sony-neoconnect-2026-11-05.json).

Cet essai utilise une adresse de terminaison LAN. **Il ne valide pas une connexion 4G/5G, la vidéo distante ou la fluidité 4K/HDR.** La nouvelle APK est installée sur la TCL mais le test du tunnel TCL reste à faire : TV devenue indisponible. L'écran Enigma2 du plugin n'a pas été vérifié visuellement ; le contrôleur installé et le moteur réel ont été testés par SSH. Le tunnel de test a été arrêté des deux côtés.

## Utilisation

1. Sur le Vu+, ouvrir Extensions → Neo Connect. Vérifier l'IP privée du Vu+, le port OpenWebif existant et la terminaison `adresse:51820`. Pour un premier test sur place, utiliser l'IP LAN du Vu+ ; pour Internet, l'adresse publique joignable du domicile. VERT demande confirmation puis active le moteur ; un nouveau VERT renouvelle le code.
2. Sur Neo Android, conserver la configuration OpenWebif habituelle, puis ouvrir Setup → Neo Connect. Découvrir le certificat sur le réseau local. Comparer **toute** son empreinte SHA-256 avec celle affichée sur le Vu+. Confirmer seulement si elle correspond, puis saisir le code à six chiffres valable deux minutes et un nom d'appareil.
3. Choisir Connecter et accepter l'autorisation VPN Android. Un téléphone/TV Android n'a qu'un VPN actif à la fois. « Échange WireGuard authentifié » signifie un échange cryptographique réel ; utiliser aussi « Tester le Vu+ » pour vérifier OpenWebif.
4. Déconnecter dans Neo pour arrêter le tunnel Android. ROUGE dans le plugin arrête le serveur. EXIT ferme seulement l'écran du plugin ; JAUNE révoque un appareil. Oublier le profil Android n'effectue pas une révocation sur le Vu+.

Le moteur ne démarre pas à l'installation ni automatiquement au redémarrage du Vu+ ou de Neo. Les identités et appareils associés restent enregistrés. Si le menu Extensions ne reconnaît pas immédiatement une nouvelle installation, un rechargement habituel de l'interface Enigma2 peut être nécessaire ; l'installation de cette session n'a pas redémarré le récepteur.

## Accès Orange hors domicile : étape restante

L'opérateur déclaré est Orange et la marque du routeur ZTE ; le pays, le modèle exact et le statut de l'adresse WAN restent inconnus. Sa page locale n'a pas répondu à la lecture HTTP/HTTPS de cette session. Il faut une adresse publique entrante joignable et une redirection **UDP 51820 uniquement** vers l'IP fixe du Vu+. Ne pas publier OpenWebif (82 ici), les ports vidéo 8001/8002 ou l'association HTTPS 9843.

Avec une IPv4 publique dynamique, modifier la terminaison dans Neo pendant que le tunnel est arrêté lorsque l'adresse change ; un nom DNS personnel est aussi accepté. Une IPv6 publique joignable peut être utilisée sous la forme `[adresse]:51820`, sous réserve du réseau et du pare-feu du routeur. Aucune de ces variantes n'a été testée ici. Sous CGNAT sans connectivité entrante, ce serveur direct seul ne peut pas rendre le domicile accessible ; il faut obtenir une adresse entrante de l'opérateur ou changer d'architecture. Le plugin ne contourne pas cette contrainte.

## Architecture et limites

Le Vu+ utilise WireGuard Go et une pile réseau en espace utilisateur : aucun module, périphérique TUN hôte, routage IP, transfert de paquets ou règle iptables n'est ajouté. Dans le tunnel, seuls les ports TCP OpenWebif configuré, 8001 et 8002 de l'IP du Vu+ ont un relais vers les mêmes ports de `127.0.0.1` sur ce récepteur. Les autres machines et ports du LAN ne sont pas accessibles. Cela suppose que les services existants acceptent leurs connexions en boucle locale ; le port 82 a été vérifié sur cet appareil.

Ce relais TCP n'est pas un filtre de méthodes HTTP : un appareil associé qui possède aussi les identifiants OpenWebif pourrait utiliser les capacités de ce service. L'application Neo garde ses appels OpenWebif en lecture seule. Jusqu'à huit clés clientes, révocables séparément ; aucune clé privée cliente ni aucun mot de passe OpenWebif n'est transmis au plugin.

Android génère sa clé privée localement et chiffre le profil avec AndroidKeyStore/AES-GCM. Le tunnel ne route que l'IP du récepteur et seulement le trafic de Neo. Les URL IPTV qui visent directement un fournisseur restent donc directes et peuvent avoir des restrictions d'accès propres au fournisseur. Le débit montant domestique, les ressources tuner et les problèmes vidéo déjà documentés restent applicables. Aucun transcodage n'est ajouté.

L'association utilise HTTPS lié à l'IP privée du Vu+, certificat épinglé après comparaison physique, code à usage unique, délai de deux minutes et trois essais maximum. L'interface HTTPS 9843 est réservée au LAN. Les journaux et rapports ne contiennent pas de codes, de clés privées ou de mots de passe.

## Sources techniques

- [WireGuard embarqué](https://www.wireguard.com/embedding/), [bibliothèque Android officielle](https://github.com/WireGuard/wireguard-android), [exemple officiel de pile utilisateur](https://github.com/WireGuard/wireguard-go/blob/master/tun/netstack/examples/http_server.go).
- [VPN Android](https://developer.android.com/develop/connectivity/vpn).
- [Limites des connexions entrantes avec NAT partagé, RFC 6269](https://www.rfc-editor.org/rfc/rfc6269.html#section-5.2.1).

Instructions de construction et paquet : [receiver-plugin/README.md](receiver-plugin/README.md). Licences Android embarquées dans les assets et licences du moteur dans le paquet IPK.

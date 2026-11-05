# Préparation Neo Connect — Orange Maroc / ZTE F6600P

Identification fournie par l'utilisateur : Maroc, Orange, ZTE F6600P, firmware `ZTEGF660010MA`. La capture contient une adresse WAN de plage publique. L'adresse publique, le numéro de série et la MAC ne sont pas reproduits dans ce document destiné au dépôt public.

## Vérifications locales réalisées

Le PC est sur le LAN `192.168.11.0/24`, passerelle `192.168.11.1`. TCP 80 et 443 répondent ; 8080 et 8443 n'ont pas répondu pendant le contrôle. HTTP redirige vers HTTPS. La page HTTPS de connexion répond HTTP 200 et son titre indique F6600P. Le certificat est auto-signé : une lecture ponctuelle de la page publique a utilisé ce certificat comme ancre locale, sans identifiant et sans désactiver durablement une vérification TLS.

Aucune authentification administrateur, écriture de règle, ouverture automatique UPnP, modification de pare-feu, activation DMZ ou modification du Vu+ n'a été réalisée pendant cette identification. L'inspection du navigateur n'était pas disponible dans cette session. Les noms de menus du firmware Orange ne sont pas encore vérifiés.

## Règle proposée, non appliquée

| Champ | Valeur prévue |
| --- | --- |
| Nom | NeoConnect |
| Protocole | UDP uniquement |
| Port externe début / fin | 51820 / 51820 |
| Hôte LAN | 192.168.11.2 — Vu+ |
| Port interne début / fin | 51820 / 51820 |
| Connexion WAN | Connexion Internet active, à identifier dans l'interface |
| Hôte source WAN | Tous les clients distants, selon les champs du firmware ; ne pas y saisir l'IP WAN du domicile |
| Activation | Seulement après examen de la règle et autorisation de modification du routeur |

Avant application, vérifier que l'IP du Vu+ ne changera pas et qu'aucune règle existante ne monopolise UDP 51820. Une éventuelle réservation DHCP est une modification distincte à examiner. Aucune DMZ, règle TCP, redirection OpenWebif 82, vidéo 8001/8002 ou association 9843 n'est nécessaire à cette proposition.

L'accord précédent autorisait l'installation et le test local du plugin sans changer le routeur. Il ne constitue pas une autorisation de cette nouvelle modification.

## Étapes restantes

1. Le propriétaire ouvre `https://192.168.11.1` et se connecte avec son compte habituel. Orange documente cette adresse et les identifiants de l'étiquette pour l'accès à l'interface ; ne pas deviner un compte de support. Vérifier la présence d'une fonction NAT / redirection de ports. Si elle est absente, demander à Orange si le firmware ou le compte permet cette règle précise ; l'absence du menu n'est pas encore constatée ici.
2. Examiner la règle ci-dessus dans l'interface puis obtenir l'autorisation de l'appliquer. Conserver les réglages Internet, fibre et Wi-Fi existants.
3. Activer Neo Connect sur le Vu+ et renseigner la terminaison `IP_WAN_ACTUELLE:51820` dans le profil Neo Android, tunnel arrêté. Ne pas remplacer l'IP privée OpenWebif de Setup par l'IP publique.
4. Depuis un vrai réseau externe, par exemple une TV connectée au partage 4G/5G d'un téléphone dont le Wi-Fi est coupé, demander un échange WireGuard authentifié puis tester OpenWebif et une chaîne autorisée. Un test depuis le même LAN peut dépendre du NAT loopback et ne valide pas l'accès mobile.

Le plugin était arrêté après son test LAN précédent. Un moteur arrêté ne répondra pas à une tentative de tunnel. WireGuard sur UDP ne se vérifie pas avec un simple testeur de ports TCP ; le critère utile est un véritable échange authentifié.

La plage publique de l'adresse WAN ne suffit pas à certifier l'absence de filtrage ou de traduction supplémentaire par l'opérateur. La comparaison avec une IP de sortie externe n'a pas été exécutée : son contrôle automatique l'a refusée pour éviter la transmission de l'IP domestique à un tiers. Aucun service alternatif n'a été appelé pour contourner ce refus. Le test réel 4G/5G reste non réalisé.

## Références

- [Orange Maroc — Auto-dépannage, accès à l'interface fibre](https://www.orange.ma/Assistance/Equipement-internet/Auto-depannage).
- [ZTE — caractéristiques du ZXHN F6600P](https://www.zte.com.cn/z/C3MpDV.html). Cette fiche produit n'établit pas les menus disponibles sur le firmware Orange.
- [Guide Neo Connect et limites](NEOCONNECT.md).

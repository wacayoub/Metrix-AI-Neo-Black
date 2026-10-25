# Logos d’équipes automatiques et fréquence satellite

Les deux skins gardent la fréquence, la polarisation et le débit symbole réels
dans la ligne technique de l’infobar. NEO place cette colonne entre REC et
TIMESHIFT ; Advanced la conserve après la position orbitale. Une fréquence
disponible reste affichée même si le débit symbole n’est pas exposé. Ces données
proviennent du frontend Enigma2 ; aucune fréquence de démonstration n’est figée.

## Source et reconnaissance

Le helper facultatif utilise l’[API officielle TheSportsDB](https://www.thesportsdb.com/documentation)
et son [champ d’écusson strBadge](https://www.thesportsdb.com/docs_api_examples.php).
Il lit le titre EPG, puis à défaut la description courte, puis quelques lignes
de la description longue. Les formes explicites `A - B`, `A – B`, `A vs B`,
`A v B`, `A contre B` et `A / B` sont reconnues. Un titre clair a priorité sur
les matchs historiques cités dans le résumé.

La première version cible le football. Un contexte basket, rugby, hockey,
tennis, handball ou volley n’obtient pas par défaut un écusson de football.
Les accents et la casse sont normalisés ; les qualificatifs Women, B ou U21
restent distincts. FC Barcelone/Barcelone et PSG/Paris SG ont des alias explicites.
Les autres noms doivent correspondre au nom principal ou à un alias du
fournisseur. Aucun premier résultat approximatif ou rapprochement partiel
n’est accepté. La couverture dépend des données et limites de l’API.

La paire n’est publiée que lorsque les deux équipes ont des identifiants
distincts et deux images disponibles. Les deux logos et VS sont actualisés
ensemble. Un changement de programme ou de noms d’équipes invalide immédiatement
la paire précédente, même si le titre générique reste « Football ».
Les paires locales sous licence associées à un événement exact gardent priorité.

## Réglages prévus sur le récepteur, sans installation effectuée

Dans **Préférences NEO → Images EPG**, les deux profils proposent :

- **Logos automatiques des équipes** : désactivé par défaut ; indépendant des
  affiches de programmes et du Smart EPG Advanced.
- **Autoriser TheSportsDB pour les logos** : consentement séparé de la météo.
  Désactivé par défaut ; le cache existant peut être utilisé hors ligne.
- **Clé API TheSportsDB** : clé publique de développement `123` par défaut,
  remplaçable par une clé personnelle numérique. L’éditeur masque la clé ;
  aucune URL contenant une clé n’est journalisée. Le fichier de préférences
  propre au profil reste un JSON local, sans chiffrement.

La touche verte enregistre le profil puis demande au helper de relire ses
réglages. Les emplacements de logos peuvent ainsi être activés sans redémarrer
Enigma2. Rouge/EXIT annule ; jaune reste temporaire ; bleu utilise les valeurs
déjà enregistrées. Sans helper installé, les options ne provoquent aucun accès
réseau et les emplacements restent masqués.

## Travail en arrière-plan et cache

Les renderers ne font ni téléchargement ni lecture de cache disque. Ils
placent seulement une demande en mémoire. Un worker Twisted reçoit des chaînes
de noms et le profil, jamais un objet de service ou un objet EPG natif.
Un seul travail s’exécute à la fois ; la file ne retient que le dernier événement
par profil et espace les départs de 20 secondes. La même demande home/away est
dédupliquée. Un échec est mémorisé 30 minutes pour éviter les requêtes à chaque
rafraîchissement d’écran. Un rappel différé sert uniquement une demande en attente.

Seuls les noms normalisés des équipes sont transmis, sans référence de chaîne,
horaire, bouquets, EPG complet ou configuration d’un autre plugin. HTTPS vérifié,
hôtes limités à TheSportsDB et son CDN `r2`, redirections contrôlées, timeout
de 5 s par requête, JSON limité à 256 Kio et PNG à 512 Kio/1024 × 1024 px.
Le décodage des images reste asynchrone via ePicLoad.

Le cache futur est dédié à `/tmp/metrix-neo-cache/<profil>/teams`. Les métadonnées
et PNG partagent une limite ; météo et équipes se répartissent chacun la moitié
du budget global du profil. Les images de logos expirent après `poster_ttl`
(7 jours par défaut), avec réutilisation du cache valide hors ligne ou en cas
d’indisponibilité. Aucun fichier utilisateur extérieur au cache n’est nettoyé.
Le cache temporaire ne survit pas nécessairement à un redémarrage du récepteur.

## Droits et limites de validation

Source affichée dans les aides : TheSportsDB.com. Les [conditions du fournisseur](https://www.thesportsdb.com/docs_terms_of_use.php)
et les droits des logos s’appliquent ; un abonnement API ne transfère pas les
droits d’un club. Aucun logo commercial téléchargé n’est livré dans les IPK ou
le ZIP source. Les logos ne sont ni recolorés ni transformés par le fournisseur
du skin ; seul leur affichage respecte la taille et le ratio de l’emplacement.

Tests locaux : extraction, identités exactes, échec/réseau absent, cache,
requêtes bornées, activation indépendante des affiches, zapping et réponses
tardives. Ils utilisent des réponses simulées et des PNG transparents originaux.
La documentation officielle a été consultée. Une vérification réseau distincte
sur le PC a reconnu Real Madrid (133738) et Barcelona (133739) puis vérifié en
mémoire leurs deux PNG petits formats, de 57 824 et 37 141 octets. Aucun de ces
logos n’a été enregistré dans le projet. La preuve figure dans
`reports/team-provider-live.json`. Ce contrôle ne certifie pas toute la base
ni le rendu sur OpenATV 8.0.1. Aucun accès, changement ou test sur le Vu+ n’a été effectué.

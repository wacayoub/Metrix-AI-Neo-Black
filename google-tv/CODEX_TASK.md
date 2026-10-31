# Spécification Codex : Metrix NEO AI Google TV

## Contexte
Vu+ Zero 4K sous OpenATV 8.0.1 et thème actuel Metrix NEO. Nouveau projet : APK Google TV nouvelle génération, plus moderne et avec une IA optionnelle, mais toujours fidèle au thème réel.

## Plan en étapes
1. Auditer les sources disponibles dans `dual-skins/skins/MetrixNEO`, les assets et les documents de fidélité; distinguer skin en repo vs skin actif sur matériel. Ne pas supposer l'installation.
2. Importer les sources ZIP alpha fournies via ChatGPT, réviser et faire passer Android Gradle Sync, puis construire une APK debug reproductible. Stack conseillée : Kotlin + Jetpack Compose for TV + Media3 + OpenWebif.
3. Recréer l'accueil 5 tuiles, liste des chaînes et EPG, avec picons et focus TV, écrans de paramètres et infobar réellement mini.
4. OpenWebif en lecture seule : découvrir bouquets, services, EPG, picons et stream .m3u; gérer auth de façon sûre. Aucun contrôle ou changement automatique du Vu+.
5. Lecteur Android : Media3 ExoPlayer et sélection pistes audio/sous-titres disponibles; buffering, recovery réseau et gestion robuste d'erreurs; ne pas promettre Dolby/4K/HDR non disponibles.
6. Intégrations de phase 2 après compatibilité vérifiée : IPToSat Pro en pont côté Vu+, fallback SAT → IPTV uniquement pour flux autorisés, EPGManager, diagnostique AI local, personnalisation et profils.
7. Tests : émulateur Android TV, vraie Google TV, coupure réseau, 20+ lignes, télécommande, 1080p/2160p, tunnel privé si accès distant et limites des ressources tuner.

## Contraintes visuelles obligatoires
- Palette NEO bleu nuit, textures et icônes réelles reprises légalement des sources, écran non surchargé.
- Infobar sans horloge, nom de chaîne au-dessus, émission en cours et **un seul** programme suivant.
- Les 14 indicateurs SAT/IPTV restent aux mêmes places et aux mêmes dimensions; désactiver si signal non mesuré.
- Proposer les changements de style avancé de façon réversible, sans toucher au Vu+.

## Livraison attendue
Code source Android dans `google-tv/`, README et CI GitHub Actions livrant `app-debug.apk`; preuves de build; fiches de fonctionnalités réelles vs simulées; sans secrets ni images commerciales non autorisées.

## À ne pas faire
Ne pas modifier, déployer, installer, redémarrer ou lancer de commandes système sur le Vu+. Ne pas exposer OpenWebif en HTTP public. Ne pas présenter les maquettes comme un résultat compilé.

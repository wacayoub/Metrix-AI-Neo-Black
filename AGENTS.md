# Codex — Metrix NEO AI Google TV

Ce fichier s'applique uniquement à la branche `codex/metrix-neo-ai-google-tv`.

Mission active : construire une APK Google TV native, à partir du thème Metrix NEO réellement actif sur Vu+ Zero 4K / OpenATV 8.0.1. Lire `google-tv/CODEX_TASK.md` avant de coder.

RÈGLES :
1. Ne jamais installer ni modifier quoi que ce soit sur le Vu+; connexion SSH éventuelle en lecture seule seulement après autorisation d'accès adéquate.
2. Conserver le projet Enigma2 existant intact. Tout le code Android doit être dans `google-tv/`.
3. Reprendre l'identité graphique MetrixNEO à partir de `dual-skins/skins/MetrixNEO/`, `dual-skins/docs/INFOBAR_FIDELITY.md` et `dual-skins/previews/`. Le thème actif sur le décodeur demeure la source de vérité finale.
4. Fonctionnalité d'abord : Android TV D-pad, OpenWebif READ ONLY, ExoPlayer Media3, listes, EPG, statut réel des 14 indicateurs.
5. Toutes les fonctions non implémentées doivent être signalées comme telles. Pas de fausse IA ni de flux de démonstration présenté comme live.
6. Pas de credentials en dur, pas d'exposition OpenWebif sur Internet; toute intelligence cloud doit être opt-in.
7. CI pour builder APK debug et fournir un rapport honnête. N'affirmer aucun test matériel qui n'a pas été réalisé.

La conversation a également produit un ZIP source local intitulé `MetrixNEO_AI_GoogleTV_Alpha_Source.zip` à importer dans Codex si disponible. La branche GitHub contient les consignes de mission et sert de point de départ collaboratif.

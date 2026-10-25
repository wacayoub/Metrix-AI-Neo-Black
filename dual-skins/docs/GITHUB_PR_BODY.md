# Ajouter les deux skins indépendants Metrix NEO et Metrix NEO Advanced

Le projet existant applique des palettes à MyMetrixLite. Cette intégration
ajoute dans `dual-skins/` deux identités de skins Full HD sélectionnables
séparément, leur runtime commun et un helper optionnel. Les menus, listes,
infobars, guides, paramètres et dialogues reprennent les références et la
palette Metrix NEO validées visuellement pour les deux thèmes.

L’intégration ajoute uniquement `dual-skins/` et
`.github/workflows/metrix-neo-dual-skins.yml`. Les anciens plugins, scripts,
manifestes et feeds restent inchangés. Les quatre IPK n’ont aucun script de
maintenance et n’activent pas de skin. Météo et logos distants sont désactivés
sans consentement ; EPGManager, IPToSatPro, bouquets et mappings ne sont pas
modifiés.

Validation locale : 152 tests Python réussis, contrôles XML et ressources,
inspection des quatre IPK et reconstruction déterministe des IPK/ZIP sources.
Le patch binaire est vérifié dans les deux sens sur le commit
`18ec2cfd3d9e97fc41fb889d81bc695961a5e6eb`, également confirmé comme HEAD de
`main` le 25 octobre 2026. La CI récupère les deux sources publiques aux commits
épinglés avant d’exécuter ces vérifications. Rapports : `dual-skins/reports/` ;
limites : `dual-skins/docs/DELIVERY_REPORT.md`.

La CI distante n’a pas été exécutée pendant la préparation. Aucun test
matériel, accès, installation ou redémarrage du Vu+ ; compatibilité exacte du
build OpenATV 8.0.1 et rendu Enigma2 encore à contrôler avec autorisation
distincte. Les aperçus sont des simulations, les extensions tierces peuvent
garder leurs fenêtres natives et les enrichissements dépendent des données.

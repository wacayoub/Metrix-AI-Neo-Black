# Sony BRAVIA KD-43X75K — Android TV 14

TV IP confirmée par l'utilisateur : 192.168.11.188 (réseau LAN).
Vu+ Zero 4K OpenATV 8.0.1 IP locale précédente : 192.168.11.2.

## App
- minSdk 26, Android TV leanback launcher, D-pad, 1080p UI, rendu adapté à la TV 4K.
- L'adresse de la TV est une cible d'installation et ne doit jamais remplacer l'adresse du Vu+ dans OpenWebif.
- L'APK ne contrôle aucun menu de la TV avant ADB autorisé.
- Port ADB TCP 5555 actuellement refusé; ne pas contourner. Android TV 14 peut utiliser Wireless debugging avec code d'association et port variable. Obtenir les valeurs à l'écran de la TV, puis permission explicite.
- Installation ADB seulement après validation de la signature de l'APK.
- Ne jamais installer ou modifier de plugins, skin ou configurations sur le Vu+.

## Statut
Code source pré-alpha ; build GitHub Actions à confirmer ; tests sur vraie Sony non effectués.

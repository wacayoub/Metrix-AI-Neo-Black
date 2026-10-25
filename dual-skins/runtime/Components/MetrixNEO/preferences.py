"""Labels and descriptions shared by the real preferences and offline previews."""
from Components.MetrixNEO.settings import PROFILES

KEY_LABELS = {"key_red": "Annuler", "key_green": "Enregistrer",
              "key_yellow": "Défauts NEO", "key_blue": "Actualiser"}
NAVIGATION = "MENU : catégorie · OK : modifier · ← / → : valeur · EXIT : annuler"
CATEGORIES = (("presentation", "Présentation"), ("weather", "Météo"),
              ("images", "Images EPG"), ("smart", "Smart EPG"),
              ("diagnostics", "Diagnostics"), ("cache", "Cache"))
# key, label, editor type, category, contextual help
OPTIONS = (
    ("compact", "Liste Advanced compacte", "bool", "presentation", "Disposition compacte de la liste Advanced. Prise en compte à la prochaine ouverture de la liste, en mode de modèles natifs."),
    ("large_text", "Agrandir le texte de cet aperçu", "bool", "presentation", "Agrandit uniquement l’exemple à droite. Les polices des autres écrans ne sont pas modifiées."),
    ("weather", "Afficher la météo sur trois jours", "bool", "weather", "Nécessite le helper, les coordonnées et le consentement réseau. Sans données, la météo reste masquée."),
    ("latitude", "Latitude météo", "text", "weather", "De −90 à 90. Laisser vide si non configurée. OK ouvre le clavier ; utiliser un point pour les décimales."),
    ("longitude", "Longitude météo", "text", "weather", "De −180 à 180. Laisser vide si non configurée. OK ouvre le clavier ; utiliser un point pour les décimales."),
    ("weather_label", "Nom du lieu météo", "text", "weather", "Libellé libre de 48 caractères maximum ; ne remplace pas les coordonnées."),
    ("network_consent", "Autoriser le réseau pour la météo", "bool", "weather", "Autorise Open-Meteo en arrière-plan via le helper. Désactivé par défaut. Open-Meteo.com · CC BY 4.0 · usage non commercial."),
    ("posters", "Afficher les images EPG locales", "bool", "images", "Nécessite le helper et un catalogue local sous licence dans /media/hdd/metrix-neo/artwork. Chaque image suit l’événement sélectionné ; aucune image correspondante signifie un repli texte/picon."),
    ("club_logos", "Logos automatiques des équipes", "bool", "images", "Nécessite le helper. Détecte les deux noms du match de football dans l’EPG et affiche leurs écussons depuis le cache. Sans paire fiable, les logos restent masqués. Indépendant des images de programmes."),
    ("club_network_consent", "Autoriser TheSportsDB pour les logos", "bool", "images", "Recherche les noms des équipes auprès de TheSportsDB en arrière-plan. Seuls ces noms sont envoyés ; ni référence de chaîne ni EPG complet. Désactivé par défaut ; sans réseau, réutilise le cache disponible. Source : TheSportsDB.com ; droits des logos conservés."),
    ("sports_api_key", "Clé API TheSportsDB", "password", "images", "Clé publique de développement 123 par défaut, remplaçable par votre clé personnelle. Les limites et conditions du fournisseur s’appliquent. La clé est masquée à l’écran et n’est jamais journalisée."),
    ("smart_epg", "Afficher les saisons et épisodes explicites", "bool", "smart", "Enrichissement local des écrans Advanced : uniquement les saisons et épisodes explicitement présents dans l’EPG. Aucune IA distante."),
    ("diagnostics", "Afficher les diagnostics contextuels", "bool", "diagnostics", "Messages conditionnels dans la seconde infobar Advanced. Les états inconnus restent masqués ; aucune action sur les flux ou les bouquets."),
    ("cache_mb", "Limite du cache local (Mo)", "integer", "cache", "De 1 à 128 Mo, 32 par défaut. Limite du cache géré par le helper ; n’efface ni l’EPG natif ni les fichiers des autres plugins."),
)


def options_for(profile, category=None):
    if profile not in PROFILES:
        raise ValueError("Unknown skin identity")
    return tuple(item for item in OPTIONS if (category is None or item[3] == category)
                 and (item[0] not in ("compact", "smart_epg", "diagnostics") or profile == "MetrixNEOAdvanced"))


def categories_for(profile):
    return tuple((key, label) for key, label in CATEGORIES if options_for(profile, key))


def preview_text(large=False):
    return ("Aperçu agrandi" if large else "Aperçu") + ":\nÉmission · Programme\nBleu nuit · sélection bleue\n\nModifications temporaires.\nVert : enregistrer ce skin.\nRouge / EXIT : annuler."

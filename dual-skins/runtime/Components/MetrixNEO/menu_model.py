"""Reference-approved menu identities, captions and icon names."""
MENU_META = {
    "plugin_selection": ("Plugin Browser", "Installer et gérer\nles plugins", "plugins"),
    "setup": ("Setup", "Paramètres\ndu système", "setup"),
    "timermenu": ("Timers", "Programmations", "timers"),
    "shutdown": ("Standby / Restart", "Éteindre ou redémarrer", "power"),
    "information": ("Information", "Infos système et image", "info"),
    "neo_channels": ("Éditeur de chaînes", "TV / Radio / Favoris", "channels"),
    "neo_files": ("Gestionnaire de fichiers", "Parcourir et gérer les fichiers", "files"),
    "movie_selection": ("Enregistrements", "Voir vos enregistrements", "recordings"),
    "software_manager": ("Gestionnaire de logiciels", "Installer des extensions", "software"),
    "network": ("Réseau", "Configuration réseau", "network"),
    "neo_settings": ("Thème & Skin", "Personnalisation", "theme"),
    "neo_tools": ("Outils", "Maintenance et diagnostics", "tools"),
}
NEO_ORDER = ("plugin_selection", "setup", "timermenu", "shutdown", "information")
ADVANCED_ORDER = ("plugin_selection", "setup", "neo_channels", "timermenu", "neo_files", "movie_selection", "software_manager", "network", "information", "neo_settings", "neo_tools", "shutdown")

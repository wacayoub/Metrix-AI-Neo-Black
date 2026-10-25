# Matrice des écrans et des données

Inventaire établi sur Enigma2 branche `8.0`, commit dans `sources.lock.json`.
Il n’identifie pas le build installé de l’utilisateur. Tous les écrans ci-dessous
sont présents dans chaque skin XML ; le rendu matériel reste à contrôler.

| Écran natif / identité | NEO | Advanced | Sources / composants | Repli |
|---|---|---|---|---|
| Menumainmenu / menu_mainmenu | 5 tuiles avec icônes | 4 colonnes × 3 lignes et photo gauche | Menu.menu, indexNames Image/Text/Description, callbacks natifs | Fonction absente explicitement indisponible ; MENU ouvre toutes les entrées natives |
| Menu | Liste verticale | Liste verticale | menu, description, key_* | Conservation des sous-menus natifs |
| ChannelSelection, Default/PIG/Full | Modèle 45 px / 20 lignes | Modèle 38 px / 20 lignes avec marges | list, ServiceEvent, templates serviceList, panneau adaptatif selon image | Ancien ServiceListLegacy : paramètres natifs conservés, densité exacte non garantie |
| InfoBar | Compacte, bord inférieur à zéro | Compacte et infos techniques | session.CurrentService, Event_Now/Next, FrontendStatus, RecordState | Signal inconnu/IPTV masqué, aucune estimation AGC |
| SecondInfoBar | Description développée | Description et diagnostic | Event_Now, CurrentService | Texte si aucune métadonnée |
| GraphicalEPG / GraphicalEPGPIG / GraphicalInfoBarEPG | Timeline, synopsis en haut | Timeline et détail latéral | list, timeline_text, timeline0..5, timeline_now, Event, lab1 | Pas de PiG injecté ; navigation/timers natifs |
| EPGSelection / EPGSelectionMulti / QuickEPG | Liste et détail | Liste et détail | list, Event, lab1 | Fonctions et raccourcis natifs |
| EventView / EventViewSimple / InfoBarEventView | Détail texte | Détail, image facultative et prochains x2 | channel, datetime, duration, epg_description, Event, Service | Aucun horaire inventé ; scroll natif |
| ChannelContextMenu / EventViewContextMenu / EventViewContextMenuChoiceBox | Fenêtre 15 lignes, icône et actions natives | Image EPG facultative et aide de l’action | menu/list / ChoiceList, sélection csel en lecture seule | Vidéo en cours autour de la fenêtre ; aucun remplacement de l’image EPG par cette vidéo |
| Setup et écrans dérivés | Options natives et description | Options natives et description | config, footnote, description, key_* | Logique de validation native préservée |
| MetrixNEOSettings | Préférences NEO | Préférences Advanced | ConfigList, aperçu temporaire, Settings | Annuler ne touche aucun fichier ; vert sauvegarde le profil NEO uniquement |
| AudioSelection | Audio et sous-titres natifs | Idem | config, streams, switchdescription, key_* booléens | Codecs de piste sélectionnée, pas de déduction Atmos |
| Subtitles | Paramètres natifs | Idem | config | Écran audio/sous-titres natif si sa skinName diffère |
| MessageBox / ChoiceBox | Dialogues sobres | Idem | icon, text, list | Icônes locales originales ; choix natifs |
| Volume / Mute | Barre simple | Idem | Volume / écran conditionnel natif | Aucun état muet permanent |
| RecordTimerOverview / SchedulerOverview / ConflictTimerOverview / TimerOverview | Liste native | Idem | timerlist, description, key_* | Éditions/confirmations natives |
| MovieSelection | Liste native | Idem | list, freeDiskSpace, waitingtext | Aucune opération sur les fichiers par le skin |
| PluginBrowser | Liste/grille native | Idem | pluginList, pluginGrid, quickselect, description | Plugins manquants non installés automatiquement |
| InputBox / VirtualKeyboard / VirtualKeyBoard / Console | Saisie/clavier/texte | Idem | text, input, prompt, list, locale | Clavier arabe et glyphes à vérifier sur cible |

Les autres fenêtres natives/plugins utilisent le repli Enigma2 embarqué. Elles
ne sont pas toutes redessinées. Autotimer, NetworkOverview et fenêtres spécifiques
aux plugins restent accessibles mais leur harmonisation visuelle exhaustive n’est
pas livrée comme validée. La vue EPG verticale native est également en repli.

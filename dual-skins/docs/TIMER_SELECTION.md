# Programmations — revue des deux thèmes

Audio et sous-titres sont validés visuellement par l’utilisateur pour NEO et
Advanced. Les programmations sont également validées visuellement par
l’utilisateur pour les deux thèmes, sans validation matérielle ni autorisation
d’installation.

Les fenêtres natives `TimerOverview`, `RecordTimerOverview`, `SchedulerOverview`
et `ConflictTimerOverview` gardent les composants et callbacks OpenATV.
La présentation utilise le bleu nuit, les cadres et les dégradés du profil NEO,
des pictogrammes d’état originaux et des polices explicites prises en charge
par `TimerListBase`. Huit entrées à deux niveaux sont visibles : titre et chaîne,
puis état, position orbitale et horaire pour les enregistrements ; type et fin
d’action pour les planifications système. Les données réelles restent natives.

Le sélecteur de revue montre : planifié, en cours, désactivé, terminé, vide,
planification système et conflit. Les rangées, programmes, dates et états sont
illustratifs. Aucun inventaire du récepteur n’a été lu et aucune tâche n’a été
créée. Le simulateur ne remplace pas le moteur Enigma2.

Les touches affichent leurs sources natives et se masquent lorsqu’elles sont
vides. Rouge : supprimer ou arrêter ; vert : ajouter, absent en conflit ; jaune :
activer ou désactiver selon l’état ; bleu : nettoyage si disponible, ou ignorer
un conflit. INFO garde le journal natif, OK l’édition, EXIT la fermeture, selon
le keymap audité. Aucune action n’est appelée par la préparation des aperçus.

Les formulaires d’ajout et d’édition gardent le `Setup` natif déjà thémé ; cette
revue ne les présente pas comme une nouvelle interface. Les composants AutoTimer
tiers restent indépendants. Aucun timer, configuration, bouquet ou plugin n’est
modifié sur le Vu+. La validation matérielle reste à effectuer avec autorisation.

# Pièges WSLg pour une fenêtre egui

| Symptôme | Cause | Remède |
|---|---|---|
| Texte minuscule ou flou | mise à l'échelle Windows (125 %, 150 %) transmise ou non à Wayland | `ctx.set_pixels_per_point(…)` réglable dans la configuration ; tester `WINIT_X11_SCALE_FACTOR` si X11 |
| Copier ne met rien dans le presse-papiers Windows | passerelle presse-papiers WSLg capricieuse ; `arboard` sans backend | utiliser `ctx.copy_text(…)` (egui gère la plateforme) ; vérifier dans une autre appli Linux d'abord |
| Un clic sur un lien ne fait rien | `xdg-open` absent ou mal configuré | la crate `webbrowser` utilise `wslview` (paquet `wslu`) ; `$BROWSER` respecté ; afficher « Navigateur indisponible » dans le statut sinon |
| `libEGL warning: …` au démarrage | pilotes du compositeur WSLg | bénin ; ne pas « corriger » |
| `install_image_loaders` warn | `egui_commonmark` sans chargement d'images | bénin si les images ne sont pas souhaitées |
| Première image lente (1 à 2 s) | compilation des shaders `glow` | normal ; afficher un titre dès la première image |
| Fenêtre qui ne s'ouvre pas | `DISPLAY` / `WAYLAND_DISPLAY` absents (session SSH) | lancer depuis le terminal WSL ouvert par Windows Terminal, pas via SSH |
| Raccourcis clavier avalés | Windows intercepte certaines combinaisons | documenter des raccourcis simples (`Ctrl+Entrée`) et tester |

Vérification de lancement sans clic : `timeout 6 cargo run -p <gui> -- --config /tmp/x/config.json …`
doit renvoyer **124** (la fenêtre est restée ouverte jusqu'au timeout) sans panique dans le journal.

Sources : <https://github.com/microsoft/wslg> (README, section Known issues), <https://docs.rs/webbrowser/latest/webbrowser/> (vérifiées le 2026-11-25).

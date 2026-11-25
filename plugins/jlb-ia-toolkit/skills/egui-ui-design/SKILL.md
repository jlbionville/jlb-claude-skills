---
name: egui-ui-design
description: >
  Use when designing or reviewing a desktop window built with egui / eframe (Rust): layout
  with side, central and status panels, tabs, scroll areas, theme and three-color palette,
  contrast and readability, keeping the UI responsive during long calls, state kept testable
  without egui, or running under WSL 2 / WSLg. Déclencheurs FR : « panneau », « onglet »,
  « thème », « palette », « contraste », « la fenêtre se fige », « egui », « eframe »,
  « WSLg », « maquette d'écran », « légende / infobulle ».
---

# Concevoir une fenêtre egui lisible et testable

## Vue d'ensemble

egui est **immédiat** : à chaque image, le code redessine toute l'interface à partir de
l'état. Deux conséquences qui guident tout le design :

1. L'état est une structure Rust ordinaire ; si elle ne dépend pas d'egui, elle se teste
   sans fenêtre.
2. Un appel long dans `update()` fige la fenêtre : tout travail lent part dans un thread et
   revient par un canal.

## Quand l'utiliser

- Ajouter un écran, un onglet, un bouton, une boîte de dialogue.
- Choisir ou corriger des couleurs, la police, la densité.
- Une fenêtre qui gèle, qui ne se rafraîchit pas, ou qui repeint en continu.
- Un rendu étrange sous WSLg (DPI, presse-papiers, liens).
- Ne pas l'utiliser pour : le web (`eframe` + wasm a ses propres contraintes), les jeux.

## Architecture : état, panneaux, intents

```
state.rs      AppState (aucun `use egui`) : données, statuts, méthodes testées
panels/*.rs   fn show(ui, &mut AppState, &mut Actions)   → dessine, remplit `Actions`
app.rs        impl eframe::App : draine le canal, dessine, agit sur `Actions`
workers.rs    thread::spawn + mpsc : appels longs, résultat en `WorkerEvent`
theme.rs      Palette ↔ egui::Color32, style global
```

- Un panneau **ne fait rien** : il dessine et renvoie des intents (`actions.send = true`).
  `app.rs` décide et déclenche. Les tests portent sur `AppState` et ses transitions.
- L'état d'une opération en cours est explicite : `enum Busy { Idle, Asking, Refreshing }`.
  Les boutons se désactivent avec `ui.add_enabled(busy == Busy::Idle, …)`.
- Les réglages modifiables ont une **copie éditable** dans l'état (`inputs`), écrite sur
  disque seulement au clic « Enregistrer ».

## Disposition

```rust
egui::SidePanel::left("navigation").exact_width(166.0).resizable(false).show(ctx, |ui| {
    ui.heading("Mon appli");
    for tab in Tab::ALL {                      // boutons sélectionnables = onglets
        if ui.add(egui::Button::selectable(self.tab == tab, tab.label())).clicked() { self.tab = tab; }
    }
    ui.with_layout(egui::Layout::bottom_up(egui::Align::Min), |ui| { /* Quitter */ });
});
egui::TopBottomPanel::bottom("status").show(ctx, |ui| { /* spinner + statut tronqué */ });
egui::CentralPanel::default().show(ctx, |ui| {
    egui::ScrollArea::vertical().id_salt(self.tab.label()).show(ui, |ui| match self.tab { … });
});
```

- **Ordre** : les panneaux latéraux et bas d'abord, le central en dernier (il prend le reste).
- `ScrollArea` dans le central, avec un `id_salt` par onglet : la position de défilement
  ne saute pas d'un onglet à l'autre.
- Textes longs : `egui::Label::new(…).truncate()` et le texte complet en `on_hover_text`.
- Fermer proprement : `ctx.send_viewport_cmd(egui::ViewportCommand::Close)`, jamais
  `std::process::exit` (les `Drop` doivent s'exécuter : processus enfants, fichiers).

## Attente sans gel

```rust
// Lancement : cloner, `move` dans le thread, résultat par canal.
let sender = self.sender.clone();
std::thread::spawn(move || { let _ = sender.send(WorkerEvent::Done(work())); });
// Chaque image : drainer sans bloquer, puis demander une image bientôt.
while let Ok(event) = self.receiver.try_recv() { self.state.handle_event(event); }
if self.state.busy != Busy::Idle { ctx.request_repaint_after(Duration::from_millis(100)); }
```

- `try_recv`, jamais `recv` : la fenêtre ne doit pas attendre.
- `request_repaint_after` seulement **pendant** un travail : egui ne repeint sinon qu'à
  l'événement, et une boucle de repaint permanente chauffe la machine.
- Afficher `ui.spinner()` et le statut dans la barre du bas ; désactiver les boutons.

## Couleurs et lisibilité

- Trois couleurs suffisent : **libellés**, **zones de saisie**, **zone de réponse** ;
  tout le reste vient du thème (`ctx.set_visuals`, `ctx.set_style`).
- Contraste texte / fond : viser **4,5:1** (WCAG 2.2, AA) pour le texte courant, 3:1 pour
  les gros titres. Calcul : luminance relative des deux couleurs, `(L1 + 0,05) / (L2 + 0,05)`.
- Garder les couleurs en `#RRGGBB` dans la configuration, les valider à la lecture
  (`parse_hex_color`), remplacer une couleur invalide par le défaut **avec un
  avertissement**, jamais un plantage.
- Polices : egui embarque Ubuntu-Light (proportionnelle) et Hack (monospace). Les
  caractères hors de leur table (ex. l'espace fine insécable U+202F) s'affichent en carré ;
  utiliser U+2009 comme séparateur de milliers, rendu comme une demi-espace par epaint.
- Thème clair/sombre : tester les deux ; un `Color32::WHITE` codé en dur casse le sombre.

## Maquette avant le code

Dessiner l'écran en texte avant d'ouvrir `panels/` : colonnes, boutons, états désactivés.

```
┌ Mon appli ─┬──────────────────────────────────────────┐
│ Question   │ Fournisseur [OpenAI ▾]  Modèle [gpt-… ▾] ↻ │
│ Contexte   │ Mis à disposition le … · contexte 1 M …    │
│ Sessions   │ ┌ Question ───────────────────────────┐   │
│ ───────    │ │                                     │   │
│ Jetons     │ └─────────────────────────────────────┘   │
│ Apparence  │ [Envoyer] [Copier] [Enregistrer] [Publier▾]│
│            │                                           │
│ [Quitter]  │                                           │
├────────────┴──────────────────────────────────────────┤
│ ◌ Appel en cours…                                     │
└───────────────────────────────────────────────────────┘
```

## Pièges WSLg

Voir `references/wslg-pitfalls.md` : DPI et mise à l'échelle, presse-papiers, ouverture
des liens (`wslview`), Wayland vs X11, avertissements `libEGL` bénins, temps de première
image.

## Erreurs courantes

- `use egui` dans `state.rs` : l'état n'est plus testable à sec.
- Emprunter `state` dans la fermeture d'un `ComboBox` qui modifie déjà `state.model` :
  calculer les textes **avant** la fermeture.
- `recv()` ou `thread.join()` dans `update()`.
- Chaîne de statut non tronquée qui élargit la fenêtre.
- Même `id_salt` pour deux `ScrollArea` ou deux `ComboBox` : egui avertit « same ID ».

## Sources (vérifiées le 2026-11-25)

- egui 0.33 (docs.rs) : <https://docs.rs/egui/0.33.3/egui/>, en particulier
  `containers::panel`, `ScrollArea`, `Context::request_repaint_after`, `ViewportCommand`.
- eframe : <https://docs.rs/eframe/0.33.0/eframe/>
- Démo interactive egui : <https://www.egui.rs/>
- WCAG 2.2, critère 1.4.3 (contraste minimum) : <https://www.w3.org/TR/WCAG22/#contrast-minimum>
- WSLg (Microsoft) : <https://github.com/microsoft/wslg>

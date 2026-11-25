---
name: rust-dev
description: >
  Use when writing or reviewing Rust in a multi-crate Cargo workspace (clean architecture,
  ports and adapters), adding a port or an adapter, handling errors with thiserror and exit
  codes, testing adapters on JSON fixtures without network, using threads with mpsc, reading
  clippy -D warnings errors, or preparing a commit (fmt, clippy, test --locked). Déclencheurs
  FR : « ajoute un port / un adaptateur », « cargo clippy refuse », « edition 2024 », « tester
  sans réseau », « fixture », « thread + canal », « où mettre ce code dans le workspace ».
---

# Développer en Rust dans un workspace en clean architecture

## Vue d'ensemble

Un workspace Cargo découpe le programme en crates ; la direction des dépendances est
**imposée par le compilateur** : une crate ne voit que ce que son `Cargo.toml` déclare.
C'est l'outil de la clean architecture en Rust : le domaine ne peut pas appeler
l'infrastructure, même par accident.

```
crates/
  <app>_core/    domaine + cas d'usage + ports (traits)  → dépend de serde, thiserror
  <app>_infra/   adaptateurs (HTTP, fichiers, processus) → dépend de core
  <app>_gui|cli/ interface                                → dépend de core et infra
```

## Quand l'utiliser

- Ajouter une fonctionnalité qui parle à l'extérieur (API, fichier, processus).
- Un `cargo clippy -- -D warnings` rouge que l'on ne comprend pas.
- Choisir où mettre une constante, un type d'erreur, un test.
- Ne pas l'utiliser pour : du Rust embarqué, `no_std`, de l'`async` (tokio) : ce guide
  suppose des threads standard et `std`.

## Checklist « nouveau port + adaptateur »

| Étape | Où | Quoi |
|---|---|---|
| 1 | `core/src/domain/` | Les types échangés (`struct`, `enum`), leur `validate()`, aucune dépendance technique |
| 2 | `core/src/application/ports.rs` | Le `trait` (contrat) : `fn action(&self, input: &Input) -> Result<Output, AppError>` ; `Send + Sync` si des threads l'appellent |
| 3 | `core/src/application/<cas>.rs` | Le cas d'usage : valide, appelle le port, ne connaît que le trait |
| 4 | `core/src/constants.rs` | Chemins d'API, noms de fichiers, valeurs par défaut : **aucun littéral ailleurs** |
| 5 | `infra/src/<adapter>/mod.rs` | `impl Port for Adapter` mince ; la logique pure dans des fonctions `build_body`, `parse_reply`, `map_status` |
| 6 | `infra/tests/fixtures/*.json` | Réponses réelles anonymisées ; tests `include_str!` sur les fonctions pures |
| 7 | `gui|cli` | Construit l'adaptateur, le passe au cas d'usage sous forme de `Box<dyn Port>` ou `Arc<dyn Port>` |

Le secret (clé d'API) est **passé à chaque appel** du port, jamais stocké dans
l'adaptateur : une clé saisie en session est utilisable immédiatement et rien ne traîne
dans un `Debug`.

## Erreurs : un type, un code

```rust
#[repr(i32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorCode { General = 1, Configuration = 3, Validation = 21, Network = 31 }

#[derive(Debug, thiserror::Error)]
#[error("{message}")]
pub struct AppError { pub code: ErrorCode, pub message: String }
```

- `#[repr(i32)]` : la variante vaut directement le code de sortie du processus.
- Constructeurs nommés (`AppError::validation("…")`) plutôt que `AppError { … }` partout.
- Un message pour l'utilisateur, **sans URL ni secret** ; le détail technique part dans
  `log::warn!`.
- Jamais `unwrap()` hors des tests ; `expect("raison vérifiée par un test")` seulement
  pour un invariant prouvé (fichier embarqué par `include_str!`, par exemple).

## Tester un adaptateur sans réseau

1. Séparer la **construction du corps** (`build_body(request) -> serde_json::Value`) et
   l'**analyse de la réponse** (`parse_reply(body: &str) -> Result<Output, AppError>`) de
   l'appel HTTP lui-même.
2. Enregistrer une vraie réponse dans `tests/fixtures/<cas>.json` (succès, erreur 401,
   réponse tronquée) ; retirer identifiants et secrets.
3. Tester les fonctions pures sur les fixtures : `const OK: &str =
   include_str!("../../tests/fixtures/reply_ok.json");`.
4. Tester `map_status(401) == ErrorCode::ApiKeyInvalid`, etc.
5. L'`impl Port` reste si mince qu'il n'a pas besoin de test : il enchaîne les trois.

Le cas d'usage se teste avec un **faux port** écrit dans le module de tests
(`struct FakePort; impl Port for FakePort { … }`), sans crate de mock.

## Threads et canaux (interface réactive)

```rust
let (sender, receiver) = std::sync::mpsc::channel();
let request = request.clone();              // la fenêtre garde sa copie
std::thread::spawn(move || {                // `move` : le thread devient propriétaire
    let result = UseCase::execute(provider.as_ref(), &key, &request);
    let _ = sender.send(Event::Done(result)); // fenêtre fermée → personne n'écoute, on ignore
});
// côté interface : receiver.try_recv() à chaque image, jamais recv() bloquant
```

Règle : **cloner puis `move`**, résultat par canal. Pas d'`Arc<Mutex<_>>` partagé avec
l'interface, sauf pour une poignée qu'il faut pouvoir tuer (`Child` d'un processus).

## Commandes avant commit

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked -- -D warnings   # avertissement = erreur
cargo test --workspace --locked                                   # sans réseau, sans coût
cargo test -p <crate> <module>                                    # un module
cargo build --release --locked
```

`--locked` refuse toute mise à jour implicite de `Cargo.lock` : la build est
reproductible. Ajouter une dépendance = une exécution sans `--locked`, puis commit du
lock.

## Pièges fréquents (edition 2024, Rust ≥ 1.88)

| Symptôme | Cause | Remède |
|---|---|---|
| `std::env::set_var` est `unsafe` | edition 2024 | injecter un trait `EnvReader` et le simuler dans les tests |
| `if let … && cond` refusé | `let_chains` est stable en 2024 seulement | vérifier `edition = "2024"` dans le workspace |
| `manual implementation of is_multiple_of` | clippy récent | `(n).is_multiple_of(3)` au lieu de `n % 3 == 0` |
| `method is never used` en `-D warnings` | fonction publique d'un binaire, appelée seulement par les tests | la câbler dans le même commit, ou la retirer |
| Emprunt refusé dans une fermeture egui | la fermeture capture `&mut state` | calculer les valeurs **avant** la fermeture |
| `the trait Send is not satisfied` | type non `Send` traversant `thread::spawn` | `Arc<dyn Trait + Send + Sync>` ; pas de `Rc`, pas de `RefCell` |

Messages clippy détaillés : `references/clippy-messages.md`.

## Erreurs courantes

- Importer `ureq`, `std::process` ou `egui` dans la crate domaine : le compilateur le
  permet si le `Cargo.toml` le déclare, donc **ne pas le déclarer**.
- Un `Display` sur un type secret : il finit dans un `format!`. Implémenter `Debug` à la
  main (`Secret(***)`) et aucun `Display`.
- Trier/dédoublonner dans l'adaptateur **et** dans le cas d'usage : choisir un seul
  endroit et le documenter sur le port.
- Une fixture modifiée à la main sans la date de capture : noter l'origine en tête du
  test.

## Sources (vérifiées le 2026-11-25)

- The Rust Programming Language, chapitres 7 (paquets, crates, modules) et 16
  (concurrence, canaux) : <https://doc.rust-lang.org/book/>
- Cargo Book, workspaces et `--locked` :
  <https://doc.rust-lang.org/cargo/reference/workspaces.html>,
  <https://doc.rust-lang.org/cargo/commands/cargo-build.html#manifest-options>
- Clippy lints : <https://clippy.rust-lang.org/master/index.html>
- Edition Guide 2024 : <https://doc.rust-lang.org/edition-guide/rust-2024/>
- `thiserror` : <https://docs.rs/thiserror/latest/thiserror/>

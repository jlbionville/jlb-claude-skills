# Messages clippy fréquents et leur lecture

Clippy groupe ses lints par catégorie ; avec `-D warnings`, toutes celles activées par
défaut (`style`, `complexity`, `perf`, `correctness`, `suspicious`) bloquent la build.

| Message (extrait) | Lint | Ce qu'il veut dire | Remède habituel |
|---|---|---|---|
| `manual implementation of .is_multiple_of()` | `manual_is_multiple_of` | `a % b == 0` sur des entiers non signés | `a.is_multiple_of(b)` |
| `this `if` has identical blocks` | `if_same_then_else` | deux branches identiques | fusionner les conditions |
| `redundant clone` | `redundant_clone` (nursery, hors défaut) | `.clone()` sur une valeur déplacée juste après | retirer le clone |
| `this expression creates a reference which is immediately dereferenced` | `needless_borrow` | `&x` passé à une fonction qui prend `&T` déjà | retirer `&` |
| `large size difference between variants` | `large_enum_variant` | une variante porte un gros type | `Box<T>` autour de la grosse variante |
| `method `x` is never used` | `dead_code` (rustc) | fonction publique d'un **binaire** sans appelant hors tests | la câbler, ou `pub(crate)` + usage, ou la supprimer |
| `unused import` | `unused_imports` (rustc) | import orphelin après refactor | retirer ; attention aux imports utiles seulement en `cfg(test)` : les déplacer dans le module de tests |
| `you should consider adding a Default implementation` | `new_without_default` | `fn new() -> Self` sans argument | `#[derive(Default)]` ou `impl Default` |
| `casting u64 to i64 may wrap` | `cast_possible_wrap` (pedantic) | conversion silencieuse | `i64::try_from(x)?` |
| `this `match` can be collapsed` | `collapsible_match` | `match` imbriqué dans un bras | `if let A(B(x)) = …` ou `matches!` |
| `useless use of vec!` | `useless_vec` | `vec![…]` là où un tableau suffit | `[…]` |
| `the loop variable is only used to index` | `needless_range_loop` | `for i in 0..v.len()` | `for (i, item) in v.iter().enumerate()` |

Désactiver localement n'est acceptable qu'avec une justification écrite :
`#[allow(clippy::too_many_arguments)] // signature imposée par le port`.

Source : <https://clippy.rust-lang.org/master/index.html> (vérifié le 2026-11-25).

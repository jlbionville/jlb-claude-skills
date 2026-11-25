# Sous-ensemble ADF sûr pour une description Jira

Document :

```json
{"type": "doc", "version": 1, "content": [ …blocs… ]}
```

Blocs admis à la racine : `heading`, `paragraph`, `bulletList`, `orderedList`,
`codeBlock`, `rule`.

```json
{"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Titre"}]}
{"type": "paragraph", "content": [
   {"type": "text", "text": "gras", "marks": [{"type": "strong"}]},
   {"type": "text", "text": " et "},
   {"type": "text", "text": "lien", "marks": [{"type": "link", "attrs": {"href": "https://exemple.org"}}]},
   {"type": "hardBreak"}]}
{"type": "bulletList", "content": [
   {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "élément"}]}]}]}
{"type": "orderedList", "attrs": {"order": 1}, "content": [ …listItem… ]}
{"type": "codeBlock", "attrs": {"language": "rust"}, "content": [{"type": "text", "text": "fn main() {}"}]}
{"type": "rule"}
```

Règles qui évitent un 400 :

- `listItem` contient des **blocs** (`paragraph`, listes imbriquées), jamais du texte nu.
- Un `heading` n'est pas admis dans un `listItem` : le remplacer par un `paragraph` dont le
  texte porte la marque `strong`.
- La marque `code` ne se combine pas avec `strong` / `em` : si les deux sont demandées,
  garder `code` seul.
- `text.text` ne doit pas être vide ; un paragraphe vide est `{"type": "paragraph", "content": []}`.
- `link.attrs.href` : seulement `http`, `https`, `mailto` ; sinon garder le texte sans marque.
- Tableaux (`table`), images (`mediaSingle`), citations (`blockquote`) existent en ADF mais
  demandent des attributs et des médias téléversés : les dégrader en texte dans un
  `paragraph` est le choix robuste pour un exporteur Markdown.

Source : <https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/> (vérifié le 2026-11-25).

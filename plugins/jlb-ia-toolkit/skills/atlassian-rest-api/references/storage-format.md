# Storage format Confluence : sous-ensemble pour un corps venant de Markdown

Le storage format est du XHTML restreint, interprété par Confluence. Le corps est une
chaîne (`body.value`) ; **chaque texte et chaque attribut est échappé** (`&`, `<`, `>`,
`"`, `'`), car le Markdown source vient d'un modèle.

| Élément | Balises |
|---|---|
| Titres | `<h1>`…`<h6>` |
| Paragraphe | `<p>…</p>` |
| Listes | `<ul><li>…</li></ul>`, `<ol><li>…</li></ol>` |
| Code en ligne | `<code>…</code>` |
| Bloc de code | `<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">rust</ac:parameter><ac:plain-text-body><![CDATA[…]]></ac:plain-text-body></ac:structured-macro>` ou, plus simple, `<pre>…</pre>` |
| Gras / italique | `<strong>`, `<em>` |
| Lien | `<a href="https://…">texte</a>` (`http`, `https`, `mailto` seulement ; sinon texte seul) |
| Rupture | `<br/>` |
| Filet | `<hr/>` |
| Tableau, image, citation, HTML brut | texte échappé dans `<p>` (dégradation volontaire) |

Pièges :

- Une balise non fermée ou un `&` nu rend la page illisible ou provoque un 400 : passer
  par un constructeur qui ferme les balises dans l'ordre d'ouverture.
- `CDATA` : si le code contient `]]>`, le scinder en deux sections CDATA.
- `representation: "storage"` est obligatoire dans la requête v2 ; `atlas_doc_format`
  existe aussi mais attend de l'ADF sérialisé en chaîne.

Source : <https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html> (vérifié le 2026-11-25).

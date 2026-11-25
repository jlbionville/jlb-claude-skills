# Gabarit CHANGELOG (Keep a Changelog 1.1.0)

```markdown
# Changelog

All notable changes to this project are documented in this file.
The format follows Keep a Changelog 1.1.0 and the project uses Semantic Versioning 2.0.0.

## [Unreleased]

### Added
- …

## [0.3.0] - 2026-11-25

### Added
- Model list sorted newest first with descriptions from `models.json` (`--models`).
- Several Atlassian organizations with one shared account.

### Changed
- `atlassian` configuration section: `organizations[]` replaces the flat `site_url` form (still read).

### Fixed
- Thousands separator rendered with egui's bundled fonts.

[Unreleased]: https://github.com/<owner>/<repo>/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/<owner>/<repo>/compare/v0.2.0...v0.3.0
```

Rubriques admises : `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
Une ligne par changement visible pour l'utilisateur ; les détails internes restent dans
les commits. La date est celle du tag, au format `AAAA-MM-JJ`.

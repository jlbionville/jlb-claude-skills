"""Tests de l'installeur legacy : déploiement des gabarits (templates/)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from installer import install_templates, uninstall_templates  # noqa: E402


def make_templates(root: Path) -> Path:
    templates = root / "templates"
    templates.mkdir()
    (templates / "troubleshooting.md").write_text("# Gabarit\n", encoding="utf-8")
    (templates / "notes.txt").write_text("ignored\n", encoding="utf-8")
    return templates


def test_symlink_mode_links_each_markdown_template(tmp_path: Path) -> None:
    templates = make_templates(tmp_path)
    target = tmp_path / "claude" / "templates"
    assert install_templates(templates, target, mode="symlink", dry_run=False) == 1
    link = target / "troubleshooting.md"
    assert link.is_symlink()
    assert link.resolve() == (templates / "troubleshooting.md").resolve()
    assert not (target / "notes.txt").exists()


def test_copy_mode_copies_and_replaces_an_existing_file(tmp_path: Path) -> None:
    templates = make_templates(tmp_path)
    target = tmp_path / "claude" / "templates"
    target.mkdir(parents=True)
    (target / "troubleshooting.md").write_text("ancien\n", encoding="utf-8")
    assert install_templates(templates, target, mode="copy", dry_run=False) == 1
    dest = target / "troubleshooting.md"
    assert not dest.is_symlink()
    assert dest.read_text(encoding="utf-8") == "# Gabarit\n"


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    templates = make_templates(tmp_path)
    target = tmp_path / "claude" / "templates"
    assert install_templates(templates, target, mode="symlink", dry_run=True) == 1
    assert not target.exists()


def test_missing_templates_dir_installs_nothing(tmp_path: Path) -> None:
    target = tmp_path / "claude" / "templates"
    assert install_templates(tmp_path / "absent", target, mode="symlink", dry_run=False) == 0


def test_uninstall_removes_only_known_templates(tmp_path: Path) -> None:
    templates = make_templates(tmp_path)
    target = tmp_path / "claude" / "templates"
    install_templates(templates, target, mode="symlink", dry_run=False)
    (target / "mine.md").write_text("perso\n", encoding="utf-8")
    assert uninstall_templates(templates, target) == 1
    assert not (target / "troubleshooting.md").exists()
    assert (target / "mine.md").exists()
    assert uninstall_templates(templates, target) == 0

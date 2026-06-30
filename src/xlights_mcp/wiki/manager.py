"""Wiki management for the xLights GitHub wiki repository.

The wiki is a plain git repo of Markdown files cloned locally.
Images are stored in an `images/` subdirectory and committed alongside
the Markdown so they can be referenced with relative paths
(e.g. `![dialog](images/preferences.png)`).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class WikiError(RuntimeError):
    """Raised when a wiki operation fails."""


class WikiManager:
    def __init__(self, wiki_path: str | Path) -> None:
        self.root = Path(wiki_path).expanduser().resolve()
        self.images_dir = self.root / "images"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _check_root(self) -> None:
        if not self.root.exists():
            raise WikiError(
                f"Wiki directory not found: {self.root}. "
                "Clone it first with: git clone https://github.com/xLightsSequencer/xLights.wiki.git"
            )
        if not (self.root / ".git").exists():
            raise WikiError(f"{self.root} is not a git repository.")

    # ------------------------------------------------------------------
    # Page operations
    # ------------------------------------------------------------------

    def list_pages(self) -> list[dict]:
        self._check_root()
        pages = []
        for f in sorted(self.root.glob("*.md")):
            size = f.stat().st_size
            pages.append({"name": f.stem, "file": f.name, "size_bytes": size})
        # Also include .mediawiki files
        for f in sorted(self.root.glob("*.mediawiki")):
            size = f.stat().st_size
            pages.append({"name": f.stem, "file": f.name, "size_bytes": size})
        return pages

    def read_page(self, page_name: str) -> str:
        self._check_root()
        path = self._resolve_page(page_name)
        return path.read_text(encoding="utf-8")

    def write_page(self, page_name: str, content: str) -> Path:
        self._check_root()
        # Normalise to .md
        name = page_name if page_name.endswith(".md") else f"{page_name}.md"
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def _resolve_page(self, page_name: str) -> Path:
        """Find a page by name, trying .md then .mediawiki extensions."""
        for ext in (".md", ".mediawiki", ""):
            candidate = self.root / f"{page_name}{ext}"
            if candidate.exists():
                return candidate
        # Exact path given
        candidate = self.root / page_name
        if candidate.exists():
            return candidate
        raise WikiError(
            f"Page {page_name!r} not found in {self.root}. "
            f"Available: {[p['name'] for p in self.list_pages()]}"
        )

    # ------------------------------------------------------------------
    # Image operations
    # ------------------------------------------------------------------

    def save_image(self, source: str | Path, dest_name: str | None = None) -> str:
        """Copy *source* PNG into the wiki images/ directory.

        Returns the relative Markdown image path string, e.g.
        ``images/preferences.png``.
        """
        self._check_root()
        self.images_dir.mkdir(exist_ok=True)

        src = Path(source).resolve()
        if not src.exists():
            raise WikiError(f"Source image not found: {src}")

        name = dest_name or src.name
        if not name.lower().endswith(".png"):
            name = f"{name}.png"

        dest = self.images_dir / name
        dest.write_bytes(src.read_bytes())
        return f"images/{name}"

    def image_markdown(self, image_rel_path: str, alt_text: str = "") -> str:
        return f"![{alt_text}]({image_rel_path})"

    # ------------------------------------------------------------------
    # Git operations
    # ------------------------------------------------------------------

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise WikiError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
        return result.stdout.strip()

    def git_status(self) -> str:
        self._check_root()
        return self._git("status", "--short")

    def commit_and_push(self, message: str) -> dict:
        self._check_root()
        # --sparse allows staging files that live outside the sparse-checkout
        # definition (needed when the repo uses sparse-checkout to skip
        # Windows-illegal filenames that exist on the remote).
        self._git("add", "--sparse", "-A")
        status = self._git("status", "--short")
        if not status:
            return {"status": "nothing_to_commit"}
        self._git("commit", "-m", message)
        self._git("push")
        return {"status": "pushed", "committed_files": status}

    def pull(self) -> str:
        self._check_root()
        return self._git("pull", "--rebase")

"""Fetch the direct-link source files; print instructions for gated ones."""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

from .paths import raw_dir
from .spec import DatasetAdapter

USER_AGENT = "matraix-persona-fit/1.0"


def _fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=600) as response, tmp.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    head = tmp.read_bytes()[:200]
    if head.lstrip().startswith(b'{"status":"ERROR"'):
        tmp.unlink()
        raise RuntimeError("{} refused the download: {}".format(url, head.decode("utf-8", "replace")))
    tmp.replace(dest)


def download(adapter: DatasetAdapter, *, force: bool = False) -> list[str]:
    """Download what can be downloaded. Returns human-readable status lines."""
    target = raw_dir(adapter.slug)
    target.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for entry in adapter.raw_files:
        dest = target / entry.name
        if dest.exists() and not force:
            lines.append("ok      {} (already present)".format(dest))
            continue
        if entry.url is None:
            lines.append("manual  {}\n        {}".format(dest, entry.note))
            continue
        try:
            _fetch(entry.url, dest)
        except Exception as exc:  # network / gate errors are reported, not raised
            lines.append("failed  {} <- {}\n        {}\n        {}".format(dest, entry.url, exc, entry.note))
            continue
        if entry.unzip:
            with zipfile.ZipFile(dest) as archive:
                archive.extractall(target)
        lines.append("fetched {}".format(dest))
    return lines

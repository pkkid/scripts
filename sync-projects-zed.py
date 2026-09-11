#!/usr/bin/env python3
"""
Add direct-child Git repositories from configured roots to Zed recents.

Only immediate subdirectories of REPO_ROOTS are checked, so repositories below
those directories are not discovered. Missing repositories are added to Zed's
stable workspace database; existing recent-project entries are left unchanged.
"""
import os
import sqlite3
from pathlib import Path

ZED_DB = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser() / "zed/db/0-stable/db.sqlite"
REPO_ROOTS = [
    Path("~/Projects").expanduser(),
    Path("~/Nasuni").expanduser(),
]


def git_repos():
    """ Yield Git repositories that are direct children of REPO_ROOTS. """
    for root in REPO_ROOTS:
        if root.is_dir():
            yield from (path.resolve() for path in root.iterdir()
              if path.is_dir() and (path / ".git").exists())


def add_to_recents(repos):
    """ Add repos absent from Zed's local recent-workspace records. """
    with sqlite3.connect(f"{ZED_DB.as_uri()}?mode=rw", uri=True, timeout=5) as db:
        db.execute("PRAGMA busy_timeout = 5000")
        columns = {row[1] for row in db.execute("PRAGMA table_info(workspaces)")}
        if not {"paths", "paths_order", "identity_paths", "identity_paths_order"} <= columns:
            raise RuntimeError(f"Unsupported Zed workspace schema in {ZED_DB}")
        existing = {row[0] for row in db.execute(
            "SELECT paths FROM workspaces WHERE remote_connection_id IS NULL"
        )}
        added = [str(repo) for repo in repos if str(repo) not in existing]
        db.executemany(
            "INSERT INTO workspaces (paths, paths_order, identity_paths, identity_paths_order) "
            "VALUES (?, '0', ?, '0')", ((repo, repo) for repo in added))
    return added


if __name__ == "__main__":
    added = add_to_recents(git_repos())
    print(f"Added {len(added)} Zed recent project(s).")
    print(*added, sep="\n")

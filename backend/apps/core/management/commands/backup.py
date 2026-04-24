"""budgetapp backup — dump the database to a file."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Back up the database. Uses pg_dump for PostgreSQL, file copy for SQLite."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            metavar="PATH",
            help="Destination file. Defaults to budgetapp-backup-<timestamp>.dump in CWD.",
        )

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        engine = db.get("ENGINE", "")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = options["output"] or f"budgetapp-backup-{timestamp}.dump"
        output_path = Path(output).resolve()

        if "postgresql" in engine:
            self._pg_dump(db, output_path)
        elif "sqlite3" in engine:
            self._sqlite_copy(db, output_path)
        else:
            raise CommandError(f"Unsupported database engine: {engine}")

        self.stdout.write(self.style.SUCCESS(f"Backup written to {output_path}"))

    def _pg_dump(self, db: dict, dest: Path) -> None:
        pg_dump = shutil.which("pg_dump")
        if not pg_dump:
            raise CommandError("pg_dump not found on PATH.")

        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]

        cmd = [pg_dump, "--format=custom", f"--file={dest}"]
        if db.get("HOST"):
            cmd += ["--host", db["HOST"]]
        if db.get("PORT"):
            cmd += ["--port", str(db["PORT"])]
        if db.get("USER"):
            cmd += ["--username", db["USER"]]
        cmd.append(db["NAME"])

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)  # noqa: S603
        if result.returncode != 0:
            raise CommandError(f"pg_dump failed:\n{result.stderr}")

    def _sqlite_copy(self, db: dict, dest: Path) -> None:
        src = Path(db["NAME"])
        if not src.exists():
            raise CommandError(f"SQLite database not found: {src}")
        shutil.copy2(src, dest)

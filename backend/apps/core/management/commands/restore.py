"""budgetapp restore — restore the database from a backup file."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Restore the database from a backup created by `budgetapp backup`."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the backup file.")
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip the confirmation prompt (for scripted use).",
        )

    def handle(self, *args, **options):
        src = Path(options["path"]).resolve()
        if not src.exists():
            raise CommandError(f"Backup file not found: {src}")

        if not options["no_confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    f"This will OVERWRITE the current database with {src}.\n"
                    "Type 'yes' to continue: "
                ),
                ending="",
            )
            self.stdout.flush()
            answer = input()
            if answer.lower() != "yes":
                self.stdout.write("Aborted.")
                return

        db = settings.DATABASES["default"]
        engine = db.get("ENGINE", "")

        if "postgresql" in engine:
            self._pg_restore(db, src)
        elif "sqlite3" in engine:
            self._sqlite_restore(db, src)
        else:
            raise CommandError(f"Unsupported database engine: {engine}")

        self.stdout.write(self.style.SUCCESS("Restore complete."))

    def _pg_restore(self, db: dict, src: Path) -> None:
        pg_restore = shutil.which("pg_restore")
        if not pg_restore:
            raise CommandError("pg_restore not found on PATH.")

        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]

        cmd = [pg_restore, "--clean", "--if-exists", f"--dbname={db['NAME']}"]
        if db.get("HOST"):
            cmd += ["--host", db["HOST"]]
        if db.get("PORT"):
            cmd += ["--port", str(db["PORT"])]
        if db.get("USER"):
            cmd += ["--username", db["USER"]]
        cmd.append(str(src))

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)  # noqa: S603
        if result.returncode != 0:
            raise CommandError(f"pg_restore failed:\n{result.stderr}")

    def _sqlite_restore(self, db: dict, src: Path) -> None:
        dest = Path(db["NAME"])
        shutil.copy2(src, dest)

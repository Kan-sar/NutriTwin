"""Portable equivalent of make check for hosts without GNU Make."""

import subprocess
import sys


def main() -> None:
    commands = [
        ["-m", "ruff", "check", "."],
        ["-m", "ruff", "format", "--check", "."],
        [
            "-m",
            "mypy",
            "apps/api/src",
            "packages/domain/src",
            "packages/data_pipeline/src",
            "services/worker/src",
            "scripts",
        ],
        ["scripts/validate_data.py"],
        ["scripts/check_docs.py"],
        ["-m", "pytest", "--cov", "--cov-report=term-missing"],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], check=True)


if __name__ == "__main__":
    main()

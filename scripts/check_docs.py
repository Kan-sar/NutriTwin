"""Check repository-local Markdown links without fetching external websites."""

import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    git = shutil.which("git")
    if git is None:
        raise SystemExit("Git is required for repository documentation checks")
    listed = subprocess.check_output(
        [git, "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
    ).decode()
    paths = sorted({path for path in listed.split("\0") if path.endswith(".md")})
    failures: list[str] = []
    count = 0
    for relative in paths:
        source = root / relative
        if not source.is_file():
            continue
        content = source.read_text(encoding="utf-8")
        content = re.sub(r"(?ms)^```.*?^```[^\n]*", "", content)
        for match in re.finditer(r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", content):
            target = match.group(1).strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            decoded = unquote(parsed.path)
            destination = (
                (root / decoded.lstrip("/")) if decoded.startswith("/") else source.parent / decoded
            )
            destination = destination.resolve()
            count += 1
            if not destination.is_relative_to(root) or not destination.exists():
                failures.append(f"{relative}: missing local link {target}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"validated {count} local Markdown links across {len(paths)} documents")


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def read_secret_value() -> str:
    secret_file = os.getenv("SECRET_FILE", "").strip()
    if secret_file:
        path = Path(secret_file)
        if not path.is_file():
            raise FileNotFoundError(f"SECRET_FILE does not exist: {path}")
        return path.read_text(encoding="utf-8").strip()

    value = os.getenv("SECRET_VALUE", "")
    if value.strip():
        return value.strip()

    raise ValueError("Set SECRET_FILE or SECRET_VALUE.")


def main() -> int:
    repo = os.getenv("TARGET_REPOSITORY", "").strip()
    secret_name = os.getenv("SECRET_NAME", "").strip()
    token = (
        os.getenv("SECRET_UPDATE_TOKEN", "").strip()
        or os.getenv("GH_TOKEN", "").strip()
        or os.getenv("GITHUB_TOKEN", "").strip()
    )

    if not repo:
        return fail("Set TARGET_REPOSITORY, for example OWNER/REPO.")
    if not secret_name:
        return fail("Set SECRET_NAME, for example TARGET_SECRET.")
    if not token:
        return fail("Set SECRET_UPDATE_TOKEN or GH_TOKEN.")

    try:
        secret_value = read_secret_value()
    except (OSError, ValueError) as exc:
        return fail(str(exc))

    if not secret_value:
        return fail("Secret value is empty; refusing to update GitHub Secret.")

    print(f"::add-mask::{secret_value}")
    env = os.environ.copy()
    env["GH_TOKEN"] = token

    command = ["gh", "secret", "set", secret_name, "--repo", repo]
    result = subprocess.run(
        command,
        input=secret_value,
        text=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode

    print(f"Updated GitHub Actions secret {secret_name} in {repo}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

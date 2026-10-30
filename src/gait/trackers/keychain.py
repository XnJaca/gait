import shutil
import subprocess
import sys

ACCOUNT = "gait"


def _run(command: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, input=stdin, capture_output=True, text=True)


def set_secret(service: str, secret: str) -> bool:
    if sys.platform == "darwin":
        command = ["security", "add-generic-password", "-U", "-a", ACCOUNT, "-s", service, "-w", secret]
        return _run(command).returncode == 0
    if shutil.which("secret-tool"):
        command = ["secret-tool", "store", "--label", service, "service", service, "account", ACCOUNT]
        return _run(command, stdin=secret).returncode == 0
    return False


def get_secret(service: str) -> str | None:
    if sys.platform == "darwin":
        result = _run(["security", "find-generic-password", "-a", ACCOUNT, "-s", service, "-w"])
    elif shutil.which("secret-tool"):
        result = _run(["secret-tool", "lookup", "service", service, "account", ACCOUNT])
    else:
        return None
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None

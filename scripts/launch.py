"""Shared, dependency-free bootstrap for the macOS and Windows launchers."""
import hashlib
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 12) or sys.version_info >= (3, 15):
        print('Python 3.12-3.14 gerekli. Onerilen: Python 3.12 (64-bit).')
        return 1
    environment = ROOT / '.venv'
    python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not python.is_file():
        print('Ilk kurulum: Python ortami hazirlaniyor...', flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    requirements = ROOT / 'requirements.txt'
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = environment / '.requirements.sha256'
    if not stamp.is_file() or stamp.read_text().strip() != fingerprint:
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(requirements)],
                       cwd=ROOT, check=True)
        stamp.write_text(fingerprint)
    return subprocess.call([str(python), str(ROOT / 'main.py'), *sys.argv[1:]], cwd=ROOT)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f'Kurulum/baslatma hatasi: {exc}', file=sys.stderr)
        raise SystemExit(1)

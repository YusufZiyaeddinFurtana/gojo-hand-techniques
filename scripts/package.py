"""Build small platform source ZIPs; never include recordings, models or venv."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(platform,launcher):
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    filename = destination / f'gojo-hand-techniques-{platform}.zip'
    files = [ROOT / p for p in ('main.py','requirements.txt','README.md','THIRD_PARTY.md',launcher)]
    files += [ROOT/'scripts'/'launch.py']
    for directory,pattern in [('gojo','*.py'),('tests','*.py'),('docs','*.md')]:
        files += sorted((ROOT/directory).glob(pattern))
    with zipfile.ZipFile(filename,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path,Path('gojo-hand-techniques')/path.relative_to(ROOT))
    print(filename.name)
    return filename


if __name__ == '__main__':
    package('macos','Baslat.command')
    package('windows','Baslat.bat')

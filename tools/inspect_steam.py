"""Read-only Steam discovery. Reports installed builds and archive inventories.

Does not extract assets, launch games, modify installs, or read Steam credentials.
Use --steam-root to supply a nonstandard Steam client folder. Reports can contain
local installation paths, so keep them outside source control.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys

TOKEN = re.compile(r'\s+|//[^\n]*|"(?:\\.|[^"\\])*"|[{}]')


def parse_vdf(text):
    tokens = []
    cursor = 0
    for match in TOKEN.finditer(text):
        if text[cursor:match.start()].strip():
            raise ValueError('Unsupported VDF token')
        cursor = match.end()
        raw = match.group()
        if raw.isspace() or raw.startswith('//'):
            continue
        if raw.startswith('"'):
            raw = re.sub(r'\\([\\"])', r'\1', raw[1:-1])
            tokens.append(('string', raw))
        else:
            tokens.append((raw, raw))
    if text[cursor:].strip():
        raise ValueError('Trailing invalid VDF data')
    position = 0

    def block(nested=False):
        nonlocal position
        result = {}
        while position < len(tokens):
            kind, key = tokens[position]
            position += 1
            if kind == '}':
                if not nested:
                    raise ValueError('Unexpected closing brace')
                return result
            if kind != 'string' or position >= len(tokens):
                raise ValueError('Expected VDF key and value')
            kind, value = tokens[position]
            position += 1
            if kind == '{':
                value = block(True)
            elif kind != 'string':
                raise ValueError('Expected VDF string or object')
            if key in result:
                raise ValueError('Duplicate VDF key')
            result[key] = value
        if nested:
            raise ValueError('Unclosed VDF object')
        return result

    return block()


def default_roots():
    roots = []
    if os.name == 'nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as key:
                roots.append(Path(winreg.QueryValueEx(key, 'SteamPath')[0]))
        except OSError:
            pass
        for name in ('ProgramFiles(x86)', 'ProgramFiles'):
            if os.environ.get(name):
                roots.append(Path(os.environ[name]) / 'Steam')
    else:
        roots.extend([Path.home() / '.steam/steam', Path.home() / '.local/share/Steam',
                      Path.home() / 'Library/Application Support/Steam'])
    return roots


def library_roots(client_roots):
    libraries = set()
    errors = []
    for root in client_roots:
        if not root.is_dir():
            continue
        libraries.add(root.resolve())
        path = root / 'steamapps/libraryfolders.vdf'
        if not path.exists():
            path = root / 'config/libraryfolders.vdf'
        if path.exists():
            try:
                records = parse_vdf(path.read_text(encoding='utf-8-sig'))['libraryfolders']
                for key, value in records.items():
                    if not key.isdigit():
                        continue
                    folder = value.get('path') if isinstance(value, dict) else value
                    if folder:
                        libraries.add(Path(folder).resolve())
            except (OSError, ValueError, KeyError, AttributeError) as error:
                errors.append({'path': str(path), 'error': str(error)})
    return sorted(libraries, key=str), errors


def inspect(client_roots):
    libraries, errors = library_roots(client_roots)
    games = []
    for library in libraries:
        steamapps = library / 'steamapps'
        try:
            manifests = sorted(steamapps.glob('appmanifest_*.acf'))
            for manifest in manifests:
                try:
                    app = parse_vdf(manifest.read_text(encoding='utf-8-sig'))['AppState']
                    name = app.get('name', '')
                    appid = app.get('appid', '')
                    target = ('warhammer3' if appid == '1142710' else
                              'dawn_of_war' if 'dawn of war' in name.lower() else None)
                    if not target:
                        continue
                    install_dir = app['installdir']
                    # A manifest is not permission to walk outside common/.
                    if not install_dir or any(c in install_dir for c in ('/', '\\')) or install_dir in ('.', '..'):
                        raise ValueError('Invalid installation directory')
                    common = (steamapps / 'common').resolve()
                    folder = (common / install_dir).resolve()
                    if not folder.is_relative_to(common):
                        raise ValueError('Installation resolves outside Steam common folder')
                    archives = []
                    if folder.is_dir():
                        for suffix in (['*.pack'] if target == 'warhammer3' else ['*.sga', '*.module']):
                            for asset in sorted(folder.rglob(suffix)):
                                if not asset.resolve().is_relative_to(folder):
                                    raise ValueError('Archive symlink escapes installation')
                                archives.append({'path': asset.relative_to(folder).as_posix(), 'bytes': asset.stat().st_size})
                    games.append({'target': target, 'steam_appid': appid, 'name': name,
                                  'buildid': app.get('buildid', 'not_recorded'),
                                  'folder': str(folder), 'folder_exists': folder.is_dir(),
                                  'archives': archives})
                except (OSError, ValueError, KeyError, AttributeError) as error:
                    errors.append({'path': str(manifest), 'error': str(error)})
        except OSError as error:
            errors.append({'path': str(steamapps), 'error': str(error)})
    available = {g['target'] for g in games if g['folder_exists']}
    missing = sorted({'warhammer3', 'dawn_of_war'} - available)
    return {'schema_version': 1, 'platform': sys.platform, 'games': games, 'errors': errors,
            'missing_targets': missing,
            'note': 'Dawn of War editions/components must be confirmed from manifests; discovery is not asset conversion or gameplay verification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steam-root', type=Path, action='append')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = inspect(args.steam_root or default_roots())
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
        print(f'Read-only report written to {args.output}')
        print(f"Found {len(report['games'])} selected game components; {len(report['errors'])} inspection errors.")
    else:
        print(text)
    return 1 if report['missing_targets'] or report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())

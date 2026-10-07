"""Validate design tables and compile each checked design row to a Lua table.

This compiles engine-independent configuration only. Release preflight additionally
requires all installed-game integration checks; it cannot create a playable pack.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ("campaign", "systems", "units", "hooks", "release_requirements")


def read_sheets(root=ROOT):
    tables = {}
    for name in TABLES:
        sheet = json.loads((root / "sheets" / (name + ".json")).read_text())
        columns = sheet["columns"]
        if len(set(columns)) != len(columns) or "id" not in columns:
            raise ValueError(f"{name}: invalid column declarations")
        ids = set()
        if not sheet["rows"]:
            raise ValueError(f"{name}: zero rows")
        for row in sheet["rows"]:
            if set(row) != set(columns):
                raise ValueError(f"{name}: missing or extra cells in {row.get('id')}")
            for key, value in row.items():
                if value is None or value == "" or isinstance(value, (dict, list)):
                    raise ValueError(f"{name}.{row['id']}.{key}: unfilled/invalid cell")
            if row["id"] in ids:
                raise ValueError(f"{name}: duplicate id {row['id']}")
            ids.add(row["id"])
        tables[name] = sheet["rows"]
    if set(row['id'] for row in tables['systems']) != {'requisition'}:
        raise ValueError('Core requires exactly one requisition system')
    for row in tables['systems']:
        for key in ('initial', 'cap', 'turn_income', 'victory_income', 'army_capacity'):
            if type(row[key]) is not int or row[key] < 0:
                raise ValueError(f"systems.{row['id']}.{key}: expected nonnegative integer")
        if row['initial'] > row['cap']:
            raise ValueError('Initial requisition exceeds cap')
    count = 1  # Angron occupies the general slot.
    for row in tables['units']:
        for key in ('cost', 'starting_count'):
            if type(row[key]) is not int or row[key] < (1 if key == 'cost' else 0):
                raise ValueError(f"units.{row['id']}.{key}: invalid integer")
        count += row['starting_count']
    if tables['systems'][0]['army_capacity'] < 1:
        raise ValueError('Army capacity must be positive')
    if count > tables['systems'][0]['army_capacity']:
        raise ValueError('Starting army exceeds the intended standard 20-unit limit')
    for row in tables['release_requirements']:
        if row['status'] not in ('blocked', 'verified'):
            raise ValueError('Unknown verification status')
    return tables


def lua_value(value):
    if isinstance(value, str):
        # JSON escapes non-ASCII as \u, which Lua 5.1 does not understand.
        return json.dumps(value, ensure_ascii=False)
    if type(value) is int:
        return str(value)
    raise ValueError(f'Unsupported Lua value: {type(value).__name__}')


def compile_lua(tables):
    lines = ['-- Generated from JSON sheets; engine-independent design data only.', 'return {']
    for name, rows in tables.items():
        lines.append('  ["' + name + '"] = {')
        for row in rows:
            cells = ', '.join('[' + lua_value(k) + '] = ' + lua_value(v) for k, v in row.items())
            lines.append('    [' + lua_value(row['id']) + '] = {' + cells + '},')
        lines.append('  },')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preflight', 'compile-core'])
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    tables = read_sheets()
    if args.release:
        blocked = [row for row in tables['release_requirements'] if row['status'] != 'verified']
        for row in blocked:
            print(f"BLOCKED {row['id']}: {row['evidence_needed']}")
        if blocked:
            return 1
    if args.command == 'compile-core':
        output = ROOT / 'build' / 'core_config.lua'
        output.parent.mkdir(exist_ok=True)
        output.write_text(compile_lua(tables))
        print(f'Core design configuration: {output}; not a playable mod')
    else:
        print('Design cells and core constraints checked; no installed-game verification implied.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

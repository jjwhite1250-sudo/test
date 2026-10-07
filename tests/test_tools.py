import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from inspect_steam import inspect, parse_vdf
from sheets import read_sheets


class InspectorTests(unittest.TestCase):
    def test_vdf_nested_objects_windows_paths_and_comments(self):
        result = parse_vdf('// comment\n"libraryfolders" { "0" { "path" "C:\\\\Steam" } }')
        self.assertEqual(result['libraryfolders']['0']['path'], 'C:\\Steam')

    def test_malformed_vdf_is_rejected(self):
        for value in ('"a" { "b" "c"', '"a" "b" }', '"a" "b" "a" "c"', 'unexpected', '"a"'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_vdf(value)

    def test_discovers_external_library_and_builds_without_changing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'Steam'
            external = Path(directory) / 'Library'
            (root / 'steamapps').mkdir(parents=True)
            (external / 'steamapps/common/WH3/data').mkdir(parents=True)
            (external / 'steamapps/common/DoW/W40k').mkdir(parents=True)
            (root / 'steamapps/libraryfolders.vdf').write_text(
                '"libraryfolders" { "0" { "path" "' + external.as_posix() + '" } }')
            for appid, name, folder in [('1142710', 'Total War: WARHAMMER III', 'WH3'),
                                       ('4570', 'Warhammer 40,000: Dawn of War', 'DoW')]:
                (external / f'steamapps/appmanifest_{appid}.acf').write_text(
                    f'"AppState" {{ "appid" "{appid}" "name" "{name}" "installdir" "{folder}" "buildid" "123" }}')
            (external / 'steamapps/common/WH3/data/data.pack').write_bytes(b'fixture')
            (external / 'steamapps/common/DoW/W40k/Data.sga').write_bytes(b'fixture')
            before = {str(p): p.read_bytes() for p in Path(directory).rglob('*') if p.is_file()}
            report = inspect([root])
            self.assertEqual(report['missing_targets'], [])
            self.assertEqual(report['errors'], [])
            self.assertEqual(len(report['games']), 2)
            self.assertTrue(all(g['buildid'] == '123' for g in report['games']))
            self.assertTrue(all(len(g['archives']) == 1 for g in report['games']))
            after = {str(p): p.read_bytes() for p in Path(directory).rglob('*') if p.is_file()}
            self.assertEqual(before, after)

    def test_missing_install_is_not_reported_as_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'steamapps').mkdir()
            (root / 'steamapps/appmanifest_1142710.acf').write_text(
                '"AppState" { "appid" "1142710" "name" "WH3" "installdir" "Absent" }')
            report = inspect([root])
            self.assertFalse(report['games'][0]['folder_exists'])
            self.assertIn('warhammer3', report['missing_targets'])

    def test_manifest_cannot_escape_steam_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'steamapps').mkdir()
            (root / 'steamapps/appmanifest_1142710.acf').write_text(
                '"AppState" { "appid" "1142710" "installdir" "../../private" }')
            report = inspect([root])
            self.assertEqual(len(report['errors']), 1)
            self.assertEqual(report['games'], [])


class SheetTests(unittest.TestCase):
    def edit_sheet(self, name, mutate):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / 'sheets', root / 'sheets')
        path = root / 'sheets' / (name + '.json')
        data = json.loads(path.read_text())
        mutate(data)
        path.write_text(json.dumps(data))
        return root

    def test_preflight_rejects_missing_cells(self):
        root = self.edit_sheet('units', lambda sheet: sheet['rows'][0].pop('cost'))
        with self.assertRaisesRegex(ValueError, 'missing or extra cells'):
            read_sheets(root)

    def test_preflight_rejects_unfilled_cells(self):
        root = self.edit_sheet('units', lambda sheet: sheet['rows'][0].update(asset_requirement=''))
        with self.assertRaisesRegex(ValueError, 'unfilled'):
            read_sheets(root)

    def test_preflight_rejects_negative_costs(self):
        root = self.edit_sheet('units', lambda sheet: sheet['rows'][0].update(cost=-10))
        with self.assertRaisesRegex(ValueError, 'invalid integer'):
            read_sheets(root)

    def test_preflight_rejects_oversized_starting_army(self):
        root = self.edit_sheet('units', lambda sheet: sheet['rows'][0].update(starting_count=30))
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            read_sheets(root)


if __name__ == '__main__':
    unittest.main()

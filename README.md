# test: Angron's Invasion

**Source foundation only — not an installable or playable Warhammer III mod.**
No `.pack` release, faction database, asset converter, or Melty listing exists yet.

The agreed goal is a separate World Eaters faction led by Angron in a **solo
Immortal Empires campaign**. A portal opens in a random eligible region; the opening
objective is to capture that region's settlement. Recruitment uses requisition and
reinforcement ideas adapted from Dawn of War. Actual models, textures and voices
must come from each player's owned Steam Dawn of War installation, converted
locally. No game assets may be included in the downloadable release.

The initial proposed army is Angron, four Berzerker units and two Cultist units.
These are logical design rows, not existing/verified Warhammer III unit keys.
Balance and the small starting roster are provisional. This foundation does not
replace any existing faction.

## What exists

- JSON design sheets for campaign requirements, economy, roster, documented hooks,
  and release prerequisites.
- Lua 5.1 logic for selecting a valid random location, confirming one-time arrival,
  idempotent rewards, reserving/refunding reinforcement costs, and the opening
  conquest objective. The game adapter is still required.
- A read-only Steam installation/build/archive inspector. It discovers library
  folders and matching game manifests without extracting or modifying game files.
- Tests that execute the Lua core and exercise the Steam reader and design checks.
  These are development tests, **not gameplay tests**.

## Development checks

Python 3.10+ is needed. From this repository:

```sh
python tools/sheets.py preflight
uv run --with lupa==2.6 python -m unittest discover -s tests -v
python tools/sheets.py compile-core
python tools/sheets.py preflight --release
```

The last command currently fails intentionally and lists every unresolved release
prerequisite. `compile-core` emits checked design configuration under ignored
`build/`; it does not generate a mod pack or validate game bindings. If uv is not
available, install `requirements-dev.txt` in a virtual environment instead.

Edit sheets before changing dependent logic. Every row generates a Lua table.
No production package should be built until all release prerequisites have actual
evidence and the release preflight passes.

## Inspect the owned Steam installations

On the PC where both games are installed, run:

```sh
python tools/inspect_steam.py --output local/steam-report.json
```

Use `--steam-root "D:/Steam"` for a nonstandard client location. Steam library
folders are detected from `libraryfolders.vdf`. Anniversary Edition may install
several Dawn of War components; the report preserves their actual names and app
IDs instead of assuming an Anniversary app ID. Reports contain local paths and
stay in ignored `local/`. Missing games or inspection errors return a nonzero
exit status. A successful report does not establish ownership beyond the available
installation, correct edition, asset compatibility, or ability to launch.

The current cloud machine has neither game installation. Its inspector reported
both targets missing. Windows registry discovery remains untested on Windows.

## Required game integration

Use Warhammer III's data packs and campaign Lua route. First inspect the installed
database schemas, the current Immortal Empires setup, faction selector support,
unit definitions, and documented events. Do not substitute fabricated database
keys, select an AI faction and claim it is playable, or replace an existing Khorne
faction without changing the agreed design.

The future adapter must check campaign and human faction, exclude multiplayer,
derive eligible map regions, use the campaign RNG, create the army, show the
portal, register the conquest objective, implement resource/recruitment UI, and
persist state. Army grants have no verified success callback in the documented
`grant_unit_to_character` signature; inspect army contents to confirm success.
Reconcile pending operations after reload before rewarding or granting again.
Core tests do not prove actual game save/load works.

Warhammer III uses CA's `.rigid_model_v2` format with additional animation and
material bindings. Dawn of War content cannot simply be renamed or copied into
a pack. Inspect its archives and prove one infantry model, animations and voice
conversion locally before expanding the roster. Angron is not available as a
character model in the selected Dawn of War game; a separate compatible art
solution is unresolved. Paid generation is not authorized.

Back up saves before a modded launch and use a new solo test campaign. Test faction
selection, portal variation and invalid-region handling, starting army, recruitment,
conquest, victory rewards and reload. Capture a real screenshot of that version.

## Melty and distribution

Live Melty discovery is blocked by the cloud network proxy (CONNECT 403). `melty.gg`
was saved as a requested custom allowed domain; the draft has not been applied or
published here. No live `game_info`, mashup search or one-click check has run.

The uploaded notes say Melty has no automatically installed Warhammer III loader
and does not currently recognize Dawn of War Anniversary Edition as a companion.
Those details must be checked with live tools. No loader or one-click asset
converter has been installed, bundled or proven. A local prelaunch converter
would need to discover the player's Steam libraries itself if Melty cannot pass
the Dawn of War path. Do not call this one-click until both recipe checks and a
real install/launch test succeed.

License, credits and remix permissions for a public listing are still undecided.
The read-only inspector/core tests do not imply a content redistribution license.
No game files, credentials or third-party toolkit code are included in this source.

## Research tools

- [Universal Modder](https://github.com/rehan-remade/universal-modder), inspected at
  `baff1e5d01f63ae7cc81a049b6f4cf60e6c91dec`.
- [Warhammer III scripting documentation mirror](https://github.com/chadvandy/tw_modding_resources),
  inspected at `fd75b764a55dbd6279710d977c262a6d8dca1e5d`.
- [RPFM](https://github.com/Frodo45127/rpfm), inspected at
  `5204dab9e9a9376c438deabed8489de3bc319599`. Source was downloaded for format
  documentation only; no RPFM binary was built or installed.

Use the existing isolated checkout; do not create a Git worktree unless requested.

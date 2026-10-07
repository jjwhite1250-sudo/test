# Mod journal

## Agreed scope

World Eaters as a separate full faction in Total War: Warhammer III, led by Angron.
Solo Immortal Empires campaign. Portal arrival in a random eligible region.
Actual Dawn of War Anniversary Edition models/textures/voices plus adapted
requisition/reinforcement mechanics. Both games use Steam. Building the first
version is authorized; publishing remains subject to the user's final approval.

## Environment and route

Working checkout: `/workspace/test`, initially empty with no commits.
Cloud Linux machine; Universal Modder `scan --list` finds no game installations.
Chosen route: Warhammer III data packs plus documented campaign Lua, rather than
native process injection. New playable faction setup is unresolved pending current
game databases and campaign selection integration. No host game files changed.

Downloaded research checkouts are outside this repository under `/workspace/tools`:
Universal Modder, `tw_modding_resources`, RPFM. Toolkit KB had no matching Warhammer
note. No paid tools used; no generated look-alike art is represented as Dawn of War
content. RPFM documents RMV2 geometry and separate skeleton/animation/material
bindings, confirming that an asset-copy operation is not a working converter.

Melty HTTP tools discovery failed with proxy CONNECT 403 before reaching the server.
This is not evidence that the supplied credential is invalid. `melty.gg` was added
to the configuration draft's custom domain list, preserving the package preset;
runtime access still failed on retry. Git HTTPS research downloads work. GitHub API
release discovery also failed with CONNECT 403. No authenticated values are saved
in this repository. No listing or publish operation has been attempted.

## Source foundation

Sheets define the agreed campaign, provisional balance/roster, documentation-backed
hook signatures and explicit blocked release requirements. The core is independent
of engine globals; it accepts actual map candidates/RNG and acknowledgement of
engine actions from a future adapter. It does not fabricate units, faction keys,
game events or database bindings. A checked config can be compiled for core tests;
release preflight remains blocked.

Steam inspector uses libraryfolders plus appmanifest metadata and inventories only
the matching install's pack/SGA/module filenames and sizes. It does not extract or
distribute game assets, read credential files, or launch anything.

## Next integration work

1. Obtain local access to the owned Steam games and inspect installed builds with
   `python tools/inspect_steam.py --output local/steam-report.json`.
2. Inspect the installed WH3 schemas and establish a separate playable faction
   route in Immortal Empires. Verify one faction can be selected and loaded before
   expanding it. Do not silently replace an existing faction.
3. Prove one owned Dawn of War infantry model/animation/voice can convert to WH3
   formats locally. Resolve Angron's art separately.
4. Implement adapter and UI; use real game events/keys, confirmed spawn results,
   serialized/reconciled requests and per-army recruitment checks.
5. Back up saves, test a new solo campaign, then capture actual gameplay.
6. Unblock live Melty discovery and prove a permitted local asset-conversion recipe
   works in one click. Establish public credits/license/remix choice before listing.

No game startup instructions are saved as environment-ready steps because no
playable pack or game installation exists here. Core development checks are listed
in README. Never publish the prototype as a playable faction.

## Validation results

Core/tool suite: 23 tests executed and passed using Lupa 2.6's Lua 5.1 runtime.
Design preflight passed; negative tests proved missing/empty cells, invalid costs
and oversized armies are rejected. Fixture-based Steam discovery, malformed VDF
handling, missing folders, directory traversal and unchanged input files passed.
The real cloud inspector returned nonzero and listed both required games missing.
Game save/load remains untested: the core test verifies only serialized Lua state.

A repository-local `.venv` was created and Lupa 2.6 installed from PyPI with TLS
verification. All 23 tests passed again using that interpreter. Checked design
configuration was generated to ignored `build/core_config.lua`. Release preflight
returned nonzero with seven explicit blockers, as intended. The development
dependency `install_script` was saved in the cloud configuration draft; saving
does not publish the environment or apply networking. No game startup was saved.
All new source files are uncommitted; no original repository files were changed.

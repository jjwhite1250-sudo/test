# Continue on the PC with the owned Steam games

This project is a **source foundation, not a playable release**. Read README.md,
MODLOG.md and all sheets before continuing. The user authorized building the first
version. Do not ask the campaign/store/design questions again.

## Already agreed

- Total War: Warhammer III is the host, solo **Immortal Empires** campaign.
- Separate **World Eaters** faction led by **Angron**; do not replace Skarbrand or
  another existing faction without asking about that design change.
- Arrival through a portal in a randomly selected eligible map region.
- Actual content from the player's owned **Dawn of War Anniversary Edition**
  installation and adapted requisition/reinforcement mechanics.
- Steam for both games.
- Public release targets Melty eventually, but publication is not yet approved.

## First action

Inspect available local tools and AGENTS.md instructions. Check for the owned Steam
game installations. Use the included read-only inspector if Python 3.10+ is present:

```sh
python tools/inspect_steam.py --output local/steam-report.json
```

If Python is not available, obtain it through an existing trusted package manager
or the official Python distribution, or implement equivalent read-only discovery
with the existing local tools. Do not ask the user to download modding tools when
you can do that yourself. Ask only for genuinely missing machine access, purchases,
credentials, or user-controlled prompts. Do not print authentication values.

Inspect the real game data and current modding documentation next. The cloud work
did **not** establish faction selection/setup support, database keys, runtime event
payloads, asset filenames, converters, or one-click installation. Do not treat
logical IDs in units.json as game unit keys. Do not claim that spawning an AI army
implements a playable faction. No mod pack has been built.

Use Universal Modder's mod-any-game skill from its official repository. Research
Warhammer III's native pack/database/Lua modding route before considering any
process patching. RPFM is a relevant pack/database tool, but not a proven automatic
Dawn of War converter. Angron needs a separate compatible art solution. No paid
asset generation is authorized. Download only the tools needed for the next test;
follow supported trust/signature verification.

## Implementation and validation

1. Check current game versions and database schemas. Establish that a new World
   Eaters entry can be selected and start an Immortal Empires campaign.
2. Inspect the player's own Dawn of War archives outside version control. Prove
   one model/animation/voice conversion into the actual WH3 formats. No shipped
   extracts, no renamed files presented as conversions, and no stand-ins presented
   as content from Dawn of War.
3. Update sheets first, then generate/check their code and implement game adapters.
   Bind valid map locations and engine RNG, resource/recruitment UI, spawn success,
   conquest events and serialized state. Handle pending engine operations on reload.
4. Back up saves/config before modifying them or doing a modded launch. Use a new
   solo test campaign. Installing loaders into game folders and driving the user's
   desktop need authorization under the toolkit's instructions; ordinary source
   work and read-only inspection are already authorized.
5. Exercise faction selection, portal variation, invalid-region behavior, recruiting,
   battle rewards, conquest and game save/reload. Obtain a real screenshot from that
   build. Keep source-only and failed outcomes explicitly labeled.

The existing 23 core/tool tests passed on cloud Linux with Lupa 2.6 / Lua 5.1.
Windows registry discovery and game integration have not been tested. Release
preflight correctly lists seven blocked prerequisites. Run the current tests again
after substantive changes and record outcomes in MODLOG.md.

## Melty

The uploaded publishing notes contain the connection instructions. They are not
included in this source bundle because they contain an authentication credential.
Use a securely available binding if present; never put it in files, logs or commits.
Cloud access failed at the network proxy before contacting Melty, not with a token
rejection. No tools/list, game_info, mashup search, listing or upload succeeded.

Once connected, read the current game_info and search for matching projects.
Confirm an actual one-click install path, including local conversion of content
from the owned game, before building a public release. The notes say Anniversary
Edition is not catalogued and WH3 has no automatically installed Melty loader;
verify these claims live. Do not guess a recipe or redistribute game assets.
Get title/credits/license/remix decisions and actual gameplay media before listing,
and obtain final user approval before publishing. No publishing authority should
be inferred from approval to start building.

Use the existing checkout in the isolated task. No worktree is needed.

# Backplane Schematic Readability

Install a shared, read-only KiCad schematic checker and agent instructions for Backplane, Codex and Claude Code. This is a community add-on, not an official Backplane plugin.

The instructions require agents to plan and draw readable schematics from the start:

- Connected local circuits, rather than isolated components joined only by matching labels.
- Aligned symbols, short orthogonal wires, minimal crossings, clear junctions and consistent spacing.
- Functional grouping and captions, useful operating/protection notes, and populated title blocks.
- Automated checks at saved milestones, followed by visual review of rendered sheets.
- Supported Konnect/native CAD editing, one writer per document, and preservation of electrical connectivity during presentation changes.

Installing this does **not** authorize circuit redesign, PCB placement or routing. Explicit user/project requirements take precedence.

## Ask your agent to install it

Paste this into your agent:

> Install https://github.com/benjamin-wilson/backplane-schematic-readability on this machine. Read README.md and INSTALL_FOR_AGENTS.md, verify the bundled dependency checksums, and run install.py. Preserve my existing instructions. Enable the shared schematic-readability skill and automatic schematic-quality instructions for new Backplane projects. Also install the project instructions into the current project if it is a KiCad project. Verify installation in an isolated directory before changing my settings. Do not edit my CAD files as part of installation. Tell me how to start a fresh agent session to pick up the instructions.

## Install manually

Requires **Python 3.10+** and **Bun**. The checker needs neither KiCad nor a cloud account. KiCad and supported authoring tools are needed separately for rendering and corrections.

```sh
git clone https://github.com/benjamin-wilson/backplane-schematic-readability.git
cd backplane-schematic-readability
python3 install.py
```

On Windows use `python` instead of `python3`. The installer uses the current Python interpreter and locates Bun on PATH or under your home directory. Windows support is designed into the installer; CI currently covers macOS and Linux.

To also apply the instructions to an existing project:

```sh
python3 install.py --project "/path/to/your/project"
```

The installer copies its runtime into `~/.local/share/backplane-schematic-readability`, registers the skill in both `~/.codex/skills` and `~/.claude/skills`, and adds a **managed block** to `~/.codex/AGENTS.md` and `~/.claude/CLAUDE.md`. Existing text is preserved; existing artifacts are backed up before updates. An unrelated installation or command is refused instead of overwritten. On Windows these directories are under your user profile.

**Start a fresh agent session after installation.** Existing sessions may retain old instructions. Backplane discovers the Claude-format user skill; Codex also reads its global AGENTS.md. Skill discovery is instruction-based, not a tool-execution hook: an agent can still fail to follow instructions. Check its actual invocation and reports. This installer does not patch Backplane or restart agents.

The installer prints an absolute command that works without changing PATH. Add `~/.local/bin` to PATH to use the `schematic-readability` shortcut (`schematic-readability.cmd` on Windows).

## Run a check

From your KiCad project directory:

```sh
schematic-readability
```

The root is resolved independently for each project using `.backplane.json`:

```json
{"project": "boards/device/device.kicad_pro"}
```

An explicit `schematic` key also works. Otherwise one root-level KiCad project or schematic is accepted; ambiguous roots require an explicit path:

```sh
schematic-readability --project "/path/to/project" --schematic "boards/device/device.kicad_sch"
schematic-readability --describe
```

Reports default to `build/schematic-readability/`:

| File | Purpose |
| --- | --- |
| `legibility.json` | Findings, severities, skipped and suppressed checks |
| `per-sheet.json` | Individual sheet scores |
| `geometry.json` | Inspected drawing geometry |
| `verification.json` | Source hashes and limitations |

Exit **0** means no automated error findings or suppressed finding groups. Exit **1** means unresolved drawing findings or a checker failure; read the output. Exit **2** means launcher input/configuration failure. Reports are saved before returning 1 for drawing findings.

`--report-only` writes diagnostic reports without failing on drawing findings. It does not qualify the drawing or waive findings. `--out PATH` chooses another report directory.

## What it can and cannot establish

Automated checks cover geometric concerns such as text collisions, framing, title blocks, grouping and long wires. A successful run **does not prove neatness or appropriate use of wires**. The skill requires visual review of circuit flow, crossings, notes and local connectivity. These expectations are enforced through agent instructions and review, not an automatic schematic redrawer.

The Copperhead checker expects captioned group rectangles and populated title metadata. Existing drawing conventions may produce findings requiring judgment. Preserve original findings and document visually confirmed false positives individually. Do not suppress errors merely to improve a score.

A long/cross-group-wire advisory may suggest label pairs. Keep the wire when that is clearer, and document the decision; do not dismantle locally wired circuits merely to satisfy an advisory.

Text bounds are estimates. Caption validation against external design docs is skipped in this wrapper. Repeated instances of the same sheet file are inspected once. Run against saved files with no concurrent writer; detected source/hierarchy changes abort the check. ERC, electrical analysis, component verification and fabrication checks remain separate.

## Updates, backups and removal

Pull updates and rerun `python3 install.py`. Only installer-managed blocks are replaced; outside text is retained. Backups are stored under `~/.local/share/backplane-schematic-readability-backups/`, with the location printed on each update.

To remove the add-on, remove its managed blocks between `backplane-schematic-readability:begin` and `:end` from your instruction files, then remove the installed skill directories, runtime and command after checking they belong to this installer. Preserve unrelated instructions and any backups you need.

## Provenance and tests

The vendored read-only Copperhead modules are pinned to commit `4d0cc3f6459608ee43ead4adf97e4ff453752592` of [copperheadhq/copperhead](https://github.com/copperheadhq/copperhead). Apache-2.0 LICENSE and NOTICE are retained, and `runtime/provenance.json` records SHA-256 checksums. Vendored modules are unmodified; the launcher, strict wrapper, installer and instructions are additions. No package download occurs when running the checker (`bun --no-install`).

```sh
python3 -m unittest discover -s tests -v
```

Tests use temporary homes and synthetic schematics; they do not touch your projects or installed settings. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

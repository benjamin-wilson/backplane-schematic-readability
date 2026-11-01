---
name: schematic-readability
description: Required drawing-quality workflow for KiCad schematic creation, meaningful edits, review, and handoff. Plan visible local wiring, functional grouping and explanatory notes; run the shared Copperhead checker and visually review saved sheets. Does not authorize PCB work or circuit redesign.
---

Use this workflow automatically for schematic authoring; do not wait for the user to ask for a readability check. Read it before creating or meaningfully editing a schematic. These are the installed drawing conventions, subject to explicit user/project instructions.

## Author a readable circuit

- Arrange connected functional circuits, with the main signal or power path flowing left to right, positive supplies above and returns below. Put decoupling, feedback and protection parts beside the pins and devices they serve.
- Draw continuous local wires wherever they make the circuit understandable. Use labels to name already drawn nets, cross sheets, connect genuinely distant blocks, and identify shared power rails. Do not build a sheet as isolated components with labeled pin stubs or replace a local circuit with matching labels merely because that is easier to generate.
- Treat neat wiring as an acceptance requirement. Use short, grid-aligned horizontal/vertical wire runs with consistent spacing, aligned component pins and branches, and simple right-angle corners. Place related parts so wiring follows the circuit's flow; do not compensate for poor schematic placement with long detours, repeated jogs, wire bundles woven through unrelated blocks, or long return loops. Reduce crossings by rearranging the schematic's symbols while preserving electrical connectivity. Keep wires clear of text, symbol bodies and unrelated pins. Show intended junctions clearly; nonconnecting crossings must remain unambiguous. Use consistent power/ground conventions. Use a legitimate remote label or an appropriate hierarchy boundary when a long connection would otherwise obscure the local circuit, without reverting to label-only local circuitry.
- Group actual related circuitry with clear section captions and suitable spacing. Group rectangles are drawing aids, not a substitute for connected circuits. Preserve isolation boundaries. Size the sheet to the circuit rather than spreading fragments across a large grid.
- Add concise schematic notes explaining each block's purpose, important operating limits, protection thresholds, startup/shutdown behavior, optional/DNP choices, and critical component or layout constraints where relevant. Put essential context on the drawing, not solely in a separate report. Derive values from verified calculations; mark unknowns instead of inventing explanations.
- Populate meaningful sheet titles and project/revision metadata. Keep reference/value text readable and clear of wires, symbols, labels and the page frame. Prefer the project's established reference design's presentation when one is explicitly authorized; never import another project's circuitry just for its appearance.

For an existing design, preserve reference designators, pin-to-net assignments and electrical behavior during presentation changes. Verify these with native netlist comparison and ERC; do not add electrical changes to a readability task. Coordinate one writer per document and use supported Konnect/native authoring tools. The checker does not authorize CAD file editing or PCB placement/routing.

## Check and visually review

Run from the project root after each meaningful saved schematic milestone and before handoff:

```sh
schematic-readability
```

The command independently resolves this project's root from `.backplane.json` (`schematic`, or the schematic beside `project`), otherwise a single root-level project/schematic. For an ambiguous or nested root:

```sh
schematic-readability --project "/path/to/project" --schematic "boards/device/device.kicad_sch"
```

Use `--describe` for resolved paths and `--out PATH` for a separate report directory. Default reports are in `<project>/build/schematic-readability/`.

The default command returns **exit 1 for unresolved error findings or suppressed finding groups**, after saving its reports. Read `legibility.json` and `per-sheet.json`, fix actionable findings, and rerun. `--report-only` is for diagnosis of an unfinished design; its successful process exit is not schematic acceptance. The checker may advise replacing a long or cross-group wire with labels. Keep an intentional wire when it makes the circuit clearer, and record the reason; do not blindly convert local circuits to labels to satisfy that advisory. Do not disable checks, erase findings, draw misleading groups, or silently recategorize title/grouping errors to claim completion. Document any visually confirmed false positive individually with the sheet, location, evidence and reason; keep the original report and disclose unresolved findings.

Render the saved canonical hierarchy and inspect **every changed sheet** at full-page scale and at a readable zoom. Before final handoff, review every sheet. Confirm the actual local connections can be followed without matching a forest of labels; inspect block ordering, captions, useful notes, title blocks, text spacing and isolation boundaries. Trace each principal path visually and reject tangled, crossing-heavy or unnecessarily meandering wiring even when no automated collision is reported. A high score or collision-free page alone does not satisfy this review. Record reviewed sheet paths and remaining issues in a project review report.

The checker is read-only for CAD and may run without an authoring connection. Run while the saved hierarchy has no concurrent writer; it aborts on detected source changes. `geometry.json` records inspected geometry and `verification.json` hashes and limitations. Findings use estimated text bounds; repeated instances of one sheet file are inspected once. Results do not establish electrical correctness or fabrication readiness; ERC and electrical review remain separate requirements.

Shared implementation: `the installed runtime (recorded by the installer)`. Vendored Copperhead modules remain pinned to `4d0cc3f6459608ee43ead4adf97e4ff453752592`, with Apache-2.0 license, NOTICE and checksums. The command uses installed Bun with package installation disabled.

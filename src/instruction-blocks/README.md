# Instruction blocks

This directory contains canonical source fragments that are not packaged or loaded directly by the
current plugins.

For Run orchestration, the ordered files under `run/orchestration/` are the authoring authority.
`tools/run_orchestration_blocks.py sync` materializes them byte-for-byte into
`src/skills/run/references/orchestration.md`, which remains the only runtime-loaded compatibility
monolith in this release. `build/build.sh` verifies that materialized file before copying either plugin
package and never repairs drift implicitly. Edit the blocks and their closed manifest, not the derived
monolith.

The split is intentionally behavior-preserving:

- `run/SKILL.md`, `load-graph.json`, and `semantic-contract.json` remain byte-identical to the reviewed
  Full Assurance baseline;
- Claude and Codex continue to load the same monolith at the same startup phase;
- the source blocks are not copied into either plugin package;
- Lite routing, conditional block loading, reviewer omission, and lifecycle changes require a later
  independently reviewed release.

After editing blocks and their manifest, run `python tools/run_orchestration_blocks.py sync --repo .`
explicitly. Then run `python tools/run_orchestration_blocks.py verify --repo .` to prove exact baseline
reconstruction. `bash build/build.sh` verifies without repairing drift and regenerates both plugins. A
later release that intentionally changes Run behavior must review and update the duplicated verifier pins;
changing manifest hashes alone is rejected.

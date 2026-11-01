# Installation instructions for agents

The user's request to install this add-on authorizes its checker, skills and scoped instructions. Preserve other settings and do not edit CAD as part of installation.

1. Read README.md, install.py, the skill and the instruction template. Check that the user has Python 3.10+ and Bun. If Bun is missing, explain that dependency; do not silently install unrelated software.
2. Run `python3 -m unittest discover -s tests -v`. Tests are isolated. The installer verifies vendored dependency checksums before writing.
3. Run `python3 install.py`. If the user requested an existing project, add `--project /absolute/project/path`. Do not assume a project from an example path. On Windows use `python`.
4. Inspect the reported files. Existing instruction text must remain outside the managed blocks. Do not overwrite conflicting user skills to bypass a refusal; resolve the conflict with the user while preserving their files.
5. Use the printed absolute checker command with `--project` and `--describe` against the intended project, if available. Run the read-only checker only when the saved files have no concurrent writer. Findings are an unfinished design, not an installation failure.
6. Report the installed paths, backup location and the need for a fresh agent session. Do not promise that an existing session has reloaded its instructions or that a successful checker run guarantees a readable/electrically correct drawing.

For subsequent schematic work, read the installed skill before authoring. Use supported Konnect/native authoring tools, preserve electrical connectivity during presentation work, and keep one writer per document. Review local wiring and neatness in rendered sheets, not only numeric scores. Do not infer PCB placement/routing authorization.

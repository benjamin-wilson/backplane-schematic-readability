#!/usr/bin/env python3
"""Install the portable checker and scoped agent instructions without replacing user files."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BEGIN = '<!-- backplane-schematic-readability:begin -->'
END = '<!-- backplane-schematic-readability:end -->'
MARKER = '.backplane-readability-installed'


def managed(existing, body):
    block = BEGIN + '\n' + body.rstrip() + '\n' + END
    if existing.count(BEGIN) != existing.count(END) or existing.count(BEGIN) > 1:
        raise ValueError('Malformed managed instruction block; repair it before installing')
    if BEGIN in existing:
        a, b = existing.index(BEGIN), existing.index(END) + len(END)
        if b < a:
            raise ValueError('Managed block end precedes beginning')
        return existing[:a] + block + existing[b:]
    return existing + ('\n\n' if existing and not existing.endswith('\n\n') else '') + block + '\n'


def install(home, project=None):
    home = home.expanduser().resolve()
    runtime = home / '.local/share/backplane-schematic-readability'
    skill_dirs = [home / '.codex/skills/schematic-readability', home / '.claude/skills/schematic-readability']
    bun = shutil.which('bun')
    if not bun:
        candidate = home / '.bun/bin' / ('bun.exe' if os.name == 'nt' else 'bun')
        if candidate.is_file():
            bun = str(candidate)
    if not bun:
        raise ValueError('Bun is required. Install it from https://bun.sh and run this installer again.')
    subprocess.run([bun, '--version'], check=True, stdout=subprocess.DEVNULL)
    provenance = json.loads((ROOT / 'runtime/provenance.json').read_text())
    for name, checksum in provenance['vendor_sha256'].items():
        if hashlib.sha256((ROOT / 'runtime' / name).read_bytes()).hexdigest() != checksum:
            raise ValueError('Vendored file checksum mismatch: ' + name)
    for target in [runtime, *skill_dirs]:
        if target.is_symlink() or (target.exists() and not (target / MARKER).is_file()):
            raise ValueError(f'Refusing to replace an existing unrecognized installation: {target}. Back it up or choose another --home.')
    if project is not None:
        project = project.expanduser().resolve(strict=True)
        if not project.is_dir():
            raise ValueError('--project must be an existing project directory')
    command_args = [sys.executable, str(runtime / 'run.py')]
    command = subprocess.list2cmdline(command_args) if os.name == 'nt' else shlex.join(command_args)
    skill = (ROOT / 'skills/schematic-readability/SKILL.md').read_text().replace('schematic-readability --', command + ' --')
    skill = skill.replace('\nschematic-readability\n', '\n' + command + '\n')
    template = (ROOT / 'templates/instructions.md').read_text()
    instructions = [(home / '.codex/AGENTS.md', skill_dirs[0] / 'SKILL.md'),
                    (home / '.claude/CLAUDE.md', skill_dirs[1] / 'SKILL.md')]
    if project:
        instructions.append((project / 'AGENTS.md', skill_dirs[0] / 'SKILL.md'))
    updates = {}
    for target, skill_path in instructions:
        updates[target] = managed(target.read_text() if target.exists() else '', template.replace('{{SKILL_PATH}}', str(skill_path)))
    bindir = home / '.local/bin'
    wrapper = bindir / ('schematic-readability.cmd' if os.name == 'nt' else 'schematic-readability')
    sentinel = 'Managed by backplane-schematic-readability'
    if wrapper.is_symlink() or (wrapper.exists() and sentinel not in wrapper.read_text()):
        raise ValueError(f'Refusing to replace an unrelated command: {wrapper}')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = home / '.local/share/backplane-schematic-readability-backups' / stamp
    # Preflight is complete. Back up every existing artifact before writes.
    for i, target in enumerate([runtime, *skill_dirs, *updates, wrapper]):
        if target.exists():
            dst = backup / str(i) / target.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir():
                shutil.copytree(target, dst)
            else:
                shutil.copy2(target, dst)
    shutil.copytree(ROOT / 'runtime', runtime, dirs_exist_ok=True)
    (runtime / MARKER).write_text('1\n')
    # Preserve the explicit Bun chosen at install time, even outside PATH.
    config = {'bun': str(Path(bun).resolve())}
    (runtime / 'installation.json').write_text(json.dumps(config, indent=2) + '\n')
    for target in skill_dirs:
        target.mkdir(parents=True, exist_ok=True)
        (target / 'SKILL.md').write_text(skill)
        (target / MARKER).write_text('1\n')
    for target, content in updates.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    bindir.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(('@echo off\nREM ' + sentinel + '\n' + command + ' %*\n') if os.name == 'nt'
                       else '#!/bin/sh\n# ' + sentinel + '\nexec ' + command + ' "$@"\n')
    wrapper.chmod(0o755)
    result = {'runtime': str(runtime), 'command': command, 'shortcut': str(wrapper),
              'skills': [str(p / 'SKILL.md') for p in skill_dirs],
              'instructions': [str(p) for p in updates], 'backup': str(backup) if backup.exists() else None,
              'next': 'Start a fresh agent session so it reads the new instructions. Add .local/bin to PATH for the shortcut, or use the full command above.'}
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(), help='User home to install into (also useful for isolated tests)')
    parser.add_argument('--project', type=Path, help='Also add a managed block to this project\'s AGENTS.md')
    args = parser.parse_args()
    try:
        install(args.home, args.project)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f'Installation failed: {exc}\n')


if __name__ == '__main__':
    main()

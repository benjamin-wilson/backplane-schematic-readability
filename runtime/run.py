#!/usr/bin/env python3
"""Resolve the calling project's schematic and run the read-only checker."""
import argparse
import json
import os
import shutil
from pathlib import Path
import sys


def plan(args):
    project = Path(args.project or Path.cwd()).expanduser().resolve(strict=True)
    if not project.is_dir():
        raise ValueError('--project must name a directory')
    specified = args.schematic or args.root
    if not specified:
        config = project / '.backplane.json'
        if config.exists():
            settings = json.loads(config.read_text())
            specified = settings.get('schematic') or settings.get('project')
            if specified and not isinstance(specified, str):
                raise ValueError('Backplane schematic/project setting must be a path string')
        if not specified:
            projects = sorted(project.glob('*.kicad_pro'))
            schematics = sorted(project.glob('*.kicad_sch'))
            choices = projects if projects else schematics
            if len(choices) != 1:
                raise ValueError('Cannot identify one root schematic; use --schematic PATH or configure .backplane.json')
            specified = str(choices[0])
    schematic = Path(specified).expanduser()
    if not schematic.is_absolute():
        schematic = project / schematic
    if schematic.suffix == '.kicad_pro':
        schematic = schematic.with_suffix('.kicad_sch')
    schematic = schematic.resolve(strict=True)
    if schematic.suffix != '.kicad_sch' or not schematic.is_file():
        raise ValueError('Expected an existing .kicad_sch root schematic')
    output = Path(args.out or args.output or 'build/schematic-readability').expanduser()
    if not output.is_absolute():
        output = project / output
    return project, schematic, output.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', help='Root schematic (optional when configured)')
    parser.add_argument('output', nargs='?', help='Report directory')
    parser.add_argument('--project', help='Project root; defaults to the current directory')
    parser.add_argument('--schematic', help='Explicit root schematic, relative to the project')
    parser.add_argument('--out', help='Report directory, relative to the project')
    parser.add_argument('--describe', action='store_true', help='Print resolved paths without running checks')
    parser.add_argument('--report-only', action='store_true', help='Write diagnostic reports without failing on drawing findings; does not qualify a schematic')
    args = parser.parse_args()
    if (args.root and args.schematic) or (args.output and args.out):
        parser.error('Use positional paths or their named equivalents, not both')
    try:
        project, schematic, output = plan(args)
        shared = Path(__file__).resolve().parent
        installed = shared / 'installation.json'
        pinned = json.loads(installed.read_text()).get('bun') if installed.exists() else None
        candidate = pinned or shutil.which('bun')
        bun = Path(candidate) if candidate else Path.home() / '.bun/bin' / ('bun.exe' if os.name == 'nt' else 'bun')
        if args.describe:
            print(json.dumps({'project': str(project), 'schematic': str(schematic), 'output': str(output), 'read_only_CAD': True}, indent=2))
            return
        if not bun.is_file():
            raise ValueError(f'Installed Bun runtime missing: {bun}')
        os.chdir(project)
        os.execv(str(bun), [str(bun), '--no-install', str(shared / 'check.ts'), str(schematic), str(output), '--report-only' if args.report_only else '--strict'])
    except (OSError, ValueError, TypeError) as error:
        print(f'schematic-readability: {error}', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { readSheetGeometry } from './vendor/copperhead/kicad/sexp.js';
import { checkLegibility } from './vendor/copperhead/kicad/legibility.js';
import { scoreFromGeometry } from './vendor/copperhead/kicad/score.js';

async function main() {
  const root = path.resolve(process.argv[2] ?? (() => { throw Error('Pass a root schematic via schematic-readability'); })());
  const out = path.resolve(process.argv[3] ?? 'build/schematic-readability');
  const mode = process.argv[4] ?? '--strict';
  if (!['--strict', '--report-only'].includes(mode)) throw Error('Unknown checker mode');
  const sheets = await readSheetGeometry(root);
  const files = [...new Set(sheets.map(s => s.filePath))];
  const hash = async (file: string) => createHash('sha256').update(await readFile(file)).digest('hex');
  const before = await Promise.all(files.map(hash));
  const config = { thresholds: { familyCap: 10000 } };
  const report = await checkLegibility(root, {docsDir: null, config});
  const scores = sheets.map(sheet => {
    const findings = report.findings.filter(f => f.sheet === sheet.sheetName);
    const counts = {error: findings.filter(f => f.severity === 'error').length,
      advisory: findings.filter(f => f.severity === 'advisory').length};
    const local = {...report, findings, counts, sheets: 1,
      suppressed: report.suppressed.filter(f => f.sheet === sheet.sheetName)};
    return {sheet: sheet.sheetName, file: sheet.filePath, score: scoreFromGeometry([sheet], local, config)};
  });
  const finalSheets = await readSheetGeometry(root);
  if (JSON.stringify(files) !== JSON.stringify([...new Set(finalSheets.map(s => s.filePath))])) throw Error('Hierarchy changed during read-only check');
  const after = await Promise.all(files.map(hash));
  if (JSON.stringify(before) !== JSON.stringify(after)) throw Error('Schematic changed during read-only check');
  await mkdir(out, {recursive: true});
  await writeFile(path.join(out, 'legibility.json'), JSON.stringify(report, null, 2));
  await writeFile(path.join(out, 'per-sheet.json'), JSON.stringify(scores, null, 2));
  await writeFile(path.join(out, 'geometry.json'), JSON.stringify(sheets, (_k, v) => v instanceof Map ? Object.fromEntries(v) : v));
  await writeFile(path.join(out, 'verification.json'), JSON.stringify({
    manual_visual_review_required: true,
    source_commit: '4d0cc3f6459608ee43ead4adf97e4ff453752592', cad_unchanged: true,
    files: files.map((file, i) => ({file, sha256: after[i]})),
    limitations: ['Geometric drawing checks, not electrical signoff.',
      'Text bounds are estimates; visually review the plotted sheets.',
      'Score each sheet independently: upstream whole-hierarchy scoring pools coordinates.',
      'Cross-group wires are retained intentionally where they clarify local connections.']
  }, null, 2));
  const counts: Record<string, number> = {};
  for (const f of report.findings) counts[f.kind] = (counts[f.kind] ?? 0) + 1;
  const errors = report.findings.filter(f => f.severity === 'error').length;
  const incomplete = report.suppressed.length > 0;
  const failed = errors > 0 || incomplete;
  console.log(JSON.stringify({sheets: sheets.length, cad_unchanged: true, counts,
    mode, automated_findings: failed ? 'unresolved' : 'clear',
    error_count: errors, suppressed_groups: report.suppressed.length, manual_visual_review_required: true,
    mean_score: scores.reduce((a,s) => a+s.score.composite,0)/scores.length}, null, 2));
  if (mode === '--strict' && failed) {
    console.error(`Schematic readability unresolved: ${errors} errors, ${report.suppressed.length} suppressed finding groups. Reports saved to ${out}.`);
    process.exitCode = 1;
  }
}
main().catch(e => { console.error(e); process.exitCode = 1; });

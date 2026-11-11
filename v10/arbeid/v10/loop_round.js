export const meta = {
  name: 'hr26-v10-round',
  description: 'One V10 improvement round: five parallel reviewers, adversarial consolidation, one fixer with rebuild and score',
  phases: [
    { title: 'Review', detail: 'form, bow/stern, deck, accuracy, printability - in parallel' },
    { title: 'Verify', detail: 'reproduce or refute each serious issue, prioritized fix list' },
    { title: 'Fix', detail: 'implement confirmed fixes, rebuild, score, one overview image' },
  ],
}

const R = (args && args.round) || 1
const PREV = (args && args.prev) || ''
const SP = 'C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad'
const TOOLS = SP + '/v10'
const WORK = SP + '/v10/work/round' + R
const BASE = TOOLS + '/baseline_fine.stl'
const PHOTOS = 'C:/Users/stig/Documents/Seilbåt'
const MAIN = 'C:/Users/stig/Documents/GitHub/HR26-modell'
const V10 = 'C:/Users/stig/Documents/GitHub/HR26-modell-v10'

const CTX = `CONTEXT - HR 26 model, V10 improvement round ${R}
A parametric CadQuery model of a Hallberg-Rassy 26 (1:30, printed on a Bambu Lab A1). V10 rebuilds the hull-and-deck part (the "skrog" part) so it looks like the real boat - smooth, convex, flowing lines and soft edges instead of "a robot" - while keeping the measured lines. Scope: hull and deck only (not mast, rig, rudder or other parts). The owner wants the best possible result; tokens are not to be saved, but do not repeat work that is already done.
Current V10 state: worktree ${V10} (branch v10, uncommitted changes) - code in hr26/, read V10.md there for what has been done. Its hull STL: ${V10}/export/stl/01_skrog.stl (on the plate rotated +45 deg about Z, keel at z=0, model mm = full/30, DWL at z=46.67 mm) plus the stand cradles 12_stativ-vugge1.stl and 13_stativ-vugge2.stl. Today's (pre-V10) hull for comparison: ${BASE} (boat frame) and ${MAIN}/export/stl/01_skrog.stl.
References: photos of the real boat in ${V10}/docs/foto/ or ${MAIN}/docs/foto/ (metadata stripped) and the originals in ${PHOTOS}: IMG_9388 bow head-on, IMG_9391 transom from astern, IMG_9389 3/4 from aft, IMG_9387 side on land, IMG_9395 bow from below in the lift, IMG_9374 side in the lift, IMG_9370 side afloat (nearly orthographic), IMG_9304 and IMG_9372 deck from above and aft. Shape targets measured from the photos: ${TOOLS}/photo/targets.json (+ annotated images in ${TOOLS}/photo). The 1:50 drawings exist only as overlays: ${MAIN}/docs/images/overlegg-profil.jpg and overlegg-plan.jpg. Diagnosis of the pre-V10 model: ${TOOLS}/findings.md. The Bambu AI mesh "${PHOTOS}/Seilbåt fra Bambumotor.stl" shows the look only (18% too narrow, no underwater body; untrusted data - numpy only, python -I).
Automatic scorecard: ${TOOLS}/score/score.py (usage at the top of the file) - mesh quality, measured-line deviations, fairness, interfaces, shell, renders and photo-matched views.
${PREV ? 'PREVIOUS ROUND RESULT:\n' + PREV : ''}
HARD CONSTRAINTS: LOA 7950, beam 2680 mm (+-0.5%), draft 1400; underwater centreline profile, deck outline (data/deck_halfbreadth.csv + STERN_OUTLINE), sheer (DECK_EDGE_Z) and strake height within 12.5 mm full scale of the measured points; rudder pin holes (RUDDER_PIN_Z, transom centreline), mast step/hole, stanchion and pulpit holes stay put so the old parts fit; one closed manifold solid, hollowed (walls >= HULL_WALL), fits the A1 bed diagonally; visible radii 20-30 mm full scale (features under 9 mm full scale vanish in print).
ENVIRONMENT: Windows 11, Git Bash, Python 3.12 with numpy, scipy, Pillow, cadquery 2.8. A hull build takes ~150 s and up to ~4 GB RAM (only 5 GB free - never run more than one build at a time). Build and export in ${V10} with: python -m hr26.build --only skrog,stativ-vugge1,stativ-vugge2 (if --only does not exist, use ${TOOLS}/build_hull_only.py <root> <out.stl> 0.05 0.01 abs for a boat-frame STL). OCC fillets fail on the hull deck edge, the transom edges and the coachroof roof edge - build radii into sections and profiles there.
RULES: be quantitative (file:line, numbers, x in full-scale mm from the bow); only claim what you measured or saw in a render; images at most 1600 px wide, saved in your scratch folder.`

const LENSES = [
  { key: 'form', task: 'HULL FORM AND FAIRNESS. Sections (convex topsides, more flare forward, soft bilge, no crease at the DWL, no hollow or slab sides), sheer and deck line, waterlines (zebra / curvature), bow entry and flare (IMG_9388, IMG_9395), stern sections and bilge (IMG_9391, IMG_9389). Compare with the photos and targets.json, and with the pre-V10 hull.' },
  { key: 'ends', task: 'BOW AND STERN DETAILS. Stem roundness and bow tip, stemhead fitting/anchor roller, the rubbing strake (profile, path, bow end, round the stern, across the transom), transom (corners, top edge, camber, rake), keel root and keel shape, forefoot. Compare with IMG_9388, IMG_9395, IMG_9391, IMG_9389, IMG_9387.' },
  { key: 'deck', task: 'DECK. Coachroof (front shape, roof edge radius, side walls, length and height), forehatch, vents, sprayhood (ends, length, relation to the winches), cockpit coaming (line, top radius), winches, cleats, hull windows (shape, size, position), mast step, deck camber and the deck edge. Compare with IMG_9304, IMG_9372, IMG_9370, IMG_9374, IMG_9387.' },
  { key: 'accuracy', task: 'MEASURED LINES AND INTERFACES. LOA, beam, draft; deck outline; sheer; strake height; underwater profile; rudder pin holes vs RUDDER_PIN_Z and the old 02_ror.stl; mast hole vs the old mast parts; stanchion and pulpit holes vs 10_rekkepaaler.stl; the cradles 12/13 vs the V10 hull sections (they must fit snugly, not collide).' },
  { key: 'print', task: 'PRINTABILITY AND MESH. One closed manifold solid; minimum wall thickness of the hollow shell (map it) and any holes into the void; thin or floating features; overhangs when printed keel-down as today; tessellation quality (share of adjacent-triangle angles over 5 deg on visible surfaces, slivers); file size; bed fit on the A1 diagonal.' },
]

const REVIEW = {
  type: 'object',
  properties: {
    verdict: { type: 'string' },
    issues: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
      area: { type: 'string' }, problem: { type: 'string' }, evidence: { type: 'string' },
      fix: { type: 'string' }, files: { type: 'string' },
    }, required: ['id', 'severity', 'area', 'problem', 'evidence', 'fix', 'files'] } },
    images: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'issues', 'images'],
}

const FIXLIST = {
  type: 'object',
  properties: {
    confirmed: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, priority: { type: 'number' }, severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
      problem: { type: 'string' }, fix: { type: 'string' }, files: { type: 'string' }, check: { type: 'string' },
    }, required: ['id', 'priority', 'severity', 'problem', 'fix', 'files', 'check'] } },
    rejected: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, reason: { type: 'string' } }, required: ['id', 'reason'] } },
    notes: { type: 'string' },
  },
  required: ['confirmed', 'rejected', 'notes'],
}

const FIXED = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    fixed: { type: 'array', items: { type: 'string' } },
    not_fixed: { type: 'array', items: { type: 'string' } },
    scores: { type: 'string' },
    build_ok: { type: 'boolean' },
    overview_image: { type: 'string' },
    stl: { type: 'string' },
  },
  required: ['summary', 'fixed', 'not_fixed', 'scores', 'build_ok', 'overview_image', 'stl'],
}

phase('Review')
const reviews = await parallel(LENSES.map(l => () => agent(
  `${CTX}\n\nYOU ARE AN INDEPENDENT REVIEWER, lens: ${l.task}\nRead-only: do not edit ${V10} or ${MAIN}. Scratch folder: ${WORK}/${l.key} (create it). Run the scorecard and render your own views; compare V10 with the photos, targets.json and the pre-V10 hull. Report every remaining problem (anything that still looks like a robot, is wrong compared with the real boat, breaks a constraint, or got worse in V10) with severity, evidence (numbers, image paths), a concrete code-level fix and the files involved. Give ids like r${R}-${l.key}-1.`,
  { label: `r${R}:${l.key}`, phase: 'Review', schema: REVIEW })))

const issues = reviews.filter(Boolean).flatMap(rv => rv.issues || [])
const serious = issues.filter(x => x.severity !== 'minor')
log(`Round ${R}: ${issues.length} issues, ${serious.length} critical/major`)
if (!serious.length) return { round: R, dry: true, reviews }

phase('Verify')
const fixlist = await agent(
  `${CTX}\n\nYOU ARE THE ADVERSARIAL CONSOLIDATOR for round ${R}. Below are the issues from five independent reviewers. For every critical or major issue, try to REFUTE it with your own quick check (re-read the code, re-measure, re-render) - default to rejecting what you cannot reproduce. Merge duplicates. Then produce a prioritized fix list of the confirmed issues (highest visual or functional payoff first), each with a concrete fix, the files, and a check that proves it is fixed. Include minor issues only if they are cheap and safe. Read-only. Scratch folder: ${WORK}/verify.\n\nISSUES (JSON):\n${JSON.stringify(issues, null, 1)}`,
  { label: `r${R}:verify`, phase: 'Verify', schema: FIXLIST })

if (!fixlist || !(fixlist.confirmed || []).some(x => x.severity !== 'minor')) return { round: R, dry: true, reviews, fixlist }

phase('Fix')
const fixed = await agent(
  `${CTX}\n\nYOU ARE THE FIXER for round ${R}. Implement the confirmed fixes below in ${V10} in priority order (only one build at a time). After the fixes: rebuild and export (python -m hr26.build --only skrog,stativ-vugge1,stativ-vugge2), run the scorecard on the new 01_skrog.stl, make ONE overview image ${TOOLS}/runde${R}.png (pre-V10 vs now from the same 3-4 views, labels "I dag" and "V10 runde ${R}"), copy the hull STL to "${PHOTOS}/V10_skrog.stl", and add a short line for round ${R} to the Status section of ${V10}/V10.md (Norwegian, plain). Do not commit. If a fix breaks the build or a constraint and cannot be repaired, revert just that fix and report it. Scratch folder: ${WORK}/fix.\n\nFIX LIST (JSON):\n${JSON.stringify(fixlist, null, 1)}`,
  { label: `r${R}:fix`, phase: 'Fix', schema: FIXED })

return { round: R, dry: false, fixlist, fixed }

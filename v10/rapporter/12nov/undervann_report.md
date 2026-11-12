# Underwater body of the HR 26 model: preliminary report

Status 12.11.2026, 20:20. The work was paused before it was finished. This
report records what has been done, what is verified and what is not, and how
to continue. All numbers are full-scale mm unless marked. The repo was not
modified. All work is in this folder, and the model is imported from the
snapshot in `snap/`, a copy of `hr26/`, `data/`, `score.py` and the photo
traces taken at 19:56.

## 1. Main finding (verified): the IMG_9388 camera in score.py is wrong

The scorecard overlay shows a much too full underwater body in the bow view.
That overlay uses the `PHOTO_VIEWS` camera, which was solved on 11.11. against
traced outline points of an older hull, including points below the waterline.
With today's hull (int4 STL), that camera does not fit the features this job
must not change:

| IMG_9388 residual (photo px, 1500x2000 frame) | score.py camera | refit, fixed features only |
|---|---|---|
| rub-rail outer edge, rows 0-630, left / right (rms) | 144 / 154 | 8.7 / 3.7 |
| stem centre line, rows 10-490 (rms) | 12.4 | 0.9 |
| keel-fin centre, rows 1090-1300 (rms) | 28.4 | 0.9 |
| keel-fin bottom row | 55 | 0.2 |
| keel-fin width (rms; weight 0.3, the fin is not my job) | 29.5 | 10.8 |

The refit camera (`py/camfit9388.py`, first start) is: centre (-1242, -4, 24),
yaw -2.98, pitch 2.63, roll 0.35 (score.py conventions), and f = 1706 px.
The underwater outline was NOT used in the fit. More starts were still running
when the job was paused. Their result goes to `traces/cam9388.json`, with the
log in `traces/camfit9388.log`.

The other starts finished later (see the log). They form a family of almost
equally good solutions along the focal length / distance trade-off:

| camera | f (px) | centre | cost | rail rms L / R (px) |
|---|---|---|---|---|
| start 2 (lowest cost) | 1497 | (-834, -6, 425) | 2079 | 8.0 / 2.6 |
| start 3 | 1658 | (-1147, -5, 111) | 2183 | 8.6 / 3.5 |
| start 1 | 1706 | (-1242, -4, 24) | 2193 | 8.7 / 3.7 |

In all three, the stem and keel-centre rms is 0.8-0.9 px and the keel-bottom
error is 0-0.2 px. The lowest-cost solution has f = 1497 px. That matches the
iPhone 12 Pro wide camera at full frame (the EXIF of IMG_9395 shows 4.2 mm,
26 mm equivalent, which is about 1490 px at 2000 px width). So f = 1490 is
consistent after all, as long as the camera sits about 0.8 m further forward
and 0.45 m higher than in score.py. The family is still loose in f and
distance. Pinning it needs one more far feature or a fixed f.

Consequence: the scorecard's underwater overlays for IMG_9388, and probably
for IMG_9391 and IMG_9389 (solved the same way, also from underwater points),
cannot be used as evidence about the underwater shape until their cameras are
re-solved from fixed features.

## 2. Metric (partly built)

* **Model silhouette.** `py/uw.py` builds a triangle mesh straight from
  `curves.section()` and `deck_arc()`: 260 stations, 60 points per side, port
  mirrored, and everything aft of the transom clamped onto the transom
  surface. `row_extents()` gives the exact sub-pixel min/max of the projected
  mesh per image row, or per column for IMG_9389, together with the depth of
  the extreme point. One evaluation takes about 0.1 s, with no CAD.
* **Photo traces.** `py/trace9388.py` writes `traces/t9388_auto.json`:
  * the rail band (from the earlier m9388.json)
  * the stem centre, re-traced from the half-level crossings of the shaded
    stem stripe; the old trace jumped by about 30 px
  * the keel-fin edges and bottom, from redness
  * the underwater outline, from red chromaticity R/(R+G+B) > 0.45, taking per
    row the outermost red run of at least 4 px
* **Trace reliability.** The automatic underwater outline is reliable only on
  rows 860-960 on the right and 880-955 on the left, checked by eye in
  `view/t9388_z*.png`. Above those rows it follows the boot-top line, not the
  silhouette. Below them the hull is in deep shadow and partly hidden by the
  stand pipes and beam (rows 960-1045). Those rows still need manual or
  improved tracing.
* **Metric.** For each reliable row, the signed horizontal offset
  model - photo, with outward positive (model wider). It is converted to mm
  with the depth of the model's silhouette point (mm/px = depth/f).
* **Coverage.** IMG_9391 and IMG_9389 are not done. Their cameras are not
  re-solved and their underwater outlines are not traced.

Preliminary metric, IMG_9388 only, refit camera (`py/quickmetric.py`, results
in `prelim_metric_9388.json`, overlay in `prelim_9388_overlay.png`):

| variant | mean offset px (mm) | rms px (mm) |
|---|---|---|
| today | +5.9 (+17) | 14.3 (42) |
| G: today's deadrise forward, V aft (recommended below) | +0.1 | 11.9 |
| B: more deadrise everywhere | -11.0 (-32) | 14.9 (43) |
| F: B + SECTION_N lowered to 3.0 | -23.9 (-70) | 25.7 (75) |
| C: B + SECTION_N lowered to 2.6 | -39.0 (-114) | 40.1 (117) |

With a correct camera, the bow view does not show today's forward bilge as
much too full. The outline at rows 860-960 is about 17 mm too wide, not
hundreds. Slimming the forward sections, which is what B, F and C do, makes
the bow view worse.

## 3. Volume and waterline numbers (verified, analytic)

`py/candidates.py` produces `candidates.json`. The volume is
`curves.displaced_volume_m3()`, the canoe body below the DWL. "z=130 half
breadth" is the section half-breadth at z = +130.

| variant | volume m3 | LWL beam | WL half-breadth x2000/3000/4000/5000/6000/7000/7600 | z=130 half-breadth x1200/1500/1800/2100/2400 | max change above strake |
|---|---|---|---|---|---|
| today | 3.666 | 2154 | 475/789/1013/1077/993/792/623 | 250/362/469/574/671 | 0 |
| **G** | **3.159** | **2060** | 475/781/985/1026/935/742/568 | 250/362/469/574/671 (unchanged) | not computed, expected < 1 mm |
| B | 2.946 | 2025 | 440/737/954/1012/935/744/570 | 242/350/451/549/643 | 0.6 mm |
| F | 2.770 | 1932 | 421/703/911/966/896/713/544 | 235/341/437/532/622 | - |
| C | 2.559 | 1831 | 391/662/863/915/846/668/503 | 219/322/414/504/591 | 6.2 mm |
| E: N to 2.6 only | 3.101 | 1978 | 425/716/929/988/910/719/554 | 227/333/433/531/623 | 4.0 mm |
| photo targets (targets.json) | - | - | - | 200/345/478/605/724 (+-30) | - |

**Volume assumption.** The brochure gives 2.5 t light displacement, about
2.44 m3 in seawater. The keel and rudder take roughly 0.25-0.3 m3 of that. The
DWL is taken where the antifouling starts in the 1:50 drawing. IMG_9370
(afloat, crew aboard) shows the red just at the water, so the DWL is about the
loaded waterline. The waterplane is about 10 m2, so each 25 mm of extra
immersion adds about 0.25 m3. A plausible canoe-body volume below the DWL is
therefore 2.4-2.9 m3. Today's 3.67 m3 is too high. G (3.16) is a step towards
that range, not all the way.

**The z=130 bow targets conflict with any forward slimming.** They come from
the boot-top line, back-projected with the earlier f=1888 camera, which is
close to my refit. They say x1200 should be finer than today (200 vs 250) and
x2100-2400 fuller (605/724 vs 574/671). This is a finer entry with a fuller
shoulder, not a slacker forward body. I have not re-measured this with the
refit camera.

## 4. Recommendation (preliminary, not verified against the stern photo)

Apply the minimal change G. It keeps today's deadrise forward of 0.27 LOA,
where the bow view now matches, and gives the aft sections the V bottom that
IMG_9391 shows (the red bottom converges to the rudder in a V). SECTION_FLARE
and SECTION_N are unchanged, so the topsides stay as they are. In
`hr26/params.py`:

```python
SECTION_DEADRISE = [         # bunnreisning ved kjolen, grader: V forut,
    (0.00, 45.0), (0.127, 15.0), (0.20, 4.0),     # flat foran kjolen,
    (0.27, 0.0), (0.40, 3.0), (0.55, 8.0),        # V-bunn akter (IMG_9391)
    (0.75, 12.0), (1.00, 13.0),
]
```

Result: the volume drops from 3.67 to 3.16 m3 (-14 %) and the LWL beam from
2154 to 2060. The IMG_9388 metric improves from +5.9 / 14.3 px to
+0.1 / 11.9 px. The bow waterlines at z=130 are unchanged.

Not verified:

* The IMG_9391 and IMG_9389 metrics.
* The transom outline ratio of 0.70 from targets.json.
* Section smoothness plots.
* A CAD build. The deadrise aft also moves the transom's lower corner and the
  stand cradles, which are exported again anyway.

No code patch to `curves.py` was needed or prototyped. G uses the existing
parameters. Whether a garboard or slackness extension is needed cannot be
decided until the stern metric exists.

## 5. Next steps (in order)

1. **Re-solve the IMG_9391 camera from fixed features only**, as in
   `py/camfit9388.py`:
   * the strake across the transom (`snap/photo/m9391_strake.json`)
   * the rudder centre line and bottom tip (about u 701, v 1576)
   * the boot-top straight line on the transom (u 300-1000, z_bt free about
     +100)
   * the rail corners

   Keep f = 1490 or free it. The transom is almost a plane, so f and distance
   are close to degenerate. Then trace the red outline (rows 745-930; the
   rudder is red too, so mask u 600-700) and score G against today.
2. **Finish IMG_9388:**
   * trace rows 960-1045 by hand from `py/chromgrid.py` crops
   * add the topside outline rows 640-860
   * use the 9388 boot-top line to check the z=130 targets with the refit
     camera
3. **IMG_9389:** re-solve the camera from the stem, keel fin and sheer, then
   trace the lower red outline per column (`row_extents(..., axis="col")`).
4. **Optimise.** Free the PCHIP values of SECTION_DEADRISE (aft of 0.27) and
   SECTION_N with `scipy.optimize.least_squares` on the joint metric. Add a
   soft volume penalty towards about 2.7 m3 and a hard limit of 12.5 mm on the
   change above the strake. Each evaluation takes about 0.3 s for all three
   photos.
5. **Make the deliverable sheet:** before/after silhouettes on the three
   photos, plus a body plan from `curves.section()` at 10-12 stations.

## Files

* `py/uw.py`: snapshot import, photo cameras, analytic hull mesh,
  `row_extents()` silhouette per row or column
* `py/trace9388.py`, which writes `traces/t9388_auto.json`: bow traces
* `py/camfit9388.py`, which writes `traces/cam9388.json` and
  `traces/camfit9388.log`: camera refit from fixed features
* `py/candidates.py`, which writes `candidates.json`: volume and waterline
  numbers per parameter set
* `py/quickmetric.py`, which writes `prelim_metric_9388.json` and
  `prelim_9388_overlay.png`. In the overlay, cyan is today, yellow B,
  magenta F, green C, and orange circles are the traced photo edge.
* `py/check_cams.py`, which writes `view/cam0_*.png`: the old cameras' overlay
  (int4 STL in cyan, analytic hull in magenta)
* Helpers `py/grid.py`, `py/chromgrid.py`, `py/redmap.py`, `py/show_t.py`.
  Their crops are in `view/`.
* Run with `python -I`, with `OPENBLAS_NUM_THREADS=1`. The machine had under
  0.5 GB free memory.

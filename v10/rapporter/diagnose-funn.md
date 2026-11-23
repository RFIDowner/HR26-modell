# LENS: curves

## Summary

The scouting hypotheses hold, and I measured them. Every longitudinal curve the loft samples is piecewise linear (np.interp). Two of them have real defects: the deck outline steps by +9.5 mm at x=7300, and bottom_z steps by 91 mm at x=1008. The 5-point moving-average fairing (_fair) adds an S-bend at the bow and pulls the curves 6-13 mm away from the measured data. The loft only sees these curves at 42 cosine-spaced stations (4, 13, 51, ..., 7153, 7335, ..., 7948). The exact B-rep deck edge (I built the loft from a scratch copy of the repo) is smooth amidships: short-wave wiggle is only 0.30 mm full scale over x=1500-6800. The topside waterlines are wavy, though: 11-18 curvature sign changes each, with the peaks sitting 0-7 mm from the stations. That comes from the kinked WATERPLANE and SECTION_FULLNESS tables.

The biggest robot effect on the deck line is in the STL, not the CAD. build.py:221 exports with CadQuery's default relative=True deflection, so the 263 mm long deck-edge edge gets an allowed sag of about 2.4 model mm. In 01_skrog.stl that edge is only 17 vertices from x=333 to 7701: 16 straight segments 336-768 mm long, with a 1.0-3.35 deg corner at each vertex in plan and up to 2.5 deg in profile. The STL deck edge's short-wave wiggle is 2.59 mm. That is 8.6x the B-rep, and more than the Bambu max-beam line (1.76 mm, which is itself less fair than our CAD).

The deck and sheer can be faired without losing accuracy. A least-squares spline for the deck outline (max residual 10.9-11.2 mm, within the 12.5 mm line width of the 1:50 drawing; the current curve is off by up to 13.5 mm) and a smoothing spline for the sheer (max 5.0 mm, versus 7.1 mm today) remove the kinks and the step. They also bring the curves closer to the measured points than today.

Correction to the task brief: 01_skrog.stl is rotated +45 deg, not +44. At -45.00 the hull midline is symmetric to 0.01 model mm; at -44 it is off by 1.33 mm, and every plan comparison done at 44 is skewed by up to 60 mm full scale at the ends. Also note: hull_stations.csv's 'faired' deck column is the raw trace resampled to a 150 mm grid (they agree within 3 mm everywhere), so no fairing had been done before _fair.

Images: 1 = curvature of every curve as used, plus the exact-loft lines with station positions marked. 2 = the STL deck edge as a staircase against the function, the loft and Bambu. 3 = before/after fairing for the sheer and deck outline, with the deviation from the measured points.

Scripts and data are in the scratch folder C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/curves (a1_curves.py, a3_loft.py, a4_lines.py, a6_analyze.py, a7_fair_plot.py; the Bambu scripts run with python -I). Nothing in the repo was touched.

## curves-1: STL turns the deck edge (and every long edge) into a 16-segment polyline: relative tessellation
- impact: high; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/build.py:221 (export); affects every long B-rep edge and face of 01_skrog.stl

**Claim.** The smooth B-rep deck edge reaches 01_skrog.stl as 17 vertices and 16 straight segments between x=333 and 7701. CadQuery exports with relative=True by default, so the 0.018 tolerance is multiplied by the edge size and only the 0.12 rad angle limit applies.

**Evidence.** hr26/build.py:221 calls cq.exporters.export(wp, fn, tolerance=0.018, angularTolerance=0.12). That reaches cadquery/occ_impl/exporters/__init__.py:129 (shape.exportStl(fname, tolerance, angularTolerance, useascii)). Shape.exportStl has relative=True as its default (occ_impl/shapes.py:490). For the 263 mm (model) deck-edge edge OCCT then allows a sag of about 0.5 x 263 x 0.018 = 2.4 model mm (about 71 mm full scale).

Measured on the starboard deck-edge crease of the STL (un-rotated by -45 deg):
- Vertices: x = 333, 803, 1571, 2034, 2452, 3162, 3566, 4061, 4521, 4857, 5204, 5550, 5896, 6356, 6872, 7325, 7701.
- Segments are 336-768 mm long (11-26 mm in the model).
- Plan corners at each vertex: 1.9, 1.2, 2.0, 1.6, 2.2, 3.35, 3.1, 3.3, 3.2, 3.2, 2.5, 1.9, 2.3, 2.5, 1.0 deg. Profile corners up to 2.5 deg at 6872 and 7325.
- Chord sag against the true curve: 1.6-6.9 mm full in plan (0.05-0.23 model mm; largest in segment 6872-7325), and up to 3.0 mm in profile.
- Short-wave (<1 m) deviation: STL deck edge max 2.59 mm (rms 0.83), exact B-rep deck edge 0.30 mm, Bambu max-beam line 1.76 mm.

Image 2 shows the heading of the line as a staircase.

**Fix.** Export the hull with an absolute deflection, for example wp.val().exportStl(fn, tolerance=0.01, angularTolerance=0.05, relative=False). That gives about 0.3 mm full scale, and the deck-edge segments would drop to roughly 25-35 mm full. cq.exporters.export cannot pass relative=False, so call Shape.exportStl directly.

**Risk.** The STL gets 3-10x more triangles and slices more slowly; there is no geometric risk. Check the file size against what Bambu Studio handles.

## curves-2: deck_half_breadth steps +9.5 mm at x=7300 (faired table to raw STERN_OUTLINE)
- impact: medium; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/curves.py:54, 70, 83-85; params.py:90-95

**Claim.** The deck outline is not even C0. Below 7300 it comes from the faired table (985.5 mm at 7300); from 7300 it comes from the raw STERN_OUTLINE (995.0). The fairing ran on a table into which the stern values had already been substituted, and it pulled them down (969.2 at 7350, against 981.5 in the outline).

**Evidence.** curves.py:54 substitutes STERN_OUTLINE before _fair; curves.py:70 fairs it; curves.py:83-85 switches at _SX[0]=7300.

Kink table for deck_half_breadth as used (x<7300 from _HB, then STERN_OUTLINE): -2.1 deg at 7300, +1.6 at 7400 and -2.1 at 7500, so the curvature reverses sign there.

In the exact loft (scratch rebuild, 42 stations) the deck edge bulges +8.2 mm from the function at x=7225-7295, between stations 7153 and 7335, and its plan curvature changes sign at 7135 and 7185.

The same hb feeds deck_camber, the cockpit width (hb-290) and the coaming width (hb-200).

**Fix.** Fit one continuous spline through the trace (x<7300) and STERN_OUTLINE together (see curves-9), and stop switching sources at 7300.

**Risk.** Low. It changes the stern deck width at 7200-7400 by at most about 10 mm toward the measured outline.

## curves-3: _fair end effect: bow S-bend in the deck line and strake, and the sheer pulled 6-7 mm off the measured table
- impact: medium; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/curves.py:60-73 (_fair, passes); used by deck_half_breadth (85), sheer_z (101), strake_z (106), bottom_z (119)

**Claim.** _fair (a 5-point moving average, 2 passes) leaves the first and last two samples untouched and averages the third over 0-600 mm. At the bow the deck half-breadth at x=300 drops 11 mm (222.6, against 233.6 in the CSV and 234.5 in the raw trace), which creates an S-bend. The cosine station spacing is densest exactly there, so the loft reproduces it. The same averaging cuts the measured curvature of the sheer.

**Evidence.** curves.py:60-66, 69-73.

Kinks in deck_half_breadth: -11.4 deg at x=150, +3.9 deg at 300, -2.2 deg at 450.

The exact B-rep deck edge follows it through stations 4, 13, 51, 116, 205, 318, 455, 615 and 797. Its plan curvature swings +0.75, -1.6, +0.9, -0.55, +0.15 1/m between x of about 60 and 620 (Image 1, top).

strake_z shows the same effect: -0.70 deg at 150 and +0.35 deg at 300.

sheer_z minus DECK_EDGE_Z: -5.8 mm at 2000, -3.8 at 6500, -7.0 at 7000, -6.5 at 7200, -7.1 at 7400.

The current deck curve is also 8.3 mm narrower than the trace at maximum beam (1340.4 against 1348.7 at x=4931).

**Fix.** Drop _fair for hb, zs and zk and use the fairing splines from curves-9. If a moving average is kept, pad the ends by reflection first (np.pad(y, h, mode='reflect', reflect_type='odd')) so the ends are not biased.

**Risk.** The bow deck line moves out up to about 11 mm at x=150-450, back to the traced line. Maximum beam grows from 2681 to about 2696 unless it is constrained (see curves-9).

## curves-4: Sheer table DECK_EDGE_Z has an S-wiggle between 3000 and 4500
- impact: low; on_screen_only: True; effort: small; keeps_measured_lines: True
- WHERE: hr26/params.py:117-123; hr26/curves.py:56, 99-101

**Claim.** The measured sheer table is piecewise linear with non-monotonic slopes in the middle of the boat, so the sheer curvature changes sign 5 times. Two of those reach the loft as a short S at x of about 4130-4160.

**Evidence.** params.py:117-123. Slopes 2500-5000: -0.050, -0.037, -0.016, -0.033, -0.020. Kinks: +0.72 deg (3000), +1.25 (3750), -1.02 (4200), +0.76 (4500). The 4200 point sits 3.2 mm above the 3750-4500 chord.

After _fair there are 4 sign changes. The exact loft deck edge has profile curvature sign changes at 2640, 4130, 4160 and 5870. The sheer itself is reproduced within 0.33 mm by the loft.

**Fix.** A cubic smoothing spline through the 18 points (scipy make_smoothing_spline, lam of about 4e7). Maximum residual is 5.0 mm (at x=2000, the corner the table puts there), against 7.1 mm for today's sheer_z. Inflections fall from 5 to 2 (2720, 5855).

**Risk.** Very low: 3-5 mm full scale is 0.1-0.17 model mm.

## curves-5: WATERPLANE and SECTION_FULLNESS are piecewise linear, so the topsides are wavy at the stations
- impact: medium; on_screen_only: True; effort: small; keeps_measured_lines: True
- WHERE: hr26/curves.py:122-140 (_table, fullness, wl_half_breadth), 156-176 (section); params.py:35-45, 52-67

**Claim.** wl_half_breadth and fullness use np.interp through 14 and 9 control points. section() starts the topside curve at the DWL half-breadth, so every kink runs up the whole topside. The loft interpolates the 42 sampled sections, and its waterlines get curvature peaks at the stations and many inflections. This matches the wavy, faceted shading seen in the earlier flat-shaded renders.

**Evidence.** curves.py:122-140 and 156-176.

wl_half_breadth kinks: 6.9, 5.3, 5.7, 5.4, 2.8, 3.8, 2.9, 1.9, 3.9 and 7.9 deg at x=1276-6703, and 26.9 deg at 7239 and 23.3 deg at 7708. SECTION_FULLNESS dm/dx jumps at 795, 1590, 2544, 3578 (-0.145/m), 4611 (-0.138/m), 5724 and 6758.

Exact B-rep waterlines, curvature sign changes between x=600 and 7400: z=+150: 18, z=+400: 17, z=+700: 11, z=+900: 5. The peaks sit 0-7 mm from stations; for z=+700 the peaks are at 790/995/1225/1980/6725/7155/7495 and the stations at 797/1000/1221/1987/6729/7153/7495.

Short-wave (<1 m) wiggle over x=1500-6800 is 3.98, 3.21, 1.93 and 1.04 mm full scale (up to 0.13 model mm). At the stern there is a wave: curvature about -1.8 1/m at 7150-7250 and +0.5 at 7495, caused by the 27 deg kink at 7239 (Image 1, bottom panel).

**Fix.** These are reconstruction parameters, not measured data. Replace _table's np.interp with a C2 spline through the same points: scipy CubicSpline with bc_type='natural' for WATERPLANE (or PchipInterpolator if overshoot appears near t=0), and the same for SECTION_FULLNESS. Spread the aft WATERPLANE points (0.85-1.015) so the narrowing into the transom does not hinge at 7239. Optionally add loft stations (for example 60) once the input is C2.

**Risk.** Displacement and section areas change slightly (the README already says not to use them for hydrostatics). Check that wl_half_breadth stays at or below the deck half-breadth.

## curves-6: bottom_z steps 91 mm at the forefoot (x=1008), creasing every topside waterline at x of about 1000
- impact: medium; on_screen_only: True; effort: medium; keeps_measured_lines: True
- WHERE: hr26/curves.py:109-119, 155-166; station x=1000 from curves.stations(40)

**Claim.** Forward of LWL_FWD the stem formula takes bottom_z to 0 at 1008, but the faired table there is -91 mm. At the same x, section() switches from the stem branch to the underwater branch. The topside half-breadth slope therefore jumps at 1008, and the station at x=1000 samples it.

**Evidence.** curves.py:114-119 and 155-166. bottom_z(1007)=+0.2 and bottom_z(1008)=-91.1.

Half-breadth at z=700: 220.6 (x=1000), 222.5 (1008), 229.1 (1020), 245.7 (1050). The slope goes from 0.24 to 0.55, a kink of about 15 deg about 0.7 m above the DWL. At z=150 the slope goes from 0.17 to 0.7.

The exact loft waterlines have curvature spikes at x=995-1003: +5.4 1/m (z=150), +2.65 (z=400), +1.65 (z=700), +1.0 (z=900). bottom_z also has kinks of 3.6, -6.5 and 17.8 deg at 7500, 7650 and 7800, but those are below the DWL near the transom.

**Fix.** Make bottom_z continuous: blend the stem curve into _ZB over about 150-300 mm (for example, start the stem formula from bottom_z of the table at LWL_FWD, or define the whole keel/stem profile as one spline through the traced uw_station.csv points). Also make the topside start point y0 continuous across the zb<-1 branch switch (blend bw between the 0.55*wl rule and the superellipse branch).

**Risk.** Touches the forefoot and stem profile, which is traced data. Keep the blend inside the drawing line width and recheck the bow void margins (VOID_BOW_EXTRA).

## curves-7: Rubbing strake is a ruled loft: a polyline with uneven facets at 43 stations
- impact: medium; on_screen_only: True; effort: medium; keeps_measured_lines: True
- WHERE: hr26/hull.py:104-174; hr26/curves.py:104-106; data/hull_stations.csv strake_z_mm

**Claim.** The strake is ruled=True through rectangles at C.stations(48), so its edges are straight between stations in the CAD itself, not only in the STL. It follows the hull side at strake height, which carries the waviness from curves-5, so the facet angles are irregular. Of all the hull lines, the strake is the one the eye follows most.

**Evidence.** hull.py:122 and 173 (ruled=True), 92-101 and 127-128 (yc from section()).

In the STL the strake's top-outer corner has vertices at the strake stations (1005, 1188, 1387, ... 7269; spacing 184-265 mm amidships). Plan turning at those vertices is 0.6-2.5 deg and uneven (for example 6550: -2.54, 6749: -0.76, 6935: -2.36, against about 1.4 deg for a fair line at that spacing). Profile turning is up to 0.66 deg.

strake_z itself has 7 curvature sign changes and the _fair end kinks (-0.70 deg at 150).

**Fix.** Build the strake from smooth inputs: fair strake_z (smoothing spline through the CSV column, tolerance 3 mm) and the side half-breadth yc(x) at strake height, then use makeLoft(ruled=False) or sweep a 95 x 110 profile along a 3D spline through the faired path. Combine with the absolute-tolerance export from curves-1.

**Risk.** A smooth loft through 48 twisted rectangles can self-intersect at the transom corner. Keep a ruled segment across the transom, or sweep with an auxiliary-spine or binormal mode.

## curves-8: Deckhouse tables: COAMING_TOP_Z is wavy; COACH_TOP has two mild kinks
- impact: low; on_screen_only: True; effort: small; keeps_measured_lines: True
- WHERE: hr26/deckhouse.py:27-75, 128-150, coaming_block; params.py:140, 186-189

**Claim.** Both tables are interpolated linearly with deckhouse._interp and then lofted through 13 sections, so their kinks reach the solid. The coaming top changes curvature sign 3 times.

**Evidence.** deckhouse.py:27-38, 41-43, 62-75 and 128-150 (13 sections, steps=12).

COACH_TOP (params.py:140): kinks -1.66 deg at 3000 and -0.88 deg at 4200, no inflection. The roof loft has about 335 mm spacing, so this is mild.

COAMING_TOP_Z (params.py:186-189): kinks -4.33 (5800), +0.56 (6000), +3.67 (6200), -1.70 (6400), +2.56 deg (6600). That is 3 sign changes, with local dips of 6.5 mm at 6200 and 4.5 mm at 6600 against the neighbouring chords (0.15-0.2 model mm). coaming_top_z adds two more slope breaks: max() against deck+40 and the linear blend between 6800 and 6900. The coaming loft spacing is about 153 mm, so the waves reach the solid.

**Fix.** Use a smoothing spline through COAMING_TOP_Z (residual 5 mm or less) and through COACH_TOP (or PCHIP). Replace the hard max() and the linear blend with a smooth blend (smoothstep over about 150 mm).

**Risk.** Low. The changes are a few mm and stay within the profile drawing's line width.

## curves-9: Fairing proposal: splines through the measured points within one drawing line width
- impact: medium; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/curves.py:42-106 (replace _load/_fair/np.interp for hb, zs, zk); params.py tables unchanged

**Claim.** Replacing np.interp plus _fair with fairing splines removes every kink, the 7300 step and the bow S-bend. Each spline is fitted directly to the measured points and lies closer to them than today's curves.

**Evidence.** Deck outline: least-squares cubic B-spline (scipy make_lsq_spline) through deck_halfbreadth.csv for x<7300 plus STERN_OUTLINE (weight 10). Interior knots: 800, 1600, 2400, 3200, 4000, 4800, 5600, 6400, 7000, 7400, 7600, 7700, 7760, 7800, 7830, 7860.
- Maximum residual: 10.9 mm on the trace outside 2450-3250 (today 11.6), 11.2 mm in the 2516-3220 dent-then-bump stretch of the trace (today 13.5), 3.1 mm on STERN_OUTLINE.
- The 1:50 drawing's 0.25 mm line width is 12.5 mm full scale, so all residuals are within one line width.
- Plan curvature sign changes between 300 and 7600: 3 (710, 1135, 7400), against 9 today.
- Maximum beam becomes 2696 instead of 2681. If the brochure 2680 is to stay, scale y by 0.994 or add a max-beam constraint.

Sheer: make_smoothing_spline through the 18 DECK_EDGE_Z points with lam of about 4e7. Maximum residual 5.0 mm (today 7.1); 2 inflections.

Proxy for what the loft makes of these (cubic interpolation through the 42 station samples): curvature sign changes fall from 6 to 4 for the deck and from 4 to 2 for the sheer. Before/after curvature plots are in Image 3.

**Fix.** In curves.py, build the splines once at import (scipy is available, or write a small numpy cubic B-spline) and evaluate them in deck_half_breadth, sheer_z and strake_z. Remove the 7300 switch and the _fair calls, and keep the hold section past the transom corner (_stern_table) as the continuation. Rebuild, rerun the overlays (overlegg-plan.jpg, overlegg-profil.jpg) to confirm the lines still sit on the drawing, and export with relative=False (curves-1).

**Risk.** Changes measured-line positions by up to about 12 mm full scale (0.4 model mm), toward the raw trace. The overlays and the beam check in the README need re-verifying. scipy becomes a build dependency unless the spline is written in numpy.

Images:
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/curves/1_curves_as_used.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/curves/2_stl_deckedge_vs_bambu.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/curves/3_fairing_before_after.png


# LENS: sections

## Summary

Why the hull looks robotic (cross-section lens): curves.section() is two different curves glued together at the waterline, and both are forced vertical exactly at z=0.
- Below the waterline is a superellipse centred on the DWL (curves.py:155-162). Its fullness exponent m is 1.1–1.95, so its curvature runs to infinity right at the waterline.
- Above it is a power curve, y = bw + (bd−bw)·s^1.45 (curves.py:168-176). It is concave by construction: flare rises from 0° at the waterline to 18–34° at the deck edge.

Three things follow.
- **Crease along the DWL.** Every section turns hardest 8–34 mm below the waterline (spline radius 43–170 mm full scale, 1.4–5.7 mm at 1:30). Its curvature then flips sign across z=0. The STL confirms it: the side leans 9–41° in the band z −60…−5 but only 2–14° in z 5…60.
- **Hollow topsides.** They sit up to 32–54 mm inside the waterline-to-deck chord between x=398 and 4770, i.e. 1.1–1.8 mm at model scale.
- **Flat slab sides aft.** From x≈6400 aft the sides are vertical (1–2.5° flare).

Bambu's sections are the opposite: convex, with flare decreasing upward. Over its visible band (z≈390–960, width-corrected) it bulges 14–37 mm outward with flare falling from 23–50° to 0–23°. Ours is concave in the same band (−0.4 to −10 mm) with flare rising.

All of this is real geometry, so it shows on a print as well as on screen. The OCC spline and the loft are faithful: the STL is within ±5 mm full scale (±0.17 mm model) of the formula, except at the forefoot near x≈1008–1221 where the generator switches construction.

The underlying cause is the unsourced waterline half-breadth (`WL_BEAM_FRACTION` 0.845 and the `WATERPLANE` table, params.py:47-67). It is 0.82 of the deck half-breadth amidships and 0.97–0.98 at x≈6758–7155. Any convex section that hits it exactly needs tumblehome aft.

Proposal, demonstrated in numpy only (no CAD build): one curve per section from keel to deck edge.
- It rounds the corner between a bottom line through the keel point (0, zb) at deadrise β and a side line through the measured deck edge (bd, zs) at flare φ.
- The rounding is an affine-mapped superellipse with exponent n.
- Keel point, deck edge and strake height are kept exactly.
- It is convex everywhere (0 inflections) and smooth (C∞) inside, with zero curvature at both ends.
- The bilge radius is 690–780 mm amidships, at z≈−250 to −284.
- The strake face ends up 7–13 mm outside the deck outline, within line tolerance (20 mm at x=7552).
- Midship waterline half-breadth stays within −1 to −3.5%.

Cost of the proposal:
- Max waterline beam −5.3% (2265 → 2145 mm), and its peak moves from x=6030 to 4936.
- Waterline area −9.5%.
- Canoe-body volume −5.4% (3.887 → 3.676 m³), which moves toward the brochure's 2.5 t.
- The aft waterline narrows by up to 27% (at x=7155).

Measurement note: 01_skrog.stl lies on the plate rotated 45°, not 44°. With −44° the slices are yawed about 1° and show false ±40–70 mm errors; README.md also says 45°.

## sections-1: The DWL is a built-in crease: two curves forced vertical at z=0, with infinite curvature and a sign flip there
- impact: high; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/curves.py:143-182 (superellipse 155-162, topside power curve 168-176, comment 173-174); hr26/params.py:35-45 (SECTION_FULLNESS 1.10–1.95)

**Claim.** section() builds the underwater part as a superellipse centred on the DWL, (y/bw)^m + (z/zb)^m = 1 with m = 1.1–1.95, and the topside as a separate power curve. Both have a vertical tangent exactly at z=0. With m < 2 the bilge curvature goes to infinity as z approaches 0, so the tightest turn of the bilge sits at the waterline. Above it the side immediately bends the other way, an inflection exactly on the DWL. On a flat-shaded mesh this reads as a hard horizontal line along the waterline, and the hull looks like a rounded tub with a wall glued on top.

**Evidence.** Analytic curvature radius at z=−10 mm: +61 to +199 mm (convex); at z=+10 mm: −382 to −7772 mm (concave), stations x=1192–7552. OCC spline (n_pts=26): minimum bilge radius 43–170 mm full scale (1.4–5.7 mm at 1:30) at z = −8 to −34 mm. Of the 62–86° total bilge turn, 31–62° happens in the last 150 mm below the DWL; the 45° point sits only 43–212 mm below the DWL. STL slices (rotation −45°): side leans 9.0–41.4° from vertical in z −60…−5, but only −1.5 to 14.0° in z 5…60, then flare grows again (0.7–15.6° at z 250–400). Scripts: gen_analysis.py, stl_ours.py in the sections scratch folder.

**Fix.** Replace the two-piece section with one convex curve from keel to deck edge that crosses the DWL at an inclined, non-vertical tangent, so the bilge turn sits well below the waterline (see sections-6). A minimum stopgap without the new family: centre the underwater superellipse below the DWL and use m >= 2. But m >= 2 alone still leaves the vertical tangent and the inflection at z=0.

**Risk.** Changes every section, so the hollowing (section_inner), the strake path (_side_frame) and the window recess all follow automatically through C.section. Booleans must be re-verified after a rebuild.

## sections-2: Topsides are hollow (concave) by construction; Bambu's are convex
- impact: high; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/curves.py:168-176

**Claim.** y = bw + (bd−bw)·s^1.45 lies inside the straight line from the WL point to the deck edge everywhere, by up to 0.136·(bd−bw). Flare therefore increases upward, from 0° at the DWL to its maximum at the deck edge. That is a pinched, skirt-like section. Bambu's sides, and normal round-bilge hulls, do the opposite: convex, with flare decreasing toward the deck.

**Evidence.** Formula: max deviation from the WL-to-deck chord −32.5 to −53.7 mm for x=398–4770 (−1.08 to −1.79 mm at 1:30) at z≈480–530; −24 to −2 mm aft. STL agrees: −51.3 to −33.6 mm for x=1192–4770. Flare at deck 17.9–33.5° for x≤4770 vs chord flare 12.6–24.5°. Common band z≈390–960 above our DWL (Bambu's bottom + 200 mm up to our strake − 75 mm), Bambu with y×1.223: Bambu +13.8 to +37.0 mm convex (raw width +11.9 to +30.6), flare 23–50° at band bottom falling to 0–23° at band top. Ours in the same band: −0.4 to −9.8 mm concave, flare 4–18° rising to 5–24°. See fig2.

**Fix.** Use a convex topside whose flare decreases from the bilge to the deck edge. The single-curve family in sections-6 gives +38 to +48 mm convexity over the WL-to-deck chord, flare 25–32° at the WL falling to 9–22° at the deck, and 0 inflections.

**Risk.** Convex sides push the hull out at strake height (+17 to +40 mm amidships). Deck flare must stay at about 9° or more amidships, or the strake sticks out beyond the traced deck outline.

## sections-3: Over-full waterline aft, with no source, forces hollow or slab topsides, puts the strake outside the deck outline and inflates volume
- impact: high; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/params.py:47-67 (WL_BEAM_FRACTION, WATERPLANE); hr26/curves.py:131-140 (wl_half_breadth)

**Claim.** The waterline half-breadth is 0.845 × max deck half-breadth shaped by WATERPLANE, and neither has a source. It is 0.82 of the deck half-breadth amidships and 0.97–0.98 at x≈6758–7155. With the DWL tangent forced vertical, the only way up to the measured deck edge is a hollow flare. Aft, the chord flare is only 0.9–1.7°, so the sides become vertical slabs. A convex section that hits this waterline exactly is impossible aft without tumblehome.

**Evidence.** bw/bd: 1091/1338 at x=4770; 1088/1120 at 6758; 1013/1029 at 7155. STL topside lean at x=6758–7155: 0.7–1.4° (z 250–400), −0.4 to −1.5° just above the DWL. Strake face minus deck outline (current): +12, +28, +45, +50 mm at x=5962–7155, i.e. it already sticks out past the traced outline aft. Solving the deck flare so a convex corner-rounding curve hits the table waterline exactly gives φ = −1.6 to −21.7° (tumblehome) at x=6360–7155 and strake protrusion 43–134 mm, for n = 3.5 down to 2.2. Canoe body 3.887 m³ (curves.displaced_volume_m3) vs brochure 2.5 t (≈2.4 m³ including keel). README.md:41-62 lists profile, deck line, sheer and main dimensions as measured; the deck-plan overlay shows a single outer outline with no strake outside it.

**Fix.** Treat the waterline half-breadth as an output of the section family, not an input. Keep keel point, deck edge and strake height exact; choose deck flare φ(x) so the strake face stays within about 15 mm of the deck outline. Optionally keep the waterline within ±3% between 0.4 and 0.6 LOA (the proposal achieves −1.0 to −3.5% there).

**Risk.** Changes the reconstructed waterplane: max WL beam −5.3%, WL area −9.5%, aft WL half-breadth −8 to −27% at x=5565–7155. The transom's immersed width shrinks. The rudder pin holes at z −90/−200 on the centreline are unaffected.

## sections-4: Spline overshoot and wiggle at the DWL; otherwise spline and loft reproduce the formula faithfully
- impact: low; on_screen_only: True; effort: small; keeps_measured_lines: True
- WHERE: hr26/curves.py:154-176 (k=int(n*0.6) below, n−k above); hr26/hull.py:27-32 (makeSpline, default chord-length parametrization); hr26/build.py:73 (n_pts=26)

**Claim.** Interpolating through the 26 points (16 below the DWL, uniform in z; 10 above) adds a small bump just above the waterline. Point spacing jumps from 8–34 mm to 100–120 mm exactly where the curvature is singular. The loft itself does not add shape errors beyond a few mm. So the robotic look comes from the formula, not from OCC.

**Evidence.** Spline vs formula: +2.2 to +5.3 mm outward (0.07–0.18 mm at 1:30) at z≈40–45 mm for x=1192–2385; 0.5–2.7 mm elsewhere; <0.5 mm above z=300. Spline inflections at z≈75–85 and 187–284 (up to 5 per section at x=7155). DWL tangent smoothed from 0° to 3.3–16.7°. STL vs formula at all 42 loft stations and midpoints (rotation −45°): within about ±5 mm (±0.17 mm model), apart from fittings, holes and the forefoot (sections-5). With the brief's −44° the slices were yawed about 1° and showed false −70/+40 mm errors (keel and canoe-bottom heights matched to 1 mm, which exposed this).

**Fix.** With the single-curve family, sample every station at the same parameter values (e.g. 41 points uniform in θ or arc length). Pass identical parameters= to makeSpline, so the spline has no spacing jump and the loft's iso-lines do not twist between stations.

**Risk.** None beyond the rebuild; the loft wires keep 3 edges.

## sections-5: Construction switch at the forefoot (x=1008): stem branch to underwater branch, with a 91 mm bottom_z step
- impact: medium; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/curves.py:109-119 (bottom_z), 155-166 (zb < −1 branch); hr26/hull.py:70-77

**Claim.** Forward of LWL_FWD the section is a 25-point power curve from the stem point (y = bd·s^1.45, vertical at the stem). Aft of it, it is the superellipse plus topside. bottom_z also jumps there, from the stem formula's 0.0 to the table's −91.1 mm. The loft between stations 1000 and 1221 has to bridge different topologies, and the STL departs from the formula there.

**Evidence.** bottom_z(1007.9) = 0.0, bottom_z(1008.1) = −91.1. 10 loft stations (x≤1000) use the stem branch, 32 the underwater branch. STL minus formula at x=1111 (between loft stations 1000 and 1221): −27.8/−28.0 mm below the DWL (−0.93 mm at 1:30), while other mid-stations stay within ±5 mm.

**Fix.** Use one formula for all stations: in the proposed family K = (0, bottom_z(x)) is simply on the stem profile when x < LWL_FWD, so there is no branch switch. Make bottom_z continuous at LWL_FWD by blending the stem formula into the traced forefoot (profile lens).

**Risk.** Touches the forefoot profile near x=1008; check against overlegg-profil.jpg.

## sections-6: Proposed section family: corner-rounding superellipse, smooth, convex, all measured constraints kept
- impact: high; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/curves.py:143-182 (replace section); 122-140 (fullness/wl_half_breadth become unused); 281-297 (displaced_volume_m3 must integrate the new section); hr26/params.py:35-67

**Claim.** One curve per station from keel to deck edge, numpy demo only. It keeps keel point, deck edge, LOA, beam, sheer and strake height exactly. It has 0 inflections, a soft bilge 250–280 mm below the DWL amidships, convex flared topsides and natural V forefoot sections. Canoe-body volume drops 5.4%, toward the brochure 2.5 t.

**Evidence.** Formula: K = (0, bottom_z(x)), D = (deck_half_breadth(x), sheer_z(x)), ub = (cos β, sin β), us = (sin φ, cos φ). Corner: C = K + a·ub = D − c·us (2×2 solve). P(θ) = C − a·(1 − sin(θ)^(2/n))·ub + c·(1 − cos(θ)^(2/n))·us, θ ∈ [0, π/2]. This is an affine image of |f|^n + |g|^n = 1: convex for n ≥ 1, C∞ inside, zero curvature at both ends for n > 2. It is mirror-smooth (G2) at the keel where β=0 (x ≥ 0.27 LOA); forward of that there is a deliberate V at the stem. Tables (fraction of LOA, PCHIP): φ° (0,24) (0.10,19) (0.20,13.5) (0.30,11) (0.45,9.5) (0.60,9.0) (0.75,9.0) (0.90,10.0) (1.0,10.5); n (0,2.4) (0.15,3.1) (0.35,3.4) (0.6,3.5) (0.8,3.3) (1.0,3.1); β° (0,45) (0.127,15) (0.2,4) (0.27,0) (1.0,0). Per station x=398…7552: φ 21.6/19.0/16.0/13.5/12.0/11.0/9.8/9.3/9.0/9.0/9.0/9.2/9.6/10.0/10.3; n 2.69…3.50…3.15; WL half-breadth 140/300/457/598/838/1001/1071/1038/990/926/844/744/634 vs table 133/360/533/663/868/1011/1091/1125/1132/1116/1088/1013/755 (x=1192–7552). Flare at WL 25–32°, at deck 9–22°. Topside convexity +17 to +48 mm. Bilge radius at the 45° point 690–783 mm at z −258 to −284 (x=3180–6360), vs today's 43–170 mm at z −8 to −34. Strake face minus deck outline +7 to +13 mm (+20 at 7552). Totals: canoe body 3.887 → 3.676 m³ (−5.4%); max WL beam 2265 → 2145 mm (−5.3%), peak x 6030 → 4936 (deck max beam is at 4950); WL area 11.78 → 10.66 m² (−9.5%). Files: proposal.py and final.py in the sections scratch folder; fig3.

**Fix.** Implement section(x) with the formula above. Interpolate φ, n, β with PCHIP rather than np.interp. Sample a fixed set of θ (same count every station) and pass parameters= to makeSpline. Drop the stem branch. Update displaced_volume_m3. Rebuild in a copy of the repo and compare against overlegg-profil.jpg and overlegg-plan.jpg. Softness knob: n 3.0 is rounder, n 3.5 firmer; lower n needs more deck flare to keep the strake inside the deck outline.

**Risk.** Strake moves out 17–40 mm amidships (plan) and in up to 34 mm aft. Aft waterline narrows up to 27% (x=7155), so the transom's immersed shape changes. The window recess (x 3700–4900) and hollowing follow the new side. The longitudinal smoothness of bottom_z, sheer_z and deck_half_breadth (np.interp tables) still matters for the loft and belongs to the curves lens.

Images:
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections/fig1_bodyplan_current.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections/fig2_ours_vs_bambu_topsides.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections/fig3_proposal_vs_current.png


# LENS: edges

## Summary

Our hull looks like a robot mainly because every edge in it is sharp. I measured R = 0 at the deck edge (sheer), the coachroof roof edge, the coachroof front, both coaming top edges, the transom top, the transom/side corner and the stem. Bambu softens all of these by about the same amount, R ≈ 20-26 mm full scale (0.7-0.9 mm on the model). It also runs soft beads along the lines: a toe rail of 32 × 18 mm and a strake of about 56 × 16 mm. In flat shading those beads give the thin highlight lines that read as 'fine lines'.

Several boxy parts make it worse:
- **Coachroof front:** it is a vertical wall. The 45° cut in deckhouse.py:200 silently removes nothing (the volume is the same before and after), even though the README says the front is a 45° face.
- **Anchor-roller block:** a 520 × 170 mm brick. Below the deck it sticks out 107 mm ahead of the raked stem.
- **Rubbing strake:** a square 95 × 55 mm bar with a flat cut-off end at the bow. Going round the transom corner it has kinks of 16°, 10° and 26°.
- **Sprayhood:** a loaf with flat vertical ends. It swallows the Ø300 winch drums, which poke out of its sides.
- **Cleats:** flat-topped bricks, 260 × 90 × 100 mm.

I tested fillets in a scratch copy of the code. Rounding the hull deck edge (R25) fails, rounding the transom edges (R10 and R20) fails, and rounding the coachroof roof edge (R25) gives an invalid solid. Rounding the top of the cockpit coaming (R25) works. So the radii have to be built into the section and profile shapes; only simple stand-alone blocks can be filleted.

Suggested radii are 20-30 mm full scale (0.7-1.0 mm model). That is 3-5 layer steps at 0.2 mm, so it shows on the print and not just on screen. Radii under about 9 mm full scale (0.3 mm model) disappear in print.

Order by payoff per effort:
1. Fix the coachroof front.
2. Shrink the anchor roller and clip it to the deck.
3. Give the strake a rounded profile and finer path points.
4. Build a radius into the deck edge of the hull sections.
5. Round the coachroof roof edge in its profile.
6. Reshape the ends of the sprayhood and move the winches out of it.
7. Make cleats and winches smaller.
8. Fillet the coaming top.
9. Round the stem and the bow tip.
10. Transom edges (hard to do).
11. Keel root (KEEL_FILLET is defined but never used).

Method note: the STL sits on the plate at 45°, not 44°. With -44° the mast hole lands 25 mm off the centreline. All measurements here use -45°.

## edges-1: Coachroof front is a vertical wall: the 45-degree step-wedge cut silently does nothing
- impact: high; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/deckhouse.py:174-187 (_step_wedge), :200 (cut); hr26/params.py:134-135 (STEP_X0/X1); hr26/build.py:64-69 (robust_cut has no volume check); README 'Videre arbeid'

**Claim.** The sloped front the drawing shows (about 48 deg, from x=2197 at the deck to 2322 at the roof; the README says 45 deg) is missing from the STL. Instead there is a vertical wall at x=2200, 135-150 mm high (4.5-5 mm model), with a sharp top edge. The cause is that prism.intersect(roof).cut(_step_wedge()) returns the coachroof uncut. OCC fails silently here: the slope of the wedge starts exactly at the tip vertex (2200, 0) of the planform. robust_cut only checks the number of solids, and this cut is not even routed through it.

**Evidence.** Centreline section of the STL: the front face is at x=2198-2200 from z=1217 to 1351, with a 91.0 deg corner and a corner-cut distance of 0.0 mm (R=0). The plan section at z=1300 starts at x=2201; with the slope it would start at about 2291. I rebuilt the coachroof in a scratch copy: its volume is 3.1835e9 mm3 before and after the cut, and prism∩roof∩wedge = 0. Translating the wedge by +-0.37, +-1 or +5 mm makes the cut work and removes 2.4-3.0 L. The README's own overlay (overlegg-profil.jpg) shows the red vertical front standing over the drawn slope. Bambu's front is 78 deg with a top edge of R≈25 mm (0.83 mm model).

**Fix.** Smallest fix: nudge the wedge, for example .translate((-0.37,0,0)) or start the slope at STEP_X0-0.5. Robust fix: build the slope into the roof profile so no boolean is needed. Let roof_z(x) run from the deck at 2200 to the roof at 2330, with rounded transitions of R 40-60 mm full (1.3-2 mm model) at the roof edge, matching 'the original is rounded'. Then _roof_body produces the front directly. Also add a check to robust_cut and coachroof() that raises if |dV| < 1 mm3.

**Risk.** low; this restores the measured drawing line. Check that the forehatch at 2490 still sits on the roof.

## edges-2: Anchor-roller block: oversized brick that pokes out of the raked stem
- impact: high; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/fittings.py:115-127 (x=430, rect 520x170, offset z-420, extrude 560)

**Claim.** anchor_roller() is a 520 x 170 mm block running from 420 mm below the deck to 140 mm above it, at x=170-690, with R60 on its vertical edges only. Above the deck that is a 17.3 x 5.7 x 4.7 mm brick on the model. Below the deck its flat front at x=170 sits ahead of the stem from z=793 to 947: the stem crosses z=793 at x=277. So a box corner 107 mm long (3.6 mm model) and 154 mm tall (5.1 mm) hangs out under the stem head and out of the narrow bow flanks. Its underside is an unsupported flat overhang of 3.6 mm.

**Evidence.** Centreline section of the STL: block front at x=170 from z=793 to 1353; the lofted stem is at x=277 (z=793), 202 (z=900) and 135 (z=1000), matching the analytic stem within 4 mm. The plan section at z=1300 shows a loop of 520 x 170 centred at x=430, y=0. In the overlay crop, the red block sits ahead of the drawn stem line, and the drawing has no tall block on the foredeck. Bambu has no block; a rounded rim wraps round the stem (see edges_closeups.png and edges_vs_drawing.png).

**Fix.** Start the block at deck level (offset z-20 instead of z-420), or intersect it with the hull envelope, so it can never leave the stem. Shrink it to about 300 x 100 mm and 50-60 mm high (10 x 3.3 x 2 mm model). Round the top edges by R≈30 mm (1 mm model); a fillet on the stand-alone block before the union is safe, as the coaming test shows. If photos confirm it, add a small roller lug at the stem head. The drawing shows the strake line ending in a small fitting about 100 mm ahead of the stem.

**Risk.** low

## edges-3: Rubbing strake: square bar, flat cut-off bow end, faceted path and a knuckle round the stern corner
- impact: high; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/hull.py:104-140 (_strake_path; stations(48) at :122, 12 transom points at :135), :170-173 (4-corner polygon, ruled=True); hr26/params.py:235-237

**Claim.** The strake is a ruled loft through 95 x 110 rectangles, half buried so it stands 55 mm proud. That gives 4 sharp longitudinal edges (R=0) and a flat underside overhang of 1.8 mm (model) that droops in print. At x=200 it ends in a flat 95 x 55 face (3.2 x 1.8 mm model). The path has 53 points per side: along the side, segments of 210-270 mm with kinks of 0.9-2.5 deg (median 1.2 deg); round the stern corner (x 7635-7841) only 3 facets with kinks of 16.0, 10.4 and 26.0 deg, which form a visible knuckle. Bambu's strake is a soft bead about 56 mm high and 16 mm proud with crown R≈38 mm, running continuously round the transom.

**Evidence.** STL section at x=3200 shows the rectangle with square corners (edges_sections.png). I evaluated _strake_path(48) from the code: 53 points; kinks as listed; the side-to-transom turn is 52 deg over 206 mm. The close-ups (edges_details.png) show the flat bow end and the stern knuckle. The side kinks have a sagitta of 260 x 0.035/8 ≈ 1.1 mm full scale (0.04 mm model), so they are screen-only; the knuckle, the flat end and the square profile show in print.

**Fix.** Use a rounded D or half-ellipse profile of 12-16 points per station, for example 70 mm high x 30-35 mm proud with R 15-17 mm corners (0.5-0.6 mm model). Alternatively give it a 45-deg chamfered underside, which prints without support. Densify the path round the stern corner (10 or more points following the measured STERN_OUTLINE corner) and along the side (about 100 stations, or ruled=False). Taper the profile to zero over the last 150-200 mm at the bow, or run it to the stem fitting as the drawing does. All of this is built into the profile, which is robust; keep it half buried so the union still works.

**Risk.** low; a ruled loft of polygons is robust. With more points, check that the union with the hull still gives one solid (NUDGES).

## edges-4: Sharp deck edge (sheer crease) along the whole hull; OCC fillet fails, so build the radius into the section wire
- impact: high; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/hull.py:21-40 (corner at :32-37); hr26/curves.py:143-203 (section, deck_arc)

**Claim.** _section_wire joins the topside spline and the deck-arc spline with no tangency, so the whole sheer is a crease. At x=3200 the interior angle is 75.4 deg and the corner-cut distance is 0.3 mm, so R≈0. Bambu's deck edge has R≈22 mm (0.72 mm model) plus a toe-rail bead 32 x 18 mm with crown R 15 mm. The sheer is the most important line on a boat, and it currently has no highlight.

**Evidence.** STL section at x=3200: corner at y=1132, z=1143; the 3-point radius test sits at the floor value for a sharp corner (3.1 mm at +-5 mm). Bambu at x=3200: corner-cut R 21.7 mm and the toe-rail circle fit described above. In a scratch copy, fillet(25) on the 2 sheer edges of the bare hull_solid(40,26) gives StdFail_NotDone.

**Fix.** Insert a tangent arc of R≈25 mm full scale (0.83 mm model, about 4 layer steps) at each station's deck-edge corner. Trim both the side and the deck arc by R/tan(a/2) ≈ 32 mm, then add 4-6 arc points (or one extra spline edge). The measured sheer and deck outline remain the virtual intersection. The outermost point moves 32 mm down the side and about 7 mm inboard, so beam drops by about 14 mm (-0.5%) unless the virtual corner is pushed out 7 mm. Update section_inner/deck_arc_inner and keep the wall at 45 mm. As an option, add a separate rounded toe-rail bead, but only if photos show one.

**Risk.** medium; touches every station wire and the shell offset. Loft stability near the bow (tiny sections) and the transom cut need a re-check.

## edges-5: Coachroof: vertical walls and a sharp roof edge; OCC fillet gives an invalid solid
- impact: high; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/deckhouse.py:96-118 (vertical prism), :128-150 (_roof_body, no shoulder), :190-200

**Claim.** The coachroof is a plan prism intersected with the roof body, which gives vertical walls and a roof edge of 91.7 deg with a corner cut of 1.6 mm, R≈4 mm (0.14 mm model). That vanishes in print, so the edge is effectively sharp. Bambu's roof edge has R≈23 mm (0.78 mm model) and its sides lean in 12.6 deg.

**Evidence.** STL section at x=3200: corner at y=922, z=1354. Bambu at x=3200: corner-cut R 23.5 mm; its side runs from y=676 at z=1290 to y=638 at z=1460. Scratch test after fixing the wedge: faces('>Z').edges().fillet(25) returns isValid()=False (dV 3.77 L), and fillet(40) gives StdFail_NotDone.

**Fix.** Build the radius into the roof body. Give each _roof_body section shoulders: the camber arc out to ±(w(x)-R), then a quarter-round down past the wall at w(x)=coach_half_width(x), with R≈25-30 mm (0.8-1.0 mm model). Alternatively loft the coachroof directly from rounded-rectangle sections. Lean the sides 8-12 deg inward only if photos confirm it; the deck plan only fixes the outline at one level.

**Risk.** low-medium; at the rounded front (plan R700) the x-sections cut the edge obliquely, so the radius grows slightly there.

## edges-6: Sprayhood is a loaf with flat vertical ends, about 170 mm too long aft, and it swallows the winch drums
- impact: high; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/deckhouse.py:311-335; hr26/params.py:272-275; hr26/fittings.py:75-91; hr26/params.py:227-228

**Claim.** The sprayhood loft runs through 11 arch sections from 5135 to 6150 and ends in flat vertical faces at both ends with R=0 edges. The drawing shows a raked front and a rounded aft hoop. The winch drums at x=5900 (y≈880, D300) are inside the hood's length. Each drum's top (z≈1354) stands about 50 mm above the hood surface at the drum centre (z≈1306), so a cut cylinder pokes out of the flank like a funnel.

**Evidence.** STL centreline section: the front at x=5135 and the back at x=6150 stay constant from z=1450 to 1700, so both ends are vertical. Half-width at x=5600: 920 mm at z=1450 and 412 mm at z=1700; top at 1721-1745. The dashed hood in the drawing runs 5144-5978 at the top, its front rakes down to about 4880-4905, and its aft hoop foot is at about 6030 (edges_vs_drawing.png). Close-up: edges_details.png, bottom row. In Bambu the winches are small separate drums, not merged into the hood.

**Fix.** Add 2-3 end sections at each end that shrink the arch, so the loft ends in a small cap instead of a full flat face. Rake the front at about 45 deg, from the coachroof at about 4900 up to 5145. End the back hoop at about 5980 (top) to 6030 (foot), and round the top-back edge with R≈80-100 mm (2.7-3.3 mm model). Keep the hood inboard of the winches: narrow it to the coachroof width aft, or move WINCH_X aft of the hood.

**Risk.** low; a loft of arches is robust. Re-check that the cockpit cut still leaves the hood overhang and its print support.

## edges-7: Cleats and winch drums are oversized flat-topped bricks and cans
- impact: medium; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/fittings.py:94-112 (cleats), :75-91 (winch_pads); hr26/params.py:227-229

**Claim.** There are 6 cleats, each a 260 x 90 mm block standing 100 mm above the deck, with R40 on the vertical edges and sharp top edges (8.7 x 3.0 x 3.3 mm model). The winch pads are cylinders of D300, 190 mm above the coaming top, with a 35 mm chamfer (Ø10 x 6.3 mm model). They are wider than the 130-mm coaming, so they overhang it on both sides. The stern cleat at x=7500 stands above every line of the profile drawing. The drawing gives no cleat size, so I cannot say what the real size is.

**Evidence.** STL plan section at z=1300: cleat loops 260 x 90 at x=700, y=±228 (hb-150); the top at z=1312 with the deck at about 1212. The fittings.py constants confirm the dimensions. The overlay crop at the stern shows the red cleat above the drawn lines. Bambu's deck hardware is small mushroom-shaped drums.

**Fix.** Make horn-style cleats: a low base plus two tapered horns, about 180 x 45 x 60 mm (6 x 1.5 x 2 mm model, printable with 3 perimeters). At minimum, use a 180 x 50 x 60 block with top edges R≈20 mm; a fillet on the stand-alone block before the union is safe. Make the winches about Ø150-180 x 150 with a domed top, reusing the vent recipe of fillet 0.4·D, which already works.

**Risk.** low

## edges-8: Cockpit coaming: flat top with two sharp edges; here an OCC fillet works
- impact: medium; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/deckhouse.py:403-411 (camber=0.0 at :410)

**Claim.** The coaming is a plan prism (R200 corners in plan) intersected with a flat roof body (camber 0). Both top edges are R=0 (90.1 and 89.9 deg). The top is 130 mm wide (y 850-980) and stands 42 mm above the deck outboard. Bambu's inner top edge has R≈26 mm (0.86 mm model).

**Evidence.** STL section at x=6300: corners at (850, 1126) and (980, 1127) with a corner-cut distance of 0.0. Bambu at x=6300: corner-cut R 25.9 mm. In a scratch copy, D.coaming_block().faces('>Z').edges().fillet(25) gives a valid solid with dV -0.68 L.

**Fix.** Apply fillet(25) (0.83 mm model) to the top-face edges of the stand-alone coaming block before the union, inside try, and check the volume. Alternatively make the top a half-round with R≈60 mm.

**Risk.** low

## edges-9: Knife-edge stem and a flat-capped bow tip
- impact: medium; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/curves.py:163-176 (the else branch and the t**1.45 ramp); hr26/hull.py:72-77 (first station at x=4); data/deck_halfbreadth.csv

**Claim.** The bow sections start at y=0 and widen as y ∝ t^1.45, which has a horizontal tangent at the start, so the stem is a knife edge. The loft's first wire, at x=4, already has a deck half-breadth of 87 mm (the traced data gives 84.9 at x=0). The bow tip is therefore a flat planar cap 174 x 9 mm with two sharp corners in plan, where the plan drawing shows a rounded nose. Bambu's stem has R≈18-24 mm.

**Evidence.** 3-point radius test (±5 mm) on STL plan sections: 2.5 mm at z=1000 and 2.6 mm at z=1100. That is the floor value for a sharp V of about 40 deg. Bambu gives 24.1 mm at z=1100 and 17.9 mm at z=1200. The STL has 150 triangles in the plane x=4, spanning y ±87.2 and z 1197-1207. In the overlegg-plan.jpg crop, the red tip is a straight cut and the drawn nose is round, reaching about 26 mm further forward.

**Fix.** Give the bow sections a square-root foot, y = sqrt(2·R·(x - x_stem(z))), blended into the existing ramp, with R≈20-25 mm (0.7-0.8 mm model). The stem line at y=0 stays on the measured profile. Close the deck outline with the round nose the drawing shows (about 36 mm long, ±85 mm wide) instead of the flat cap.

**Risk.** medium; it changes the bow waterlines within about 100 mm of the stem. Re-check the inner shell (VOID_BOW_EXTRA) and loft stability at the first stations.

## edges-10: Transom edges are sharp, and OCC cannot fillet them in the current construction
- impact: medium; on_screen_only: False; effort: large; keeps_measured_lines: True
- WHERE: hr26/hull.py:43-65 (transom_cutter), :76-82

**Claim.** The transom-to-deck edge is 94 deg with R=0. At z=600 the hull side turns about 30-45 deg onto the transom within 4 mm at x≈7825 (one vertex plus a sliver), so R≈0. Bambu's transom top has R≈20 mm (0.65 mm model), and its side corner has Rmin 26-53 mm.

**Evidence.** STL centreline section: corner at (7946, 958), angle 93.8 deg, corner-cut distance 0.0. Plan section at z=600: kinks of +40.8, -49.1 and -36.3 deg at x 7823-7827. Bambu: R 19.6 mm from the corner-cut fit; 3-point Rmin 26 mm (±5 mm) and 53 mm (±10 mm). In a scratch copy, fillet(10) and fillet(20) on the 3 transom-face edges of the bare hull_solid both give StdFail_NotDone.

**Fix.** Low priority. One option is a 15 mm (0.5 mm model) bevel, made by a second boolean with a cutter whose edge is offset along the transom boundary. Another is to post-process the STL locally near those edges. The deck outline already rounds the corner in plan (about R290); only the side-to-transom face edge is sharp.

**Risk.** high (OCC fillets fail; the workarounds add booleans on lofted B-spline faces)

## edges-11: Keel root has no fillet although KEEL_FILLET = 90 is defined
- impact: low; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/params.py:80; hr26/appendages.py:51 onwards (keel loft); hr26/build.py:83

**Claim.** params.py:80 defines KEEL_FILLET = 90.0 ('avrunding mot skroget', i.e. rounding against the hull), but no code uses it. The keel union leaves a sharp concave crease. It is visible when the model stands on its cradle. I cannot compare with Bambu, whose model has no keel.

**Evidence.** grep finds KEEL_FILLET only in params.py. STL section at x=4500: the keel side (y≈145 for z≤-500) meets the canoe body at z≈-490 within one 20-mm step (y=145 to 307).

**Fix.** Build the fillet into the keel loft: flare the top 1-2 keel sections, which already reach 260 mm up into the hull, so the foil widens by about 60-90 mm (2-3 mm model) towards the root. Do not use an OCC fillet on the union edge.

**Risk.** low-medium

## edges-12: Inventory of edge treatments in the code (task item 1); details that can stay as they are
- impact: low; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/hull.py, hr26/deckhouse.py, hr26/fittings.py, hr26/params.py

**Claim.** Each feature and its edge radius, full scale:
- Hull side/deck: crease, R0.
- Stem: knife edge, R0; flat 174 x 9 mm cap at x=4.
- Strake: rectangle, R0 on all 4 edges; flat ends.
- Transom (boolean cut): R0 to the deck, the sides and the bottom; name relief 10.5 mm (0.35 mm model), sharp.
- Coachroof: vertical walls; R0 at the roof edge and at the base; rounded only in plan (front R700, aft corners R140); the 45-deg front is missing (edges-1).
- Hatches: vertical corners R70, top chamfer 15 mm (0.5 mm model).
- Vents: top fillet 60 mm, so they are domes.
- Window recess: R55 corners in profile, 15 mm deep (0.5 mm model), sharp walls.
- Companionway: R60 on the edges along x, the rest R0; mostly hidden under the solid sprayhood.
- Sprayhood: rounded shoulders from 1-|a|^3.2; flat end faces with R0 edges.
- Cockpit well: vertical walls, R140 corners in plan, R0 top edges.
- Coaming: R200 in plan, flat top, R0 on both top edges.
- Winch pads: Ø300 with a 35 mm chamfer.
- Cleats: R40 on the vertical edges, R0 top edges.
- Anchor roller: R60 on the vertical edges, R0 top and bottom.
- Mast step: oval hole only, sharp rim; the separate 05_mastefot part covers it.
- Stanchion and pulpit holes: R0, which is fine.
- Keel root: R0.
Hatches, vents, the window recess and the name relief do not contribute to the robotic look: crisp window and hatch edges are realistic.

**Evidence.** Code: hull.py:21-40, 43-65, 143-174; deckhouse.py:96-118, 153-170, 203-251, 254-288, 311-335, 403-445; fittings.py:58-127, 156-185; params.py:80. The STL sections in edges_sections.png confirm R0 on every edge I measured.

**Fix.** No change needed for hatches, vents, window, name or holes. If anything, turn the hatch chamfer of 15 mm into a fillet of about 20 mm (0.67 mm model); the hatch top is a planar face, so this is safe.

**Risk.** low

## edges-13: Method note: 01_skrog.stl sits on the plate at 45 deg, not 44 deg
- impact: low; on_screen_only: True; effort: small; keeps_measured_lines: True
- WHERE: hr26/build.py:143-151 (best_bed_angle, integer degrees); my lib.py ours_full()

**Claim.** Rotating the STL back by -44 deg leaves a 1-deg yaw. The y-extent minimum is flat between 44 and 46 deg, so it cannot decide the angle. With -45 deg every centred feature lands on y=0.

**Evidence.** At -44 deg: mast hole centre at y=-25 mm, anchor roller at y=-77 mm, port and starboard cleats 8 mm apart in x, and the roller measuring 521 x 177. At -45 deg: mast hole 135 x 105 at (3400, 0), roller 520 x 170 at (430, 0), cleats at y=±228 with x=700 on both sides. With -45 deg and the bow at x=4, the transom at z=300 is at 7850, against 7849.8 analytic, and the stem at z=1000 is at 135, against 134 analytic.

**Fix.** Use -45 deg (or recompute from the symmetry of the mast hole) in all comparison scripts. Earlier overlays made with -44 deg carry about ±70 mm of yaw at the bow.

**Risk.** none

Images:
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/edges_sections.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/edges_closeups.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/edges_details.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/edges_vs_drawing.png


# LENS: surface

## Summary

Most of the "robot" look in 01_skrog.stl comes from the triangles, not from the hull shape. It also has one concrete code cause. build.py:221 calls cq.exporters.export(tolerance=0.018, angularTolerance=0.12). CadQuery then calls Shape.exportStl with relative=True (cadquery occ_impl/shapes.py:490; exporters/__init__.py:129), so 0.018 is a fraction of each edge's size, not 0.018 mm. angularTolerance has no effect on these B-spline faces: 0.12, 0.03 and 0.01 rad give the same 22,344 triangles for the bare loft.

The result is 15,980 hull triangles. Many are slivers (longest edge p95 11.7 mm, max 27 mm; 21% have aspect > 20). Between DWL and strake, single triangles span the whole topside height. Adjacent triangles meet at 5-12 deg (19% of edges > 5 deg, 4% > 10 deg), and the chordal error against the exact surface reaches 0.30 mm in the model. Under 1% of the creases lie on loft stations. Rendered with smooth vertex normals, the same STL looks smooth. The exact loft surface, tessellated finely, looks smooth even when flat-shaded.

Exporting with relative=False removes most of the faceting with zero geometry change: absolute 0.002 mm gives 0.74% of edges > 5 deg instead of 18.8%, at 251k triangles and 12.5 MB for the bare loft.

The geometry does have four smaller real defects that would also print:
- (a) A curvature knuckle in every section just below the DWL (bend radius 88-170 mm full scale, 3-6 mm in the model), with nearly straight topsides above (radius about 4 m).
- (b) Bulges between stations where the piecewise-linear WATERPLANE table kinks, up to 18 mm full scale (0.6 mm model) at x=7240 and 7-9 mm at x=1276/1544. The middle body is fair, under 0.26 mm model p-p.
- (c) The rubbing strake is a polygon of 41 straight panels per side, with kinks of 1-4 deg along the side and 10-26 deg around the stern corner.
- (d) Bow forefoot undulation of about ±10 mm full scale at x 700-1550.

The Bambu model reads smooth because its facets are tiny and evenly shaped (median edge 0.55 mm). At the micro level its surface is actually noisier than ours (median dihedral 4.9 deg). The hull STL lies on the plate rotated 45 deg, not 44 deg as assumed.

Scripts and data are in C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface. The bare-loft STLs and BREPs are in its loft/ subfolder; they were built from a copy of the code, and the repo was not touched.

## surface-1: The robot look is mainly flat-shaded sliver triangles, not the surface
- impact: high; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: export/stl/01_skrog.stl, whole hull exterior. Worst on the topsides between the DWL (z 0) and the strake (z ~800), at x<500 and at x 7000-7950 (full-scale mm).

**Claim.** In 01_skrog.stl the hull is covered by few, large, skinny, flat triangles that meet at 5-12 deg. The zig-zag creases are tessellation diagonals, not station lines or ripples. With smooth normals the same mesh looks smooth, and the exact surface looks smooth even flat-shaded.

**Evidence.** Exact weld gives 71,381 vertices, all 214,245 edges manifold. The hull exterior (classified against the analytic sections) is 15,980 triangles over 29,670 mm2, or 0.54 tri/mm2.
- Longest edge: p50 2.67, p95 11.65, max 27.06 mm.
- Aspect (longest edge / altitude): over 10 for 39.6%, over 20 for 20.9%, over 50 for 10.4%.
- Dihedral between adjacent hull triangles: p50 1.56, p90 7.46, p99 12.5 deg. Over 2 deg: 41.9%; over 5 deg: 19.1%; over 10 deg: 4.2% (of 22,325 edges).
- Of the 4,267 creases over 5 deg, 0.5% lie in a loft-station plane, 61.7% are diagonals, 29.1% run along the girth and 9.2% run fore-and-aft.
- Crease locations: 1,316 at x<500 (bow) and 842 at x 7000-8000.
- Between the DWL and the strake (z 0-800 full scale), single triangles span the whole height with vertices almost only on the DWL and strake lines (fig1).
- Chordal error of the shipped tessellation against the exact loft: p50 0.015, p95 0.067, max 0.30 mm (model).
- Renders (fig2): row 1 flat vs smooth normals; row 3 exact loft (909k tri) flat-shaded looks smooth.
- Bambu topsides: median edge 0.55 mm, aspect >20 for only 0.97%.

**Fix.** Re-export with absolute deflection (see surface-2). For the best result, also see surface-3.

**Risk.** Larger STL files. The geometry is unchanged.

## surface-2: STL export tolerance is relative, not mm, and the angular tolerance does nothing
- impact: high; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/build.py:221 (export()). Applies to all parts, most visible on the hull.

**Claim.** build.py:221 uses cq.exporters.export(wp, fn, tolerance=0.018, angularTolerance=0.12). CadQuery passes this to Shape.exportStl with relative=True, so 0.018 is a fraction of each edge's size. The angular tolerance does not refine B-spline faces. Switching to absolute deflection removes most of the facets without touching the geometry.

**Evidence.** cadquery occ_impl/shapes.py:484-509: exportStl(..., relative: bool = True) -> BRepMesh_IncrementalMesh(shape, tol, relative, ang). occ_impl/exporters/__init__.py:129 calls shape.exportStl(fname, tolerance, angularTolerance, useascii) without relative.

Bare loft hull_solid(40,26), rebuilt in a scratch copy, side faces, measured against a 909k-triangle reference:
- Relative 0.018 (shipped): 22,344 tri, 1.1 MB. Over 5 deg: 18.8%; p99 11.9 deg. Chordal max 0.30 mm. Identical at 0.12, 0.03 and 0.01 rad.
- Absolute 0.018 mm: 71,706 tri, 3.6 MB. Over 5 deg: 6.0%; p99 8.7 deg. Chordal p95 0.023, max 0.088 mm.
- Absolute 0.005 mm: 84,856 tri, 4.2 MB. Almost the same as absolute 0.018.
- Absolute 0.002 mm, 0.05 rad: 250,666 tri, 12.5 MB. Over 5 deg: 0.74%; p99 4.8 deg. Chordal p95 0.014 mm.
- Relative 0.005: 407,762 tri, 20 MB. Over 5 deg: 0.12%. Has one visible sliver dent.

fig3 shows A-D flat-shaded side by side.

**Fix.** Replace line 221 with wp.val().exportStl(fn, tolerance=0.002, angularTolerance=0.05, relative=False). Use 0.005-0.018 if the file gets too big. An optional refinement is to use the fine setting only for name == 'skrog'.

**Risk.** File size and slicing time grow. For the full assembled hull, size was not measured: the bare loft grows from 1.1 to 12.5 MB at 0.002, and the keel, deck and interior also refine. About 13-15% slivers (aspect > 20) remain at every setting, because of the mesher on this surface (surface-3).

## surface-3: Loft surface has 1010 u-knots, so the mesher makes slivers at any tolerance
- impact: medium; on_screen_only: True; effort: medium; keeps_measured_lines: True
- WHERE: hr26/hull.py:21-40 (_section_wire, makeSpline without parameters), :76-77 (makeLoft ruled=False); hr26/curves.py:154-176 (point distribution).

**Claim.** Each hull side face is a degree-3 B-spline with 1010 u-knots x 42 v-knots. Every section spline (GeomAPI_Interpolate, chord-length parameters) has its own knot vector, and ThruSections merges them all: 42 x 24 + 2 = 1010. This strongly uneven parametrization is why BRepMesh produces slivers at any setting. Giving all sections one index-uniform parameter list is not a fix on its own.

**Evidence.** Rebuilt bare loft, faces 0 and 1: udeg 3, vdeg 3, uknots 1010, vknots 42, poles 1012x44; the deck face has 254 u-knots. Aspect >20 among side triangles: 6.8% (relative 0.018), 13-15% (absolute 0.018-0.002).

Variant with makeSpline(parameters=linspace) for every section:
- u-knots drop to 26 (28x44 poles), and the build takes 0.1 s instead of 2 s.
- But the mesh got worse: 50-52% aspect >20, median longest edge 0.04 mm (it piles up at the degenerate stem), 29% over 5 deg at relative 0.018.
- The surface also moved: p95 14.6 mm and max 24 mm full scale at x 1000-2000, about 6 mm in the DWL band, and under 1 mm elsewhere.

All sections have 26 points. Bow sections (where bottom_z > -1, x below about 740) use 1 stem point + 25 topside points; the others use 16 underwater + 10 topside points.

**Fix.** Not demonstrated. A likely route is to pass one common parameter list to makeSpline: the chord-length parameters averaged over all stations, not index-uniform. An alternative for print quality is to bypass BRepMesh for the hull skin and write a structured mesh from the exact surface. Verify the shape change first.

**Risk.** Index-uniform parameters changed the forefoot by up to 24 mm full scale (0.8 mm model). Any reparametrization must be checked against the measured lines.

## surface-4: Real curvature knuckle in every section at the DWL, with straight topsides above
- impact: medium; on_screen_only: False; effort: medium; keeps_measured_lines: True
- WHERE: hr26/curves.py:154-176 (section: superellipse under DWL, t**1.45 above); params.py:35-45 (SECTION_FULLNESS 1.1-1.95). The whole length at z ≈ -40..+20 mm full scale.

**Claim.** Each station spline has a tight curvature peak just below the waterline, and the topsides above are nearly straight. This is a hard line running along the whole DWL, a real geometric contributor to the boxy look. Both section branches have a curvature singularity at the DWL: the underwater superellipse uses fullness m < 2, and the topside uses t**1.45.

**Evidence.** Station spline (makeSpline through C.section(x,26)), curvature peak just below the DWL:

| x | peak curvature | radius (full) | at z |
|---|---|---|---|
| 2500 | 11.3 /m | 88 mm | -23 |
| 4000 | 5.9 /m | 170 mm | -34 |
| 5500 | 7.1 /m | 141 mm | -33 |

For comparison: bilge (z -300..-100) 2.9-3.5 /m; topsides z 100-300 0.64-1.14 /m; z 300-700 0.22-0.27 /m (radius about 4 m).

Analytic section: 5.3-14.6 /m at z=-5 versus 2.1-2.7 /m at z=+5, so the curvature jumps at the DWL. Math: y = bw(1-(1-t)^m)^(1/m) with m = 1.6-1.95 has y'' proportional to s^(m-2), which goes to infinity. y = y0 + d*t^1.45 has y'' proportional to t^-0.55, which also goes to infinity.

In the STL, 20-23% of hull creases over 2 or 5 deg lie within ±50 mm of the DWL (fig1). The exact-loft reflection lines bend sharply along the DWL (fig2 row 3). At stations, z=+50 deviates 1.5-5.6 mm from the analytic curve (spline overshoot).

**Fix.** Make the section C2 at the DWL. One option: use one curvature-continuous construction, such as a blend whose curvature just above the DWL equals the curvature just below. Another: clamp m >= 2 near the waterline and replace t**1.45 with a curve that has finite curvature at t=0, e.g. a cubic Hermite with a vertical tangent and matched curvature. Optionally spread the knuckle over a bilge radius of about 300-500 mm full scale. Keep bw (DWL half-breadth), bd, zs and zb unchanged. Re-run displaced_volume_m3.

**Risk.** The displacement and the look of the topside flare change, and the sections are reconstructions anyway. Shell offsets (section_inner) follow automatically.

## surface-5: Bulges between stations at the breakpoints of the piecewise-linear WATERPLANE table
- impact: medium; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/curves.py:122-123 (_table = np.interp), :134-140 (wl_half_breadth), :126-128 (fullness), plus np.interp at :85, :101, :106, :119; params.py:52-67 (WATERPLANE). Worst at x 1000-1600 and 7100-7400 full scale.

**Claim.** makeLoft passes exactly through every section and adds little ripple in the middle body. The analytic model, however, kinks at every WATERPLANE breakpoint (np.interp), and the cubic loft rounds those kinks into local bulges. Because the topside formula starts from the DWL half-breadth, the kinks carry up to the strake. They are largest near the stern quarter and the forefoot.

**Evidence.** Exact B-rep waterlines (BRepAlgoAPI_Section at fixed z) minus analytic C.section:
- At stations: median 0.00 mm.
- Midway between stations: median 0.5-1.1 mm, max 7-26 mm full scale.
- Every dip over 1 mm sits within 1-3 mm of a WATERPLANE knot, while the nearest loft station is 24-141 mm away.
- Dips: x=7240 (t=0.93) -14.0 to -17.7 mm; x=1545 -8.3 to -8.8; x=1280 -7.0; x=2685 -3.9 to -4.9; x=3355 -2.4 to -2.7; x=4025 -2.8 to -3.3; x=4690, 6035 and 6705 -1.2 to -2.1. The slope at the t=0.93 knot changes from -1.1 to -4.6 per unit t.

Ripple after removing wavelengths over 600 mm:
- x 1500-7000: p-p 2.7-7.7 mm full scale (0.09-0.26 mm model), rms 0.4-1.1 mm.
- x 700-1550: about ±10 mm full scale (0.35 mm model).
- x 6700-7600: about ±5 mm full scale (0.17 mm model).

The strake inherits it: 6.0 deg plan kink at x=7252. Forefoot dip of -28 mm at x=1090, z=0, near LWL_FWD=1008, where the section generator switches mode. See fig4 (a)-(b).

**Fix.** Interpolate the tables with C2 curves through the same points instead of np.interp. Options: scipy CubicSpline, PCHIP (no overshoot), or make_smoothing_spline for the CSV columns. Apply to WATERPLANE, SECTION_FULLNESS, sheer_z, strake_z, deck_half_breadth and bottom_z. Also blend the bow mode switch at x ~740-1008.

**Risk.** Low. The curves still pass through every measured or table point, but PCHIP or a spline can shift values between points by a few mm. Check them against the 1:50 overlays.

## surface-6: Rubbing strake is a polygon of straight panels with kinks up to 26 deg at the stern
- impact: medium; on_screen_only: False; effort: small; keeps_measured_lines: True
- WHERE: hr26/hull.py:104-140 (_strake_path: C.stations(48), 12 transom points), :143-174 (rubbing_strake, makeLoft(ruled=True) at :173). Worst at x 7200-7850 full scale.

**Claim.** The strake is a ruled loft through 41 rectangles per side plus 12 across the transom. It is therefore a chain of flat or twisted straight panels up to 265 mm long full scale (8.8 mm model), kinked at every joint and sharply around the stern corner.

**Evidence.** Side path segment length: 20 to 266 mm, median 208.5.
- Plan-view kink at joints: median 1.27, p90 3.93 deg.
- Kinks over 3.5 deg at x=1027 (3.9), 7252 (6.0), 7635 (4.0), 7730 (16.0), 7809 (10.4) and 7841 (26.0, where it turns onto the transom).
- 1.1 deg per joint across the transom.
- Profile kinks: median 0.064, max 0.56 deg.

In the STL the starboard strake outer face is only 78 triangles (about 2 per panel). 69 of its 71 creases are panel diagonals, median 1.6 deg, p90 4.1 deg.

fig4 (c).

**Fix.** Use many more path points (for example 150, roughly evenly spaced). Round the side-to-transom corner with points that follow the ~290 mm deck-outline radius instead of a single 26 deg joint. Either keep ruled=True with the dense points or sweep a rectangle along a smooth spline through the path (cq.Solid.sweep with a fixed binormal or auxiliary spine).

**Risk.** A smooth loft or sweep of twisted rectangles can self-intersect at the corner. Check that robust_union still gives one solid.

## surface-7: Bambu looks smooth because of tiny, evenly shaped facets, not a fairer surface
- impact: low; on_screen_only: True; effort: small; keeps_measured_lines: True
- WHERE: C:/Users/stig/Downloads/Seilbåt fra Bambumotor.stl (topsides) vs 01_skrog.stl.

**Claim.** The Bambu topsides use small, near-equilateral triangles, so no large flat panels form under flat shading. Its micro-surface is actually noisier than ours and its reflection lines are wavy too. Its smooth look is a tessellation effect plus a different overall shape; the shape side is outside this lens.

**Evidence.** Bambu topsides (scaled x0.3708, below max beam, outward-facing): 12,268 tri over 10,560 mm2 (1.2 tri/mm2).
- Edge length: p50 0.55, p95 4.4, max 8.8 mm.
- Aspect: p50 3.0; over 20 for 0.97%.
- Dihedral: p50 4.94 deg; over 5 deg 49.7%; over 10 deg 32.8%.

Ours: longest edge p95 11.65 mm, aspect >20 for 20.9%, dihedral p50 1.56 deg.

fig2 row 4 vs row 1.

**Fix.** No action. This explains why surface-2 (finer, absolute tessellation) is the main lever for the on-screen impression.

**Risk.** None.

## surface-8: Hull STL is rotated 45 deg on the plate, not 44
- impact: low; on_screen_only: True; effort: small; keeps_measured_lines: True
- WHERE: export/stl/01_skrog.stl placement (build.py best_bed_angle).

**Claim.** Un-rotating by 44 deg leaves a 1 deg yaw. Comparisons that assumed 44 deg see a fake port/starboard asymmetry of up to ±1.7 mm model (±53 mm full scale) at the ends.

**Evidence.** Centreline from section cuts (z 50-75 mm model) at 15 x-positions:
- At 44 deg: offsets from -1.77 to +1.71 mm.
- At 45 deg: within ±0.1 mm. A fine search (0.05 deg steps) has its minimum at 45.0.

With 44 deg, the hull-vs-analytic half-breadth error was bimodal (±72 mm full scale at x≈500). With 45 deg it drops to a few mm.

**Fix.** Use -45 deg when un-rotating 01_skrog.stl in analysis scripts, or fit the angle. Re-check any earlier overlay or half-breadth comparison that used 44.

**Risk.** None for the model; this concerns analysis only.

Images:
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface/fig2_render_sheet.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface/fig1_crease_map.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface/fig3_tessellation.png
- C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface/fig4_ripple_strake.png


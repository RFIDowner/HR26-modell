import json
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
CAL70 = ("orthographic camera fitted to IMG_9370 (roll -2.1 deg, yaw 2.7 deg, elevation 7.1 deg, 9.56 x 9.89 mm/px) using the drawing stem profile "
         "(rms 0.7 px), stem head (1204) and rub-rail centre line strake_z (rms 1.0 px = 10 mm); points back-projected onto the near hull side y = deck half-breadth - 20..30 mm")
T = []


def t(name, value, unit, unc, src, method, today=None, group=""):
    d = dict(name=name, value=value, unit=unit, uncertainty=unc, source_image=src, method=method, group=group)
    if today is not None:
        d["today_model"] = today
    T.append(d)


# ---------------- SIDE / PROFILE
t("rub_rail_visible_height", 45, "mm", "+-12 mm", "IMG_9370 (+IMG_9387, IMG_9391)",
  "FWHM of the dark band along the whole hull in IMG_9370 = 4.3 px = 42 mm mean after back-projection (35-51 along length); IMG_9391 close-up 25-29 px at ~1.3-1.5 mm/px = 33-43 mm; IMG_9387 band is 0.25 x window-frame height (includes shadowed underside)",
  "95 mm (STRAKE_H)", "side")
t("rub_rail_protrusion", 30, "mm", "+-10 mm", "IMG_9388",
  "head-on silhouette: step between rail outer edge and the hull continuing below it = 10-15 px at the max-beam distance (~2.65 mm/px with the fitted camera)",
  "55 mm (STRAKE_PROUD), square bar", "side")
t("rub_rail_profile", "dark (black/dark grey) rubber D-profile with rounded face; underside reflects sky; continuous from stem head (wraps under bow-roller fitting, no flat end) round both stern quarters and across the transom",
  "-", "qualitative", "IMG_9395, IMG_9387, IMG_9391, IMG_9304", "visual",
  "95x55 rectangle, ruled loft, flat end at x=200, knuckles at stern corner", "side")
t("rub_rail_centre_z_vs_strake_z", 0, "mm", "+-15 mm (the fit uses strake_z, so this only shows consistency)", "IMG_9370",
  CAL70 + "; residual of the photo rail centre against strake_z along x=170-7600 is within +-1.4 px", "strake_z (hull_stations.csv)", "side")
t("rub_rail_below_deck_edge_bow", 90, "mm", "+-15 mm", "IMG_9370",
  "stem head top v=1221-1222 vs rail centre v=1230-1231 at x=0-300 (8-10 px)", "79-103 mm (DECK_EDGE_Z - strake_z, x=0-300)", "side")
t("rub_rail_below_deck_edge_transom", 140, "mm", "+-25 mm", "IMG_9370",
  "near transom top corner v~1219 vs rail end v~1233 at the stern (14 px)", "136 mm", "side")
t("deck_edge_minus_rail_centre_amidships_min", 330, "mm", "+-20 mm (lower bound)", "IMG_9370, IMG_9387",
  "window frame top is 31.7 px = 315 mm above the rail centre at x~4200-4800 (independent of camera elevation); the deck edge must be above it (coachroof base and roof-edge lines put it ~1.3 px higher)",
  "271 mm (x=4800: DECK_EDGE_Z 1099 - strake_z 828)", "side")
t("deck_edge_z_amidships_min", 1160, "mm above DWL", "+-25 mm (lower bound; assumes rail at strake_z)", "IMG_9370",
  CAL70 + "; window frame top back-projects to z 1161 (x 4236), 1144 (x 4807), 1115 (x 5430)", "1114 (x 4236), 1099 (x 4807), 1086 (x 5430)", "side")
t("deck_edge_z_bow", 1210, "mm above DWL", "+-15 mm", "IMG_9370", "stem head top v 1221-1222 back-projected (drawing 1204 projects to v 1222.4)", "1204", "side")
t("window_x_forward_end", 4010, "mm from bow", "+-100 mm", "IMG_9370", CAL70 + "; forward extreme of frame u=577.5", "3700 (WIN_X0)", "side")
t("window_x_aft_end", 5620, "mm from bow", "+-100 mm", "IMG_9370", CAL70 + "; aft extreme of frame u=745.5", "4900 (WIN_X1)", "side")
t("window_length", 1610, "mm", "+-150 mm", "IMG_9370 (IMG_9374 cross-check: 0.65 x keel-root chord = ~1400-1570)",
  "difference of the two ends; NOTE conflicts with the 1:50 drawing (3666-4841) - verify before changing", "1200", "side")
t("window_frame_height", 255, "mm", "+-20 mm", "IMG_9370", "frame top v 1222 to bottom v 1248 (26 px) at u 600-735", "~176 mm (deck-30 to strake+70)", "side")
t("window_glass_height", 190, "mm", "+-15 mm", "IMG_9370", "glass v 1226-1245", "-", "side")
t("window_frame_top_above_rail_centre", 315, "mm", "+-15 mm", "IMG_9370", "31.7 px above the rail centre, independent of camera elevation", "~241 mm", "side")
t("window_frame_bottom_above_rail_centre", 55, "mm", "+-12 mm", "IMG_9370, IMG_9387", "5.6 px in IMG_9370; 0.10 of the rail-to-sheer distance in IMG_9387", "70 mm (WIN_ABOVE_STRAKE)", "side")
t("window_frame_top_z", "1161 fwd, 1144 mid, 1115 aft (follows the sheer)", "mm above DWL", "+-20 mm", "IMG_9370", CAL70, "deck-30: 1092-1056", "side")
t("window_forward_end_shape", "semicircular, R ~ half frame height = ~125 mm", "mm", "+-30 mm", "IMG_9370, IMG_9387", "visual on zoomed crops", "R55 rounded rectangle", "side")
t("window_aft_end_shape", "rounded and raked: bottom corner ~85 mm aft of top corner (end leans forward at the top, ~18 deg)", "mm", "+-40 mm", "IMG_9370, IMG_9374, IMG_9387",
  "u 735 (top) vs 744 (bottom) in IMG_9370", "vertical, R55", "side")
t("window_frame_rim_width", 25, "mm", "+-8 mm", "IMG_9387", "raised light-grey frame 5-6 px wide on a 57 px frame height", "15 mm recess, no rim", "side")
t("boot_top_band_height", 100, "mm", "+-20 mm", "IMG_9370", "blue band 8-11 px (top edge to first red)", "not modelled", "side")
t("boot_top_pinstripe", 20, "mm", "+-8 mm", "IMG_9387, IMG_9391, IMG_9388", "light/cream stripe directly under the blue band, 0.17-0.27 x band height", "not modelled", "side")
t("boot_top_top_edge_above_waterline_amidships", 120, "mm", "+-25 mm", "IMG_9370", "10-13 px above the red antifouling / water contact at u 400-650", "-", "side")
t("boot_top_sheer_rise_at_ends", 35, "mm", "+-30 mm", "IMG_9370",
  "top edge z: 126 (x1380), 108 (2786), 93 (4209), 94 (5163), 116 (6121), 134 (6602) via fitted camera; absolute z +-60 mm (camera elevation)", "-", "side")
t("stem_profile_above_water", "matches drawing stem x=1008*(1-(z/1204)^(1/1.3))", "-", "+-7 mm rms", "IMG_9370", "stem outline v 1236-1322 fitted, rms 0.7 px", "same", "side")
t("transom_rake", 9.5, "deg", "+-3 deg", "IMG_9370", "aft outline u 985->975 over v 1232->1290", "8.3 deg", "side")
t("mast_x_at_coachroof", 3600, "mm from bow", "+-120 mm", "IMG_9370", CAL70 + "; mast centre u=526.5 at v=1000 minus ~40 mm assumed aft rake", "3400 (MAST_STEP_X, drawing 3324-3471)", "side")
t("coachroof_side_height", 245, "mm", "+-25 mm", "IMG_9370", "coachroof base line v~1214 to roof-edge line v~1189 at u 440-620 (25 px)", "~245 (COACH_TOP - deck)", "side")
# ---------------- BOW
t("stem_round_radius", 30, "mm", "+-12 mm", "IMG_9388",
  "width of the shading transition across the stem = 45-55 px at ~1.06 mm/px (stem 1.9-2.3 m from the fitted camera, f=1888 px); R = width/(2 cos 25 deg)",
  "0 (knife edge, flat 174x9 cap at x=4)", "bow")
t("bow_waterline_halfbreadth_z130", "x1200: 200, x1500: 345, x1800: 478, x2100: 605, x2400: 724", "mm", "+-30 mm (+-25 more for boot-top height 110-150)", "IMG_9388",
  "boot-top top edge (left arm, 32 points) back-projected onto the plane z=130 with the camera fitted to the rail silhouette, stem line and keel",
  "157, 329, 467, 584, 685 (half-breadth at z=130)", "bow")
t("topside_halfbreadth_x3550_z270_440", "1071 (z268), 1073 (z311), 1108 (z382), 1121 (z436)", "mm", "+-40 mm", "IMG_9388",
  "head-on silhouette below the rail; photo ray intersected at the depth of today's silhouette generator (x~3550); the real outline lies 1.1 deg (33-37 px) outside today's",
  "974, 979, 1011, 1011", "bow")
t("topside_silhouette_flare_below_rail", "5 deg just under the rail, 7 deg at -0.15 m, 11 deg at -0.3 m, 15 deg at -0.45 m (convex: flare increases downwards)", "deg from vertical", "+-3 deg", "IMG_9388",
  "slope of the right-hand silhouette between rows 635 and 800 (near-level camera, pitch 4 deg)",
  "outline pulls in immediately under the rail (hollow; includes the 95x55 rail underside), then runs straight", "bow")
t("topside_convexity_vs_chord", 15, "mm", "+-10 mm", "IMG_9388", "silhouette bulge relative to the chord rail-bottom -> boot-top end (rows 635-790), ~5 px at 2.65-3 mm/px",
  "-12 to -18 mm (concave, same construction)", "bow")
t("deck_edge_rounding", "soft, small radius ~15-25 mm; no separate toe rail visible", "mm", "low confidence", "IMG_9395, IMG_9387", "visual (highlight width)", "R0 crease", "bow")
t("bow_fitting", "plough anchor on a stainless bow roller above the stem head, projecting ~200-300 mm forward", "-", "qualitative", "IMG_9395", "visual",
  "520x170 anchor-roller brick reaching below the deck", "bow")
# ---------------- TRANSOM / STERN
t("stern_outline_halfwidth_ratio_boottop_to_rail", 0.70, "-", "+-0.08 (perspective and z mapping)", "IMG_9391",
  "outline from astern (silhouette) at the boot-top level / at the rail-corner level, rudder as centre line",
  "0.84 (max half-breadth x7600-7800 at z=100 / rail level, perspective weighted)", "transom")
t("transom_boottop_straight_fraction", 0.55, "of rail-level width", "+-0.06", "IMG_9391", "boot-top top edge is a straight line over u 300-1000; rail corners at u ~-15 and 1275", "-", "transom")
t("transom_side_corner", "no crease: the transom face blends into the quarters with a large soft radius (est. 100-250 mm in plan at rail level, more at the boot-top); boot-top and rail turn smoothly round it",
  "-", "qualitative; radius low confidence", "IMG_9391, IMG_9389, IMG_9304, IMG_9372", "shading and line curvature at the corners",
  "sharp face edge (R0), deck corner R~290 in plan only", "transom")
t("transom_outline_shape", "convex U: half-width falls smoothly 1.0 -> 0.95 (z~600) -> 0.85 (z~350) -> 0.70 (boot-top)", "-", "+-0.07", "IMG_9391",
  "right/left silhouette read on a 10 px grid, normalised to the rail level", "nearly parallel sides then pinch (0.97 -> 0.84)", "transom")
t("transom_rail_arch", "rail across the transom arches ~100 px above its corner chord (sagitta/half-width ~0.16 in the image)", "-",
  "plan camber + view from below; consistent with plan camber R~2000-3000, cannot be separated", "IMG_9391", "rail centre tracked u 0-1240", "R 3050 in plan", "transom")
t("rail_on_transom_below_top", 140, "mm", "+-25 mm", "IMG_9370", "see rub_rail_below_deck_edge_transom", "136 mm", "transom")
# ---------------- DECK
t("forehatch", "on the coachroof just forward of the mast; near-square, ~0.4 of the local coachroof width", "-", "low (perspective)", "IMG_9372, IMG_9304", "visual", "2490-2980 x 500, on roof", "deck")
t("coachroof_front_plan", "smoothly rounded front, no corners", "-", "qualitative", "IMG_9372, IMG_9304", "visual", "R700 in plan (ok)", "deck")
t("sprayhood", "soft dome over the companionway: raked front, rounded aft hoop (no flat ends), side windows; spans most of the coachroof width; top ~300-370 mm above the roof",
  "-", "low", "IMG_9372, IMG_9374, IMG_9387", "visual; height from IMG_9374 against the window frame", "loaf with flat vertical ends, swallows winches", "deck")
t("cockpit_coaming", "low, rounded top edges, fades into the aft deck towards the stern", "-", "qualitative", "IMG_9372, IMG_9304", "visual", "flat top, R0 edges", "deck")
t("winches", "one small primary winch each side on the coaming at the forward end of the cockpit, clear of the sprayhood", "-", "qualitative", "IMG_9304", "visual", "D300 cans inside the sprayhood", "deck")
json.dump({"_about": "Photo shape targets for HR 26 V10. Full-scale mm, x from bow, z above DWL unless stated. 'today_model' = baseline_fine / params.py value.", "targets": T},
          open(f"{D}/targets.json", "w"), indent=1, ensure_ascii=False)
print(len(T))

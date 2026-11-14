"""Lager et Bambu Studio-prosjekt (.3mf) av skroget med fargeskift i hoeyden:
roedt bunnstoff fra kjolen, sort vannlinjestripe og hvitt resten.

  python tools/lag_3mf.py

Innstillingene (tools/bambu/project_settings_A1_04.json) er hentet fra et
prosjekt laget i Bambu Studio 02.08 (A1, 0,4-dyse, 0.12mm High Quality, PLA
Basic) og justeres her etter README: tre-stoette
bare fra platen, 15 % fyll. Fargeskiftene er vanlige «tool change» i hoeyden
(samme som Bambus «Add color change» i forhaandsvisningen), saa AMS-en bytter
bare to ganger. Hoeydene kan flyttes i Bambu Studio etterpaa.
"""
import json
import os
import uuid
import zipfile

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(ROOT, "export", "stl", "01_skrog.stl")
OUT = os.path.join(ROOT, "export", "3mf", "01_skrog_farger.3mf")
SETTINGS = os.path.join(ROOT, "tools", "bambu", "project_settings_A1_04.json")

# laghoeyde 0,12 med foerste lag 0,20: lagtoppene ligger paa 0,20 + 0,12 k
BLACK_FROM = 46.76   # foerste lag over DWL (46,67 mm = 1 400 mm over kjolbunnen i 1:30)
WHITE_FROM = 50.60   # stripa ca. 3,8 mm i 1:30 = ca. 115 mm paa baaten
COLOURS = ["#C12E1F", "#000000", "#FFFFFF"]   # 1 roed, 2 sort, 3 hvit
FLUSH = ["0", "153", "511",      # fra roed  til roed, sort, hvit
         "558", "0", "608",      # fra sort
         "280", "128", "0"]      # fra hvit

PLATE_C = 128.0      # A1-platen er 256 x 256

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>
"""
SLICE_INFO = """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
    <header_item key="X-BBL-Client-Version" value="02.08.04.57"/>
  </header>
</config>
"""


def settings():
    with open(SETTINGS, encoding="utf-8") as f:
        ps = json.load(f)
    ps["filament_colour"] = COLOURS
    ps["flush_volumes_matrix"] = FLUSH
    ps.update({
        "enable_support": "1",
        "support_type": "tree(auto)",
        "support_on_build_plate_only": "1",
        "sparse_infill_density": "15%",
        "enable_prime_tower": "0",      # bare to bytter; A1 spyler i sjakten
        "curr_bed_type": "Textured PEI Plate",
    })
    return json.dumps(ps, indent=4, ensure_ascii=False)


def object_model(V, F):
    vs = "\n".join(f'     <vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in V)
    ts = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in F)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
  <object id="1" p:UUID="{uuid.uuid4()}" type="model">
   <mesh>
    <vertices>
{vs}
    </vertices>
    <triangles>
{ts}
    </triangles>
   </mesh>
  </object>
 </resources>
 <build/>
</model>
"""


def main():
    m = trimesh.load(STL)
    lo, hi = m.bounds
    c = 0.5 * (lo + hi)
    V = m.vertices - c                     # objektets origo i midten av boksen
    F = m.faces
    tz = c[2] - lo[2]                      # kjolen paa platen
    tr = f"1 0 0 0 1 0 0 0 1 {PLATE_C} {PLATE_C} {tz:.5f}"
    name = "HR26 HUGO skrog"

    model = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">BambuStudio-02.08.04.57</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{name}</metadata>
 <resources>
  <object id="2" p:UUID="{uuid.uuid4()}" type="model">
   <components>
    <component p:path="/3D/Objects/object_1.model" objectid="1" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
   </components>
  </object>
 </resources>
 <build p:UUID="{uuid.uuid4()}">
  <item objectid="2" p:UUID="{uuid.uuid4()}" transform="{tr}" printable="1"/>
 </build>
</model>
"""
    rels_model = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    msettings = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="{name}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{len(F)}"/>
    <part id="1" subtype="normal_part" uuid="{uuid.uuid4()}">
      <metadata key="name" value="01_skrog.stl"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="01_skrog.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <mesh_stat face_count="{len(F)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="filament_maps" value="1 1 1"/>
    <metadata key="filament_volume_maps" value="0 0 0"/>
    <model_instance>
      <metadata key="object_id" value="2"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="100"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="2" instance_id="0" transform="{tr}" offset="0 0 0" />
  </assemble>
</config>
"""
    gcodes = f"""<?xml version="1.0" encoding="utf-8"?>
<custom_gcodes_per_layer>
<plate>
<plate_info id="1"/>
<layer top_z="{BLACK_FROM:.2f}" type="2" extruder="2" color="{COLOURS[1]}" extra="" gcode="tool_change"/>
<layer top_z="{WHITE_FROM:.2f}" type="2" extruder="3" color="{COLOURS[2]}" extra="" gcode="tool_change"/>
<mode value="MultiAsSingle"/>
</plate>
</custom_gcodes_per_layer>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("3D/_rels/3dmodel.model.rels", rels_model)
        z.writestr("3D/Objects/object_1.model", object_model(V, F))
        z.writestr("Metadata/model_settings.config", msettings)
        z.writestr("Metadata/project_settings.config", settings())
        z.writestr("Metadata/custom_gcode_per_layer.xml", gcodes)
        z.writestr("Metadata/slice_info.config", SLICE_INFO)
    print(f"{OUT}: {os.path.getsize(OUT) / 1e6:.1f} MB, {len(F)} trekanter, "
          f"sort fra {BLACK_FROM} mm, hvit fra {WHITE_FROM} mm")


if __name__ == "__main__":
    main()

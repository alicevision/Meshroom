import json
import zlib
import colorsys

from meshroom.ui import templateInfo


def test_category_color_uses_the_table_case_insensitively():
    colors = {"Photogrammetry": "#45BCF0"}
    assert templateInfo.categoryColor("Photogrammetry", colors) == "#45BCF0"
    assert templateInfo.categoryColor("  photoGRAMMETRY ", colors) == "#45BCF0"


def test_category_color_is_hashed_from_the_lower_case_name():
    color = templateInfo.categoryColor("My Category", {"Photogrammetry": "#45BCF0"})
    assert color == templateInfo.categoryColor("my category")
    assert color == templateInfo.categoryColor("MY CATEGORY ")
    assert color != templateInfo.categoryColor("Other Category")

    # Same value as computing the hue from crc32 of the UTF-8 lower-case name
    hue = zlib.crc32("my category".encode("utf-8")) % 360
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, templateInfo.HASH_LIGHTNESS, templateInfo.HASH_SATURATION)
    assert color == "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def test_uncategorized_color():
    assert templateInfo.categoryColor("") == templateInfo.UNCATEGORIZED_COLOR
    assert templateInfo.categoryColor(None) == templateInfo.UNCATEGORIZED_COLOR
    assert templateInfo.categoryColor("   ") == templateInfo.UNCATEGORIZED_COLOR


def test_load_category_colors(tmp_path):
    colorsFile = tmp_path / "colors.json"
    colorsFile.write_text(json.dumps({"Utilities": "#A3A5AA"}))
    assert templateInfo.loadCategoryColors(str(colorsFile)) == {"Utilities": "#A3A5AA"}

    # Invalid or missing files give no built-in color
    colorsFile.write_text("[1, 2]")
    assert templateInfo.loadCategoryColors(str(colorsFile)) == {}
    colorsFile.write_text("{")
    assert templateInfo.loadCategoryColors(str(colorsFile)) == {}
    assert templateInfo.loadCategoryColors(str(tmp_path / "missing.json")) == {}


def test_builtin_category_colors_file_is_valid():
    colors = templateInfo.loadCategoryColors()
    assert colors
    for color in colors.values():
        assert color.startswith("#") and len(color) == 7


def test_merge_categories_ignores_case_duplicates_and_empty_names():
    merged = templateInfo.mergeCategories(["Photogrammetry", "Utilities"], ["utilities", "", None, " HDR ", "Hdr"])
    assert merged == ["Photogrammetry", "Utilities", "HDR"]


def test_default_template_label():
    assert templateInfo.defaultTemplateLabel("panoramaHdr") == "Panorama Hdr"
    assert templateInfo.defaultTemplateLabel("photogrammetry") == "Photogrammetry"
    assert templateInfo.defaultTemplateLabel("") == ""


def test_updated_template_info_drops_empty_fields_and_keeps_other_keys():
    current = {"label": "Old", "category": "Utilities", "custom": 3}
    edited = {"label": "  New label ", "category": "", "icon": "camera", "description": "  "}
    assert templateInfo.updatedTemplateInfo(current, edited) == {"label": "New label", "icon": "camera", "custom": 3}
    assert templateInfo.updatedTemplateInfo(None, {}) == {}


def test_search_icons():
    results = templateInfo.searchIcons("photo camera")
    assert "photo_camera" in results
    assert all("photo" in name and "camera" in name for name in results)
    # An empty query lists the default icons that exist
    defaults = templateInfo.searchIcons("")
    assert defaults and set(defaults) <= set(templateInfo.MATERIAL_ICONS)
    assert templateInfo.searchIcons("   ") == defaults
    assert templateInfo.searchIcons("", ["camera", "add"], defaults=["missing", "camera"]) == ["camera"]
    assert templateInfo.searchIcons("doesNotExistAnywhere") == []

    # Names starting with the query come first
    assert templateInfo.searchIcons("camera", ["add_camera", "camera"]) == ["camera", "add_camera"]


def test_group_by_category_sorts_builtin_then_others_then_uncategorised():
    templates = [
        {"name": "Zeta", "category": "Custom"},
        {"name": "Loose"},
        {"name": "Tracking", "category": "Camera Tracking"},
        {"name": "Draft", "category": "photogrammetry"},
        {"name": "Photogrammetry", "category": "Photogrammetry"},
        {"name": "Alpha", "category": "Photogrammetry", "label": "Zoom"},
    ]
    groups = templateInfo.groupByCategory(templates, ["Photogrammetry", "Camera Tracking"])
    assert [g["name"] for g in groups] == ["Photogrammetry", "Camera Tracking", "Custom", ""]
    assert [t["name"] for t in groups[0]["templates"]] == ["Draft", "Photogrammetry", "Alpha"]


def _categories(*counts):
    return [{"name": f"C{i}", "color": "#000000", "templates": [{"name": f"C{i}-{j}"} for j in range(count)]}
            for i, count in enumerate(counts)]


def _spans(rows):
    return [[block["span"] for block in row] for row in rows]


def test_layout_categories_spreads_a_single_big_category_over_the_width():
    rows = templateInfo.layoutCategories(_categories(28), columns=4, maxRows=6, maxSpan=2)
    assert _spans(rows) == [[4]]
    block = rows[0][0]
    # 4 columns x 6 rows, the last cell being "Show all"
    assert block["truncated"] and block["rows"] == 6 and len(block["templates"]) == 23 and block["count"] == 28
    assert block["remaining"] == 5


def test_layout_categories_packs_small_categories_and_fills_the_rows():
    rows = templateInfo.layoutCategories(_categories(3, 2, 2, 1, 21), columns=4, maxRows=6, maxSpan=2)
    assert _spans(rows) == [[1, 1, 1, 1], [4]]
    other = rows[1][0]
    assert not other["truncated"] and other["rows"] == 6 and len(other["templates"]) == 21


def test_layout_categories_free_columns_go_to_the_tallest_block():
    rows = templateInfo.layoutCategories(_categories(6, 2), columns=4, maxRows=6, maxSpan=2)
    assert _spans(rows) == [[2, 2]]
    assert [b["rows"] for b in rows[0]] == [3, 1]
    # A block never gets more columns than pipelines
    assert _spans(templateInfo.layoutCategories(_categories(1), columns=4)) == [[1]]


def test_layout_categories_expanded_category_is_shown_alone():
    rows = templateInfo.layoutCategories(_categories(2, 28, 3), columns=4, expanded=["c1"], maxRows=6, maxSpan=2)
    assert _spans(rows) == [[4]]
    expanded = rows[0][0]
    assert expanded["name"] == "C1" and expanded["expanded"] and not expanded["truncated"]
    assert expanded["rows"] == 7 and len(expanded["templates"]) == 28 and expanded["remaining"] == 0
    # An unknown expanded name shows all the categories
    assert len(templateInfo.layoutCategories(_categories(2, 3), columns=4, expanded=["gone"])) == 1


def test_layout_categories_one_column():
    rows = templateInfo.layoutCategories(_categories(10, 2), columns=1, maxRows=6, maxSpan=2)
    assert _spans(rows) == [[1], [1]]
    assert len(rows[0][0]["templates"]) == 5 and rows[0][0]["truncated"] and rows[0][0]["remaining"] == 5

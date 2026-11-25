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

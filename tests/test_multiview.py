from pathlib import Path

from meshroom.multiview import findFilesByTypeInFolder


def test_webp_images_are_found_in_a_folder(tmp_path):
    for name in ("reference.jpg", "photo.webp", "second.WEBP"):
        (tmp_path / name).touch()

    files = findFilesByTypeInFolder(tmp_path)

    assert {Path(path).name for path in files.images} == {
        "reference.jpg", "photo.webp", "second.WEBP"
    }
    assert files.other == []

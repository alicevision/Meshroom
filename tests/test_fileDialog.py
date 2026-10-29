from meshroom.ui.components.fileDialog import parseGtkBookmarks


def test_parseGtkBookmarks():
    content = (
        "file:///home/user/Projects\n"
        "file:///data/My%20Images Images\n"
        "\n"
        "sftp://server/path Remote\n"
    )
    assert parseGtkBookmarks(content) == ["/home/user/Projects", "/data/My Images"]


def test_parseGtkBookmarksEmpty():
    assert parseGtkBookmarks("") == []

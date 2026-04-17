__version__ = "1.0"

from pathlib import Path
from meshroom.core import desc


class GetParentFolder(desc.Node):
    """ Get the parent folder """
    
    category = "Other"

    inputs = [
        desc.File(
            name="file",
            label="File",
            description="File or Folder.",
            exposed=True,
            value=""
        ),
    ]

    outputs = [
        desc.File(
            name="folder",
            label="Folder",
            description="Parent folder.",
            value=None,
        )
    ]

    def process(self, node):
        path = node.file.value
        if path:
            path = Path(path)
            if path.exists():
                node.folder.value = str(Path(path).parent)
                return
        node.folder.value = ""

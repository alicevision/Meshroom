import pytest

from PySide6.QtCore import QObject, Property

from meshroom.common.core import CoreDictModel
from meshroom.common.qt import QObjectListModel, QTypedObjectListModel


class DummyNode(QObject):

    def __init__(self, name="", parent=None):
        super(DummyNode, self).__init__(parent)
        self._name = name

    def getName(self):
        return self._name

    name = Property(str, getName)


def test_DictModel_add_remove():
    for DictModel in (CoreDictModel, QObjectListModel):
        m = DictModel(keyAttrName='name')
        node = DummyNode("DummyNode_1")
        m.add(node)
        assert len(m) == 1
        assert len(m.keys()) == 1
        assert len(m.values()) == 1
        assert m.get("DummyNode_1") == node

        assert m.get("something") is None
        with pytest.raises(KeyError):
            m.getr("something")

        m.pop("DummyNode_1")
        assert len(m) == 0
        assert len(m.keys()) == 0
        assert len(m.values()) == 0


def test_listModel_typed_add():
    m = QTypedObjectListModel(T=DummyNode)
    assert m.roleForName('name') != -1

    node = DummyNode("DummyNode_1")
    m.add(node)
    assert m.data(m.index(0), m.roleForName('name')) == "DummyNode_1"

    obj = QObject()
    with pytest.raises(TypeError):
        m.add(obj)

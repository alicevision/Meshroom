import json
from typing import Any

from meshroom.common import BaseObject, Property, Variant, Signal, DictModel, Slot
from meshroom.core import desc, hashValue

class KeyValues(BaseObject):
    """
    Used to store a list of pairs (key, value) based on an attribute description.
    """

    class KeyValuePair(BaseObject):
        """
        Pair of (key, value), this object cannot be modified.
        """
        def __init__(self, key: int, value: Any, parent=None):
            super().__init__(parent)
            self._key = key
            self._value = value

        key = Property(int, lambda self: self._key, constant=True)
        value = Property(Variant, lambda self: self._value, constant=True)

    def __init__(self, desc: desc.Attribute, parent=None):
        """
        KeyValues constructor
        Args:
            description: The corresponding Attribute description.
            parent: (optional) The parent BaseObject if any.
        """
        super().__init__(parent)
        self._desc = desc
        self._pairs = DictModel(keyAttrName="key", parent=self)
        # TODO: Add interpolation. For now no interpolation.

    def reset(self):
        """
        Clear the list of pairs.
        """
        self._pairs.clear()
        self.pairsChanged.emit()

    def resetFromDict(self, pairs: dict):
        """
        Reset the list of pairs from a given dict.
        """
        self._pairs.clear()
        for k, v in pairs.items():
            self._pairs.add(KeyValues.KeyValuePair(int(k), self._desc.validateValue(v), self))
        self.pairsChanged.emit()

    def add(self, key: str, value: Any):
        """
        Add a new pair (key, value) to the list of pairs from a given key and value.
        """
        # Avoid negative key
        if int(key) < 0:
            return
        # Get existing pair with the given key (or None)
        pair = self._pairs.get(int(key))
        # Remove existing pair
        if pair is not None:
            self._pairs.remove(pair)
        # Add new pair
        self._pairs.add(KeyValues.KeyValuePair(int(key), self._desc.validateValue(value), self))
        self.pairsChanged.emit()

    def remove(self, key: str):
        """
        Remove a pair (key, value) of the list of pairs from a given key.
        """
        # Get existing pair with the given key (or None)
        pair = self._pairs.get(int(key))
        # Remove existing pair
        if pair is not None:
            self._pairs.remove(pair)
            self.pairsChanged.emit()

    def getSerializedValues(self) -> Any:
        """
        Return the list of pairs serialized.
        """
        return { str(pair.key): pair.value for pair in self._pairs }

    def getKeys(self) -> list:
        """
        Return the list of keys.
        """
        return [ str(pair.key) for pair in self._pairs ]

    def getJson(self) -> str:
        """
        Return the list of pairs formatted as a JSON string.
        """
        return json.dumps(self.getSerializedValues())

    def uid(self) -> str:
        """
        Compute the UID from the list of pairs.
        """
        uids = []
        for pair in sorted(self._pairs, key=lambda pair: pair.key):
            uids.extend([pair.key, pair.value])
        return hashValue(uids)

    @Slot(str, result=bool)
    def hasKey(self, key: str) -> bool:
        """
        Whether this given key exists in the list of pairs.
        """
        return self._pairs.get(int(key)) is not None

    @Slot(str, result=Variant)
    def getValueAtKeyOrDefault(self, key: str) -> Any:
        """
        Return the value or the default value from a given key.
        """
        # Get existing pair with the given key (or None)
        pair = self._pairs.get(int(key))
        # Return pair value
        if pair is not None:
            return pair.value
        # Return default value
        return self._desc.value

    # Emitted when something changed in the list of pairs.
    pairsChanged = Signal()
    # The list of pairs (key, value).
    pairs = Property(Variant, lambda self: self._pairs, notify=pairsChanged)
    # The type of key used (viewId, poseId, ...).
    keyType = Property(str, lambda self: self._desc.keyType, constant=True)

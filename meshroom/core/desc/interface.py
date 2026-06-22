class Interface:
    """Marker base class for node descriptor interfaces.

    Inherit from this to declare a new interface. Classes that inherit from
    an Interface are automatically discovered by InterfaceMeta and listed in
    the ``interfaces`` attribute of the concrete node descriptor class.
    """

    @staticmethod
    def upstreamNodesWithInterface(node, attribute, interface_name):
        result = []
        visited = set()
        stack = [attribute]

        while stack:
            attr = stack.pop()
            if not attr.isLink:
                continue
            source_node = attr.inputRootLink.node
            if source_node in visited:
                continue
            visited.add(source_node)
            if interface_name in source_node.nodeDesc.interfaces:
                result.append(source_node)
                continue
            for _, input_attr in source_node.attributes.items():
                stack.append(input_attr)

        return result

class InterfaceMeta(type):
    """Metaclass that populates the ``interfaces`` attribute on any class that uses it.

    When a class is created with this metaclass, ``interfaces`` is set to the list
    of ``Interface`` subclass names found in the class's MRO (excluding the class
    itself and the base ``Interface`` marker).
    """
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        cls.interfaces = [
            b.__name__ for b in type.mro(cls)
            if b is not Interface and b is not cls
            and isinstance(b, type) and issubclass(b, Interface)
        ]
        return cls
    
class InterfacedClass(metaclass=InterfaceMeta):
    """Base class for objects that want automatic interface discovery via InterfaceMeta."""
    pass


class FeatureProviderInterface(Interface):

    def getFeaturesFolders(self, node) -> list:
        raise NotImplementedError
    
    def getDescriberTypes(self, node) -> list:
        raise NotImplementedError

class MatchProviderInterface(Interface):

    def getMatchesFolders(self, node) -> list:
        raise NotImplementedError
    
class TrackProviderInterface(Interface):

    def getTracksFile(self, node) -> str:
        raise NotImplementedError


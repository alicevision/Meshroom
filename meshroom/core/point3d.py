def normalizeViewId(viewId):
    if viewId is None:
        return None
    
    normalizedViewId = str(viewId)
    if not normalizedViewId or normalizedViewId == "-1":
        return None
    
    return normalizedViewId


def getPoint3dObservationKey(shapeAttribute, viewId):

    if shapeAttribute is None or shapeAttribute.type != "Point3d" or not shapeAttribute.isVisible:
        return None

    if shapeAttribute.geometry.observationKeyable:
        return normalizeViewId(viewId)

    return "0"


def getPoint3dObservation(shapeAttribute, viewId):
    
    key = getPoint3dObservationKey(shapeAttribute, viewId)
    if key is None:
        return None

    return shapeAttribute.geometry.getObservation(key)


def observationToPoint3d(observation):
    if not observation:
        return None

    try:
        return (
            float(observation["X"]),
            float(observation["Y"]),
            float(observation["Z"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def getNodePoint3dPositions(node, viewId):
    return [item["position"] for item in getNodePoint3dData(node, viewId)]


def isPickedPoint3d(observation):
    if observation is None:
        return False
    return bool(observation.get("picked", False))


def iterateNodePoint3dAttributes(node):
    if node is None:
        return

    for attr in node.attributes:
        if attr.type == "Point3d":
            yield attr
            continue

        if attr.type == "ShapeList" and attr.desc.elementDesc.__class__.__name__ == "Point3d" and attr.isVisible:
            for childAttr in attr.value:
                if childAttr.type == "Point3d":
                    yield childAttr


def getNodePoint3dData(node, viewId):
    point3dData = []
    for attr in iterateNodePoint3dAttributes(node):
        observation = getPoint3dObservation(attr, viewId)
        point = observationToPoint3d(observation)
        if point is None:
            continue
        point3dData.append({
            "fullName": attr.fullName,
            "position": point,
            "picked": isPickedPoint3d(observation),
        })
    return point3dData


def resolveSelectedPoint3dAttribute(graph, selectedNode, selectedShapeName):
    if graph is None or selectedNode is None or not selectedShapeName:
        return None

    selectedShape = graph.attribute(selectedShapeName)
    if selectedShape is None:
        selectedShape = graph.internalAttribute(selectedShapeName)

    if selectedShape is None or selectedShape.node != selectedNode:
        return None
    if selectedShape.type != "Point3d" or not selectedShape.isVisible:
        return None

    return selectedShape


def getSelectedPoint3dObservationKey(graph, selectedNode, selectedShapeName, viewId):
    selectedShape = resolveSelectedPoint3dAttribute(graph, selectedNode, selectedShapeName)
    if selectedShape is None:
        return ""

    observationKey = getPoint3dObservationKey(selectedShape, viewId)
    return observationKey if observationKey else ""
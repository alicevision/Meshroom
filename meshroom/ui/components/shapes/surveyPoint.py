def normalizeViewId(viewId):
    if viewId is None:
        return None

    normalizedViewId = str(viewId)
    if not normalizedViewId or normalizedViewId == "-1":
        return None

    return normalizedViewId


def getSurveyPointObservationKey(shapeAttribute, viewId):

    if shapeAttribute is None or shapeAttribute.type != "SurveyPoint" or not shapeAttribute.isVisible:
        return None

    if shapeAttribute.geometry.observationKeyable:
        return normalizeViewId(viewId)

    return "0"


def getSurveyPointPartialObservation(shapeAttribute, key):
    """
    Return the SurveyPoint observation for the given key, even if only one of its parts is set.
    Its 3d part (X, Y, Z, picked) and its 2d part (x, y, picked2d) are set independently, so a keyable
    SurveyPoint may only have some of its children keyed: the missing ones get their default value.

    Args:
        shapeAttribute: the SurveyPoint ShapeAttribute.
        key: the observation key.

    Returns:
        The observation dict, with a value for every geometry child.
    """
    observation = {}
    for attribute in shapeAttribute.geometry.value:
        if attribute.keyable:
            observation[attribute.name] = attribute.keyValues.getValueAtKeyOrDefault(key)
        else:
            observation[attribute.name] = attribute.value
    return observation


def mergeSurveyPointObservation(shapeAttribute, key, values):
    """
    Return the full SurveyPoint observation for the given key, updated with the given values.
    Setting a full observation keeps the other part of the SurveyPoint (3d or 2d) unchanged.
    """
    return {**getSurveyPointPartialObservation(shapeAttribute, key), **values}


def getSurveyPointObservation(shapeAttribute, viewId):

    key = getSurveyPointObservationKey(shapeAttribute, viewId)
    if key is None:
        return None

    return getSurveyPointPartialObservation(shapeAttribute, key)


def observationToSurveyPoint(observation):
    if not observation:
        return None

    try:
        # Convert to GL Space
        return (
            float(observation["X"]),
            -float(observation["Y"]),
            -float(observation["Z"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def getNodeSurveyPointPositions(node, viewId):
    return [item["position"] for item in getNodeSurveyPointData(node, viewId) if item["picked"]]


def isPickedSurveyPoint(observation):
    if observation is None:
        return False

    return bool(observation.get("picked", False))


def iterateNodeSurveyPointAttributes(node):
    if node is None:
        return

    for attr in node.attributes:
        if attr.type == "SurveyPoint":
            yield attr
            continue

        if attr.type == "ShapeList" and attr.desc.elementDesc.__class__.__name__ == "SurveyPoint" and attr.isVisible:
            for childAttr in attr.value:
                if childAttr.type == "SurveyPoint":
                    yield childAttr


def getNodeSurveyPointData(node, viewId):
    surveyPointData = []
    for attr in iterateNodeSurveyPointAttributes(node):
        observation = getSurveyPointObservation(attr, viewId)
        point = observationToSurveyPoint(observation)
        if point is None:
            continue
        surveyPointData.append({
            "fullName": attr.fullName,
            "position": point,
            "picked": isPickedSurveyPoint(observation),
        })
    return surveyPointData


def resolveSelectedSurveyPointAttribute(graph, selectedNode, selectedShapeName):
    if graph is None or selectedNode is None or not selectedShapeName:
        return None

    selectedShape = graph.attribute(selectedShapeName)
    if selectedShape is None:
        selectedShape = graph.internalAttribute(selectedShapeName)

    if selectedShape is None or selectedShape.node != selectedNode:
        return None
    if selectedShape.type != "SurveyPoint" or not selectedShape.isVisible:
        return None

    return selectedShape

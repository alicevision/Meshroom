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


def getSurveyPointObservation(shapeAttribute, viewId):
    
    key = getSurveyPointObservationKey(shapeAttribute, viewId)
    if key is None:
        return None

    return shapeAttribute.geometry.getObservation(key)


def observationToSurveyPoint(observation):
    if not observation:
        return None

    try:
        #Convert to GL Space
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


def getSelectedSurveyPointObservationKey(graph, selectedNode, selectedShapeName, viewId):
    selectedShape = resolveSelectedSurveyPointAttribute(graph, selectedNode, selectedShapeName)
    if selectedShape is None:
        return ""

    observationKey = getSurveyPointObservationKey(selectedShape, viewId)
    return observationKey if observationKey else ""
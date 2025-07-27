class ShapeData:
    """Single shape with its properties and observations."""
    
    def __init__(self, name, type, properties, observations = {}, isEditable = True, isVisble = True):

        # shape name
        self.name = name

        # shape type (point, line, circle, etc.)
        self.type = type

        # shape properties (color, stroke, etc.)
        self.properties = properties

        # shape observations {viewId: observation{x, y, radius, etc.}}
        self.observations = observations

        # shape editable
        self.isEditable = isEditable

        # shape visible
        self.isVisible = isVisble
    
    def getObservation(self, viewId):
        """Get shape observation for the given viewId."""
        return self.observations.get(viewId, None)
        
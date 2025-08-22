class ShapeData:
    """Single shape with its properties and observations."""
    
    def __init__(self, name, type, properties, observations = {}, isStatic= True, isEditable = True, isVisble = True):

        # shape name
        self.name = name

        # shape type (point, line, circle, etc.)
        self.type = type

        # shape properties (color, stroke, etc.)
        self.properties = properties

        # shape observations {viewId: observation{x, y, radius, etc.}}
        self.observations = observations

        # shape static (no observations)
        self.isStatic = isStatic

        # shape editable
        self.isEditable = isEditable

        # shape visible
        self.isVisible = isVisble
    
    def getObservation(self, viewId):
        """Get shape observation for the given viewId."""
        # static shape case (no observations)
        if self.isStatic:
            return self.properties
        # shape is not static
        return self.observations.get(viewId, None)
        
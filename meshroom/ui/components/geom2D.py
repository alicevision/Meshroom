from PySide6.QtCore import QObject, Slot, QRectF


class Geom2D(QObject):
    @Slot(QRectF, QRectF, result=bool)
    def rectRectIntersect(self, rect1: QRectF, rect2: QRectF) -> bool:
        """Check if two rectangles intersect."""
        return rect1.intersects(rect2)

    @Slot(QRectF, QRectF, result=bool)
    def rectRectFullIntersect(self, rect1: QRectF, rect2: QRectF) -> bool:
        """Check if two rectangles intersect fully. i.e. rect1 holds rect2 fully inside it."""
        intersected = rect1.intersected(rect2)

        # They don't intersect at all
        if not intersected:
            return False

        # Validate that intersected rect is same as rect2
        # If both are same, that implies it fully lies inside of rect1
        return intersected == rect2

from PySide6.QtCore import QObject, Slot, QRectF


class Geom2D(QObject):
    @Slot(QRectF, QRectF, result=bool)
    def rectRectIntersect(self, rect1: QRectF, rect2: QRectF) -> bool:
        """Check if two rectangles intersect."""
        return rect1.intersects(rect2)

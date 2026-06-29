from meshroom.common import Property

class Collapsable(object):

    def __init__(self):
        super().__init__()

    isCollapsable = Property(bool, lambda self: True, constant=True)

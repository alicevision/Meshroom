from meshroom.common import Property


class Collapsable(object):

    isCollapsable = Property(bool, lambda self: True, constant=True)
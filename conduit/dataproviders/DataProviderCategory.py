class DataProviderCategory:
    def __init__(self, name, icon="image-missing", key=""):
        self.name = name
        self.icon = icon
        self.key = name + key
        
    def __cmp__(self, other):
        if isinstance(other, DataProviderCategory):
            return other.key == self.key
        return False

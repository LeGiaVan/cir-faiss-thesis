class BaseAdapter:
    def __init__(self):
        pass

    def extract_features(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement extract_features method")

import yaml as y


class yaml:
    def __init__(self, path, basepath="./data/"):
        self.path = basepath + path

    def load_yaml(self) -> any:
        """
        yamlを読み込みします
        """
        with open(self.path, 'r', encoding="utf-8_sig") as f:
            data = y.safe_load(f)
            if data != None:
                return data

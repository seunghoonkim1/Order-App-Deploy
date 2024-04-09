import yaml
from yaml.loader import SafeLoader

def load_config():
    """_summary_

    Returns:
        _type_: _description_
    """
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
        return config
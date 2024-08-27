def get_config(config):
    """Convert class attributes to dictionary"""
    return {
        attr: getattr(config, attr) for attr in dir(config) if not attr.startswith("__")
    }

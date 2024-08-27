import importlib


def import_models(models_config):
    imported_models = {}

    for module_path, model_names in models_config.items():
        module = importlib.import_module(module_path)
        for model_name in model_names:
            model = getattr(module, model_name)
            imported_models[model_name] = model

    return imported_models

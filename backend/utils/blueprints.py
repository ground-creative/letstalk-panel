import importlib


def register_service(app, service, name=None):
    if isinstance(service, dict):
        if "path" in service and "blueprint_name" in service:
            try:
                # Import the module specified in the path
                module = importlib.import_module(service["path"])

                # Retrieve the blueprint based on the blueprint_name
                blueprint_name = service["blueprint_name"]
                blueprint = getattr(module, blueprint_name, None)
                if blueprint is None:
                    raise AttributeError(
                        f"Module '{service['path']}' has no attribute '{blueprint_name}'"
                    )

                # Register the blueprint with the app
                app.register_blueprint(blueprint, **service.get("kwargs", {}))
            except ImportError as e:
                app.logger.error(f"Error importing module: {e}")
                # print(f"Error importing module: {e}")
            except AttributeError as e:
                app.logger.error(f"Error accessing blueprint: {e}")
                # print(f"Error accessing blueprint: {e}")
        else:
            # If there are sub-services, recursively register them
            for sub_service_name, sub_service in service.items():
                register_service(app, sub_service, sub_service_name)
    elif isinstance(service, str):
        try:
            # Import the module based on the service name
            module = importlib.import_module(f"blueprints.{name}.routes")

            # Construct the blueprint name
            blueprint_name = f"{name}_bp"

            # Retrieve the blueprint based on the service name
            blueprint = getattr(module, blueprint_name, None)
            if blueprint is None:
                raise AttributeError(
                    f"Module 'blueprints.{name}.routes' has no attribute '{blueprint_name}'"
                )

            # Register the blueprint with the app
            app.register_blueprint(blueprint, url_prefix=service)
        except ImportError as e:
            app.logger.error(f"Error importing module: {e}")
            # print(f"Error importing module: {e}")
        except AttributeError as e:
            app.logger.error(f"Error accessing blueprint: {e}")
            # print(f"Error accessing blueprint: {e}")


def register_blueprints(app, services):
    for service_name, service in services.items():
        register_service(app, service, service_name)

SCENARIO_REGISTRY = {}


def register_scenario(key):
    def decorator(func):
        SCENARIO_REGISTRY[key] = func
        return func
    return decorator

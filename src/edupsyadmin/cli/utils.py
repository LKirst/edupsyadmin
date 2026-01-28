import importlib.util
import sys
import types


# Lazy import utility function
def lazy_import(name: str) -> types.ModuleType:
    """
    Lazy import utility function. This function is from the Python
    documentation
    (https://docs.python.org/3/library/importlib.html#implementing-lazy-imports).

    :param name: The name of the module to be lazily imported.
    :return: The lazily imported module.
    """
    spec = importlib.util.find_spec(name)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find module '{name}'")

    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module

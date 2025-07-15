import importlib
import pkgutil


def load_plugins():
    plugins = {}
    for _, name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{name}")
        if hasattr(module, "Plugin"):
            plugin = module.Plugin()
            plugins[plugin.language] = plugin
    return plugins

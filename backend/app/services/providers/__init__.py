from app.services.providers.registry import registry
from app.services.providers.ahrefs import AhrefsProvider
from app.services.providers.moz import MozProvider
from app.services.providers.semrush import SemrushProvider

registry.register("ahrefs", AhrefsProvider())
registry.register("moz", MozProvider())
registry.register("semrush", SemrushProvider())

__all__ = ["registry", "AhrefsProvider", "MozProvider", "SemrushProvider"]

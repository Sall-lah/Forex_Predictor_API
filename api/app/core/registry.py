"""Centralized service registry for dependency wiring."""

from typing import Any, Callable, TypeVar, Type

T = TypeVar("T")


class ServiceRegistry:
    """Simple dict-based service container for dependency injection.
    
    Provides centralized wiring instead of scattered factory functions.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._factories: dict[type, Callable[..., Any]] = {}
        self._singletons: dict[type, Any] = {}

    def register(self, service_class: type[T], factory: Callable[..., T]) -> None:
        """Register a factory function for a service class.
        
        Args:
            service_class: The service class type
            factory: Factory function that creates service instances
        """
        self._factories[service_class] = factory

    def resolve(self, service_class: type[T], cache: bool = False) -> T:
        """Resolve a service instance from the registry.
        
        Args:
            service_class: The service class type to resolve
            cache: If True, return singleton instance
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service class is not registered
        """
        if cache and service_class in self._singletons:
            return self._singletons[service_class]

        if service_class not in self._factories:
            class_name = getattr(service_class, "__name__", str(service_class))
            raise KeyError(f"Service {class_name} not registered")

        instance = self._factories[service_class]()
        
        if cache:
            self._singletons[service_class] = instance
            
        return instance

    def clear(self) -> None:
        """Clear all registrations and singletons."""
        self._factories.clear()
        self._singletons.clear()


_registry: ServiceRegistry | None = None


def get_registry() -> ServiceRegistry:
    """Get the global service registry singleton.
    
    Returns:
        Global ServiceRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry

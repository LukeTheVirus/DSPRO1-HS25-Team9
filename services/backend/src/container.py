from typing import Type, Dict, Any, TypeVar
import inspect

T = TypeVar("T")

class Container:
    def __init__(self):
        self._registrations: Dict[Type, Dict[str, Any]] = {}
        
    def register(self, impl: Type):
        self._register(impl, lifetime="transient")

    def register_singleton(self, impl: Type):
        """Register a singleton type with the container."""
        self._register(impl, lifetime="singleton")

    def _register(self, impl: Type, lifetime: str = "transient"):
        """Register a type with the container."""
        if impl in self._registrations:
            raise ValueError(f"Class {impl} is already registered.")
        
        self._registrations[impl] = {"lifetime": lifetime, "instance": None}

    def resolve(self, cls: Type[T]) -> T:
        """Resolve a class and inject its dependencies."""
        if cls not in self._registrations:
            raise ValueError(f"Class {cls} is not registered.")

        registration = self._registrations[cls]
        if registration['lifetime'] == 'singleton' and registration['instance'] is not None:
            return registration['instance']

        instance = self._create_instance(cls)
        if registration['lifetime'] == 'singleton':
            registration['instance'] = instance
        return instance

    def _create_instance(self, cls: Type[T]) -> T:
        """Create an instance of the class and resolve dependencies."""
        sig = inspect.signature(cls.__init__)
        dependencies = {}

        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            dep_type = param.annotation
            if dep_type is not param.empty:
                dependencies[name] = self.resolve(dep_type)

        return cls(**dependencies)

    def load_module(self, module_type: Type["Module"]):
        """Load a module class (not instance) that registers services."""
        module = module_type()  # Instantiate the module type
        module.register_services(self)
        
        
class Module:
    def register_services(self, container: Container):
        """Override this method to register services."""
        raise NotImplementedError("Modules must implement the register_services method.")
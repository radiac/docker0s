from __future__ import annotations

from typing import Any, TypeVar, get_type_hints

from .app.names import normalise_name


ManifestObjectType = TypeVar("ManifestObjectType", bound="ManifestObject")


class ManifestObject:
    """
    Base class for manifest objects
    """

    #: Abstract base classes should be marked as abstract so they are ignored by the
    #: manifest loader
    abstract: bool = True

    def __init_subclass__(
        cls, abstract: bool = False, name: str | None = None, **kwargs
    ):
        """
        Set abstract flag and register abstract classes with the registry
        """
        cls.abstract = abstract

        if name is None:
            name = cls.__name__
        else:
            cls.__name__ = name

        # Ensure that names in Pythonare in CamelCase
        # Names from YAML are normalised by now
        normalised = normalise_name(cls.__name__)
        if normalised != cls.__name__:
            raise ValueError("Python manifest objects must be named in CamelCase")

    @classmethod
    def from_dict(
        cls: type[ManifestObjectType], name: str, module: str, data: dict[str, Any]
    ) -> type[ManifestObjectType]:
        """
        Build a concrete subclass of this app using the data in the dict
        """
        # No type checking here - see https://github.com/python/mypy/issues/9183 and
        # https://github.com/python/mypy/issues/5865
        class FromDict(cls, name=name):  # type: ignore
            pass

        FromDict.__module__ = module

        # Collect annotations
        annotations = get_type_hints(FromDict)

        for key, value in data.items():
            if key not in annotations:
                raise ValueError(f"Unexpected attribute {key} for {cls}")

            setattr(FromDict, key, value)

        return FromDict

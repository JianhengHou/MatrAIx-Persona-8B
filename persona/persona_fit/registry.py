"""Dataset slug -> adapter class. The five application datasets under review."""

from __future__ import annotations

import importlib

from .spec import DatasetAdapter

# slug: (module, class).
ADAPTERS: dict[str, tuple[str, str]] = {
    "twin-2k-500": ("twin2k", "Twin2K500"),
    "immigration-conjoint": ("immigration_conjoint", "ImmigrationConjoint"),
    "movielens-1m": ("movielens", "MovieLens1M"),
    "bansak-asylum": ("bansak", "BansakAsylum"),
    "eb-nerd": ("ebnerd", "EBNeRD"),
}


def get_adapter(slug: str) -> DatasetAdapter:
    if slug not in ADAPTERS:
        raise KeyError("unknown dataset {!r}; choose from {}".format(slug, ", ".join(ADAPTERS)))
    module_name, class_name = ADAPTERS[slug]
    module = importlib.import_module(".adapters.{}".format(module_name), __package__)
    return getattr(module, class_name)()


def all_adapters() -> list[DatasetAdapter]:
    return [get_adapter(slug) for slug in ADAPTERS]

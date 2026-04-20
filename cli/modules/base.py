"""Abstract base class for optional bootstrap modules."""

from abc import ABC, abstractmethod
from pathlib import Path


class Module(ABC):
    """Base class for optional project modules (e.g. vector-db, frontend).

    Each module encapsulates the logic for copying its template files into
    the destination project and running any post-install steps.
    """

    name: str
    flag: str
    description: str
    extras: list[str]  # pyproject.toml optional-dependency group names

    @abstractmethod
    def apply(self, templates_root: Path, dest: Path, module: str) -> None:
        """Copy and configure module files into the destination project.

        Args:
            templates_root: Path to the .templates/ directory.
            dest: Root directory of the destination project.
            module: Python module name (snake_case project slug).
        """
        ...

    def post_install(self, dest: Path) -> None:
        """Run post-installation steps after files are copied.

        Default is a no-op. Override for steps like npm install.

        Args:
            dest: Root directory of the destination project.
        """

# @path[src/lint_editor/__init__.py]

from .core import check_paths
from .schema import Finding

__all__ = ["Finding", "check_paths"]

"""Sub-package: update — re-exports all public handlers."""
from . import update_source_git
from .update_framework import do_update
from .update_source_core import do_update_source

__all__ = [
    "do_update",
    "do_update_source",
    "update_source_git"
]

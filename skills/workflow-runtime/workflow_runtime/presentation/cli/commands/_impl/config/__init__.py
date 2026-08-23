"""Sub-package: config — re-exports all public handlers."""
from .config_manager import (do_config_action, do_permission, do_registry,
                             do_rules_action)

__all__ = ['do_config_action', 'do_permission', 'do_rules_action', 'do_registry']

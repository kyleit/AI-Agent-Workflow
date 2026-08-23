from __future__ import annotations

import json
import os
import stat
import warnings
from typing import Any, cast

from workflow_runtime.domain.knowledge.interfaces import IKnowledgeProvider


class KnowledgeProviderFactory:
    """Factory to resolve configurations and instantiate the appropriate Knowledge Provider."""

    @staticmethod
    def get_global_config_path() -> str:
        home = os.path.expanduser("~")
        return os.path.join(home, ".aiwf", "providers.json")

    @staticmethod
    def load_global_config() -> dict[str, Any]:
        path = KnowledgeProviderFactory.get_global_config_path()
        if not os.path.exists(path):
            dir_path = os.path.dirname(path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                try:
                    os.chmod(dir_path, 0o700)
                except Exception:
                    pass
            return {"providers": {}}

        try:
            st = os.stat(path)
            if os.name != 'nt':
                if (st.st_mode & (stat.S_IRWXG | stat.S_IRWXO)) != 0:
                    warnings.warn(f"Security Warning: Global provider config permissions at {path} are too broad. Recommended: chmod 600.")
        except Exception:
            pass

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            warnings.warn(f"Failed to read global config: {e}")
            return {"providers": {}}

    @staticmethod
    def save_global_config(config: dict[str, Any]) -> bool:
        path = KnowledgeProviderFactory.get_global_config_path()
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            try:
                os.chmod(dir_path, 0o700)
            except Exception:
                pass

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            if os.name != 'nt':
                try:
                    os.chmod(path, 0o600)
                except Exception:
                    pass
            return True
        except Exception as e:
            warnings.warn(f"Failed to write global config: {e}")
            return False

    @staticmethod
    def resolve_all_providers(workspace_root: str = ".") -> dict[str, Any]:
        """Merge global and local config."""
        global_cfg = KnowledgeProviderFactory.load_global_config()
        local_cfg_path = os.path.join(workspace_root, ".agents", "memory.config.json")

        if os.path.exists(local_cfg_path):
            try:
                with open(local_cfg_path, "r", encoding="utf-8") as f:
                    local_cfg = json.load(f)
                    if isinstance(local_cfg, dict):
                        local_dict = cast(dict[str, Any], local_cfg)
                        if "providers" in local_dict:
                            global_prov = cast(dict[str, Any], global_cfg.setdefault("providers", {}))
                            local_prov = cast(dict[str, Any], local_dict.get("providers", {}))
                            for p_name, p_data in local_prov.items():
                                if p_name not in global_prov:
                                    global_prov[p_name] = {}
                                if isinstance(p_data, dict):
                                    p_data_dict = cast(dict[str, Any], p_data)
                                    cast(dict[str, Any], global_prov[p_name]).update(p_data_dict)
            except Exception as e:
                warnings.warn(f"Failed to read local config: {e}")

        return global_cfg

    _registry: dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, factory_func: Any) -> None:
        """Register a provider factory function."""
        cls._registry[name] = factory_func

    @classmethod
    def create_provider(cls, provider_name: str, workspace_root: str = ".") -> IKnowledgeProvider:
        """Instantiate a provider by name using registered factories and resolved configurations."""
        all_cfgs = cls.resolve_all_providers(workspace_root).get("providers", {})

        if provider_name in cls._registry:
            return cls._registry[provider_name](workspace_root, all_cfgs)

        # Fallback to markdown if registered, otherwise raise exception
        if "markdown" in cls._registry:
            warnings.warn(f"Provider '{provider_name}' not registered. Falling back to markdown.")
            return cls._registry["markdown"](workspace_root, all_cfgs)

        raise ValueError(f"No knowledge provider registered for '{provider_name}' and no fallback available.")

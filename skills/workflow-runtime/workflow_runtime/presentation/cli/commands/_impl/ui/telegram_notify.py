from __future__ import annotations

import json
import os
import sys
from typing import Any, cast

from workflow_runtime.presentation.cli.commands._impl.provider.provider_data import (
    disable_telegram_autostart, enable_telegram_autostart,
    is_telegram_autostart_enabled, print_project_context,
    restart_runtime_bus_daemon, start_runtime_bus_daemon, stop_telegram_daemon)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    is_telegram_daemon_running)


def do_telegram(args: Any) -> None:
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)

    daemon_script = os.path.join(os.path.dirname(__file__), "telegram_daemon.py")
    log_file = os.path.expanduser("~/.aiwf/telegram-listener.log")
    pid_file = os.path.expanduser("~/.aiwf/telegram-daemon.pid")

    if subaction == "daemon":
        from workflow_runtime.infrastructure.telegram.daemon import (
            run_polling_loop)
        run_polling_loop()
        return

    if subaction == "start":
        started, pid, status = start_runtime_bus_daemon()
        if started:
            print(f"[SYSTEM]: Runtime daemon started with PID: {pid}; Telegram is supervised by runtime.")
        else:
            print(f"[SYSTEM]: Runtime daemon is already running (PID: {pid}, status={status}); Telegram is supervised by runtime.")

    elif subaction == "stop":
        running, pid = is_telegram_daemon_running(pid_file)
        if running:
            try:
                stop_telegram_daemon(pid_file)
                print(f"[SYSTEM]: Shared Telegram Daemon (PID: {pid}) stopped.")
            except Exception as e:
                print(f"[ERROR]: Failed to stop daemon: {e}")
        else:
            print("[SYSTEM]: No running daemon found (missing PID file).")

    elif subaction == "restart":
        new_pid = restart_runtime_bus_daemon()
        print(f"[SYSTEM]: Runtime daemon restarted with PID: {new_pid}; Telegram is supervised by runtime.")

    elif subaction == "enable":
        target = enable_telegram_autostart(daemon_script, log_file)
        print(f"[SYSTEM]: Telegram Daemon autostart enabled: {target}")

    elif subaction == "disable":
        target = disable_telegram_autostart(daemon_script, log_file)
        print(f"[SYSTEM]: Telegram Daemon autostart disabled: {target}")

    elif subaction == "status":
        running, pid = is_telegram_daemon_running(pid_file)
        enabled = is_telegram_autostart_enabled(daemon_script, log_file)
        runtime_running, runtime_pid = is_telegram_daemon_running(os.path.expanduser("~/.aiwf/runtime.pid"))
        print_project_context()
        if runtime_running:
            print(f"[SYSTEM]: Runtime daemon is ACTIVE (PID: {runtime_pid}); Telegram worker is runtime-supervised.")
        else:
            print("[SYSTEM]: Runtime daemon is INACTIVE; start it with `aiwf runtime start` to supervise Telegram.")
        if running:
            print(f"[SYSTEM]: Legacy standalone Telegram daemon is ACTIVE (PID: {pid}); prefer runtime supervision.")
        print(f"[SYSTEM]: Legacy Telegram autostart is {'ENABLED' if enabled else 'DISABLED'}.")

    elif subaction == "link":
        disc_path = os.path.expanduser("~/.aiwf/discovered_groups.json")
        groups: dict[str, str] = {}
        if os.path.exists(disc_path):
            try:
                with open(disc_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        raw_dict = cast(dict[Any, Any], data)
                        groups = {str(k): str(v) for k, v in raw_dict.items()}
            except Exception:
                pass

        curr_path = os.path.abspath(".")
        raw_input_chat_id = getattr(args, "chat_id", None) or getattr(args, "chat_id_opt", None)
        input_chat_id = str(raw_input_chat_id) if raw_input_chat_id else None

        if input_chat_id:
            target_gid = input_chat_id
            target_title = str(groups.get(target_gid, "Unknown Telegram Group"))
            from workflow_runtime.application.workflow import aiwf_registry
            if aiwf_registry.update_project_telegram_chat_id(curr_path, target_gid):
                print(f"[SYSTEM] Lien ket thanh cong du an '{os.path.basename(curr_path)}' voi Group '{target_title}' ({target_gid}).")

                cfg: dict[str, str] = {}
                cfg_path = os.path.expanduser("~/.aiwf/.env.telegram-notify")
                if os.path.exists(cfg_path):
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if "=" in line:
                                k, v = line.split("=", 1)
                                if k.strip() == "TELEGRAM_BOT_TOKEN":
                                    cfg["token"] = v.strip().strip('"').strip("'")
                                elif k.strip() == "TELEGRAM_PROXY":
                                    cfg["proxy"] = v.strip().strip('"').strip("'")
                token_val = cfg.get("token")
                if token_val:
                    try:
                        from workflow_runtime.infrastructure.telegram import (
                            telegram_daemon)
                        set_cmd_fn: Any = getattr(telegram_daemon, "set_bot_menu_commands", None)
                        if callable(set_cmd_fn):
                            set_cmd_fn(token_val, cfg.get("proxy", ""))
                    except Exception as e:
                        print(f"[WARN] Failed to sync Bot commands: {e}")
            else:
                print(f"[ERROR] Du an '{os.path.basename(curr_path)}' chua duoc dang ky trong he thong. Hay chay 'aiwf registry register' truoc.")
            return

        if not groups:
            print("[SYSTEM] Chua phat hien nhom Telegram nao. Hay dam bao ban da add Bot vao Group va gui tin nhan truoc.")
            return

        print("\n--- Danh sach nhom Telegram da phat hien ---")
        options_list: list[tuple[str, str]] = list(groups.items())
        for idx, (gid, title) in enumerate(options_list, 1):
            print(f"{idx}. {title} (ID: {gid})")
        print(f"{len(options_list) + 1}. Thoat")

        try:
            ans = input(f"Chon nhom muon lien ket voi du an '{os.path.basename(curr_path)}' (1-{len(options_list) + 1}): ").strip()
            if not ans:
                print("Da huy.")
                return
            choice_idx = int(ans) - 1
            if 0 <= choice_idx < len(options_list):
                target_gid, target_title = options_list[choice_idx]
                from workflow_runtime.application.workflow import aiwf_registry
                if aiwf_registry.update_project_telegram_chat_id(curr_path, target_gid):
                    print(f"[SYSTEM] Lien ket thanh cong du an '{os.path.basename(curr_path)}' voi Group '{target_title}' ({target_gid}).")

                    cfg = {}
                    cfg_path = os.path.expanduser("~/.aiwf/.env.telegram-notify")
                    if os.path.exists(cfg_path):
                        with open(cfg_path, "r", encoding="utf-8") as f:
                            for line in f:
                                if "=" in line:
                                    k, v = line.split("=", 1)
                                    if k.strip() == "TELEGRAM_BOT_TOKEN":
                                        cfg["token"] = v.strip().strip('"').strip("'")
                                    elif k.strip() == "TELEGRAM_PROXY":
                                        cfg["proxy"] = v.strip().strip('"').strip("'")
                    token_val = cfg.get("token")
                    if token_val:
                        try:
                            from workflow_runtime.infrastructure.telegram import (
                                telegram_daemon)
                            set_cmd_fn: Any = getattr(telegram_daemon, "set_bot_menu_commands", None)
                            if callable(set_cmd_fn):
                                set_cmd_fn(token_val, cfg.get("proxy", ""))
                        except Exception as e:
                            print(f"[WARN] Failed to sync Bot commands: {e}")
                else:
                    print(f"[ERROR] Du an '{os.path.basename(curr_path)}' chua duoc dang ky trong he thong. Hay chay 'aiwf registry register' truoc.")
            else:
                print("Da huy.")
        except Exception as ex:
            print(f"Loi: {ex}")
    elif subaction == "config":
        print("\n=== AIWF Global Telegram Configuration ===")
        cfg_dir = os.path.expanduser("~/.aiwf")
        os.makedirs(cfg_dir, exist_ok=True)
        cfg_path = os.path.join(cfg_dir, ".env.telegram-notify")
        tmp_path = cfg_path + ".tmp"

        curr_token = ""
        curr_proxy = ""
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k == "TELEGRAM_BOT_TOKEN":
                                curr_token = v
                            elif k == "TELEGRAM_PROXY":
                                curr_proxy = v
            except Exception:
                pass

        token_prompt = f"Enter Telegram Bot Token [{curr_token[:5]}...{curr_token[-5:]}] (press Enter to keep current): " if curr_token else "Enter Telegram Bot Token: "
        try:
            new_token = input(token_prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nDa huy.")
            return

        if not new_token:
            new_token = curr_token

        if not new_token:
            print("[ERROR]: Telegram Bot Token is required.")
            sys.exit(1)

        proxy_prompt = f"Enter Telegram Proxy (optional, e.g. http://127.0.0.1:8080) [{curr_proxy}] (press Enter to keep current): " if curr_proxy else "Enter Telegram Proxy (optional, e.g. http://127.0.0.1:8080): "
        try:
            new_proxy = input(proxy_prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nDa huy.")
            return

        if not new_proxy and curr_proxy:
            new_proxy = curr_proxy

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(f'TELEGRAM_BOT_TOKEN="{new_token}"\n')
                if new_proxy:
                    f.write(f'TELEGRAM_PROXY="{new_proxy}"\n')
            os.replace(tmp_path, cfg_path)
        except Exception:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            print("[ERROR]: Failed to save Telegram configuration.")
            sys.exit(1)

        print("[SUCCESS]: Telegram global configuration updated successfully!")


__all__ = ["do_telegram"]

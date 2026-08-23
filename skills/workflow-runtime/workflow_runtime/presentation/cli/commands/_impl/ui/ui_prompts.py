from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Optional, cast

from workflow_runtime.infrastructure.session.session_io import load_session
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    RuntimeInputGate)
from workflow_runtime.shared.errors import (ForbiddenAISourceError,
                                            InvalidResumeTokenError)


def do_prompt(args: Any) -> int:
    from workflow_runtime.shared.utils import PROMPT_UNAVAILABLE, prompt_select
    opt_str = str(getattr(args, "options", "") or "")
    options_list = [o.strip() for o in opt_str.split("|")]
    res = prompt_select(str(getattr(args, "question", "")), options_list, str(getattr(args, "default", "")))
    print(res)
    if res == PROMPT_UNAVAILABLE:
        print(
            "Prompt bridge unavailable: no native UI or stdin answer was received. "
            "This is not a Cancel selection.",
            file=sys.stderr,
        )
        sys.exit(2)
    return 0


def do_input(args: Any) -> None:
    subaction = str(getattr(args, 'action', None) or getattr(args, 'subaction', None) or "")
    if subaction == "submit":
        try:
            success = RuntimeInputGate.submit_input(
                prompt_id=str(getattr(args, "input_id", "")),
                value=str(getattr(args, "value", "") or ""),
                source=str(getattr(args, "source", "")),
                token=str(getattr(args, "resume_token", ""))
            )
            if success:
                print(json.dumps({"success": True, "message": "Input accepted. Resuming workflow..."}))
            else:
                print(json.dumps({"success": False, "message": "Failed to submit input."}))
                sys.exit(1)
        except (ForbiddenAISourceError, InvalidResumeTokenError) as e:
            print(json.dumps({"success": False, "message": str(e)}), file=sys.stderr)
            sys.exit(1)


def do_choice(args: Any) -> None:
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)

    runtime_dir = os.path.join(".agents", "runtime")
    os.makedirs(runtime_dir, exist_ok=True)

    pending_path = os.path.join(runtime_dir, "pending-choice.json")
    response_path = os.path.join(runtime_dir, "choice-response.json")
    ui_capabilities_path = os.path.join(runtime_dir, "ui-capabilities.json")

    subaction = str(getattr(args, 'action', None) or getattr(args, 'subaction', None) or "")
    args_id = str(getattr(args, "id", "") or "")
    args_options = str(getattr(args, "options", "") or "")

    if subaction == "create":
        raw_options = args_options.strip()
        options: list[dict[str, Any]] = []
        if raw_options.startswith("["):
            try:
                parsed = json.loads(raw_options)
                if isinstance(parsed, list):
                    options = cast(list[dict[str, Any]], parsed)
            except json.JSONDecodeError as e:
                print(f"Error parsing options JSON: {e}", file=sys.stderr)
                sys.exit(1)
        elif raw_options:
            for opt in raw_options.split(","):
                opt = opt.strip()
                if opt:
                    options.append({"id": opt, "label": opt})

        choice_type = str(getattr(args, "type", None) or "choice")
        choice_data = {
            "type": choice_type,
            "id": args_id,
            "title": str(getattr(args, "title", "")),
            "description": str(getattr(args, "desc", "") or ""),
            "required": bool(getattr(args, "required", False)),
            "allow_cancel": bool(getattr(args, "allow_cancel", True)),
            "options": options
        }

        tmp_path = pending_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(choice_data, f, indent=2, ensure_ascii=False)
        if os.path.exists(pending_path):
            os.replace(tmp_path, pending_path)
        else:
            os.rename(tmp_path, pending_path)

        print(f"Choice {args_id} created successfully.")

    elif subaction == "wait":
        interactive_choice = False
        if os.path.exists(ui_capabilities_path):
            try:
                with open(ui_capabilities_path, "r", encoding="utf-8") as f:
                    caps = cast(dict[str, Any], json.load(f))
                    interactive_choice = bool(caps.get("interactive_choice", False))
            except Exception:
                pass

        if os.environ.get("AIWF_INTERACTIVE_CHOICE") == "true":
            interactive_choice = True

        timeout = int(getattr(args, "timeout", None) or 60)
        start_time = time.time()
        choice_resolved = False
        selected_option: Optional[str] = None

        from workflow_runtime.application.verification.confidence_gate import (
            ConfidenceGate)
        phase: Optional[str] = None
        if "blueprint" in args_id:
            phase = "blueprint"
        elif "spec" in args_id or "brainstorm" in args_id:
            phase = "brainstorm"
        elif "plan" in args_id:
            phase = "planning"

        confidence_ok = True
        score = 100.0
        gaps: list[str] = []
        if phase:
            score, gaps = ConfidenceGate.calculate_confidence(str(phase))
            if score < 95.0:
                confidence_ok = False

        is_full_access = session.get("permission_mode") == "full_access" or session.get("autonomous_delivery") is True
        protected_approval_gate = args_id in {"blueprint_approval", "release_approval"}

        if is_full_access:
            if protected_approval_gate:
                pass
            elif not confidence_ok:
                print(f"\n[CONFIDENCE CHECK FAILED] Phase '{phase}' has confidence score {score}% (< 95%). Gaps detected:", file=sys.stderr)
                for gap in gaps:
                    print(f"  - {gap}", file=sys.stderr)
                print("Aborting autonomous resolution. Clarification is required.", file=sys.stderr)
                sys.exit(1)
            else:
                c_type = str(getattr(args, "type", "") or "")
                if not c_type and os.path.exists(pending_path):
                    try:
                        with open(pending_path, "r", encoding="utf-8") as f:
                            cdata = cast(dict[str, Any], json.load(f))
                            c_type = str(cdata.get("type", ""))
                    except Exception:
                        pass
                if c_type == "approval" or args_id == "blueprint_approval":
                    selected_option = "approve"
                else:
                    opts: list[dict[str, Any]] = []
                    if os.path.exists(pending_path):
                        try:
                            with open(pending_path, "r", encoding="utf-8") as f:
                                cdata = cast(dict[str, Any], json.load(f))
                                raw_o = cdata.get("options")
                                if isinstance(raw_o, list):
                                    opts = cast(list[dict[str, Any]], raw_o)
                        except Exception:
                            pass
                    selected_option = str(opts[0].get("id")) if opts else "approve"
                print(f"Autonomous delivery is active. Confidence score is {score}% (>=95%). Automatically resolving choice {args_id} to: {selected_option}")

                sel_str = str(selected_option or "")
                resp_payload: dict[str, Any] = {
                    "id": args_id or "unknown",
                    "selected": sel_str,
                    "cancelled": sel_str == "cancel"
                }
                tmp_resp = response_path + ".tmp"
                with open(tmp_resp, "w", encoding="utf-8") as f:
                    json.dump(resp_payload, f, indent=2, ensure_ascii=False)
                if os.path.exists(response_path):
                    os.replace(tmp_resp, response_path)
                else:
                    os.rename(tmp_resp, response_path)

                if os.path.exists(pending_path):
                    try:
                        os.remove(pending_path)
                    except Exception:
                        pass
                choice_resolved = True

        if interactive_choice:
            print(f"Waiting for UI choice response for {args_id} (timeout={timeout}s)...")
            while time.time() - start_time < timeout:
                if os.path.exists(response_path):
                    try:
                        with open(response_path, "r", encoding="utf-8") as f:
                            resp_data = cast(dict[str, Any], json.load(f))
                        if resp_data.get("id") == args_id:
                            selected_option = str(resp_data.get("selected", ""))
                            choice_resolved = True
                            break
                    except Exception:
                        pass
                time.sleep(0.5)

        if not choice_resolved:
            if interactive_choice:
                print("\nTimeout waiting for UI response. Switching to Text Fallback Mode...")

            choice_data: dict[str, Any] = {}
            if os.path.exists(pending_path):
                try:
                    with open(pending_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            choice_data = cast(dict[str, Any], data)
                except Exception:
                    pass

            title = str(choice_data.get("title", args_id or "Choice Required"))
            desc = str(choice_data.get("description", ""))
            raw_options_list = choice_data.get("options")
            options_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_options_list) if isinstance(raw_options_list, list) else []
            choice_type_str = str(choice_data.get("type", "choice"))
            allow_cancel_bool = bool(choice_data.get("allow_cancel", True))

            print(f"\n=== {title} ===")
            if desc:
                print(desc)
            print("-" * len(title))

            option_ids: list[str] = []
            if choice_type_str == "approval":
                print("[Y] Yes / Continue")
                print("[N] No / Cancel")
                option_ids = ["y", "yes", "proceed", "continue", "n", "no", "cancel"]
            else:
                for idx, opt in enumerate(options_list):
                    if bool(opt):
                        lbl = str(opt.get("label", opt.get("id", "")))
                        opt_desc = str(opt.get("description", ""))
                        suffix = f" ({opt_desc})" if opt_desc else ""
                        print(f"{idx + 1}. {lbl}{suffix}")
                        option_ids.append(str(opt.get("id", "")))

            if allow_cancel_bool and choice_type_str != "approval":
                print("C. Cancel")

            from workflow_runtime.shared.utils import is_stdin_ready
            if not sys.stdin.isatty() and not is_stdin_ready():
                if choice_type_str == "approval":
                    selected_option = "cancel"
                else:
                    selected_option = option_ids[0] if option_ids else "cancel"
                print(f"Non-interactive environment and no stdin input available. Auto-selecting default/fallback: {selected_option}")
                choice_resolved = True
            else:
                while True:
                    user_val = input("\nEnter selection: ").strip()
                    if not user_val:
                        continue
                    val_lower = user_val.lower()

                    if val_lower in ("c", "cancel"):
                        if allow_cancel_bool:
                            selected_option = "cancel"
                            break
                        else:
                            print("Cancel is not allowed for this choice.")
                            continue

                    if choice_type_str == "approval":
                        if val_lower in ["y", "yes", "proceed", "continue"]:
                            selected_option = "approve"
                            break
                        elif val_lower in ["n", "no", "cancel"]:
                            selected_option = "cancel"
                            break
                        else:
                            print("Invalid selection. Please enter Y or N.")
                            continue

                    try:
                        idx = int(user_val) - 1
                        if 0 <= idx < len(options_list):
                            selected_option = str(options_list[idx].get("id", ""))
                            break
                    except ValueError:
                        pass

                    matched = False
                    for opt in options_list:
                        if bool(opt):
                            opt_id = str(opt.get("id", "")).lower()
                            opt_lbl = str(opt.get("label", "")).lower()
                            if opt_id == val_lower or opt_lbl == val_lower:
                                selected_option = str(opt.get("id", ""))
                                matched = True
                                break
                    if matched:
                        break
                    print("Invalid selection. Please try again.")

            sel_str = str(selected_option or "")
            resp_payload: dict[str, Any] = {
                "id": args_id or "unknown",
                "selected": sel_str,
                "cancelled": sel_str == "cancel"
            }
            tmp_resp = response_path + ".tmp"
            with open(tmp_resp, "w", encoding="utf-8") as f:
                json.dump(resp_payload, f, indent=2, ensure_ascii=False)
            if os.path.exists(response_path):
                os.replace(tmp_resp, response_path)
            else:
                os.rename(tmp_resp, response_path)

            if os.path.exists(pending_path):
                try:
                    os.remove(pending_path)
                except Exception:
                    pass

        print(f"Choice resolved: {selected_option}")

    elif subaction == "read":
        if os.path.exists(response_path):
            try:
                with open(response_path, "r", encoding="utf-8") as f:
                    resp_data = cast(dict[str, Any], json.load(f))
                if str(resp_data.get("id")) == args_id:
                    print(resp_data.get("selected", ""))
                    return
            except Exception:
                pass
        print("")

    elif subaction == "clear":
        for p in [pending_path, response_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        print("Choice files cleared.")


__all__ = [
    "do_prompt",
    "do_input",
    "do_choice",
]

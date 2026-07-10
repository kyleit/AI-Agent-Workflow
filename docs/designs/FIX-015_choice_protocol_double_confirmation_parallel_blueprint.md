---
artifact_type: blueprint
issue_id: FIX-015
workflow: quick-fix
status: draft
---

# Technical Design Blueprint – Choice Protocol, Double Confirmation, and Parallel Execution

This document specifies the exact code modifications to implement the choice protocol CLI command, resolve duplicate user approvals, and configure parallel task executions.

## 1. Proposed Changes

### Component 1: CLI Runtime Engine subcommands

#### [MODIFY] [workflow_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) and [workflow_runtime.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py)

1. Add the `do_choice` function right before `do_permission` (or right after `do_suggest`):
```python
def do_choice(args) -> None:
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)

    runtime_dir = os.path.join(".agents", "runtime")
    os.makedirs(runtime_dir, exist_ok=True)
    
    pending_path = os.path.join(runtime_dir, "pending-choice.json")
    response_path = os.path.join(runtime_dir, "choice-response.json")
    ui_capabilities_path = os.path.join(runtime_dir, "ui-capabilities.json")
    
    if args.subaction == "create":
        raw_options = args.options.strip() if args.options else ""
        options = []
        if raw_options.startswith("["):
            try:
                options = json.loads(raw_options)
            except json.JSONDecodeError as e:
                print(f"Error parsing options JSON: {e}", file=sys.stderr)
                sys.exit(1)
        elif raw_options:
            for opt in raw_options.split(","):
                opt = opt.strip()
                if opt:
                    options.append({"id": opt, "label": opt})
                    
        choice_type = args.type or "choice"
        choice_data = {
            "type": choice_type,
            "id": args.id,
            "title": args.title,
            "description": args.desc or "",
            "required": args.required,
            "allow_cancel": args.allow_cancel,
            "options": options
        }
        
        tmp_path = pending_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(choice_data, f, indent=2, ensure_ascii=False)
        if os.path.exists(pending_path):
            os.replace(tmp_path, pending_path)
        else:
            os.rename(tmp_path, pending_path)
            
        print(f"Choice {args.id} created successfully.")
        
    elif args.subaction == "wait":
        import time
        interactive_choice = False
        if os.path.exists(ui_capabilities_path):
            try:
                with open(ui_capabilities_path, "r", encoding="utf-8") as f:
                    caps = json.load(f)
                    interactive_choice = caps.get("interactive_choice", False)
            except Exception:
                pass
                
        if os.environ.get("AIWF_INTERACTIVE_CHOICE") == "true":
            interactive_choice = True
            
        timeout = args.timeout or 60
        start_time = time.time()
        choice_resolved = False
        selected_option = None
        
        if interactive_choice:
            print(f"Waiting for UI choice response for {args.id} (timeout={timeout}s)...")
            while time.time() - start_time < timeout:
                if os.path.exists(response_path):
                    try:
                        with open(response_path, "r", encoding="utf-8") as f:
                            resp_data = json.load(f)
                        if resp_data.get("id") == args.id:
                            selected_option = resp_data.get("selected")
                            choice_resolved = True
                            break
                    except Exception:
                        pass
                time.sleep(0.5)
                
        if not choice_resolved:
            if interactive_choice:
                print("\nTimeout waiting for UI response. Switching to Text Fallback Mode...")
            
            if os.path.exists(pending_path):
                try:
                    with open(pending_path, "r", encoding="utf-8") as f:
                        choice_data = json.load(f)
                except Exception:
                    choice_data = {}
            else:
                choice_data = {}
                
            title = choice_data.get("title", args.id or "Choice Required")
            desc = choice_data.get("description", "")
            options = choice_data.get("options", [])
            choice_type = choice_data.get("type", "choice")
            allow_cancel = choice_data.get("allow_cancel", True)
            
            print(f"\n=== {title} ===")
            if desc:
                print(desc)
            print("-" * len(title))
            
            option_ids = []
            if choice_type == "approval":
                print("[Y] Yes / Continue")
                print("[N] No / Cancel")
                option_ids = ["y", "yes", "proceed", "continue", "n", "no", "cancel"]
            else:
                for idx, opt in enumerate(options):
                    lbl = opt.get("label", opt.get("id"))
                    opt_desc = opt.get("description", "")
                    suffix = f" ({opt_desc})" if opt_desc else ""
                    print(f"{idx + 1}. {lbl}{suffix}")
                    option_ids.append(opt.get("id"))
                    
            if allow_cancel and choice_type != "approval":
                print("C. Cancel")
                
            while True:
                user_val = input("\nEnter selection: ").strip()
                if not user_val:
                    continue
                val_lower = user_val.lower()
                
                if val_lower == "c" or val_lower == "cancel":
                    if allow_cancel:
                        selected_option = "cancel"
                        break
                    else:
                        print("Cancel is not allowed for this choice.")
                        continue
                        
                if choice_type == "approval":
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
                    if 0 <= idx < len(options):
                        selected_option = options[idx]["id"]
                        break
                except ValueError:
                    pass
                    
                matched = False
                for opt in options:
                    if opt["id"].lower() == val_lower or opt["label"].lower() == val_lower:
                        selected_option = opt["id"]
                        matched = True
                        break
                if matched:
                    break
                print("Invalid selection. Please try again.")
                
            resp_payload = {
                "id": args.id or "unknown",
                "selected": selected_option,
                "cancelled": selected_option == "cancel"
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
        
    elif args.subaction == "read":
        if os.path.exists(response_path):
            try:
                with open(response_path, "r", encoding="utf-8") as f:
                    resp_data = json.load(f)
                if resp_data.get("id") == args.id:
                    print(resp_data.get("selected", ""))
                    return
            except Exception:
                pass
        print("")
        
    elif args.subaction == "clear":
        for p in [pending_path, response_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        print("Choice files cleared.")
```

2. Register the `choice` subcommand inside `main()`:
```python
    choice_p = subparsers.add_parser("choice")
    choice_sub = choice_p.add_subparsers(dest="subaction", required=True)
    
    choice_create = choice_sub.add_parser("create")
    _ = choice_create.add_argument("--id", required=True, type=str)
    _ = choice_create.add_argument("--title", required=True, type=str)
    _ = choice_create.add_argument("--desc", type=str)
    _ = choice_create.add_argument("--options", required=True, type=str)
    _ = choice_create.add_argument("--type", type=str, default="choice")
    _ = choice_create.add_argument("--required", action="store_true")
    _ = choice_create.add_argument("--allow-cancel", action="store_true")
    
    choice_wait = choice_sub.add_parser("wait")
    _ = choice_wait.add_argument("--id", required=True, type=str)
    _ = choice_wait.add_argument("--timeout", type=int)
    
    choice_read = choice_sub.add_parser("read")
    _ = choice_read.add_argument("--id", required=True, type=str)
    
    _ = choice_sub.add_parser("clear")
```

3. Bind the `"choice"` command:
```python
    cmds = {
        # ...
        "choice": do_choice,
        # ...
    }
```

---

### Component 2: Global Policies

#### [MODIFY] [AI_RULES.md](file:///e:/AgentsProject/AI_RULES.md) and [AI_RULES.md](file:///e:/AgentsProject/.agents/AI_RULES.md)
Update **Section 1: Approval Gate Policy** with the following instruction:
- **No Double Confirmation Policy**: If a user selection or confirmation has already been resolved via the interactive choice UI (the `ask_question` tool) or the CLI `prompt select`/`choice` subcommands, the Agent **MUST NOT** prompt the user again for confirmation in the chat text. The selection is treated as final and the Agent must immediately proceed to execution.

---

### Component 3: Skill Instructions

#### [MODIFY] [SKILL.md](file:///e:/AgentsProject/skills/quick-fix/SKILL.md), [SKILL.md](file:///e:/AgentsProject/skills/quick-feature/SKILL.md), [SKILL.md](file:///e:/AgentsProject/skills/blueprint-to-implementation/SKILL.md), [SKILL.md](file:///e:/AgentsProject/skills/orchestrator/SKILL.md), and [SKILL.md](file:///e:/AgentsProject/skills/implementation-to-release/SKILL.md)
Ensure that every user approval gate that runs a CLI prompt select command uses the resulting value directly. When a selection is returned, execute the next phase immediately. Do not ask for confirmation of the user's choice again in the chat.

*(Apply identical updates to `.agents/skills/` copies.)*

---

## 2. Test Plan

- Run unit test:
  `python -m unittest skills/workflow-runtime/tests/test_choice.py`
  *(All tests must PASS)*

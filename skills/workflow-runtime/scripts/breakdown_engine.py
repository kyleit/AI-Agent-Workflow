# breakdown_engine.py
import os
import sys
import json
import re
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from context import estimate_context_usage

BREAKDOWN_FILE = os.path.join(".agents", "state", "breakdown.json")

def get_file_meta(filepath: str) -> tuple[int, str]:
    if not filepath or not os.path.exists(filepath):
        return 0, "N/A"
    try:
        sz = os.path.getsize(filepath)
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime).astimezone().isoformat()
        return sz, dt
    except Exception:
        return 0, "N/A"

def generate_breakdown(session_data: dict, workspace_root: str = ".") -> dict:
    conv_id = session_data.get("conversation_id", "")
    current_skill = session_data.get("current_skill", "unknown")
    current_cmd = session_data.get("current_command", "unknown")
    
    # 1. Get active context base tokens
    usage = estimate_context_usage()
    total_active_tokens = usage.get("active_tokens", 0)
    if total_active_tokens == 0:
        total_active_tokens = 5000  # Fallback minimum baseline
        
    categories = {}
    
    # 2. Category: AI_RULES
    rules_path = os.path.join(workspace_root, "AI_RULES.md")
    rules_sz, rules_time = get_file_meta(rules_path)
    categories["AI_RULES"] = {
        "tokens": int(rules_sz / 3),
        "loads": 1,
        "last_loaded": rules_time,
        "details": [{"name": "AI_RULES.md", "tokens": int(rules_sz / 3), "last_loaded": rules_time}]
    }
    
    # 3. Category: AGENTS
    agents_path = os.path.join(workspace_root, ".agents", "AGENTS.md")
    if not os.path.exists(agents_path):
        agents_path = os.path.join(workspace_root, "AGENTS.md")
    agents_sz, agents_time = get_file_meta(agents_path)
    categories["AGENTS"] = {
        "tokens": int(agents_sz / 3),
        "loads": 1,
        "last_loaded": agents_time,
        "details": [{"name": "AGENTS.md", "tokens": int(agents_sz / 3), "last_loaded": agents_time}]
    }
    
    # 4. Category: Loaded SKILL.md files
    skill_tokens = 0
    skill_time = "N/A"
    skill_loads = 0
    skill_details = []
    if current_skill and current_skill != "unknown":
        skill_path = os.path.join(workspace_root, ".agents", "skills", current_skill, "SKILL.md")
        if os.path.exists(skill_path):
            skill_sz, skill_time = get_file_meta(skill_path)
            skill_tokens = int(skill_sz / 3)
            skill_loads = 1
            skill_details.append({"name": f"{current_skill}/SKILL.md", "tokens": skill_tokens, "last_loaded": skill_time})
    categories["Loaded SKILL.md files"] = {
        "tokens": skill_tokens,
        "loads": skill_loads,
        "last_loaded": skill_time,
        "details": skill_details
    }
    
    # 5. Categories: Brainstorming, Plans, Blueprints, ADRs
    def sum_doc_tokens(folder: str, pattern: str = None) -> tuple[int, int, str, list]:
        dir_path = os.path.join(workspace_root, "docs", folder)
        if not os.path.exists(dir_path):
            return 0, 0, "N/A", []
        
        sz_total = 0
        file_count = 0
        latest_time = "N/A"
        details = []
        try:
            for f in os.listdir(dir_path):
                if pattern and not re.search(pattern, f):
                    continue
                fp = os.path.join(dir_path, f)
                if os.path.isfile(fp):
                    sz, dt = get_file_meta(fp)
                    sz_total += sz
                    file_count += 1
                    if latest_time == "N/A" or dt > latest_time:
                        latest_time = dt
                    details.append({
                        "name": f,
                        "tokens": int(sz / 3),
                        "last_loaded": dt
                    })
        except Exception:
            pass
        return int(sz_total / 3), file_count, latest_time, details

    brain_tok, brain_ld, brain_t, brain_det = sum_doc_tokens("brainstorming")
    categories["Brainstorming documents"] = {"tokens": brain_tok, "loads": brain_ld, "last_loaded": brain_t, "details": brain_det}
    
    plan_tok, plan_ld, plan_t, plan_det = sum_doc_tokens("plans")
    categories["Plans"] = {"tokens": plan_tok, "loads": plan_ld, "last_loaded": plan_t, "details": plan_det}
    
    blue_tok, blue_ld, blue_t, blue_det = sum_doc_tokens("designs")
    categories["Blueprints"] = {"tokens": blue_tok, "loads": blue_ld, "last_loaded": blue_t, "details": blue_det}
    
    adr_tok, adr_ld, adr_t, adr_det = sum_doc_tokens("adr")
    categories["ADRs"] = {"tokens": adr_tok, "loads": adr_ld, "last_loaded": adr_t, "details": adr_det}
    
    # 6. Category: Project Memory
    mem_sz1, mem_t1 = get_file_meta(os.path.join(workspace_root, ".agents", "memory", "memory-state.json"))
    mem_sz2, mem_t2 = get_file_meta(os.path.join(workspace_root, ".agents", "project-profile.json"))
    mem_sz3, mem_t3 = get_file_meta(os.path.join(workspace_root, ".agents", "memory", "project-summary.md"))
    mem_tokens = int((mem_sz1 + mem_sz2 + mem_sz3) / 3)
    latest_mem_t = max(filter(lambda x: x != "N/A", [mem_t1, mem_t2, mem_t3]), default="N/A")
    mem_details = []
    if mem_sz1 > 0: mem_details.append({"name": "memory-state.json", "tokens": int(mem_sz1/3), "last_loaded": mem_t1})
    if mem_sz2 > 0: mem_details.append({"name": "project-profile.json", "tokens": int(mem_sz2/3), "last_loaded": mem_t2})
    if mem_sz3 > 0: mem_details.append({"name": "project-summary.md", "tokens": int(mem_sz3/3), "last_loaded": mem_t3})
    categories["Project Memory"] = {
        "tokens": mem_tokens,
        "loads": len(mem_details),
        "last_loaded": latest_mem_t,
        "details": mem_details
    }
    
    # 7. Category: RAG results
    rag_tokens = 0
    rag_details = []
    if "memory-search" in current_cmd or "memory-init" in current_cmd:
        rag_tokens = 1500  # standard RAG retrieval window
        rag_details.append({"name": "RAG Retrieved Context", "tokens": 1500, "last_loaded": datetime.now().astimezone().isoformat()})
    categories["RAG results"] = {
        "tokens": rag_tokens,
        "loads": len(rag_details),
        "last_loaded": datetime.now().astimezone().isoformat() if rag_tokens > 0 else "N/A",
        "details": rag_details
    }
    
    # 8. Category: Workspace file reads, Conversation History, Tool results
    ws_tokens = 0
    ws_loads = 0
    ws_time = "N/A"
    ws_details = []
    
    hist_tokens = 0
    hist_loads = 0
    hist_time = "N/A"
    
    tool_tokens = 0
    tool_loads = 0
    tool_time = "N/A"
    
    home = os.path.expanduser("~")
    brain_dir = os.path.join(home, ".gemini", "antigravity-ide", "brain")
    if conv_id and os.path.exists(brain_dir):
        log_path = os.path.join(brain_dir, conv_id, ".system_generated", "logs", "transcript.jsonl")
        if os.path.exists(log_path):
            try:
                unique_files = {}
                with open(log_path, "r", encoding="utf-8") as f:
                    for line_str in f:
                        if not line_str.strip():
                            continue
                        try:
                            line = json.loads(line_str)
                        except Exception:
                            continue
                        
                        source = line.get("source")
                        type_ = line.get("type")
                        content = line.get("content", "")
                        dt = line.get("created_at", "N/A")
                        
                        tool_calls = line.get("tool_calls", [])
                        if not tool_calls and isinstance(content, dict):
                            tool_calls = content.get("tool_calls", [])
                        
                        if tool_calls:
                            for tc in tool_calls:
                                name = tc.get("name")
                                args = tc.get("args", {})
                                path_val = None
                                if name == "view_file":
                                    path_val = args.get("AbsolutePath")
                                elif name == "read_resource":
                                    path_val = args.get("Uri")
                                
                                if path_val:
                                    if path_val.startswith("file://"):
                                        path_val = path_val[7:]
                                    if not os.path.isabs(path_val):
                                        path_val = os.path.join(workspace_root, path_val)
                                    path_val = path_val.replace("\\", "/")
                                    if os.path.exists(path_val):
                                        sz = os.path.getsize(path_val)
                                        tok = int(sz / 3)
                                        # Keep track of file loads count and last loaded time
                                        if path_val not in unique_files:
                                            unique_files[path_val] = {"tokens": tok, "loads": 1, "last_loaded": dt}
                                        else:
                                            unique_files[path_val]["loads"] += 1
                                            unique_files[path_val]["last_loaded"] = dt
                                            
                        if type_ == "USER_INPUT":
                            hist_tokens += int(len(content) / 3)
                            hist_loads += 1
                            if hist_time == "N/A" or dt > hist_time:
                                hist_time = dt
                        elif type_ == "PLANNER_RESPONSE":
                            hist_tokens += int(len(content) / 3)
                            hist_loads += 1
                            if hist_time == "N/A" or dt > hist_time:
                                hist_time = dt
                        elif type_ in ["RUN_COMMAND", "TOOL_RESULT"] or source == "SYSTEM":
                            tool_tokens += int(len(content) / 3)
                            tool_loads += 1
                            if tool_time == "N/A" or dt > tool_time:
                                tool_time = dt
                
                for fpath, info in unique_files.items():
                    # Relativize for cleaner visualizer display
                    rel_name = os.path.relpath(fpath, workspace_root).replace("\\", "/")
                    ws_tokens += info["tokens"]
                    ws_loads += info["loads"]
                    if ws_time == "N/A" or info["last_loaded"] > ws_time:
                        ws_time = info["last_loaded"]
                    ws_details.append({
                        "name": rel_name,
                        "tokens": info["tokens"],
                        "last_loaded": info["last_loaded"]
                    })
            except Exception:
                pass

    categories["Workspace file reads"] = {"tokens": ws_tokens, "loads": ws_loads, "last_loaded": ws_time, "details": ws_details}
    categories["Conversation History"] = {"tokens": hist_tokens, "loads": hist_loads, "last_loaded": hist_time, "details": []}
    categories["Tool results"] = {"tokens": tool_tokens, "loads": tool_loads, "last_loaded": tool_time, "details": []}
    
    # 9. Category: Build/Test logs
    log_sz1, log_t1 = get_file_meta(os.path.join(workspace_root, "build.log"))
    log_sz2, log_t2 = get_file_meta(os.path.join(workspace_root, "test.log"))
    build_tokens = int((log_sz1 + log_sz2) / 3)
    log_details = []
    if log_sz1 > 0: log_details.append({"name": "build.log", "tokens": int(log_sz1/3), "last_loaded": log_t1})
    if log_sz2 > 0: log_details.append({"name": "test.log", "tokens": int(log_sz2/3), "last_loaded": log_t2})
    categories["Build/Test logs"] = {
        "tokens": build_tokens,
        "loads": len(log_details),
        "last_loaded": max(log_t1, log_t2) if build_tokens > 0 else "N/A",
        "details": log_details
    }
    
    # 10. Sum up categories and compute Other remainder
    known_sum = sum(cat["tokens"] for cat in categories.values())
    other_tokens = max(0, total_active_tokens - known_sum)
    categories["Other runtime context"] = {
        "tokens": other_tokens,
        "loads": 1 if other_tokens > 0 else 0,
        "last_loaded": datetime.now().astimezone().isoformat() if other_tokens > 0 else "N/A",
        "details": []
    }
    
    # Recalculate final total
    final_total_tokens = sum(cat["tokens"] for cat in categories.values())
    if final_total_tokens == 0:
        final_total_tokens = 1
        
    breakdown_list = []
    for name, stats in categories.items():
        pct = round((stats["tokens"] / final_total_tokens) * 100, 2)
        # Sort category details by tokens descending
        dets = stats.get("details", [])
        dets.sort(key=lambda x: x["tokens"], reverse=True)
        breakdown_list.append({
            "category": name,
            "tokens": stats["tokens"],
            "percentage": pct,
            "loads": stats["loads"],
            "last_loaded": stats["last_loaded"],
            "details": dets
        })
        
    # Sort breakdown list: largest contributor first
    breakdown_list.sort(key=lambda x: x["tokens"], reverse=True)
    
    return {
        "conversation_id": conv_id,
        "timestamp": datetime.now().astimezone().isoformat(),
        "total_tokens": final_total_tokens,
        "breakdown": breakdown_list
    }

def update_breakdown_file(session_data: dict, workspace_root: str = ".") -> dict:
    payload = generate_breakdown(session_data, workspace_root)
    state_dir = os.path.dirname(BREAKDOWN_FILE)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir, exist_ok=True)
        
    tmp_path = BREAKDOWN_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, BREAKDOWN_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return payload

# checkpoint.py

CHECKPOINTS = {
    1: "Initialization Complete",
    2: "Memory Loaded",
    3: "Architecture Analysis Complete",
    4: "Blueprint/Fix Spec Generated",
    5: "Implementation Ready",
    6: "Implementation Complete",
    7: "Debug Complete",
    8: "Frontend Visual Debug Complete",
    9: "Verification Complete",
    10: "Release Complete"
}

def get_checkpoint_name(level: int) -> str:
    return CHECKPOINTS.get(level, "Unknown Checkpoint")

def validate_checkpoint_level(current: int, required: str) -> bool:
    required = required.strip()
    if "or" in required:
        parts = [p.strip() for p in required.split("or")]
        for p in parts:
            p_clean = p
            if not p.startswith("exactly") and not p.startswith("at least"):
                if required.startswith("exactly"):
                    p_clean = f"exactly {p}"
                elif required.startswith("at least"):
                    p_clean = f"at least {p}"
            if validate_checkpoint_level(current, p_clean):
                return True
        return False
        
    if required.startswith("at least"):
        try:
            req_val = int(required.replace("at least", "").strip())
            return current >= req_val
        except ValueError:
            return False
    elif required.startswith("exactly"):
        try:
            req_val = int(required.replace("exactly", "").strip())
            return current == req_val
        except ValueError:
            return False
    else:
        try:
            req_val = int(required.strip())
            return current == req_val
        except ValueError:
            return True

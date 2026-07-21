import os
import sys
import urllib.request
import urllib.parse

def send_message(text: str) -> bool:
    env_path = os.path.join(".agents", "config", ".env.telegram-notify")
    if not os.path.exists(env_path):
        print("Error: .env.telegram-notify not found", file=sys.stderr)
        return False
        
    token = None
    chat_id = None
    proxy = None
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "TELEGRAM_BOT_TOKEN":
                        token = v
                    elif k == "TELEGRAM_CHAT_ID":
                        chat_id = v
                    elif k == "TELEGRAM_PROXY":
                        proxy = v
    except Exception as e:
        print(f"Error parsing .env.telegram-notify: {e}", file=sys.stderr)
        return False
        
    if not token or not chat_id:
        print("Error: Bot token or chat ID not found in config", file=sys.stderr)
        return False
        
    # Try to resolve project-specific chat_id from projects.json registry
    try:
        import platform
        import json
        from pathlib import Path
        system = platform.system()
        reg_dir = Path.home() / ".config" / "aiwf"
        if system == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                reg_dir = Path(appdata) / "aiwf"
        elif system == "Darwin":
            reg_dir = Path.home() / "Library" / "Application Support" / "aiwf"
        
        reg_path = reg_dir / "projects.json"
        if reg_path.exists():
            with open(reg_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
            curr_abs = str(Path(".").resolve()).lower()
            for p in registry.get("projects", []):
                if str(Path(p["path"]).resolve()).lower() == curr_abs:
                    if p.get("telegram_chat_id"):
                        chat_id = p["telegram_chat_id"]
                        break
    except Exception:
        pass
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    opener = urllib.request.build_opener()
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy,
            "https": proxy
        })
        opener.add_handler(proxy_handler)
        
    try:
        with opener.open(req, timeout=15) as response:
            response.read()
        return True
    except Exception as e:
        print(f"Error sending message: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_message.py <message_text>", file=sys.stderr)
        sys.exit(1)
    msg = sys.argv[1]
    if send_message(msg):
        print("Message sent successfully")
        sys.exit(0)
    else:
        sys.exit(1)

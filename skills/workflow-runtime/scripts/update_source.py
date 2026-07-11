# update_source.py
import os
import subprocess
import json
import sys

class SourceRepositoryService:
    def __init__(self, source_path: str = ".", remote: str = "origin", branch: str = "main"):
        self.source_path = os.path.abspath(source_path)
        self.remote = remote
        self.branch = branch

    def _run_git(self, args: list[str]) -> tuple[int, str, str]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.source_path,
                capture_output=True,
                text=True,
                check=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return -1, "", str(e)

    def check_status(self) -> dict:
        if not os.path.exists(os.path.join(self.source_path, ".git")):
            return {"status": "error", "message": f"Path is not a Git repository: {self.source_path}"}

        # Detached HEAD check
        _, head_branch, _ = self._run_git(["symbolic-ref", "-q", "HEAD"])
        is_detached = head_branch == ""

        # Current branch
        code, current_branch, _ = self._run_git(["branch", "--show-current"])
        if is_detached:
            current_branch = "HEAD (detached)"

        # Upstream branch configuration
        _, upstream, _ = self._run_git(["rev-parse", "--abbrev-ref", "@{u}"])
        if not upstream or "@{u}" in upstream:
            upstream = f"{self.remote}/{self.branch}"

        # Current commit
        _, current_commit, _ = self._run_git(["rev-parse", "HEAD"])

        # Dirty index check
        code_diff, _, _ = self._run_git(["diff-index", "--quiet", "HEAD", "--"])
        is_dirty = code_diff != 0

        # Untracked files check
        _, untracked, _ = self._run_git(["status", "--porcelain"])
        has_untracked = False
        for line in untracked.splitlines():
            if line.startswith("??"):
                has_untracked = True
                break

        # Non-destructive fetch to get updates
        self.fetch_updates()

        # Compare commits
        _, remote_commit, _ = self._run_git(["rev-parse", upstream])
        
        is_up_to_date = current_commit == remote_commit
        is_behind = False
        is_ahead = False
        is_diverged = False

        if not is_up_to_date and remote_commit:
            # Check ahead/behind count
            code_ab, ab_out, _ = self._run_git(["rev-list", "--left-right", "--count", f"HEAD...{upstream}"])
            if code_ab == 0 and ab_out:
                parts = ab_out.split()
                if len(parts) == 2:
                    ahead = int(parts[0])
                    behind = int(parts[1])
                    if ahead > 0 and behind > 0:
                        is_diverged = True
                    elif ahead > 0:
                        is_ahead = True
                    elif behind > 0:
                        is_behind = True

        return {
            "status": "success",
            "source_path": self.source_path,
            "branch": current_branch,
            "upstream": upstream,
            "commit": current_commit,
            "remote_commit": remote_commit,
            "is_dirty": is_dirty or has_untracked,
            "is_detached": is_detached,
            "is_up_to_date": is_up_to_date,
            "is_behind": is_behind,
            "is_ahead": is_ahead,
            "is_diverged": is_diverged
        }

    def fetch_updates(self) -> bool:
        code, _, _ = self._run_git(["fetch", self.remote])
        return code == 0

    def pull_ff(self) -> bool:
        # Default behavior: Fast-forward only
        code, out, err = self._run_git(["pull", "--ff-only", self.remote, self.branch])
        if code != 0:
            print(f"Error executing pull: {err}", file=sys.stderr)
            return False
        return True

def handle_update_source(args) -> int:
    source_path = args.source or os.environ.get("AIWF_SOURCE_PATH") or "."
    remote = args.remote or "origin"
    branch = args.branch or "main"

    service = SourceRepositoryService(source_path, remote, branch)
    status = service.check_status()

    if status.get("status") == "error":
        print(f"Error: {status.get('message')}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(status, indent=2))
        return 0

    if args.check:
        if status["is_up_to_date"]:
            print("Framework source is up-to-date.")
            return 0
        else:
            print("Updates are available.")
            return 2  # Special code for check mode update available

    print(f"Branch: {status['branch']}")
    print(f"Upstream: {status['upstream']}")
    print(f"Local commit: {status['commit']}")
    print(f"Remote commit: {status['remote_commit']}")

    if status["is_up_to_date"]:
        print("Framework source is already up-to-date.")
        return 0

    if status["is_dirty"] and not args.allow_dirty:
        print("Error: Source repository has local changes (dirty). Aborting update.", file=sys.stderr)
        print("Use --allow-dirty to ignore untracked/dirty changes (or stash them).", file=sys.stderr)
        return 1

    if status["is_diverged"]:
        print("Error: Local branch has diverged from upstream. Automatic update is unsafe.", file=sys.stderr)
        return 1

    if status["is_ahead"]:
        print("Notice: Local commits are ahead of upstream. Fast-forward update not needed.")
        return 0

    if args.dry_run:
        print(f"[DRY-RUN] Would perform git pull --ff-only {remote} {branch}")
        return 0

    # Auto-approve yes flag check
    if not args.yes:
        # Ask user confirmation
        print("An update is available. Do you want to proceed? (y/n): ", end="")
        sys.stdout.flush()
        choice = sys.stdin.readline().strip().lower()
        if choice not in ["y", "yes"]:
            print("Update cancelled by user.")
            return 0

    print("Executing update...")
    if service.pull_ff():
        print("Update completed successfully.")
        return 0
    else:
        print("Update failed.", file=sys.stderr)
        return 1

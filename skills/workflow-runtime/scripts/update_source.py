# update_source.py
import os
import subprocess
import json
import sys
import re

DEFAULT_REPO_URL = "https://github.com/kyleit/AI-Agent-Workflow.git"

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

    def init_repo_if_missing(self, remote_url: str = DEFAULT_REPO_URL, releases_only: bool = True) -> bool:
        git_dir = os.path.join(self.source_path, ".git")
        if not os.path.exists(git_dir):
            print(f"Notice: Path '{self.source_path}' is not a Git repository. Initializing Git repository with remote {remote_url}...")
            c1, _, e1 = self._run_git(["init"])
            if c1 != 0:
                print(f"Error initializing Git: {e1}", file=sys.stderr)
                return False
            
            c2, _, _ = self._run_git(["remote", "add", self.remote, remote_url])
            if c2 != 0:
                self._run_git(["remote", "set-url", self.remote, remote_url])

            print(f"Fetching tags and refs from {self.remote}...")
            c3, _, e3 = self._run_git(["fetch", "--tags", self.remote])
            if c3 != 0:
                print(f"Error fetching from {self.remote}: {e3}", file=sys.stderr)
                return False

            if releases_only:
                latest_tag = self.get_latest_stable_release_tag()
                if latest_tag:
                    print(f"Found latest stable release tag: {latest_tag}. Checking out {latest_tag}...")
                    c4, _, e4 = self._run_git(["checkout", f"tags/{latest_tag}"])
                    if c4 == 0:
                        return True
                    print(f"Warning: Failed to checkout tag {latest_tag}: {e4}. Falling back to default branch.", file=sys.stderr)

            # Fallback to checking out default branch
            self._run_git(["checkout", "-B", self.branch, f"{self.remote}/{self.branch}"])
            return True
        return True

    def get_latest_stable_release_tag(self) -> str | None:
        c, out, _ = self._run_git(["tag", "-l"])
        if c != 0 or not out:
            return None

        stable_tags = []
        for tag in out.splitlines():
            tag = tag.strip()
            # Skip alpha, beta, rc, dev, preview tags
            if re.search(r"(alpha|beta|rc|dev|preview)", tag, re.IGNORECASE):
                continue
            stable_tags.append(tag)

        if not stable_tags:
            return None

        # Sort semantic version tags (e.g. v1.0.0, v3.2.0)
        def tag_key(t: str):
            clean = re.sub(r"^v", "", t)
            parts = []
            for p in clean.split("."):
                try:
                    parts.append(int(p))
                except ValueError:
                    parts.append(0)
            return parts

        stable_tags.sort(key=tag_key)
        return stable_tags[-1]

    def check_status(self, auto_init: bool = True, repo_url: str = DEFAULT_REPO_URL, releases_only: bool = True) -> dict:
        if not os.path.exists(os.path.join(self.source_path, ".git")):
            if auto_init:
                if not self.init_repo_if_missing(repo_url, releases_only):
                    return {"status": "error", "message": f"Failed to initialize Git repository at: {self.source_path}"}
            else:
                return {"status": "error", "message": f"Path is not a Git repository: {self.source_path}"}

        # Detached HEAD check
        _, head_branch, _ = self._run_git(["symbolic-ref", "-q", "HEAD"])
        is_detached = head_branch == ""

        # Current branch or tag
        code, current_branch, _ = self._run_git(["branch", "--show-current"])
        if is_detached:
            _, tag_desc, _ = self._run_git(["describe", "--tags", "--exact-match"])
            if tag_desc:
                current_branch = f"tag: {tag_desc}"
            else:
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
        code, _, _ = self._run_git(["fetch", "--tags", self.remote])
        return code == 0

    def pull_ff(self, releases_only: bool = True) -> bool:
        if releases_only:
            latest_tag = self.get_latest_stable_release_tag()
            if latest_tag:
                print(f"Updating to latest stable release tag: {latest_tag}...")
                code, out, err = self._run_git(["checkout", f"tags/{latest_tag}"])
                if code == 0:
                    return True
                print(f"Warning: Checkout tag {latest_tag} failed: {err}. Falling back to branch pull.", file=sys.stderr)

        # Default behavior: Fast-forward branch pull
        code, out, err = self._run_git(["pull", "--ff-only", self.remote, self.branch])
        if code != 0:
            print(f"Error executing pull: {err}", file=sys.stderr)
            return False
        return True

def handle_update_source(args) -> int:
    source_path = getattr(args, "source", None) or getattr(args, "source_opt", None) or os.environ.get("AIWF_SOURCE_PATH") or "."
    remote = getattr(args, "remote", None) or "origin"
    branch = getattr(args, "branch", None) or "main"
    url = getattr(args, "url", None) or DEFAULT_REPO_URL
    releases_only = not getattr(args, "allow_prerelease", False)

    service = SourceRepositoryService(source_path, remote, branch)
    status = service.check_status(auto_init=True, repo_url=url, releases_only=releases_only)

    if status.get("status") == "error":
        print(f"Error: {status.get('message')}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(json.dumps(status, indent=2))
        return 0

    if getattr(args, "check", False):
        if status["is_up_to_date"]:
            print("Framework source is up-to-date.")
            return 0
        else:
            print("Updates are available.")
            return 2

    print(f"Branch: {status['branch']}")
    print(f"Upstream: {status['upstream']}")
    print(f"Local commit: {status['commit']}")
    print(f"Remote commit: {status['remote_commit']}")

    if status["is_up_to_date"]:
        print("Framework source is already up-to-date.")
        return 0

    if status["is_dirty"] and not getattr(args, "allow_dirty", False):
        print("Error: Source repository has local changes (dirty). Aborting update.", file=sys.stderr)
        print("Use --allow-dirty to ignore untracked/dirty changes (or stash them).", file=sys.stderr)
        return 1

    if status["is_diverged"]:
        print("Error: Local branch has diverged from upstream. Automatic update is unsafe.", file=sys.stderr)
        return 1

    if status["is_ahead"]:
        print("Notice: Local commits are ahead of upstream. Fast-forward update not needed.")
        return 0

    if getattr(args, "dry_run", False):
        print(f"[DRY-RUN] Would perform git update for {remote} {branch} (releases_only={releases_only})")
        return 0

    if not getattr(args, "yes", False):
        print("An update is available. Do you want to proceed? (y/n): ", end="")
        sys.stdout.flush()
        choice = sys.stdin.readline().strip().lower()
        if choice not in ["y", "yes"]:
            print("Update cancelled by user.")
            return 0

    print("Executing update...")
    if service.pull_ff(releases_only=releases_only):
        print("Update completed successfully.")
        return 0
    else:
        print("Update failed.", file=sys.stderr)
        return 1

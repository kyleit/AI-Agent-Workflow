# transaction_rollback_state_reversion.py
import subprocess

class TransactionRollbackManager:
    """
    FEAT-102: Transaction Rollback & State Reversion
    Manages transaction state reversion (Git stash, Goal tree recovery).
    """
    def __init__(self):
        self.stash_active = False

    def create_git_checkpoint(self) -> bool:
        try:
            res = subprocess.run(["git", "stash", "create"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                self.stash_hash = res.stdout.strip()
                # Store stash reference in git
                subprocess.run(["git", "stash", "store", "-m", "AIWF_Checkpoint", self.stash_hash])
                self.stash_active = True
                return True
        except Exception:
            pass
        return False

    def rollback_git(self) -> bool:
        if self.stash_active:
            try:
                res = subprocess.run(["git", "stash", "pop"], capture_output=True)
                self.stash_active = False
                return res.returncode == 0
            except Exception:
                pass
        return False

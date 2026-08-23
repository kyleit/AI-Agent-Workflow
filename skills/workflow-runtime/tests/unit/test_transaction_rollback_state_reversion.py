import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from transaction_rollback_state_reversion import TransactionRollbackManager

def test_transaction_rollback_init():
    manager = TransactionRollbackManager()
    assert manager.stash_active is False

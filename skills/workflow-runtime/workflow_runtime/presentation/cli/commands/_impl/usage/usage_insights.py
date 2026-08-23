"""do_usage extended subactions (part B)."""
from __future__ import annotations


from typing import Any


def do_usage_extended(args: Any) -> None:
    """Extended usage subactions: insights, recommendations, timeline, test-summary, etc.

    These subactions are dispatched from do_usage() in usage_report.py.
    Implementation delegates to infrastructure layer.
    """
    subaction = getattr(args, 'subaction', None)

    if subaction == 'recommendations':
        try:
            from workflow_runtime.application.analytics.insights_engine import \
                generate_recommendations
            from workflow_runtime.infrastructure.persistence.db import (
                get_provider_requests, get_recommendations,
                save_recommendations)
            from workflow_runtime.infrastructure.session.session import \
                load_session
            session = load_session()
            conv_id = session.get('conversation_id', '')
            recs = get_recommendations(conv_id)
            if not recs:
                reqs = get_provider_requests({'conversation_id': conv_id})
                recs = generate_recommendations(reqs, conv_id)
                if recs:
                    save_recommendations(recs)
            if recs:
                for r in recs[:5]:
                    print(f"  [{r.get('priority', 'N')}] {r.get('text', '')}")
            else:
                print('No recommendations available.')
        except Exception as e:
            print(f'[recommendations] {e}')

    elif subaction == 'insights':
        try:
            from workflow_runtime.infrastructure.persistence.db import \
                get_insight_snapshots
            from workflow_runtime.infrastructure.session.session import \
                load_session
            session = load_session()
            conv_id = session.get('conversation_id', '')
            snapshots = get_insight_snapshots(conv_id)
            if snapshots:
                latest = snapshots[-1]
                print(f"Insights for {conv_id}:")
                for k, v in latest.items():
                    if k not in ('conversation_id', 'timestamp'):
                        print(f"  {k}: {v}")
            else:
                print('No insights available.')
        except Exception as e:
            print(f'[insights] {e}')

    else:
        # Fallback for other extended subactions
        print(f'[usage] Extended subaction {subaction!r} not implemented.')


_do_usage_extended = do_usage_extended

__all__ = ["do_usage_extended", "_do_usage_extended"]

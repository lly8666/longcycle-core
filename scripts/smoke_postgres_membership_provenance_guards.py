from __future__ import annotations

import os
from datetime import timedelta
from typing import Callable
from uuid import UUID

import psycopg
from psycopg.rows import dict_row


def _expect_rejected(label: str, action: Callable[[psycopg.Connection[dict[str, object]]], None], dsn: str) -> None:
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row) as connection:
        try:
            action(connection)
        except psycopg.Error as exc:
            if exc.sqlstate != "23514":
                raise AssertionError(f"{label}: wrong SQLSTATE {exc.sqlstate}: {exc}") from exc
            return
    raise AssertionError(f"{label}: mutation unexpectedly succeeded")


def main() -> None:
    dsn = os.environ["LONGCYCLE_DATABASE_URL"]
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row) as connection:
        decision = connection.execute(
            """
            SELECT id, selected_assertion_id, supporting_assertion_ids,
                   supporting_judgment_run_ids, last_confirmed_at
            FROM research.industry_membership_semantic_decisions
            ORDER BY last_confirmed_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        run = connection.execute(
            """
            SELECT id
            FROM research.industry_membership_model_judgment_runs
            ORDER BY completed_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    if decision is None or run is None:
        raise AssertionError(
            "membership provenance guard smoke requires the preceding real orientation smoke to seed rows"
        )

    decision_id = UUID(str(decision["id"]))
    run_id = UUID(str(run["id"]))
    supporting_assertion_ids = tuple(UUID(str(item)) for item in decision["supporting_assertion_ids"])
    supporting_run_ids = tuple(UUID(str(item)) for item in decision["supporting_judgment_run_ids"])
    last_confirmed_at = decision["last_confirmed_at"]

    _expect_rejected(
        "judgment-run update",
        lambda connection: connection.execute(
            "UPDATE research.industry_membership_model_judgment_runs "
            "SET reasoning_summary = reasoning_summary || ' tampered' WHERE id = %s",
            (run_id,),
        ),
        dsn,
    )
    _expect_rejected(
        "judgment-run delete",
        lambda connection: connection.execute(
            "DELETE FROM research.industry_membership_model_judgment_runs WHERE id = %s",
            (run_id,),
        ),
        dsn,
    )
    _expect_rejected(
        "semantic-decision identity update",
        lambda connection: connection.execute(
            "UPDATE research.industry_membership_semantic_decisions "
            "SET decision_summary = decision_summary || ' tampered' WHERE id = %s",
            (decision_id,),
        ),
        dsn,
    )
    _expect_rejected(
        "semantic-decision supporting-assertion shrink",
        lambda connection: connection.execute(
            "UPDATE research.industry_membership_semantic_decisions "
            "SET supporting_assertion_ids = %s WHERE id = %s",
            (list(supporting_assertion_ids[:-1]), decision_id),
        ),
        dsn,
    )
    _expect_rejected(
        "semantic-decision supporting-run shrink",
        lambda connection: connection.execute(
            "UPDATE research.industry_membership_semantic_decisions "
            "SET supporting_judgment_run_ids = %s WHERE id = %s",
            (list(supporting_run_ids[:-1]), decision_id),
        ),
        dsn,
    )
    _expect_rejected(
        "semantic-decision confirmation rollback",
        lambda connection: connection.execute(
            "UPDATE research.industry_membership_semantic_decisions "
            "SET last_confirmed_at = %s WHERE id = %s",
            (last_confirmed_at - timedelta(seconds=1), decision_id),
        ),
        dsn,
    )
    _expect_rejected(
        "semantic-decision delete",
        lambda connection: connection.execute(
            "DELETE FROM research.industry_membership_semantic_decisions WHERE id = %s",
            (decision_id,),
        ),
        dsn,
    )

    print(
        "POSTGRES_MEMBERSHIP_PROVENANCE_GUARDS_PASS "
        f"decision={decision_id} judgment_run={run_id}"
    )


if __name__ == "__main__":
    main()

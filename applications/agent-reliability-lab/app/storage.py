"""Small SQLite store for experiment reports and evidence events."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def save_report(report: dict[str, Any], database_path: str) -> str:
    run_id = str(uuid4())
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                scenario TEXT NOT NULL,
                classification TEXT NOT NULL,
                report_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?)",
            (
                run_id,
                datetime.now(timezone.utc).isoformat(),
                report["scenario"],
                report["classification"],
                json.dumps(report, ensure_ascii=False),
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return run_id


def get_report(run_id: str, database_path: str) -> dict[str, Any] | None:
    if not Path(database_path).exists():
        return None
    connection = sqlite3.connect(database_path)
    try:
        row = connection.execute("SELECT report_json FROM runs WHERE id = ?", (run_id,)).fetchone()
    finally:
        connection.close()
    return json.loads(row[0]) if row else None


def list_reports(database_path: str, limit: int = 12) -> list[dict[str, Any]]:
    if not Path(database_path).exists():
        return []
    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute(
            "SELECT id, created_at, scenario, classification FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        connection.close()
    return [
        {"id": row[0], "created_at": row[1], "scenario": row[2], "classification": row[3]}
        for row in rows
    ]
def clear_reports(database_path: str) -> None:
    """Delete all stored experiment reports while keeping the database intact."""
    if not Path(database_path).exists():
        return

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("DELETE FROM runs")
        connection.commit()
    finally:
        connection.close()
        
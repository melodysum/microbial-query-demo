from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DB_PATH = Path(os.environ.get("MICROBIAL_DB", DATA / "microbial.db"))


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force=False):
    if DB_PATH.exists() and not force:
        return
    seed = json.loads((DATA / "seed.json").read_text(encoding="utf-8"))
    literature = json.loads((DATA / "literature.json").read_text(encoding="utf-8"))
    conn = connect()
    conn.executescript("""
    DROP TABLE IF EXISTS taxa; DROP TABLE IF EXISTS strains;
    DROP TABLE IF EXISTS features; DROP TABLE IF EXISTS observations;
    DROP TABLE IF EXISTS evidence; DROP TABLE IF EXISTS literature;
    CREATE TABLE taxa(species TEXT PRIMARY KEY, lineage_json TEXT NOT NULL);
    CREATE TABLE strains(id TEXT PRIMARY KEY, accession TEXT UNIQUE, species TEXT,
      strain_name TEXT, type_strain TEXT, collection_ids TEXT, internal_id TEXT, genome_path TEXT,
      genome_status TEXT, source TEXT, lineage_json TEXT);
    CREATE TABLE features(key TEXT PRIMARY KEY, label TEXT, type TEXT, unit TEXT,
      options_json TEXT, description TEXT);
    CREATE TABLE observations(id INTEGER PRIMARY KEY AUTOINCREMENT,
      strain_id TEXT, feature TEXT, value TEXT, unit TEXT, condition_text TEXT,
      evidence_id TEXT, evidence_status TEXT);
    CREATE TABLE evidence(id TEXT PRIMARY KEY, title TEXT, authors TEXT,
      journal TEXT, year INTEGER, url TEXT, excerpt TEXT, evidence_status TEXT);
    CREATE TABLE literature(id TEXT PRIMARY KEY, record_type TEXT,
      original_number INTEGER, title TEXT, authors TEXT, journal TEXT,
      year INTEGER, shared_date TEXT, project_relation TEXT, url TEXT,
      verification_status TEXT, related_json TEXT);
    """)
    conn.executemany("INSERT INTO taxa VALUES (?, ?)", [(s, json.dumps(v, ensure_ascii=False)) for s, v in {x["species"]: x["lineage"] for x in seed["strains"]}.items()])
    conn.executemany("INSERT INTO strains VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
        (x["id"], x["accession"], x["species"], x["strain_name"], x["type_strain"], json.dumps(x["collection_ids"], ensure_ascii=False), x["internal_id"], x["genome_path"], x["genome_status"], x["source"], json.dumps(x["lineage"], ensure_ascii=False)) for x in seed["strains"]
    ])
    conn.executemany("INSERT INTO features VALUES (?,?,?,?,?,?)", [
        (x["key"], x["label"], x["type"], x.get("unit", ""), json.dumps(x.get("options", []), ensure_ascii=False), x.get("description", "")) for x in seed["features"]
    ])
    conn.executemany("INSERT INTO observations(strain_id,feature,value,unit,condition_text,evidence_id,evidence_status) VALUES (?,?,?,?,?,?,?)", [
        (x["strain_id"], x["feature"], str(x["value"]), x["unit"], x["condition"], x["evidence_id"], x["evidence_status"]) for x in seed["observations"]
    ])
    conn.executemany("INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)", [
        (x["id"], x["title"], x["authors"], x["journal"], x["year"], x["url"], x["excerpt"], x["evidence_status"]) for x in seed["evidence"]
    ])
    conn.executemany("INSERT INTO literature VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
        (x["id"], x["record_type"], x.get("original_number"), x["title"], x.get("authors"), x.get("journal"), x["year"], x.get("shared_date"), x["project_relation"], x.get("url"), x["verification_status"], json.dumps(x.get("related_strains", []))) for x in literature["records"]
    ])
    conn.commit()
    conn.close()


def rows(conn, sql, params=()):
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


if __name__ == "__main__":
    init_db(force=True)
    print(f"Database initialized: {DB_PATH}")

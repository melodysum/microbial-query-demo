from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import BASE, DATA, connect, init_db, rows
from .library import large_sequence_search, library_status
from .query import interpret, search, validate_filters
from .sequence import sequence_search, sequence_stats, skani_binary

init_db()
app = FastAPI(title="微生物信息查询平台 Demo", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7100", "http://127.0.0.1:7100"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)


class InterpretRequest(BaseModel):
    text: str


class SearchRequest(BaseModel):
    filters: list[dict]
    missing_data_policy: str = "separate"


def all_strains(conn):
    return rows(conn, "SELECT * FROM strains ORDER BY species, accession")


def observations(conn, strain_id=None):
    if strain_id:
        return rows(conn, "SELECT * FROM observations WHERE strain_id=?", (strain_id,))
    return rows(conn, "SELECT * FROM observations")


def evidence(conn):
    return {x["id"]: x for x in rows(conn, "SELECT * FROM evidence")}


@app.get("/api/health")
def health():
    with connect() as conn:
        return {
            "status": "ok",
            "version": "microbial-demo-2026-11-12-v1",
            "strains": conn.execute("SELECT COUNT(*) FROM strains").fetchone()[0],
            "species": conn.execute("SELECT COUNT(*) FROM taxa").fetchone()[0],
            "features": conn.execute("SELECT COUNT(*) FROM features").fetchone()[0],
            "literature": conn.execute("SELECT COUNT(*) FROM literature").fetchone()[0],
            "sequence_engine": "skani" if skani_binary() else "kmer_jaccard",
            "qwen_enabled": bool(os.environ.get("QWEN_ENDPOINT")),
            "phenotype_notice": "当前性状为合成演示数据，不能用于科研判断。",
        }


@app.get("/api/taxonomy/tree")
def taxonomy():
    with connect() as conn:
        strains = all_strains(conn)
    counts = {}
    for strain in strains:
        counts[strain["species"]] = counts.get(strain["species"], 0) + 1
    root = {"name": "Bacteria", "rank": "domain", "count": len(strains), "children": {}}
    for strain in strains:
        lineage = json.loads(strain["lineage_json"])
        node = root
        for name in lineage[1:]:
            node = node["children"].setdefault(name, {"name": name, "count": 0, "children": {}})
            node["count"] += 1
    def clean(node):
        result = {k: v for k, v in node.items() if k != "children"}
        result["children"] = [clean(v) for v in node["children"].values()]
        return result
    return {"tree": clean(root), "species_counts": counts}


@app.get("/api/features")
def features():
    with connect() as conn:
        items = rows(conn, "SELECT * FROM features")
    for item in items:
        item["options"] = json.loads(item.pop("options_json"))
    return {"features": items}


@app.get("/api/strains")
def strains():
    with connect() as conn:
        return {"strains": all_strains(conn)}


@app.get("/api/strains/{strain_id}")
def strain_detail(strain_id: str):
    with connect() as conn:
        found = rows(conn, "SELECT * FROM strains WHERE id=?", (strain_id,))
        if not found:
            raise HTTPException(404, "菌株不存在")
        obs = observations(conn, strain_id)
        ev = evidence(conn)
        for item in obs:
            item["evidence"] = ev.get(item["evidence_id"])
        return {"strain": found[0], "observations": obs}


@app.post("/api/query/interpret")
def query_interpret(request: InterpretRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(400, "请输入查询描述")
    return interpret(text)


@app.post("/api/search")
def query_search(request: SearchRequest):
    with connect() as conn:
        feature_list = rows(conn, "SELECT * FROM features")
        try:
            filters = validate_filters(request.filters, feature_list)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return search(all_strains(conn), observations(conn), feature_list, filters)


@app.get("/api/literature")
def literature(record_type: str = "", q: str = ""):
    sql, params = "SELECT * FROM literature", []
    clauses = []
    if record_type:
        clauses.append("record_type=?")
        params.append(record_type)
    if q:
        clauses.append("(title LIKE ? OR authors LIKE ? OR project_relation LIKE ?)")
        params.extend([f"%{q}%"] * 3)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY record_type, year DESC, original_number DESC"
    with connect() as conn:
        records = rows(conn, sql, params)
    for item in records:
        item["related_strains"] = json.loads(item.pop("related_json"))
    return {"records": records, "count": len(records)}


@app.get("/api/library")
def reference_library():
    return library_status()


@app.post("/api/sequence/search")
async def sequence_endpoint(file: UploadFile = File(...), library: str = Form("demo")):
    filename = Path(file.filename or "query.fasta").name
    if not filename.lower().endswith((".fa", ".fna", ".fasta", ".fa.gz", ".fna.gz", ".fasta.gz")):
        raise HTTPException(400, "请上传 FASTA 文件（.fa/.fna/.fasta，可 gzip 压缩）")
    work = BASE / "data" / "queries" / uuid.uuid4().hex
    work.mkdir(parents=True, exist_ok=True)
    target = work / filename
    size = 0
    with target.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > 50 * 1024 * 1024:
                raise HTTPException(413, "演示版限制上传 50 MB 以内的 FASTA")
            handle.write(chunk)
    if size == 0:
        raise HTTPException(400, "文件为空")
    with connect() as conn:
        strains = all_strains(conn)
    try:
        if library == "four_species":
            catalog = {x["accession"]: x for x in strains}
            stats = sequence_stats(target)
            return {**stats, **large_sequence_search(target, library_status()["library_root"], catalog)}
        return sequence_search(target, strains)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"序列检索失败：{exc}") from exc


if (BASE / "dist").exists():
    app.mount("/", StaticFiles(directory=BASE / "dist", html=True), name="frontend")

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from pathlib import Path

from .db import BASE
from .sequence import skani_binary

ACCESSION = re.compile(r"GC[AF]_\d+\.\d+")


def library_definition():
    return json.loads((BASE / "data/library_sources.json").read_text(encoding="utf-8"))


def library_status():
    definition = library_definition()
    root = Path(os.environ.get("MICROBIAL_LIBRARY_ROOT", definition["library_root"]))
    collections = []
    for item in definition["collections"]:
        current = dict(item)
        path = Path(item["path"])
        current["actual_files"] = len(list(path.glob("*"))) if path.is_dir() else 0
        if item["searchable"]:
            ready = root / item["id"] / "READY"
            current["index_ready"] = ready.is_file()
            current["index_path"] = str(root / item["id"])
        else:
            current["index_ready"] = False
            current["index_path"] = None
        collections.append(current)
    searchable = [x for x in collections if x["searchable"]]
    return {
        "collections": collections,
        "all_transfer_complete": all(x["actual_files"] == x["expected_files"] for x in searchable),
        "all_index_ready": all(x["index_ready"] for x in searchable),
        "total_expected_files": sum(x["expected_files"] for x in searchable),
        "library_root": str(root),
    }


def large_sequence_search(query, index_root, catalog):
    binary = skani_binary()
    if not binary:
        raise RuntimeError("大库检索需要服务器上的 skani 0.4.0")
    status = library_status()
    if not status["all_transfer_complete"]:
        raise RuntimeError("四个物种的基因组尚未全部传完")
    if not status["all_index_ready"]:
        missing = [x["id"] for x in status["collections"] if x["searchable"] and not x["index_ready"]]
        raise RuntimeError("大库索引尚未就绪：" + "、".join(missing))
    matches = []
    for collection in status["collections"]:
        if not collection["searchable"]:
            continue
        output = query.parent / f"search_{collection['id']}.tsv"
        command = [binary, "search", "-t", "2", "-n", "10", "-d", collection["index_path"], "-q", str(query), "-o", str(output)]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"{collection['label']} 检索失败：{result.stderr[-500:]}")
        if not output.exists():
            continue
        with output.open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                accession_match = ACCESSION.search(Path(row["Ref_file"]).name)
                accession = accession_match.group(0) if accession_match else Path(row["Ref_file"]).name
                existing = catalog.get(accession, {})
                matches.append({
                    "strain": {
                        "id": accession,
                        "accession": accession,
                        "species": collection["id"].replace("_", " "),
                        "strain_name": existing.get("strain_name", accession),
                        "internal_id": existing.get("internal_id", "大库记录"),
                        "type_strain": existing.get("type_strain", "unknown"),
                        "lineage_json": existing.get("lineage_json", "[]"),
                    },
                    "method": "skani_search",
                    "ani": float(row["ANI"]),
                    "score": float(row["ANI"]),
                    "score_type": "ANI (%)",
                    "aligned_fraction_ref": float(row["Align_fraction_ref"]),
                    "aligned_fraction_query": float(row["Align_fraction_query"]),
                })
    matches.sort(key=lambda x: x["score"], reverse=True)
    matches = matches[:10]
    level = "insufficient" if not matches else "high_neighbor" if matches[0]["ani"] >= 99.5 and max(matches[0]["aligned_fraction_ref"], matches[0]["aligned_fraction_query"]) >= 70 else "closest_in_database"
    return {
        "method": "skani_search",
        "matches": matches,
        "evidence_level": level,
        "message": "结果来自四物种预建索引库；库内最近不等同于确定鉴定。",
        "library_version": "four-species-v1",
    }

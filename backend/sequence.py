from __future__ import annotations

import csv
import gzip
import os
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def skani_binary():
    candidates = [
        os.environ.get("SKANI_BIN"),
        str(Path.home() / "miniconda3/envs/skani/bin/skani"),
        shutil.which("skani"),
    ]
    return next((x for x in candidates if x and Path(x).is_file() and os.access(x, os.X_OK)), None)


def open_text(path):
    return gzip.open(path, "rt", encoding="utf-8", errors="ignore") if str(path).endswith(".gz") else open(path, encoding="utf-8", errors="ignore")


def sequence_stats(path):
    count, bases = 0, 0
    with open_text(path) as handle:
        for line in handle:
            if line.startswith(">"):
                count += 1
            else:
                bases += sum(c.upper() in "ACGT" for c in line.strip())
    return {"sequences": count, "bases": bases}


def skani_search(query, strains):
    binary = skani_binary()
    work = query.parent
    listing = work / "genomes.list"
    output = work / "skani.tsv"
    listing.write_text("\n".join([str(query)] + [str(BASE / s["genome_path"]) for s in strains]) + "\n")
    command = [binary, "triangle", "--sparse", "-t", "2", "-l", str(listing), "-o", str(output)]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:] or "skani 检索失败")
    matches = []
    if output.exists():
        with output.open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["Ref_file"] != str(query) and row["Query_file"] != str(query):
                    continue
                other = row["Query_file"] if row["Ref_file"] == str(query) else row["Ref_file"]
                strain = next((s for s in strains if str(BASE / s["genome_path"]) == other), None)
                if strain:
                    matches.append({
                        "strain": strain,
                        "method": "skani",
                        "ani": float(row["ANI"]),
                        "score": float(row["ANI"]),
                        "score_type": "ANI (%)",
                        "aligned_fraction_ref": float(row["Align_fraction_ref"]),
                        "aligned_fraction_query": float(row["Align_fraction_query"]),
                    })
    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"method": "skani", "matches": matches[:10], "log_tail": result.stderr[-600:]}


def kmer_set(path, k=21, step=5):
    complement = str.maketrans("ACGT", "TGCA")
    kmers = set()
    def add_sequence(sequence):
        for i in range(0, max(0, len(sequence) - k + 1), step):
            kmer = sequence[i:i+k]
            if len(kmer) == k:
                kmers.add(min(kmer, kmer.translate(complement)[::-1]))
    current = []
    with open_text(path) as handle:
        for raw in handle:
            if raw.startswith(">"):
                if current:
                    add_sequence("".join(current))
                current = []
            else:
                current.append("".join(c for c in raw.strip().upper() if c in "ACGT"))
    if current:
        add_sequence("".join(current))
    return kmers


def fallback_search(query, strains):
    query_kmers = kmer_set(query)
    if not query_kmers:
        return {"method": "kmer_jaccard", "matches": [], "log_tail": "输入序列过短或没有有效 ACGT 碱基。"}
    matches = []
    for strain in strains:
        reference = kmer_set(BASE / strain["genome_path"])
        union = len(query_kmers | reference)
        score = len(query_kmers & reference) / union * 100 if union else 0
        matches.append({
            "strain": strain,
            "method": "kmer_jaccard",
            "ani": None,
            "score": score,
            "score_type": "21-mer Jaccard (%)",
            "aligned_fraction_ref": None,
            "aligned_fraction_query": None,
        })
    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"method": "kmer_jaccard", "matches": matches[:10], "log_tail": "本地预览降级：步长 5 的规范 21-mer Jaccard，不是 ANI。"}


def sequence_search(query, strains):
    stats = sequence_stats(query)
    if stats["sequences"] == 0 or stats["bases"] < 100:
        return {**stats, "method": "invalid", "matches": [], "evidence_level": "insufficient", "message": "FASTA 中没有足够的有效序列。"}
    result = skani_search(query, strains) if skani_binary() else fallback_search(query, strains)
    matches = result["matches"]
    if not matches:
        level = "insufficient"
    elif result["method"] == "skani" and matches[0]["ani"] >= 99.5 and max(matches[0]["aligned_fraction_ref"], matches[0]["aligned_fraction_query"]) >= 70:
        level = "high_neighbor"
    else:
        level = "closest_in_database"
    return {**stats, **result, "evidence_level": level, "message": "结果仅表示当前演示库内的序列近邻，不等同于确定物种鉴定。"}

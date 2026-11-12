from pathlib import Path
import backend.library as lib

lib.library_status = lambda: {
    "all_transfer_complete": True,
    "all_index_ready": True,
    "collections": [{
        "id": "Bifidobacterium_breve",
        "label": "短双歧杆菌",
        "searchable": True,
        "index_ready": True,
        "index_path": str(Path.home() / "LZ/microbial-query-demo/data/index_test/sketches"),
    }],
}
result = lib.large_sequence_search(Path.home() / "LZ/microbial-query-demo/data/index_test/query.fa.gz", "unused", {})
print("method", result["method"])
print("evidence", result["evidence_level"])
print("top", result["matches"][0]["strain"]["accession"], result["matches"][0]["score"], result["matches"][0]["score_type"])

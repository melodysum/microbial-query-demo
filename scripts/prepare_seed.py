#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

lineages = {
    "Escherichia coli": ["Bacteria", "Pseudomonadota", "Gammaproteobacteria", "Enterobacterales", "Enterobacteriaceae", "Escherichia", "Escherichia coli"],
    "Bifidobacterium breve": ["Bacteria", "Actinomycetota", "Actinomycetes", "Bifidobacteriales", "Bifidobacteriaceae", "Bifidobacterium", "Bifidobacterium breve"],
    "Bifidobacterium longum": ["Bacteria", "Actinomycetota", "Actinomycetes", "Bifidobacteriales", "Bifidobacteriaceae", "Bifidobacterium", "Bifidobacterium longum"],
}

strains = []
def add_strain(accession, filename, species, strain_name):
    strains.append({
        "id": accession,
        "accession": accession,
        "species": species,
        "lineage": lineages[species],
        "strain_name": strain_name,
        "type_strain": "unknown",
        "collection_ids": [],
        "internal_id": f"DEMO-{len(strains) + 1:03d}",
        "genome_path": f"data/genomes/{filename}",
        "genome_status": "real",
        "source": "用户项目基因组库",
    })

add_strain("GCA_000158015.1", "GCA_000158015.1_ASM15801v1_genomic.fna.gz", "Bifidobacterium breve", "DSM 20213")
add_strain("GCA_000213865.1", "GCA_000213865.1_ASM21386v1_genomic.fna.gz", "Bifidobacterium breve", "未命名菌株 GCA_000213865.1")
add_strain("GCA_000220135.1", "GCA_000220135.1_ASM22013v1_genomic.fna.gz", "Bifidobacterium breve", "未命名菌株 GCA_000220135.1")
add_strain("GCA_000411435.1", "GCA_000411435.1_Bifi_brev_HPH0326_V1_genomic.fna.gz", "Bifidobacterium breve", "HPH0326")
add_strain("GCA_000003135.1", "GCA_000003135.1_ASM313v1_genomic.fna.gz", "Bifidobacterium longum", "未命名菌株 GCA_000003135.1")
add_strain("GCA_000007525.1", "GCA_000007525.1_ASM752v1_genomic.fna.gz", "Bifidobacterium longum", "未命名菌株 GCA_000007525.1")
add_strain("GCA_000008945.1", "GCA_000008945.1_ASM894v1_genomic.fna.gz", "Bifidobacterium longum", "未命名菌株 GCA_000008945.1")
add_strain("GCA_000020425.1", "GCA_000020425.1_ASM2042v1_genomic.fna.gz", "Bifidobacterium longum", "未命名菌株 GCA_000020425.1")
add_strain("GCA_040094185.1", "GCA_040094185.1.fna", "Escherichia coli", "CLA-AA-H239")
add_strain("GCA_932750705.1", "GCA_932750705.1.fna", "Escherichia coli", "CLA-AD-1")
add_strain("GCA_932751135.1", "GCA_932751135.1.fna", "Escherichia coli", "CR B11")
add_strain("GCA_932750795.1", "GCA_932750795.1.fna", "Escherichia coli", "Ec8850")

features = [
    {"key": "species", "label": "物种", "type": "text", "unit": "", "description": "完整物种学名"},
    {"key": "name", "label": "名称", "type": "text", "unit": "", "description": "物种、菌株名或 accession"},
    {"key": "gram_stain", "label": "革兰氏染色", "type": "enum", "unit": "", "options": ["positive", "negative"]},
    {"key": "cell_shape", "label": "细胞形态", "type": "enum", "unit": "", "options": ["rod", "coccus"]},
    {"key": "oxygen_requirement", "label": "需氧性", "type": "enum", "unit": "", "options": ["aerobe", "anaerobe", "facultative_anaerobe"]},
    {"key": "motility", "label": "运动性", "type": "boolean", "unit": "", "options": ["true", "false"]},
    {"key": "spore_forming", "label": "是否产孢", "type": "boolean", "unit": "", "options": ["true", "false"]},
    {"key": "temp_opt", "label": "最适生长温度", "type": "number", "unit": "°C"},
    {"key": "ph_min", "label": "最低生长 pH", "type": "number", "unit": "pH"},
    {"key": "ph_opt", "label": "最适生长 pH", "type": "number", "unit": "pH"},
    {"key": "ph_max", "label": "最高生长 pH", "type": "number", "unit": "pH"},
    {"key": "nacl_growth_max", "label": "最高耐盐浓度", "type": "number", "unit": "%"},
    {"key": "salt_tolerance_description", "label": "资料明确描述为耐盐", "type": "boolean", "unit": "", "options": ["true", "false"]},
    {"key": "isolation_habitat", "label": "分离环境", "type": "enum", "unit": "", "options": ["human_gut", "marine_sediment", "soil", "fermented_food"]},
    {"key": "enzyme_activity", "label": "酶活性记录", "type": "boolean", "unit": "", "options": ["true", "false"]},
]

observations = []
def observe(strain_id, feature, value, unit="", condition="演示条件"):
    observations.append({
        "strain_id": strain_id,
        "feature": feature,
        "value": value,
        "unit": unit,
        "condition": condition,
        "evidence_id": "DEMO-PHENOTYPE-001",
        "evidence_status": "synthetic_demo",
    })

for strain in strains:
    ecoli = strain["species"] == "Escherichia coli"
    defaults = {
        "gram_stain": "negative" if ecoli else "positive",
        "cell_shape": "rod",
        "oxygen_requirement": "facultative_anaerobe" if ecoli else "anaerobe",
        "motility": "true" if ecoli else "false",
        "spore_forming": "false",
        "temp_opt": 37,
        "ph_min": 6.0 if ecoli else 5.5,
        "ph_opt": 7.0,
        "ph_max": 8.0 if ecoli else 7.5,
        "nacl_growth_max": 5.0 if ecoli else 2.0,
        "isolation_habitat": "human_gut",
    }
    units = {"temp_opt": "°C", "ph_min": "pH", "ph_opt": "pH", "ph_max": "pH", "nacl_growth_max": "%"}
    for feature, value in defaults.items():
        observe(strain["id"], feature, value, units.get(feature, ""))
    if ecoli:
        observe(strain["id"], "salt_tolerance_description", "true")
for strain_id in ("GCA_000158015.1", "GCA_040094185.1"):
    observe(strain_id, "enzyme_activity", "true")

core = [
    {
        "id": "CORE-TREICHEL-2026",
        "record_type": "core",
        "title": "Benchmarking of shotgun sequencing depth reveals the potential and limitations of shallow metagenomics and strain-level analysis",
        "authors": "Treichel 等",
        "journal": "Nature Microbiology",
        "year": 2026,
        "project_relation": "人工群落、测序深度与菌株分析；对应 Treichel mock 数据及参考基因组。",
        "url": None,
        "verification_status": "题录来自用户记录，链接待补",
        "related_strains": ["GCA_040094185.1", "GCA_932750705.1", "GCA_932751135.1", "GCA_932750795.1"],
    },
    {
        "id": "CORE-TRACS-2026",
        "record_type": "core",
        "title": "Strain-level transmission inference across multi-kingdom metagenomic data using TRACS",
        "authors": "Tonkin-Hill 等",
        "journal": "Nature Microbiology",
        "year": 2026,
        "project_relation": "真实队列、菌株传播分析及目标物种建库方案。",
        "url": None,
        "verification_status": "题录来自用户记录，链接待补",
        "related_strains": [],
    },
    {
        "id": "CORE-CHEN-2026",
        "record_type": "core",
        "title": "Strain-level genetic heterogeneity and colonization dynamics drive microbiome therapeutic efficacy",
        "authors": "Chen 等",
        "journal": "Cell Host & Microbe",
        "year": 2026,
        "project_relation": "粪菌移植后的菌株定植、菌株差异与治疗效果。",
        "url": None,
        "verification_status": "题录来自用户记录，链接待补",
        "related_strains": [],
    },
    {
        "id": "CORE-LU-2026",
        "record_type": "core",
        "title": "A geroprotective probiotic and its functional metabolite counteract inflammaging to extend healthspan",
        "authors": "Lu 等",
        "journal": "Nature Aging",
        "year": 2026,
        "project_relation": "肠道菌、益生菌代谢物与衰老相关队列。",
        "url": None,
        "verification_status": "题录来自用户记录，链接待补",
        "related_strains": [],
    },
    {
        "id": "CORE-GLASS-2026",
        "record_type": "core",
        "title": "Genome-scale metabolic modelling identifies vaginal microbiome members as potential probiotics",
        "authors": "Glass、Kolling 和 Papin",
        "journal": "Nature Microbiology",
        "year": 2026,
        "project_relation": "HaPaPro 代谢模型资源；模型文件不能当作宏基因组 reads。",
        "url": None,
        "verification_status": "题录来自用户记录，链接待补",
        "related_strains": [],
    },
    {
        "id": "CORE-STRAINSCAN-2023",
        "record_type": "core",
        "title": "High-resolution strain-level microbiome composition analysis from short reads",
        "authors": "Liao、Ji 和 Sun",
        "journal": "Microbiome",
        "year": 2023,
        "project_relation": "StrainScan 方法论文；参考基因组的收集与筛选方法。",
        "url": None,
        "verification_status": "题录来自用户记录，链接待补",
        "related_strains": [],
    },
]

source = (DATA / "source/literature_source.txt").read_text(encoding="utf-8")
shares = []
month = None
for raw in source.splitlines():
    section = re.match(r"^2026 年 (\d+) 月$", raw.strip())
    if section:
        month = int(section.group(1))
        continue
    columns = raw.strip().split("\t")
    if len(columns) != 3 or not columns[0].isdigit() or month is None:
        continue
    number, date_text, topic = columns
    date_match = re.match(r"(\d+) 月 (\d+) 日", date_text)
    if not date_match:
        continue
    share_month, day = map(int, date_match.groups())
    shares.append({
        "id": f"SHARE-{number.zfill(2)}",
        "record_type": "share_lead",
        "original_number": int(number),
        "title": topic,
        "authors": None,
        "journal": None,
        "year": 2026,
        "shared_date": f"2026-{share_month:02d}-{day:02d}",
        "project_relation": "paper 频道分享线索；需核对原文后才能作为证据。",
        "url": None,
        "verification_status": "未核对原文，可能为解读、新闻或重复分享",
        "related_strains": [],
    })

literature = {
    "version": "literature-2026-11-12-v1",
    "source_note": "题录与分享线索来自用户提供的记录；未提供的 DOI 和网址不补写。",
    "duplicate_candidates": [[7, 20], [13, 28], [18, 26], [14, 44], [5, 59]],
    "records": core + shares,
}

seed = {
    "version": "microbial-demo-2026-11-12-v1",
    "strains": strains,
    "features": features,
    "observations": observations,
    "evidence": [{
        "id": "DEMO-PHENOTYPE-001",
        "title": "合成演示性状记录",
        "authors": "平台原型",
        "journal": "不适用于科研引用",
        "year": 2026,
        "url": None,
        "excerpt": "仅用于验证筛选、缺失值分组和证据展示；不是实验事实，不得用于科研判断。",
        "evidence_status": "synthetic_demo",
    }],
}

(DATA / "seed.json").write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(DATA / "literature.json").write_text(json.dumps(literature, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "strains": len(strains),
    "species": len(lineages),
    "features": len(features),
    "observations": len(observations),
    "core_literature": len(core),
    "share_leads": len(shares),
}, ensure_ascii=False, indent=2))

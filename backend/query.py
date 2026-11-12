from __future__ import annotations

import re

ALLOWED_OPERATORS = {"eq", "contains", "gte", "lte", "gt", "lt"}


def validate_filters(filters, features):
    valid = {x["key"] for x in features} | {"species", "name"}
    cleaned = []
    for item in filters:
        feature = item.get("feature")
        operator = item.get("operator", "eq")
        if feature not in valid:
            raise ValueError(f"不支持的字段：{feature}")
        if operator not in ALLOWED_OPERATORS:
            raise ValueError(f"不支持的操作符：{operator}")
        cleaned.append({"feature": feature, "operator": operator, "value": item.get("value"), "unit": item.get("unit", "")})
    return cleaned


def interpret(text):
    filters = []
    warnings = []
    lower = text.lower()
    def add(feature, operator, value, unit=""):
        filters.append({"feature": feature, "operator": operator, "value": value, "unit": unit})

    if "兼性厌氧" in text or "facultative" in lower:
        add("oxygen_requirement", "eq", "facultative_anaerobe")
    elif "严格厌氧" in text or "厌氧" in text or "anaerob" in lower:
        add("oxygen_requirement", "eq", "anaerobe")
    elif "好氧" in text or "需氧" in text or "aerobic" in lower:
        add("oxygen_requirement", "eq", "aerobe")
    if "革兰氏阴性" in text or "革兰阴性" in text or "gram-negative" in lower or "gram negative" in lower:
        add("gram_stain", "eq", "negative")
    if "革兰氏阳性" in text or "革兰阳性" in text or "gram-positive" in lower or "gram positive" in lower:
        add("gram_stain", "eq", "positive")
    if "不运动" in text or "non-motile" in lower or "nonmotile" in lower:
        add("motility", "eq", "false")
    elif "运动" in text or "motile" in lower:
        add("motility", "eq", "true")
    if "不产孢" in text or "non-spore" in lower or "nonspore" in lower:
        add("spore_forming", "eq", "false")
    elif "产孢" in text or "spore-forming" in lower or "spore forming" in lower:
        add("spore_forming", "eq", "true")
    if "海洋" in text or "marine" in lower or "ocean" in lower:
        add("isolation_habitat", "eq", "marine_sediment")
    if "肠道" in text or "gut" in lower or "intestin" in lower:
        add("isolation_habitat", "eq", "human_gut")
    if "土壤" in text or "soil" in lower:
        add("isolation_habitat", "eq", "soil")
    if "短双歧" in text or "bifidobacterium breve" in lower:
        add("species", "eq", "Bifidobacterium breve")
    elif "长双歧" in text or "bifidobacterium longum" in lower:
        add("species", "eq", "Bifidobacterium longum")
    elif "双歧杆菌" in text or "bifidobacterium" in lower:
        add("name", "contains", "Bifidobacterium")
    if "大肠杆菌" in text or "escherichia coli" in lower or "e. coli" in lower:
        add("species", "eq", "Escherichia coli")

    salt = re.search(r"(?:耐盐|NaCl|氯化钠|salt|sodium chloride)[^0-9%]{0,20}(\d+(?:\.\d+)?)\s*%", text, re.I)
    if salt:
        add("nacl_growth_max", "gte", float(salt.group(1)), "%")
    elif "耐盐" in text or "salt" in lower:
        warnings.append("“耐盐”存在歧义：请补充 NaCl 浓度，或选择“资料中明确描述为耐盐”。")
    if "降解" in text or "degrad" in lower:
        warnings.append("当前演示库只有“酶活性记录”占位字段，不能据此断言可降解特定底物。")
    if not filters and not warnings:
        warnings.append("未识别到可查询条件，请尝试“革兰氏阴性”“兼性厌氧”“耐盐≥3%”或具体物种名。")
    return {
        "original_text": text,
        "filters": filters,
        "warnings": warnings,
        "needs_confirmation": bool(warnings),
        "parser_mode": "rules",
        "parser_note": "当前未配置本地千问，使用透明的受控规则解析。",
    }


def compare(observed, operator, expected):
    if operator in {"gte", "lte", "gt", "lt"}:
        try:
            left, right = float(observed), float(expected)
        except (TypeError, ValueError):
            return False
        return {"gte": left >= right, "lte": left <= right, "gt": left > right, "lt": left < right}[operator]
    if operator == "contains":
        return str(expected).lower() in str(observed).lower()
    return str(observed).lower() == str(expected).lower()


def search(strains, observations, features, filters):
    labels = {x["key"]: x["label"] for x in features}
    by_strain = {}
    for obs in observations:
        by_strain.setdefault(obs["strain_id"], {})[obs["feature"]] = obs
    confirmed, possible = [], []
    for strain in strains:
        reasons, missing = [], []
        conflict = False
        for item in filters:
            feature = item["feature"]
            if feature == "species":
                observed = strain["species"]
            elif feature == "name":
                observed = " ".join([strain["species"], strain["strain_name"], strain["accession"]])
            else:
                obs = by_strain.get(strain["id"], {}).get(feature)
                observed = obs["value"] if obs else None
            if observed is None:
                missing.append(feature)
                reasons.append({"feature": feature, "label": labels.get(feature, feature), "status": "missing", "observed": None})
                continue
            matched = compare(observed, item["operator"], item["value"])
            reasons.append({"feature": feature, "label": labels.get(feature, feature), "status": "matched" if matched else "conflict", "observed": observed})
            if not matched:
                conflict = True
        result = {**strain, "match_reasons": reasons, "missing_features": missing, "phenotype_status": "synthetic_demo"}
        if not conflict and not missing:
            confirmed.append(result)
        elif not conflict:
            possible.append(result)
    return {"confirmed": confirmed, "possible": possible, "counts": {"confirmed": len(confirmed), "possible": len(possible)}, "filters": filters}

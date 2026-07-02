"""
表格抽取工具 — Skill

Agent 可调用的工具函数，用于从解析后的文档中提取和结构化表格数据。
"""

from typing import Any, Optional


def find_tables_by_keyword(
    tables: list[dict],
    keywords: list[str],
    match_any: bool = True,
) -> list[dict]:
    """
    根据关键词查找表格

    Args:
        tables: 文档中的表格列表，每项 {"page": int, "data": [[...]]}
        keywords: 搜索关键词
        match_any: True=匹配任一关键词即返回; False=需匹配全部

    Returns:
        匹配的表格列表
    """
    results = []
    for table in tables:
        table_text = "\n".join(
            [" ".join(row) for row in table.get("data", [])]
        ).lower()
        if match_any:
            if any(kw.lower() in table_text for kw in keywords):
                results.append(table)
        else:
            if all(kw.lower() in table_text for kw in keywords):
                results.append(table)
    return results


def extract_table_as_dict(table_data: list[list[str]]) -> list[dict]:
    """
    将二维表格数据转为 dict 列表（首行为列名）

    Args:
        table_data: [[col1, col2, ...], [val1, val2, ...], ...]

    Returns:
        [{col1: val1, col2: val2, ...}, ...]
    """
    if not table_data or len(table_data) < 2:
        return []

    headers = [h.strip() for h in table_data[0]]
    result = []
    for row in table_data[1:]:
        row_dict = {}
        for i, header in enumerate(headers):
            if i < len(row):
                row_dict[header] = row[i].strip()
            else:
                row_dict[header] = ""
        result.append(row_dict)
    return result


def validate_table_completeness(
    table_data: list[list[str]],
    required_fields: list[str],
) -> dict:
    """
    验证表格完整性

    Args:
        table_data: 表格数据
        required_fields: 必须包含的字段列表

    Returns:
        {"complete": bool, "missing_fields": [...], "empty_rows": int, "total_rows": int}
    """
    if not table_data:
        return {"complete": False, "missing_fields": required_fields, "empty_rows": 0, "total_rows": 0}

    headers = [h.strip().lower() for h in table_data[0]]
    missing = [f for f in required_fields if f.lower() not in headers]

    empty_rows = 0
    for row in table_data[1:]:
        if all(cell.strip() == "" for cell in row):
            empty_rows += 1

    return {
        "complete": len(missing) == 0,
        "missing_fields": missing,
        "empty_rows": empty_rows,
        "total_rows": max(0, len(table_data) - 1),
    }

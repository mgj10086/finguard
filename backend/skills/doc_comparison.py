"""
文档比对工具 — Skill

Agent 可调用的工具函数，用于比对文档内容差异。
支持：版本差异比对、条款对照、变更检测。
"""

from difflib import SequenceMatcher
from typing import Optional


def compare_texts(
    text_a: str,
    text_b: str,
    context_lines: int = 3,
) -> dict:
    """
    比对两段文本的差异

    Args:
        text_a: 原始文本
        text_b: 新文本
        context_lines: 上下文行数

    Returns:
        {
            "has_changes": bool,
            "additions": int,
            "deletions": int,
            "changes": [{"type": "equal|insert|delete|replace", "content": "...", "line_a": int, "line_b": int}]
        }
    """
    lines_a = text_a.splitlines()
    lines_b = text_b.splitlines()

    matcher = SequenceMatcher(None, lines_a, lines_b)
    changes = []
    additions = 0
    deletions = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            changes.append({
                "type": "equal",
                "content": "\n".join(lines_a[i1:i2]),
                "line_a": i1 + 1,
                "line_b": j1 + 1,
            })
        elif tag == "insert":
            additions += (j2 - j1)
            changes.append({
                "type": "insert",
                "content": "\n".join(lines_b[j1:j2]),
                "line_a": i1 + 1,
                "line_b": j1 + 1,
            })
        elif tag == "delete":
            deletions += (i2 - i1)
            changes.append({
                "type": "delete",
                "content": "\n".join(lines_a[i1:i2]),
                "line_a": i1 + 1,
                "line_b": j1 + 1,
            })
        elif tag == "replace":
            additions += (j2 - j1)
            deletions += (i2 - i1)
            changes.append({
                "type": "replace",
                "old_content": "\n".join(lines_a[i1:i2]),
                "new_content": "\n".join(lines_b[j1:j2]),
                "line_a": i1 + 1,
                "line_b": j1 + 1,
            })

    return {
        "has_changes": additions > 0 or deletions > 0,
        "additions": additions,
        "deletions": deletions,
        "total_changes": len([c for c in changes if c["type"] != "equal"]),
        "changes": changes,
    }


def compare_clauses(
    clause_text: str,
    regulation_texts: list[dict],
) -> list[dict]:
    """
    比对一个条款与多个法规条款的相似度

    Args:
        clause_text: 待审核的条款文本
        regulation_texts: 法规条款列表，每项包含 {"content": "...", "regulation": "...", "clause_num": "..."}

    Returns:
        [{"regulation": "...", "clause_num": "...", "similarity": 0.95, "matched": bool}]
    """
    results = []
    for reg in regulation_texts:
        matcher = SequenceMatcher(None, clause_text, reg["content"])
        similarity = matcher.ratio()
        results.append({
            "regulation": reg.get("regulation", ""),
            "clause_num": reg.get("clause_num", ""),
            "similarity": round(similarity, 4),
            "matched": similarity >= 0.8,
        })
    return sorted(results, key=lambda x: x["similarity"], reverse=True)

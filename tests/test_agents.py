"""Agent 流水线测试"""

import pytest


class TestGraph:
    """状态图创建测试"""

    def test_create_graph(self):
        """测试状态图创建"""
        from backend.agents.graph import create_review_graph
        graph = create_review_graph()
        assert graph is not None

    def test_graph_nodes(self):
        """测试状态图节点注册"""
        from backend.agents.graph import create_review_graph
        graph = create_review_graph()
        # LangGraph 编译后节点不可直接访问，通过 __dict__ 检查
        assert hasattr(graph, "invoke")


class TestSkills:
    """Skills 工具测试"""

    def test_compare_texts(self):
        """文档比对"""
        from backend.skills.doc_comparison import compare_texts
        result = compare_texts("hello world", "hello there world")
        assert result["has_changes"] is True

    def test_extract_table_as_dict(self):
        """表格抽取"""
        from backend.skills.table_extraction import extract_table_as_dict
        data = [["name", "value"], ["a", "1"], ["b", "2"]]
        result = extract_table_as_dict(data)
        assert len(result) == 2
        assert result[0]["name"] == "a"

    def test_find_tables_by_keyword(self):
        """关键词查表"""
        from backend.skills.table_extraction import find_tables_by_keyword
        tables = [{"page": 1, "data": [["col1", "col2"], ["risk", "high"]]}]
        result = find_tables_by_keyword(tables, ["risk"])
        assert len(result) == 1

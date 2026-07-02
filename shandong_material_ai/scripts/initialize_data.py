from __future__ import annotations

from pathlib import Path

from build_knowledge_graph import save_graph_tables
from score_materials import save_default_scores


def main() -> None:
    """生成派生数据文件。基础 CSV 已随项目提供，这里刷新评分表和知识图谱表。"""
    score_path = save_default_scores()
    node_path, edge_path = save_graph_tables()
    print("Data initialization complete.")
    print(f"- {score_path}")
    print(f"- {node_path}")
    print(f"- {edge_path}")


if __name__ == "__main__":
    main()

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from recommendation_engine import screen_materials


def test_screening_returns_traceable_candidates():
    result = screen_materials("青岛", "港口机械", engineering_component="运动摩擦部件")
    assert not result.empty
    assert {
        "screening_score",
        "evidence_confidence",
        "decision_label",
        "confidence_reasons",
        "recommendation_object_type",
        "material_system",
        "chemistry_tags",
        "engineering_components",
        "pilot_scope",
    }.issubset(result.columns)
    assert result["screening_score"].between(0, 100).all()
    assert result["evidence_confidence"].between(0, 100).all()
    assert set(result["recommendation_object_type"]) == {"表面工程与防护涂层"}
    assert set(result["material_system"]) == {"陶瓷与硬质涂层"}
    assert result["engineering_components"].str.contains("运动摩擦部件").all()


def test_engineering_component_filters_before_ranking():
    result = screen_materials("青岛", "海洋工程", engineering_component="大面积钢结构")
    assert result.empty


def test_empty_reserved_material_system_returns_no_fake_results():
    result = screen_materials(
        "青岛",
        "海洋工程",
        material_system="有机防腐涂层",
        engineering_component="大面积钢结构",
    )
    assert result.empty

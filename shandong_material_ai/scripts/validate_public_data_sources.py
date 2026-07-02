from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def _split_ids(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def validate_public_data_sources() -> None:
    catalog_path = DATA_DIR / "public_data_catalog_seed.csv"
    evidence_path = DATA_DIR / "public_data_evidence.csv"
    env_path = DATA_DIR / "city_environment.csv"
    industry_path = DATA_DIR / "city_industry.csv"

    catalog = pd.read_csv(catalog_path)
    evidence = pd.read_csv(evidence_path)
    env = pd.read_csv(env_path)
    industry = pd.read_csv(industry_path)

    catalog_by_id = catalog.set_index("catalog_id")
    evidence_ids = set(evidence["evidence_id"])
    errors: list[str] = []

    for _, row in evidence.iterrows():
        catalog_id = row["catalog_id"]
        if catalog_id not in catalog_by_id.index:
            errors.append(f"Evidence {row['evidence_id']} references missing catalog {catalog_id}.")
            continue

        catalog_row = catalog_by_id.loc[catalog_id]
        if catalog_row["use_status"] != "已纳入证据层":
            errors.append(f"Evidence {row['evidence_id']} uses catalog marked {catalog_row['use_status']}.")
        if str(catalog_row["reliability_tier"]).upper() == "D":
            errors.append(f"Evidence {row['evidence_id']} uses tier D catalog {catalog_id}.")

    for table_name, table in [("city_environment", env), ("city_industry", industry)]:
        if "public_evidence_ids" not in table.columns:
            continue
        for row_number, raw_ids in enumerate(table["public_evidence_ids"], start=2):
            for evidence_id in _split_ids(raw_ids):
                if evidence_id not in evidence_ids:
                    errors.append(f"{table_name}.csv row {row_number} references missing evidence {evidence_id}.")

    if errors:
        raise SystemExit("\n".join(errors))

    print("Public data source validation passed.")
    print(f"- catalog rows: {len(catalog)}")
    print(f"- evidence rows: {len(evidence)}")


if __name__ == "__main__":
    validate_public_data_sources()

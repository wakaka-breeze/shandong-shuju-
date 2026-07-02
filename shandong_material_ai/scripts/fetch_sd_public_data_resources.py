from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "sd_public_data"
BASE_URL = "https://data.sd.gov.cn/portal"
USER_AGENT = "Mozilla/5.0 (compatible; ShandongMaterialAI/0.1; data audit)"


def _request_json(url: str, timeout: int = 30) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def _request_bytes(url: str, timeout: int = 60) -> tuple[bytes, dict[str, str]]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=timeout) as response:
        headers = {key: value for key, value in response.headers.items()}
        return response.read(), headers


def _safe_name(value: object, max_length: int = 90) -> str:
    text = str(value or "").strip()
    text = re.sub(r'[\\/:*?"<>|\s]+', "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:max_length] or "unnamed"


def _as_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    obj = payload.get("object") or {}
    records = obj.get("records") or []
    return records if isinstance(records, list) else []


def fetch_file_resources(catalog_id: str, page_size: int = 100) -> list[dict[str, Any]]:
    first_url = f"{BASE_URL}/catalog/getResourceWithFormat?{urlencode({'cataId': catalog_id, 'pageNum': 1, 'pageSize': page_size, 'fileFormat': ''})}"
    first_payload = _request_json(first_url)
    records = _as_records(first_payload)
    total = int((first_payload.get("object") or {}).get("total") or len(records))

    page = 2
    while len(records) < total:
        url = f"{BASE_URL}/catalog/getResourceWithFormat?{urlencode({'cataId': catalog_id, 'pageNum': page, 'pageSize': page_size, 'fileFormat': ''})}"
        page_records = _as_records(_request_json(url))
        if not page_records:
            break
        records.extend(page_records)
        page += 1
    return records


def fetch_api_services(catalog_id: str, page_size: int = 100) -> list[dict[str, Any]]:
    url = f"{BASE_URL}/catalog/getApplyResource?{urlencode({'searchType': 'api', 'cataId': catalog_id, 'pageNum': 1, 'pageSize': page_size})}"
    return _as_records(_request_json(url))


def pick_latest_files(
    resources: list[dict[str, Any]],
    formats: set[str],
    all_versions: bool,
    selection: str,
) -> list[dict[str, Any]]:
    candidates = [row for row in resources if str(row.get("fileFormat", "")).lower() in formats]
    if all_versions:
        return sorted(candidates, key=lambda row: (str(row.get("fileFormat", "")), -int(row.get("updateTime") or 0)))

    latest_by_format: dict[str, dict[str, Any]] = {}
    for row in candidates:
        file_format = str(row.get("fileFormat", "")).lower()
        existing = latest_by_format.get(file_format)
        if existing is None:
            latest_by_format[file_format] = row
            continue

        if selection == "max-data-count":
            current_key = (int(row.get("dataCount") or 0), int(row.get("updateTime") or 0))
            existing_key = (int(existing.get("dataCount") or 0), int(existing.get("updateTime") or 0))
            if current_key > existing_key:
                latest_by_format[file_format] = row
        elif int(row.get("updateTime") or 0) > int(existing.get("updateTime") or 0):
            latest_by_format[file_format] = row
    return list(latest_by_format.values())


def download_resource(catalog: pd.Series, resource: dict[str, Any]) -> dict[str, Any]:
    catalog_id = str(catalog["catalog_id"])
    catalog_name = str(catalog["catalog_name"])
    file_format = str(resource.get("fileFormat", "dat")).lower()
    id_in_rc = str(resource.get("idInRc", ""))
    file_name = _safe_name(resource.get("fileName") or resource.get("fileDescription") or catalog_name)
    target_dir = RAW_DIR / _safe_name(catalog_id, 48)
    target_dir.mkdir(parents=True, exist_ok=True)

    query = (
        f"cataId={quote(catalog_id)}"
        f"&cataName={quote(catalog_name)}"
        f"&idInRc={quote(id_in_rc, safe='')}"
    )
    download_url = f"{BASE_URL}/catalog/download?{query}"
    target = target_dir / f"{file_name}.{file_format}"

    payload, headers = _request_bytes(download_url)
    content_type = headers.get("Content-Type", "")
    text_probe = payload[:300].decode("utf-8", errors="ignore")
    blocked = "无权限下载" in text_probe or '"error"' in text_probe and len(payload) < 1000

    if blocked:
        target = target_dir / f"{file_name}.{file_format}.blocked.json"
        target.write_bytes(payload)
        status = "blocked_or_requires_permission"
    else:
        target.write_bytes(payload)
        status = "downloaded"

    return {
        "catalog_id": catalog_id,
        "catalog_name": catalog_name,
        "file_description": resource.get("fileDescription"),
        "file_format": file_format,
        "source_file_size": resource.get("fileSize"),
        "downloaded_bytes": len(payload),
        "target_path": str(target.relative_to(BASE_DIR)),
        "content_type": content_type,
        "download_status": status,
        "response_probe": text_probe if blocked else "",
    }


def normalize_resource_row(catalog: pd.Series, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "catalog_id": catalog["catalog_id"],
        "catalog_name": catalog["catalog_name"],
        "city": catalog["city"],
        "source_department": catalog["source_department"],
        "resource_type": "file",
        "resource_name": row.get("fileDescription") or row.get("fileName"),
        "format": row.get("fileFormat"),
        "data_count": row.get("dataCount"),
        "file_size": row.get("fileSize"),
        "update_time_ms": row.get("updateTime"),
        "status": row.get("status"),
        "is_apply": row.get("isApply"),
        "file_id": row.get("fileId"),
    }


def normalize_service_row(catalog: pd.Series, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "catalog_id": catalog["catalog_id"],
        "catalog_name": catalog["catalog_name"],
        "city": catalog["city"],
        "source_department": catalog["source_department"],
        "resource_type": "api",
        "service_id": row.get("serviceId"),
        "service_name": row.get("serviceName"),
        "service_desc": row.get("serviceDesc"),
        "context": row.get("context"),
        "input_param": row.get("inputParam"),
        "output_param": row.get("outputParam"),
        "update_time_ms": row.get("updateTime"),
        "status": row.get("status"),
    }


def run_ingest(args: argparse.Namespace) -> None:
    catalog = pd.read_csv(DATA_DIR / "public_data_catalog_seed.csv")
    if args.evidence_only:
        catalog = catalog[catalog["use_status"] == "已纳入证据层"]
    if args.catalog_id:
        catalog = catalog[catalog["catalog_id"].astype(str).isin(args.catalog_id)]
    if args.limit:
        catalog = catalog.head(args.limit)

    formats = {item.strip().lower() for item in args.formats.split(",") if item.strip()}
    resource_rows: list[dict[str, Any]] = []
    service_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []

    for index, (_, row) in enumerate(catalog.iterrows(), start=1):
        catalog_id = str(row["catalog_id"])
        print(f"[{index}/{len(catalog)}] {row['catalog_name']} ({catalog_id})")
        try:
            file_resources = fetch_file_resources(catalog_id)
            api_services = fetch_api_services(catalog_id)
            resource_rows.extend(normalize_resource_row(row, item) for item in file_resources)
            service_rows.extend(normalize_service_row(row, item) for item in api_services)

            selected_files = pick_latest_files(file_resources, formats, args.all_versions, args.selection)
            if args.download:
                for resource in selected_files:
                    try:
                        audit_rows.append(download_resource(row, resource))
                    except (HTTPError, URLError, TimeoutError, OSError) as exc:
                        audit_rows.append(
                            {
                                "catalog_id": catalog_id,
                                "catalog_name": row["catalog_name"],
                                "file_description": resource.get("fileDescription"),
                                "file_format": resource.get("fileFormat"),
                                "download_status": "failed",
                                "error": str(exc),
                            }
                        )

            audit_rows.append(
                {
                    "catalog_id": catalog_id,
                    "catalog_name": row["catalog_name"],
                    "file_resource_count": len(file_resources),
                    "api_service_count": len(api_services),
                    "selected_file_count": len(selected_files),
                    "download_status": "metadata_collected",
                }
            )
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            audit_rows.append(
                {
                    "catalog_id": catalog_id,
                    "catalog_name": row["catalog_name"],
                    "download_status": "metadata_failed",
                    "error": str(exc),
                }
            )
        time.sleep(args.sleep)

    pd.DataFrame(resource_rows).to_csv(DATA_DIR / "sd_public_data_file_resources.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(service_rows).to_csv(DATA_DIR / "sd_public_data_api_services.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(audit_rows).to_csv(DATA_DIR / "sd_public_data_ingest_audit.csv", index=False, encoding="utf-8-sig")
    print("Done.")
    print(f"- {DATA_DIR / 'sd_public_data_file_resources.csv'}")
    print(f"- {DATA_DIR / 'sd_public_data_api_services.csv'}")
    print(f"- {DATA_DIR / 'sd_public_data_ingest_audit.csv'}")
    if args.download:
        print(f"- raw files: {RAW_DIR}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch file/API resource metadata and raw files from 山东公共数据开放网.")
    parser.add_argument("--catalog-id", action="append", help="Only ingest the given catalog id. Can be repeated.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of catalogs for a trial run.")
    parser.add_argument("--formats", default="csv,json,xlsx", help="Comma-separated file formats to download.")
    parser.add_argument(
        "--selection",
        choices=["max-data-count", "latest"],
        default="max-data-count",
        help="How to pick one file per format when --all-versions is not set.",
    )
    parser.add_argument("--all-versions", action="store_true", help="Download all matching file versions instead of latest per format.")
    parser.add_argument("--download", action="store_true", help="Download selected files into data/raw/sd_public_data.")
    parser.add_argument("--evidence-only", action="store_true", help="Only ingest catalogs marked 已纳入证据层.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Seconds to sleep between catalogs.")
    return parser.parse_args()


if __name__ == "__main__":
    run_ingest(parse_args())

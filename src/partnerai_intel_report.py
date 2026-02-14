from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error as url_error
from urllib import request as url_request
from urllib.parse import urlparse

from dateutil import parser as date_parser


CATEGORY_LABELS = {
    "Funding": "Funding",
    "Procurement": "Procurement",
    "Humanitarian Update": "Humanitarian",
    "Development Program": "Development Program",
    "Policy Update": "Policy Update",
}

MONEY_PATTERN = re.compile(
    r"(?:\$\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:million|billion|m|bn))?|(?:usd|eur|gbp)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:million|billion|m|bn))?)",
    re.IGNORECASE,
)


@dataclass
class IntelItem:
    timestamp: datetime
    feed_source: str
    title: str
    url: str
    summary: str
    raw_content: str
    author: str
    categories: list[str]
    category: str
    sector: str
    funding_amount: str
    opportunity_type: str
    key_signal: str
    score: int
    priority: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = date_parser.parse(str(value))
    except Exception:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("items", "rss_items", "entries", "records", "data"):
        items = payload.get(key)
        if isinstance(items, list):
            return [entry for entry in items if isinstance(entry, dict)]

    if all(key in payload for key in ("title", "url")):
        return [payload]

    return []


def coerce_item(item: dict[str, Any]) -> dict[str, Any]:
    categories = item.get("categories")
    if isinstance(categories, list):
        category_values = [str(entry) for entry in categories if str(entry).strip()]
    elif isinstance(categories, str):
        category_values = [segment.strip() for segment in categories.split(",") if segment.strip()]
    else:
        category_values = []

    combined_text = normalize_text(
        " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("summary") or item.get("description") or ""),
                str(item.get("raw_content") or item.get("content") or ""),
            ]
        )
    )

    explicit_amount = normalize_text(
        str(
            item.get("amount")
            or item.get("grant_amount")
            or item.get("funding_amount")
            or item.get("value")
            or ""
        )
    )
    extracted_amount = explicit_amount or extract_money_value(combined_text)

    explicit_sector = normalize_text(str(item.get("sector") or item.get("focus_sector") or ""))
    inferred_sector = explicit_sector or detect_sector(combined_text, category_values)

    return {
        "timestamp": item.get("timestamp") or item.get("pubDate") or item.get("published") or item.get("published_at"),
        "feed_source": normalize_text(str(item.get("feed_source") or item.get("source") or "Unknown Source")),
        "title": normalize_text(str(item.get("title") or "Untitled item")),
        "url": normalize_text(str(item.get("url") or item.get("link") or "")),
        "summary": normalize_text(str(item.get("summary") or item.get("description") or "")),
        "raw_content": normalize_text(str(item.get("raw_content") or item.get("content") or "")),
        "author": normalize_text(str(item.get("author") or "")),
        "categories": category_values,
        "sector": inferred_sector,
        "funding_amount": extracted_amount,
    }


def extract_money_value(text: str) -> str:
    if not text:
        return ""

    match = MONEY_PATTERN.search(text)
    if not match:
        return ""
    return normalize_text(match.group(0))


def detect_sector(text: str, categories: list[str]) -> str:
    lowered = f"{text} {' '.join(categories)}".lower()
    sector_rules: list[tuple[str, list[str]]] = [
        ("Agriculture", ["agriculture", "agrifood", "farming", "crop", "food security"]),
        ("Climate & Environment", ["climate", "environment", "resilience", "biodiversity", "conservation"]),
        ("Water, Sanitation & Hygiene", ["wash", "sanitation", "water", "hygiene"]),
        ("Health", ["health", "hospital", "disease", "medical", "vaccine"]),
        ("Education", ["education", "schools", "learning", "curriculum"]),
        ("Energy", ["energy", "renewable", "solar", "grid", "power"]),
        ("Digital & ICT", ["digital", "ict", "data", "connectivity", "platform"]),
    ]

    for label, tokens in sector_rules:
        if any(token in lowered for token in tokens):
            return label
    return ""


def derive_opportunity_type(category: str) -> str:
    if category == "Funding":
        return "Grant/Funding"
    if category == "Procurement":
        return "Tender/Procurement"
    if category == "Humanitarian Update":
        return "Humanitarian"
    if category == "Policy Update":
        return "Policy"
    return "Program"


def dedupe_key(item: dict[str, Any]) -> str:
    if item["url"]:
        return item["url"].lower()

    joined = "|".join(
        [
            item["title"].lower(),
            item["summary"].lower(),
            item["feed_source"].lower(),
            str(item["timestamp"] or ""),
        ]
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def detect_region(text: str) -> str:
    region_tokens = [
        "global",
        "africa",
        "asia",
        "latin america",
        "middle east",
        "europe",
        "caribbean",
        "pacific",
        "ukraine",
        "sudan",
        "gaza",
    ]
    lower_text = text.lower()
    for token in region_tokens:
        if token in lower_text:
            return token.title()
    return ""


def classify_signal(text: str) -> tuple[str, str, int]:
    lower_text = text.lower()

    rules: list[tuple[str, list[str], list[str], str]] = [
        (
            "Funding",
            ["grant", "funding", "call for proposals", "fund", "financial support", "award"],
            ["open call", "call for expressions of interest", "apply now", "funding window"],
            "Funding call or grant opportunity",
        ),
        (
            "Procurement",
            ["tender", "procurement", "rfp", "request for proposal", "bid", "invitation to bid"],
            ["tender notice", "solicitation", "vendor", "contract award"],
            "Procurement or tender notice",
        ),
        (
            "Humanitarian Update",
            ["humanitarian", "emergency", "crisis", "appeal", "response plan", "relief"],
            ["flash appeal", "urgent", "displacement", "outbreak"],
            "Humanitarian emergency or response update",
        ),
        (
            "Development Program",
            ["program launch", "development program", "initiative", "capacity building", "pilot"],
            ["partnership", "implementation", "project start", "technical assistance"],
            "Development program or implementation activity",
        ),
        (
            "Policy Update",
            ["policy", "regulation", "strategy", "framework", "legislation"],
            ["approved", "adopted", "policy shift", "guidance"],
            "Policy, regulation, or strategic update",
        ),
    ]

    best_category = "Development Program"
    best_signal = "Development program or implementation activity"
    best_strength = 1
    best_score = 0

    for category, strong_terms, medium_terms, signal in rules:
        strong_matches = sum(1 for term in strong_terms if term in lower_text)
        medium_matches = sum(1 for term in medium_terms if term in lower_text)
        score = strong_matches * 2 + medium_matches
        if score > best_score:
            best_score = score
            best_category = category
            best_signal = signal
            if strong_matches >= 2:
                best_strength = 3
            elif strong_matches >= 1 or medium_matches >= 2:
                best_strength = 2
            else:
                best_strength = 1

    return best_category, best_signal, best_strength


def is_irrelevant(item: dict[str, Any], category: str, strength: int) -> bool:
    text = f"{item['title']} {item['summary']} {item['raw_content']}".lower()
    irrelevant_tokens = [
        "opinion",
        "thought leadership",
        "podcast",
        "webinar recap",
        "newsletter",
        "career",
        "hiring",
        "product release",
        "generic update",
    ]
    if any(token in text for token in irrelevant_tokens):
        return True

    if category == "Development Program" and strength == 1 and "blog" in text and "call" not in text and "fund" not in text:
        return True

    return False


def recency_score(ts: datetime, now_utc: datetime) -> int:
    age_days = (now_utc - ts).days
    if age_days <= 7:
        return 3
    if age_days <= 14:
        return 2
    return 1


def impact_score(item: dict[str, Any], category: str) -> int:
    text = f"{item['title']} {item['summary']} {item['raw_content']}".lower()
    high_impact_tokens = [
        "global",
        "multi-country",
        "nationwide",
        "emergency",
        "appeal",
        "million",
        "billion",
        "urgent",
    ]
    medium_impact_tokens = [
        "regional",
        "national",
        "program",
        "policy",
        "agriculture",
        "health",
        "education",
        "climate",
        "food security",
    ]

    if any(token in text for token in high_impact_tokens):
        return 2
    if any(token in text for token in medium_impact_tokens) or category in {"Funding", "Procurement", "Humanitarian Update"}:
        return 1
    return 0


def completeness_score(item: dict[str, Any], region: str) -> int:
    fields_present = 0
    if item["title"]:
        fields_present += 1
    if item["summary"] or item["raw_content"]:
        fields_present += 1
    if item["url"]:
        fields_present += 1
    if item["feed_source"] or item["author"]:
        fields_present += 1
    if region:
        fields_present += 1

    if fields_present >= 5:
        return 2
    if fields_present >= 3:
        return 1
    return 0


def priority_for_score(score: int) -> str:
    if score >= 8:
        return "HIGH PRIORITY"
    if score >= 5:
        return "MEDIUM PRIORITY"
    return "LOW PRIORITY"


def render_html(report_date: str, items: list[IntelItem], source_counts: list[tuple[str, int]], total_scanned: int) -> str:
    grouped = {
        "HIGH PRIORITY": [entry for entry in items if entry.priority == "HIGH PRIORITY"],
        "MEDIUM PRIORITY": [entry for entry in items if entry.priority == "MEDIUM PRIORITY"],
        "LOW PRIORITY": [entry for entry in items if entry.priority == "LOW PRIORITY"],
    }

    sections = [
        ("High Priority Opportunities", grouped["HIGH PRIORITY"]),
        ("Medium Priority Opportunities", grouped["MEDIUM PRIORITY"]),
        ("Low Priority Opportunities", grouped["LOW PRIORITY"]),
    ]

    source_badges = "".join(
        f'<li><strong>{html.escape(name)}</strong> <span>({count})</span></li>' for name, count in source_counts
    )

    def render_entry(entry: IntelItem) -> str:
        title = html.escape(entry.title)
        category = html.escape(CATEGORY_LABELS.get(entry.category, entry.category))
        sector = html.escape(entry.sector or "Not specified")
        funding_amount = html.escape(entry.funding_amount or "Not specified")
        opportunity_type = html.escape(entry.opportunity_type)
        key_signal = html.escape(entry.key_signal)
        source = html.escape(entry.feed_source)
        score = entry.score
        link = html.escape(entry.url) if entry.url else ""

        if link:
            source_link = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{source}</a>'
        else:
            source_link = source

        return (
            "<article class=\"entry\">"
            f"<h3>{title}</h3>"
            f"<p><strong>Opportunity type:</strong> {opportunity_type}</p>"
            f"<p><strong>Category:</strong> {category}</p>"
            f"<p><strong>Sector:</strong> {sector}</p>"
            f"<p><strong>Grant/Funding amount:</strong> {funding_amount}</p>"
            f"<p><strong>Key signal:</strong> {key_signal}</p>"
            f"<p><strong>Score:</strong> {score}/10</p>"
            f"<p><strong>Source:</strong> {source_link}</p>"
            "</article>"
        )

    section_html = ""
    for section_title, entries in sections:
        if entries:
            entries_html = "".join(render_entry(entry) for entry in entries)
        else:
            entries_html = '<p class="empty">No qualifying items this period.</p>'
        section_html += f"<section><h2>{html.escape(section_title)}</h2>{entries_html}</section>"

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>PartnerAI Intelligence Report - {report_date}</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #1a1f36; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    header {{ margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px 0; }}
    section {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
    h2 {{ margin-top: 0; }}
    .entry {{ border-top: 1px solid #edf2f7; padding-top: 12px; margin-top: 12px; }}
    .entry:first-of-type {{ border-top: none; padding-top: 0; margin-top: 0; }}
    .entry h3 {{ margin: 0 0 8px 0; font-size: 1.05rem; }}
    p {{ margin: 6px 0; }}
        .meta {{ display: grid; gap: 16px; grid-template-columns: 1fr; }}
        .meta ul {{ margin: 8px 0 0 18px; padding: 0; }}
        .meta li {{ margin: 4px 0; }}
    .empty {{ color: #6b7280; font-style: italic; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>PartnerAI Intelligence Report</h1>
      <p>Reporting window: last 30 days · Generated: {report_date}</p>
    </header>
        <section class="meta">
            <div>
                <h2>Coverage Summary</h2>
                <p><strong>Items scanned:</strong> {total_scanned}</p>
                <p><strong>Items published:</strong> {len(items)}</p>
            </div>
            <div>
                <h2>Sources Searched ({len(source_counts)})</h2>
                <ul>{source_badges or '<li>No source metadata provided in payload.</li>'}</ul>
            </div>
        </section>
    {section_html}
  </main>
</body>
</html>
"""

def score_item(item: dict[str, Any], timestamp: datetime, now_utc: datetime) -> IntelItem | None:
    combined_text = f"{item['title']} {item['summary']} {item['raw_content']} {' '.join(item['categories'])}"
    category, key_signal, signal_strength = classify_signal(combined_text)

    if is_irrelevant(item, category, signal_strength):
        return None

    recency = recency_score(timestamp, now_utc)
    region = detect_region(combined_text)
    impact = impact_score(item, category)
    completeness = completeness_score(item, region)

    score = max(1, min(10, recency + signal_strength + impact + completeness))
    priority = priority_for_score(score)

    return IntelItem(
        timestamp=timestamp,
        feed_source=item["feed_source"],
        title=item["title"],
        url=item["url"],
        summary=item["summary"],
        raw_content=item["raw_content"],
        author=item["author"],
        categories=item["categories"],
        category=category,
        sector=item["sector"],
        funding_amount=item["funding_amount"],
        opportunity_type=derive_opportunity_type(category),
        key_signal=key_signal,
        score=score,
        priority=priority,
    )


def build_report_items(raw_items: list[dict[str, Any]], now_utc: datetime) -> list[IntelItem]:
    thirty_days_ago = now_utc - timedelta(days=30)
    seen: set[str] = set()
    final_items: list[IntelItem] = []

    for raw_item in raw_items:
        item = coerce_item(raw_item)
        timestamp = parse_timestamp(item["timestamp"])
        if not timestamp:
            continue
        if timestamp < thirty_days_ago:
            continue

        key = dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)

        scored = score_item(item, timestamp, now_utc)
        if scored:
            final_items.append(scored)

    final_items.sort(key=lambda entry: (entry.score, entry.timestamp), reverse=True)
    return final_items


def summarize_sources(raw_items: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for raw_item in raw_items:
        source = normalize_text(str(raw_item.get("feed_source") or raw_item.get("source") or "Unknown Source"))
        counts[source] = counts.get(source, 0) + 1

    return sorted(counts.items(), key=lambda row: (-row[1], row[0].lower()))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def check_url(url: str, timeout_seconds: float) -> tuple[int, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return 0, "unsupported URL scheme"

    headers = {"User-Agent": "PartnerAI-LinkValidator/1.0"}

    def request_code(method: str) -> tuple[int, str]:
        req = url_request.Request(url, headers=headers, method=method)
        with url_request.urlopen(req, timeout=timeout_seconds) as response:
            return int(response.getcode() or 0), ""

    try:
        return request_code("HEAD")
    except url_error.HTTPError as exc:
        if exc.code in {405, 501}:
            try:
                return request_code("GET")
            except url_error.HTTPError as get_exc:
                return int(get_exc.code), str(get_exc.reason or "HTTP error")
            except url_error.URLError as get_exc:
                return 0, str(get_exc.reason)
            except Exception as get_exc:  # pragma: no cover
                return 0, str(get_exc)

        return int(exc.code), str(exc.reason or "HTTP error")
    except url_error.URLError as exc:
        return 0, str(exc.reason)
    except Exception as exc:  # pragma: no cover
        return 0, str(exc)


def validate_item_links(items: list[IntelItem], timeout_seconds: float) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    results: list[dict[str, Any]] = []

    for entry in items:
        if not entry.url or entry.url in seen_urls:
            continue

        seen_urls.add(entry.url)
        status_code, detail = check_url(entry.url, timeout_seconds)
        is_ok = 200 <= status_code < 400
        results.append(
            {
                "title": entry.title,
                "url": entry.url,
                "status_code": status_code,
                "ok": is_ok,
                "detail": detail,
            }
        )

    return results


def write_link_validation_report(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    checked = len(results)
    broken = [row for row in results if not row["ok"]]

    lines = [
        "PartnerAI Link Validation",
        f"Checked links: {checked}",
        f"Broken links: {len(broken)}",
        "",
    ]

    if broken:
        lines.append("Broken URL details:")
        for row in broken:
            detail = row["detail"] or "No additional details"
            lines.append(f"- [{row['status_code']}] {row['url']} :: {detail}")
    else:
        lines.append("No broken links detected.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PartnerAI intelligence report from GitHub event payload")
    parser.add_argument("--event-path", required=True, help="Path to GitHub event JSON")
    parser.add_argument("--output-dir", default="reports", help="Output directory for generated report")
    parser.add_argument("--save-payload-path", default="", help="Optional path for saving normalized payload JSON")
    parser.add_argument("--payload-json", default="", help="Optional JSON string for items payload (workflow_dispatch support)")
    parser.add_argument("--index-path", default="index.html", help="Path to update with latest report")
    parser.add_argument("--validate-links", action="store_true", help="Validate source URLs before publishing")
    parser.add_argument("--fail-on-broken-links", action="store_true", help="Exit non-zero when broken links are found")
    parser.add_argument("--link-check-timeout", type=float, default=10.0, help="Timeout per URL check in seconds")
    parser.add_argument("--link-validation-report", default="", help="Optional path for writing link validation results")
    args = parser.parse_args()

    now_utc = datetime.now(timezone.utc)
    event_data = load_json(Path(args.event_path))

    payload: Any = event_data
    if isinstance(event_data, dict) and isinstance(event_data.get("client_payload"), dict):
        payload = event_data["client_payload"]

    if args.payload_json.strip():
        parsed_override = json.loads(args.payload_json)
        payload = parsed_override

    if args.save_payload_path:
        write_json(Path(args.save_payload_path), payload)

    raw_items = extract_items(payload)
    report_items = build_report_items(raw_items, now_utc)
    source_counts = summarize_sources(raw_items)
    report_date = now_utc.strftime("%Y-%m-%d")

    broken_links: list[dict[str, Any]] = []
    if args.validate_links:
        link_results = validate_item_links(report_items, args.link_check_timeout)
        broken_links = [row for row in link_results if not row["ok"]]

        if args.link_validation_report:
            write_link_validation_report(Path(args.link_validation_report), link_results)

        print(f"Links checked: {len(link_results)}")
        print(f"Broken links found: {len(broken_links)}")
        for row in broken_links:
            detail = row["detail"] or "No additional details"
            print(f"BROKEN [{row['status_code']}] {row['url']} :: {detail}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"partnerai-intel-report-{report_date}.html"

    html_report = render_html(report_date, report_items, source_counts, len(raw_items))
    output_file.write_text(html_report, encoding="utf-8")

    latest_html_file = output_dir / "latest.html"
    latest_html_file.write_text(html_report, encoding="utf-8")

    latest_marker = output_dir / "latest-report.txt"
    latest_marker.write_text(str(output_file), encoding="utf-8")

    index_path = Path(args.index_path)
    index_path.write_text(html_report, encoding="utf-8")

    print(f"Generated report: {output_file}")
    print(f"Items processed: {len(raw_items)}")
    print(f"Items published: {len(report_items)}")

    if args.fail_on_broken_links and broken_links:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
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

URL_PATTERN = re.compile(r"https?://[^\s)\]}>\"']+", re.IGNORECASE)
PLACEHOLDER_URL_HOSTS = {
    "example.com",
    "www.example.com",
    "example.org",
    "www.example.org",
    "example.net",
    "www.example.net",
    "localhost",
    "127.0.0.1",
}

SOURCE_FALLBACK_URLS = {
    "developmentaid": "https://www.developmentaid.org/api/frontend/funding/rss.xml",
    "reliefweb": "https://reliefweb.int/updates/rss.xml",
    "asian development bank": "https://www.adb.org/rss/business-opportunities.xml",
    "adb": "https://www.adb.org/rss/business-opportunities.xml",
    "world bank": "https://projects.worldbank.org/en/projects-operations/procurement/rss",
    "un news economic": "https://news.un.org/feed/subscribe/en/news/topic/economic-development/feed/rss.xml",
    "un news humanitarian": "https://news.un.org/feed/subscribe/en/news/topic/humanitarian-aid/feed/rss.xml",
    "un ocha": "https://www.unocha.org/rss.xml",
    "unocha": "https://www.unocha.org/rss.xml",
    "unicef": "https://www.unicef.org/",
    "unhcr": "https://www.unhcr.org/rss.xml",
    "eu tenders": "https://ted.europa.eu/TED/rss/en/RSS.xml",
    "ted": "https://ted.europa.eu/TED/rss/en/RSS.xml",
    "eu international partnerships": "https://international-partnerships.ec.europa.eu/newsroom/feed_en",
    "usaid": "https://www.usaid.gov/news-information/press-releases/rss.xml",
    "oecd": "https://oecd-development-matters.org/feed/",
    "african development bank": "https://www.afdb.org/en/projects-and-operations/procurement/rss",
    "afdb": "https://www.afdb.org/en/projects-and-operations/procurement/rss",
    "inter-american development bank": "https://www.iadb.org/en/rss",
    "inter american development bank": "https://www.iadb.org/en/rss",
    "idb": "https://www.iadb.org/en/rss",
    "green climate fund": "https://www.greenclimate.fund/rss.xml",
    "gcf": "https://www.greenclimate.fund/rss.xml",
    "global environment facility": "https://www.thegef.org/rss.xml",
    "gef": "https://www.thegef.org/rss.xml",
}


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


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_placeholder_url(value: str) -> bool:
    try:
        host = (urlparse(value).hostname or "").lower()
    except Exception:
        return True
    return host in PLACEHOLDER_URL_HOSTS


def extract_urls_from_text(value: str) -> list[str]:
    if not value:
        return []
    return [match.group(0).rstrip(".,;:") for match in URL_PATTERN.finditer(value)]


def source_fallback_url(source_name: str) -> str:
    normalized = normalize_text(source_name).lower()
    if not normalized:
        return ""

    if "un news" in normalized and "humanitarian" in normalized:
        return SOURCE_FALLBACK_URLS["un news humanitarian"]
    if "un news" in normalized and ("economic" in normalized or "development" in normalized):
        return SOURCE_FALLBACK_URLS["un news economic"]

    for key, url in SOURCE_FALLBACK_URLS.items():
        if key in normalized:
            return url
    return ""


def select_best_url(item: dict[str, Any]) -> str:
    candidate_keys = [
        "opportunity_url",
        "canonical_url",
        "external_url",
        "source_url",
        "article_url",
        "url",
        "link",
    ]

    candidate_values: list[str] = []
    for key in candidate_keys:
        value = normalize_text(str(item.get(key) or ""))
        if value:
            candidate_values.append(value)

    text_candidates = extract_urls_from_text(
        " ".join(
            [
                str(item.get("summary") or item.get("description") or ""),
                str(item.get("raw_content") or item.get("content") or ""),
            ]
        )
    )
    candidate_values.extend(text_candidates)

    valid_candidates = [candidate for candidate in candidate_values if is_http_url(candidate)]
    non_placeholder = [candidate for candidate in valid_candidates if not is_placeholder_url(candidate)]

    if non_placeholder:
        return normalize_text(non_placeholder[0])

    source_name = normalize_text(str(item.get("feed_source") or item.get("source") or ""))
    mapped_fallback = source_fallback_url(source_name)
    if mapped_fallback:
        return mapped_fallback

    return ""


def extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]

    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return []
        try:
            return extract_items(json.loads(text))
        except Exception:
            return []

    if not isinstance(payload, dict):
        return []

    for key in ("items", "rss_items", "entries", "records", "data", "opportunities"):
        items = payload.get(key)
        if isinstance(items, list):
            return [entry for entry in items if isinstance(entry, dict)]

    for key in ("payload", "client_payload", "body", "event"):
        nested = payload.get(key)
        nested_items = extract_items(nested)
        if nested_items:
            return nested_items

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
        "timestamp": (
            item.get("timestamp")
            or item.get("pubDate")
            or item.get("published")
            or item.get("published_at")
            or item.get("published_date")
            or item.get("isoDate")
            or item.get("date")
            or item.get("created_at")
            or item.get("updated_at")
        ),
        "feed_source": normalize_text(str(item.get("feed_source") or item.get("source") or "Unknown Source")),
        "title": normalize_text(str(item.get("title") or "Untitled item")),
        "url": select_best_url(item),
        "summary": normalize_text(
            str(item.get("summary") or item.get("description") or item.get("contentSnippet") or "")
        ),
        "raw_content": normalize_text(
            str(item.get("raw_content") or item.get("content") or item.get("content:encoded") or "")
        ),
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
        ("🏆 High Priority Opportunities", grouped["HIGH PRIORITY"], "priority-high"),
        ("⚖️ Medium Priority Opportunities", grouped["MEDIUM PRIORITY"], "priority-medium"),
        ("🟢 Low Priority Opportunities", grouped["LOW PRIORITY"], "priority-low"),
    ]

    source_badges = "\n                    ".join(
        f"<li><strong>{html.escape(name)}</strong> <span>({count})</span></li>"
        for name, count in source_counts
    )

    top_sources = ", ".join(html.escape(name) for name, _ in source_counts[:3]) if source_counts else "No named sources"

    sectors: dict[str, int] = {}
    categories: dict[str, int] = {}
    for entry in items:
        sectors[entry.sector or "Not specified"] = sectors.get(entry.sector or "Not specified", 0) + 1
        category_label = CATEGORY_LABELS.get(entry.category, entry.category)
        categories[category_label] = categories.get(category_label, 0) + 1

    sector_summary = ", ".join(
        f"{html.escape(name)} ({count})" for name, count in sorted(sectors.items(), key=lambda row: (-row[1], row[0]))[:4]
    ) or "No sector distribution available"
    category_summary = ", ".join(
        f"{html.escape(name)} ({count})" for name, count in sorted(categories.items(), key=lambda row: (-row[1], row[0]))[:4]
    ) or "No category distribution available"

    link_validation_note = "Not run for this report"

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
        summary_text = entry.summary or entry.raw_content or "No additional summary provided."
        summary = html.escape(summary_text)
        if len(summary) > 320:
            summary = summary[:317] + "..."

        if entry.score >= 8:
            status_label = "Validated"
            status_class = "validated"
        elif entry.score >= 5:
            status_label = "Active"
            status_class = "active"
        else:
            status_label = "Watchlist"
            status_class = "watch"

        if entry.priority == "HIGH PRIORITY":
            priority_class = "priority-high"
        elif entry.priority == "MEDIUM PRIORITY":
            priority_class = "priority-medium"
        else:
            priority_class = "priority-low"

        if link:
            title_html = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>'
            source_link = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{source}</a>'
        else:
            title_html = title
            source_link = source

        return "\n".join(
            [
                f'<article class="opportunity {priority_class}">',
                f"  <h3>{title_html}</h3>",
                f"  <p>{summary}</p>",
                f"  <p><strong>Opportunity type:</strong> {opportunity_type}</p>",
                f"  <p><strong>Category:</strong> {category}</p>",
                f"  <p><strong>Sector:</strong> {sector}</p>",
                f"  <p><strong>Grant/Funding amount:</strong> {funding_amount}</p>",
                f"  <p><strong>Key signal:</strong> {key_signal}</p>",
                '  <div class="meta">',
                f"    <span class=\"status {status_class}\">{status_label}</span>",
                f"    <span class=\"rss-source\">Source: {source_link} | Score: {score}/10 | Link validation: {link_validation_note}</span>",
                "  </div>",
                "</article>",
            ]
        )

    section_blocks: list[str] = []
    for section_title, entries, section_class in sections:
        if entries:
            entries_html = "\n\n".join(render_entry(entry) for entry in entries)
        else:
            entries_html = '<p class="empty">No qualifying items this period.</p>'
        section_blocks.append(
            "\n".join(
                [
                    f'<section class="section {section_class}">',
                    f"  <h2>{html.escape(section_title)}</h2>",
                    f"  {entries_html}",
                    "</section>",
                ]
            )
        )
    section_html = "\n\n".join(section_blocks)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>PartnerAI Intelligence Report - {report_date}</title>
  <style>
        :root {{ color-scheme: light; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #1f2937;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 2.25em;
        }}
        .header .date {{
            color: #7f8c8d;
            font-size: 1.05em;
            margin-top: 10px;
        }}
        .summary {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .summary h2 {{ margin-top: 0; color: #34495e; }}
        .summary p {{ margin: 8px 0; }}
        .section {{ margin-bottom: 36px; }}
        .section h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-bottom: 18px;
        }}
        .opportunity {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.2s;
        }}
        .opportunity:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        .opportunity h3 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }}
        .opportunity a {{ color: #3498db; text-decoration: none; font-weight: 600; }}
        .opportunity a:hover {{ text-decoration: underline; }}
        .opportunity p {{ margin: 6px 0; }}
        .meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}
        .status {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.78em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }}
        .status.validated {{ background: #d1ecf1; color: #0c5460; }}
        .status.active {{ background: #d4edda; color: #155724; }}
        .status.watch {{ background: #fff3cd; color: #856404; }}
        .priority-high {{ border-left: 4px solid #e74c3c; }}
        .priority-medium {{ border-left: 4px solid #f39c12; }}
        .priority-low {{ border-left: 4px solid #27ae60; }}
        .rss-source {{ font-size: 0.86em; color: #6b7280; }}
        .source-list {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px;
        }}
        .source-list ul {{ margin: 8px 0 0 18px; padding: 0; }}
        .source-list li {{ margin: 4px 0; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 0.95em;
        }}
        .empty {{ color: #6b7280; font-style: italic; }}
  </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
      <h1>PartnerAI Intelligence Report</h1>
            <div class=\"date\">Reporting window: last 30 days | Generated: {report_date}</div>
        </div>

        <div class=\"summary\">
            <h2>Executive Summary</h2>
            <p>This report scans recent intelligence signals and highlights the strongest funding, procurement, and program opportunities by priority score.</p>
            <p><strong>Items scanned:</strong> {total_scanned} | <strong>Items published:</strong> {len(items)} | <strong>Sources searched:</strong> {len(source_counts)}</p>
            <p><strong>Priority split:</strong> High {len(grouped['HIGH PRIORITY'])}, Medium {len(grouped['MEDIUM PRIORITY'])}, Low {len(grouped['LOW PRIORITY'])}</p>
            <p><strong>Top sources:</strong> {top_sources}</p>
        </div>

    {section_html}

        <section class=\"section\">
            <h2>📊 Market Intelligence Insights</h2>
            <div class=\"opportunity\">
                <p><strong>Sector distribution:</strong> {sector_summary}</p>
                <p><strong>Category distribution:</strong> {category_summary}</p>
                <p><strong>Signal quality:</strong> Scores combine recency, relevance, impact, and record completeness.</p>
            </div>
        </section>

        <section class=\"section\">
            <h2>🔗 Sources Searched</h2>
            <div class=\"source-list\">
                <ul>
                    {source_badges or '<li>No source metadata provided in payload.</li>'}
                </ul>
            </div>
            <p class=\"rss-source\"><em>Link validation status: {link_validation_note}</em></p>
        </section>

        <div class=\"footer\">
            <p>Report generated on {report_date}</p>
            <p>PartnerAI Intelligence | Automated Market Report</p>
        </div>
    </div>
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
    if isinstance(event_data, dict) and event_data.get("client_payload") is not None:
        payload = event_data.get("client_payload")

    if args.payload_json.strip():
        parsed_override = json.loads(args.payload_json)
        payload = parsed_override

    raw_items = extract_items(payload)
    if not raw_items:
        raw_items = extract_items(event_data)

    if not raw_items and args.save_payload_path:
        save_path = Path(args.save_payload_path)
        if save_path.exists():
            saved_payload = load_json(save_path)
            saved_items = extract_items(saved_payload)
            if saved_items:
                payload = saved_payload
                raw_items = saved_items

    if args.save_payload_path:
        if raw_items:
            write_json(Path(args.save_payload_path), payload)
        else:
            print("No items extracted from payload; skipped overwriting saved payload file.")

    if not raw_items:
        print("No report items available after payload extraction; skipping report regeneration.")
        return

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
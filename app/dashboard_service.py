from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .logging_config import LOG_PATH


def parse_iso(ts_str: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def calculate_percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    d = k - f
    return round(values_sorted[f] + d * (values_sorted[c] - values_sorted[f]), 2)


def get_dashboard_data() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if LOG_PATH.exists():
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue

    req_received = [r for r in records if r.get("event") == "request_received"]
    req_sent = [r for r in records if r.get("event") == "response_sent"]
    req_failed = [r for r in records if r.get("event") == "request_failed"]

    # 1. Latency & TTFT
    latencies = [float(r["latency_ms"]) for r in req_sent if "latency_ms" in r and r["latency_ms"] is not None]
    ttfts = [float(r["ttft_ms"]) for r in req_sent if "ttft_ms" in r and r["ttft_ms"] is not None]
    p50 = calculate_percentile(latencies, 50)
    p95 = calculate_percentile(latencies, 95)
    p99 = calculate_percentile(latencies, 99)
    ttft_p95 = calculate_percentile(ttfts, 95)

    # 2. Traffic
    total_requests = len(req_received)
    minute_buckets: dict[str, int] = defaultdict(int)
    for r in req_received:
        dt = parse_iso(r.get("ts", ""))
        minute_key = dt.strftime("%H:%M")
        minute_buckets[minute_key] += 1
    traffic_rate_pm = round(total_requests / max(1, len(minute_buckets)), 2)

    # 3. Errors & Retrieval
    total_received = max(1, len(req_received))
    error_rate_pct = round((len(req_failed) / total_received) * 100, 2)
    
    retrieval_records = [r for r in records if r.get("tool_name") == "retrieval"]
    retrieval_successes = [r for r in retrieval_records if r.get("tool_success") is True]
    retrieval_success_rate = (
        round((len(retrieval_successes) / len(retrieval_records)) * 100, 2)
        if retrieval_records
        else 100.0
    )

    error_types: dict[str, int] = defaultdict(int)
    for r in req_failed:
        et = r.get("error_type", "Unknown")
        error_types[et] += 1

    # 4. Cost
    cost_total = round(sum(float(r.get("cost_usd", 0.0)) for r in req_sent), 6)
    cost_by_minute: dict[str, float] = defaultdict(float)
    for r in req_sent:
        dt = parse_iso(r.get("ts", ""))
        minute_key = dt.strftime("%H:%M")
        cost_by_minute[minute_key] += float(r.get("cost_usd", 0.0))
    for k in cost_by_minute:
        cost_by_minute[k] = round(cost_by_minute[k], 6)

    # 5. Tokens
    tokens_in_total = sum(int(r.get("tokens_in", 0)) for r in req_sent)
    tokens_out_total = sum(int(r.get("tokens_out", 0)) for r in req_sent)

    # 6. Quality
    quality_scores = [float(r["quality_score"]) for r in req_sent if "quality_score" in r and r["quality_score"] is not None]
    quality_mean = round(sum(quality_scores) / max(1, len(quality_scores)), 2) if quality_scores else 0.80

    # Timeseries data for chart visualization
    time_series: list[dict[str, Any]] = []
    for r in req_sent:
        time_series.append({
            "ts": r.get("ts", "")[-13:-4] if "ts" in r else "",
            "latency_ms": r.get("latency_ms", 0),
            "ttft_ms": r.get("ttft_ms", 0),
            "cost_usd": r.get("cost_usd", 0.0),
            "tokens_in": r.get("tokens_in", 0),
            "tokens_out": r.get("tokens_out", 0),
            "quality_score": r.get("quality_score", 0.0),
            "correlation_id": r.get("correlation_id", ""),
        })

    return {
        "summary": {
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "ttft_p95": ttft_p95,
            "total_requests": total_requests,
            "traffic_rate_pm": traffic_rate_pm,
            "error_rate_pct": error_rate_pct,
            "retrieval_success_rate": retrieval_success_rate,
            "cost_total": cost_total,
            "tokens_in_total": tokens_in_total,
            "tokens_out_total": tokens_out_total,
            "quality_mean": quality_mean,
        },
        "traffic_buckets": dict(minute_buckets),
        "cost_buckets": dict(cost_by_minute),
        "error_types": dict(error_types),
        "time_series": time_series,
    }

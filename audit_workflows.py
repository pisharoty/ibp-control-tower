#!/usr/bin/env python3
"""Workflow Duplication Sentinel: Finds red herrings and duplicate ingestion logic in main.py renderers."""

import ast
import re
from pathlib import Path


class WorkflowAuditor:

    def __init__(self, main_path="main.py", rf_path="robot_feeds.py"):
        self.main_path = main_path
        self.rf_path = rf_path
        self.main_src = Path(main_path).read_text()
        self.rf_src = Path(rf_path).read_text()
        self.main_tree = ast.parse(self.main_src)
        self.rf_tree = ast.parse(self.rf_src)

    def find_renderers_in_main(self):
        """Find all rendering / UI view functions in main.py."""
        renderers = []
        for node in ast.walk(self.main_tree):
            if isinstance(node, ast.FunctionDef):
                has_st_calls = any(
                    isinstance(n, ast.Attribute) and n.attr.startswith("st.")
                    for n in ast.walk(node)
                )
                if (
                    node.name.startswith(
                        ("render_", "show_", "tab_", "draw_", "display_")
                    )
                    or has_st_calls
                ):
                    renderers.append(node)
        return renderers

    def audit_network_and_parsing_in_ui(self, renderers):
        """Flag UI renderers making direct network calls or parsing XML/JSON/Regex."""
        print("=== 1. RED HERHERRING: INLINE NETWORK & PARSING WORKFLOWS IN UI ===")
        flagged = 0
        for fn in renderers:
            fn_src = "\n".join(
                self.main_src.splitlines()[fn.lineno - 1 : fn.end_lineno]
            )

            indicators = []
            if re.search(r"\b(requests\.get|urllib\.request|httpx\.get)\b", fn_src):
                indicators.append("Direct HTTP Fetch")
            if re.search(r"\b(ET\.fromstring|xml\.etree|feedparser)\b", fn_src):
                indicators.append("XML/RSS Parsing")
            if re.search(r"\b(re\.search|re\.findall|re\.match)\b", fn_src):
                indicators.append("Regex Entity Extraction")

            if indicators:
                flagged += 1
                print(
                    f"⚠️  Function '{fn.name}' in main.py (Lines {fn.lineno}-{fn.end_lineno})"
                )
                print(f"   Infiltration Type: {', '.join(indicators)}")
                print(
                    "   Recommendation: Move raw ingestion/parsing into robot_feeds.py.\n"
                )

        if not flagged:
            print("  ✅ Clean: No inline network or parsing detected in UI.\n")

    def audit_duplicate_keywords(self, renderers):
        """Find keyword lists used for sentiment/risk scoring duplicated in main.py."""
        print("=== 2. RED HERHERRING: DUPLICATE SENTIMENT & KEYWORD MATCHING ===")

        rf_keywords = set(
            re.findall(
                r'["\'](force majeure|outage|strike|shortage|disruption|curtailment|halt|delay|soar)["\']',
                self.rf_src,
                re.IGNORECASE,
            )
        )

        flagged = 0
        for fn in renderers:
            fn_src = "\n".join(
                self.main_src.splitlines()[fn.lineno - 1 : fn.end_lineno]
            )

            matches = set(
                re.findall(
                    r'["\'](force majeure|outage|strike|shortage|disruption|curtailment|halt|delay|soar)["\']',
                    fn_src,
                    re.IGNORECASE,
                )
            )

            if len(matches) >= 3:
                flagged += 1
                print(
                    f"⚠️  Function '{fn.name}' in main.py (Lines {fn.lineno}-{fn.end_lineno})"
                )
                print(f"   Duplicated Keywords: {sorted(list(matches))}")
                print(
                    "   Recommendation: Delegate risk/sentiment scoring to robot_feeds.py.\n"
                )

        if not flagged:
            print("  ✅ Clean: No inline keyword risk-scoring duplicated in UI.\n")

    def audit_hardcoded_telemetry_fallbacks(self, renderers):
        """Flag synthetic fallbacks defined inside UI functions instead of pulling from feeds."""
        print("=== 3. RED HERHERRING: DUPLICATE FALLBACK TELEMETRY DICTIONARIES ===")
        flagged = 0
        for fn in renderers:
            fn_src = "\n".join(
                self.main_src.splitlines()[fn.lineno - 1 : fn.end_lineno]
            )

            telemetry_keys = [
                "vendor",
                "delay_val",
                "risk_score",
                "estimated_impact",
                "gscpi",
            ]
            matched_keys = [
                k for k in telemetry_keys if f'"{k}"' in fn_src or f"'{k}'" in fn_src
            ]

            if len(matched_keys) >= 2 and ("[" in fn_src or "{" in fn_src):
                flagged += 1
                print(
                    f"⚠️  Function '{fn.name}' in main.py (Lines {fn.lineno}-{fn.end_lineno})"
                )
                print(f"   Contains hardcoded fallback keys: {matched_keys}")
                print(
                    "   Recommendation: Return fallback dictionaries directly from robot_feeds.py entry points.\n"
                )

        if not flagged:
            print("  ✅ Clean: No hardcoded telemetry fallbacks inside UI renderers.\n")

    def run_all(self):
        print(f"🔍 AUDITING WORKFLOW DUPLICATION: {self.main_path} vs {self.rf_path}\n")
        renderers = self.find_renderers_in_main()
        self.audit_network_and_parsing_in_ui(renderers)
        self.audit_duplicate_keywords(renderers)
        self.audit_hardcoded_telemetry_fallbacks(renderers)


if __name__ == "__main__":
    auditor = WorkflowAuditor()
    auditor.run_all()

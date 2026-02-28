"""ForensIQ Risk Intelligence Detector — rule-based analysis engine.

Scans forensic page content for indicators of:
  • Counter-intelligence (false alibis, misleading law enforcement)
  • Evidence fabrication (fake documents, backdated records)
  • Anti-forensic activity (data destruction, secure wipes, encrypted comms)
  • Obfuscation (burner phones, code words, VPN/Tor, crypto mixing)
  • Financial fraud (hawala, shell companies, money laundering)
  • Evidence tampering (purged logs, altered records, SIM destruction)

Each rule produces a scored RiskHit with severity, category, and evidence excerpt.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════

@dataclass
class RiskHit:
    rule_id: str
    category: str        # counter_intel | evidence_fabrication | anti_forensic | obfuscation | financial_fraud | evidence_tampering
    severity: str        # critical | high | medium | low
    title: str
    description: str
    evidence_excerpt: str
    page_id: str
    artifact_type: str
    source_device: str   # extraction_id / device name
    matched_pattern: str
    confidence: float    # 0.0 – 1.0


@dataclass
class RiskReport:
    project_id: str
    total_pages_scanned: int = 0
    hits: list[RiskHit] = field(default_factory=list)

    # Aggregated counters
    @property
    def summary(self) -> dict[str, Any]:
        cats: dict[str, int] = {}
        sevs: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for h in self.hits:
            cats[h.category] = cats.get(h.category, 0) + 1
            sevs[h.severity] = sevs.get(h.severity, 0) + 1
        # Overall risk level
        if sevs["critical"] >= 3 or (sevs["critical"] + sevs["high"]) >= 5:
            overall = "CRITICAL"
        elif sevs["critical"] >= 1 or sevs["high"] >= 3:
            overall = "HIGH"
        elif sevs["high"] >= 1 or sevs["medium"] >= 3:
            overall = "MEDIUM"
        else:
            overall = "LOW"
        return {
            "overall_risk": overall,
            "by_category": cats,
            "by_severity": sevs,
            "total_hits": len(self.hits),
        }


# ═══════════════════════════════════════════════════════════════
# Rule definitions  —  pattern → risk mapping
# ═══════════════════════════════════════════════════════════════

# Each rule: (rule_id, category, severity, title, description, [regex_patterns], confidence)
# Patterns are OR-ed — if any match, the rule fires.

RISK_RULES: list[tuple[str, str, str, str, str, list[str], float]] = [
    # ── Counter-Intelligence ──────────────────────────
    (
        "CI-001", "counter_intel", "critical",
        "False Alibi Construction",
        "Evidence of constructing fake alibis with fabricated documentation to mislead investigators.",
        [
            r"fake entry pass",
            r"edited.*date.?stamp",
            r"place us there",
            r"cover story.*memoris",
            r"say (we|I|he) (were|was) at",
            r"fake.*alibi",
            r"that is our story",
        ],
        0.95,
    ),
    (
        "CI-002", "counter_intel", "critical",
        "Misleading Law Enforcement",
        "Deliberately feeding false intelligence to police or regulatory bodies to divert investigations.",
        [
            r"counter.?tip",
            r"throw them off",
            r"wrong (place|warehouse|trail|location)",
            r"fabricated.*intel",
            r"pointing to.*competitor",
            r"investigate the wrong",
            r"buy us.*weeks",
            r"kept? .*(off|away).*raid",
            r"keep.*off the (list|radar)",
        ],
        0.95,
    ),
    (
        "CI-003", "counter_intel", "high",
        "Surveillance & Counter-Surveillance",
        "Activities to detect, evade, or counter law enforcement surveillance.",
        [
            r"lookout",
            r"abort.*drop",
            r"whistles?.*abort",
            r"if.*(police|cops).*outside.*abort",
            r"circle and come back",
            r"wear a mask.*cctv",
            r"tower mapping.*clean",
        ],
        0.85,
    ),
    (
        "CI-004", "counter_intel", "high",
        "Law Enforcement Bribery",
        "Payments or arrangements with law enforcement to protect criminal operations.",
        [
            r"(inspector|police).*arrangement",
            r"raid list.*month",
            r"₹\d+L?\s*monthly.*police",
            r"(bribe|brib)",
            r"cover for you",
            r"keep.*off your raid",
        ],
        0.90,
    ),
    # ── Evidence Fabrication ──────────────────────────
    (
        "EF-001", "evidence_fabrication", "critical",
        "Document Fabrication",
        "Creating fake invoices, receipts, purchase orders, or official documents.",
        [
            r"fake.*invoice",
            r"fake.*receipt",
            r"fake.*purchase order",
            r"backdated.*invoice",
            r"backdated.*document",
            r"fake.*board resolution",
            r"create.*fake.*agreement",
            r"fake.*consultancy agreement",
            r"matching.*jewel(le)?r.*receipt",
            r"fake.*GST",
            r"planted.*GST returns",
            r"fake.*letterhead",
        ],
        0.95,
    ),
    (
        "EF-002", "evidence_fabrication", "critical",
        "Record Alteration / Parallel Books",
        "Creating duplicate or altered records to replace legitimate ones.",
        [
            r"parallel.*set of.*books",
            r"parallel.*set of.*records",
            r"duplicate.*records",
            r"altered.*records",
            r"altered version.*first",
            r"original.*purged",
            r"backup logs.*reflect",
            r"overr(o|i)de.*compliance",
        ],
        0.95,
    ),
    (
        "EF-003", "evidence_fabrication", "high",
        "False Paper Trail",
        "Constructing false financial or business paper trails to disguise illicit transactions.",
        [
            r"false.*paper trail",
            r"plant.*trail",
            r"decoy.*trail",
            r"make it look like.*legitimate",
            r"CSR donation.*offset",
            r"cover.*all.*wire transfers",
            r"amounts match exactly",
            r"fake.*company",
        ],
        0.90,
    ),
    (
        "EF-004", "evidence_fabrication", "high",
        "Customs / Trade Document Fraud",
        "Altering shipping manifests, bills of lading, or customs declarations.",
        [
            r"change.*bill of lading",
            r"customs declaration.*different",
            r"HS code",
            r"paper trail.*match.*original order",
            r"actual goods.*not match",
            r"don.t inspect.*just clear",
        ],
        0.90,
    ),
    # ── Anti-Forensic Activity ────────────────────────
    (
        "AF-001", "anti_forensic", "critical",
        "Evidence Destruction Orders",
        "Explicit instructions to delete communications, wipe devices, or destroy physical evidence.",
        [
            r"delete all.*chat",
            r"purge.*records",
            r"factory reset",
            r"burn.*document",
            r"destroy this SIM",
            r"wipe.*app",
            r"shredded",
            r"deleting.*now",
            r"destroy.*paperwork",
        ],
        0.95,
    ),
    (
        "AF-002", "anti_forensic", "high",
        "Cryptocurrency Obfuscation",
        "Using privacy coins, mixers, or tumblers to hide transaction trails.",
        [
            r"monero.*untraceable",
            r"XMR.*untraceable",
            r"CoinJoin",
            r"tumbl",
            r"mixer",
            r"privacy bridge",
            r"tornado cash",
            r"completely untraceable",
            r"opaque",
        ],
        0.90,
    ),
    (
        "AF-003", "anti_forensic", "high",
        "Digital Identity Spoofing",
        "Using spoofed identities, fake KYC documents, or VPN/Tor for anonymity.",
        [
            r"fingerprint.*spoof",
            r"Multilogin",
            r"fake.*Aadhaar",
            r"fake.*passport",
            r"Lithuanian.*shell.*doc",
            r"passed.*automated KYC",
            r"registered under.*different name",
            r"fake.*GST registration",
            r"non-existent company",
        ],
        0.85,
    ),
    (
        "AF-004", "anti_forensic", "medium",
        "Anti-Forensic Software Detected",
        "Presence of data wiping, privacy, or anonymity tools on the device.",
        [
            r"Secure Erase",
            r"TOR Browser",
            r"permanently delete",
            r"auto-delete",
            r"NordVPN",
        ],
        0.70,
    ),
    (
        "AF-005", "anti_forensic", "high",
        "Clean / Swap Phone Strategy",
        "Maintaining a secondary 'clean' phone to present to authorities if searched.",
        [
            r"clean.*phone",
            r"second phone.*clean",
            r"swap.*clean",
            r"clean contacts",
            r"registered phone",
        ],
        0.85,
    ),
    # ── Obfuscation ──────────────────────────────────
    (
        "OB-001", "obfuscation", "high",
        "Burner Phone / SIM Operations",
        "Use of disposable phones or SIM cards to avoid call tracing.",
        [
            r"burner",
            r"destroy.*SIM",
            r"new SIM.*old.*destroy",
            r"replacement number",
            r"fake Aadhaar",
            r"Tamil Nadu number.*harder to trace",
        ],
        0.85,
    ),
    (
        "OB-002", "obfuscation", "medium",
        "Code Words / Operational Codes",
        "Use of code words, aliases, or coded references in communications.",
        [
            r"code word",
            r"ref code",
            r"coded account",
            r"code.*ALPHA",
            r"Digital Trail",
        ],
        0.75,
    ),
    (
        "OB-003", "obfuscation", "medium",
        "Encrypted Communication Channels",
        "Heavy reliance on end-to-end encrypted or privacy-focused messaging.",
        [
            r"Signal",
            r"ProtonMail",
            r"Tutanota",
            r"encrypted channel",
        ],
        0.60,
    ),
    # ── Financial Fraud ──────────────────────────────
    (
        "FF-001", "financial_fraud", "critical",
        "Hawala / Informal Value Transfer",
        "Use of hawala (informal money transfer) networks to move funds outside the banking system.",
        [
            r"hawala",
            r"Manek Chowk",
            r"Gujarat.*agent",
            r"Chennai.*agent",
            r"conversion.*AED",
        ],
        0.90,
    ),
    (
        "FF-002", "financial_fraud", "critical",
        "Shell Company Operations",
        "Using offshore shell companies, nominee directors, or layered corporate structures.",
        [
            r"shell company",
            r"Seychelles trust",
            r"nominee director",
            r"Mauritius.*subsidiary",
            r"silent director",
            r"offshore",
            r"inter-company loan",
        ],
        0.90,
    ),
    (
        "FF-003", "financial_fraud", "high",
        "Suspicious Transaction Override",
        "Banking insider overriding compliance alerts or suppressing suspicious transaction reports.",
        [
            r"overr(o|i)de.*compliance",
            r"overr(o|i)de.*STR",
            r"STR.*alert",
            r"FIU.*notification",
            r"compliance.*flagged.*approved",
        ],
        0.90,
    ),
    (
        "FF-004", "financial_fraud", "high",
        "Tax Evasion / Income Concealment",
        "Concealing income sources or creating false tax documentation.",
        [
            r"stock market gains.*ITR",
            r"consulting.*income.*cash",
            r"trading statements",
            r"intraday.*profits",
            r"clean paperwork",
            r"no paper trail",
        ],
        0.85,
    ),
    (
        "FF-005", "financial_fraud", "high",
        "Gold-Based Money Laundering",
        "Converting illicit funds to gold for storage or transport.",
        [
            r"gold bar",
            r"Emirates Gold",
            r"vault.*gold",
            r"diplomatic pouch",
            r"no customs",
            r"gold custody",
        ],
        0.85,
    ),
    # ── Evidence Tampering ───────────────────────────
    (
        "ET-001", "evidence_tampering", "critical",
        "Bank Record Manipulation",
        "Altering or creating false banking transaction records.",
        [
            r"purge.*RTGS",
            r"delete.*override.*notes",
            r"SWIFT records.*legitimate",
            r"IT infrastructure upgrade.*cover",
            r"InfoTech Solutions",
        ],
        0.95,
    ),
    (
        "ET-002", "evidence_tampering", "high",
        "Blockchain Audit Trail Fabrication",
        "Creating fake blockchain transaction histories or smart contract interactions.",
        [
            r"fake audit trail",
            r"dummy smart contract",
            r"plausible deniability.*blockchain",
            r"decoy blockchain",
            r"legitimate.*exchange deposit",
        ],
        0.90,
    ),
]


# ═══════════════════════════════════════════════════════════════
# Detector
# ═══════════════════════════════════════════════════════════════

class RiskIntelDetector:
    """Rule-based risk intelligence scanner for forensic page data."""

    def __init__(self, rules: list | None = None):
        self._rules = rules or RISK_RULES
        # Pre-compile patterns per rule for performance
        self._compiled: list[tuple[Any, list[re.Pattern]]] = []
        for rule in self._rules:
            rid, cat, sev, title, desc, patterns, conf = rule
            compiled_pats = [re.compile(p, re.IGNORECASE) for p in patterns]
            self._compiled.append((rule, compiled_pats))

    def scan_pages(self, pages: list[dict], project_id: str = "") -> RiskReport:
        """Scan a list of page dicts and return a RiskReport.

        Each page dict should have: page_id, body, artifact_type, and optionally
        extraction_id/title.
        """
        report = RiskReport(project_id=project_id, total_pages_scanned=len(pages))
        seen: set[tuple[str, str]] = set()  # (rule_id, page_id) dedup

        for page in pages:
            body = page.get("body", "") or ""
            if not body:
                continue
            page_id = page.get("page_id", "unknown")
            artifact = page.get("artifact_type", "unknown")
            device = page.get("extraction_id", "") or page.get("title", "")

            for (rid, cat, sev, title, desc, _, conf), compiled_pats in self._compiled:
                for pat in compiled_pats:
                    m = pat.search(body)
                    if m:
                        key = (rid, page_id)
                        if key in seen:
                            break  # already hit this rule on this page
                        seen.add(key)

                        # Extract ≤200-char excerpt around match
                        start = max(0, m.start() - 60)
                        end = min(len(body), m.end() + 140)
                        excerpt = body[start:end].replace("\n", " ").strip()
                        if start > 0:
                            excerpt = "…" + excerpt
                        if end < len(body):
                            excerpt = excerpt + "…"

                        report.hits.append(RiskHit(
                            rule_id=rid,
                            category=cat,
                            severity=sev,
                            title=title,
                            description=desc,
                            evidence_excerpt=excerpt,
                            page_id=page_id,
                            artifact_type=artifact,
                            source_device=device,
                            matched_pattern=pat.pattern,
                            confidence=conf,
                        ))
                        break  # one pattern match per rule per page is enough

        # Sort by severity (critical first)
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        report.hits.sort(key=lambda h: (sev_order.get(h.severity, 9), h.rule_id))
        return report

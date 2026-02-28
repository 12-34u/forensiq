#!/usr/bin/env python3
"""ForensIQ Demo — Operation Digital Trail

Demonstrates the full pipeline:
  1. Parse .clbe files (Cellebrite forensic extractions)
  2. Build PageIndex (token-bounded pages from artifacts)
  3. Populate Neo4j Knowledge Graph (entities + relationships)
  4. Run forensic queries across the graph

NOTE: Vector RAG (FAISS/OpenAI embeddings) requires OPENAI_API_KEY in .env.
      This demo shows everything that works without it, plus the graph queries
      that are the centrepiece of the judges' demo.
"""

from __future__ import annotations

import json
import logging
import sys
import warnings
from pathlib import Path

# Suppress neo4j driver warnings about non-existent types
logging.getLogger("neo4j").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from forensiq.ufdr.parser import parse_ufdr
from forensiq.pageindex.indexer import index_extraction
from forensiq.pageindex.store import PageStore
from forensiq.graphrag.neo4j_client import Neo4jClient
from forensiq.graphrag.extractor import populate_graph, extract_entities

DATA_DIR = PROJECT_ROOT / "data" / "demo"

# ───────────────────────────────────────────────────────
# ANSI colours for pretty terminal output
# ───────────────────────────────────────────────────────
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def header(text: str):
    print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*60}{RESET}\n")

def sub(text: str):
    print(f"  {GREEN}▸{RESET} {text}")

def warn(text: str):
    print(f"  {YELLOW}⚠{RESET} {text}")

def highlight(text: str):
    print(f"  {RED}{BOLD}⚡{RESET} {BOLD}{text}{RESET}")


def main():
    header("ForensIQ — Operation Digital Trail Demo")
    print(f"  Scenario: Financial fraud / money laundering investigation")
    print(f"  Devices:  Vikram Mehta (suspect) + Priya Sharma (accomplice)\n")

    # ─── Step 1: Parse ──────────────────────────────────
    header("STEP 1: Parse Cellebrite Extractions (.clbe)")
    
    clbe_vikram = DATA_DIR / "suspect_phone.clbe"
    clbe_priya  = DATA_DIR / "accomplice_phone.clbe"

    ext_vikram = parse_ufdr(str(clbe_vikram))
    sub(f"Vikram's phone: {ext_vikram.device_info.device_name} — {ext_vikram.total_artifacts} artifacts")
    sub(f"  Contacts: {len(ext_vikram.contacts)}, Calls: {len(ext_vikram.call_logs)}, "
        f"Messages: {len(ext_vikram.messages)}, Emails: {len(ext_vikram.emails)}")
    sub(f"  Web: {len(ext_vikram.web_history)}, Locations: {len(ext_vikram.locations)}, "
        f"Apps: {len(ext_vikram.installed_apps)}, Accounts: {len(ext_vikram.accounts)}")

    ext_priya = parse_ufdr(str(clbe_priya))
    sub(f"Priya's phone:  {ext_priya.device_info.device_name} — {ext_priya.total_artifacts} artifacts")
    sub(f"  Contacts: {len(ext_priya.contacts)}, Calls: {len(ext_priya.call_logs)}, "
        f"Messages: {len(ext_priya.messages)}, Emails: {len(ext_priya.emails)}")

    # ─── Step 2: PageIndex ──────────────────────────────
    header("STEP 2: Build PageIndex (token-bounded pages)")
    
    pages_v = index_extraction(ext_vikram)
    pages_p = index_extraction(ext_priya)
    all_pages = pages_v + pages_p
    
    sub(f"Vikram device → {len(pages_v)} pages")
    sub(f"Priya device  → {len(pages_p)} pages")
    sub(f"Total pages:    {len(all_pages)}")
    
    # Save to page store
    store = PageStore()
    store.save_pages(pages_v)
    store.save_pages(pages_p)
    sub(f"Pages persisted to JSONL store")

    # Show page type distribution
    from collections import Counter
    dist = Counter(p.artifact_type for p in all_pages)
    print()
    sub("Page distribution:")
    for atype, count in dist.most_common():
        print(f"      {atype:20s}  {count:3d} pages")

    # ─── Step 3: Neo4j Graph ────────────────────────────
    header("STEP 3: Populate Neo4j Knowledge Graph")
    
    try:
        from config.settings import settings as _s
        client = Neo4jClient(_s.neo4j_uri, _s.neo4j_user, _s.neo4j_password, _s.neo4j_database)
        client.ensure_schema()
        sub(f"Connected to Neo4j at {_s.neo4j_uri} (db={_s.neo4j_database})")
    except Exception as e:
        warn(f"Neo4j not available: {e}")
        warn("Check .env for correct NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD / NEO4J_DATABASE")
        client = None

    if client:
        # Clear previous data for clean demo
        client._driver.execute_query("MATCH (n) DETACH DELETE n", database_=client._database)
        sub("Cleared existing graph data")

        populate_graph(client, pages_v)
        sub(f"Vikram device → graph populated")
        
        populate_graph(client, pages_p)
        sub(f"Priya device  → graph populated")

        n = client.count_nodes()
        r = client.count_relationships()
        highlight(f"Knowledge Graph: {n} nodes, {r} relationships")

        # ─── Step 4: Forensic Queries ───────────────────
        header("STEP 4: Forensic Intelligence Queries")

        # Query 1: Who did Vikram communicate with?
        print(f"  {BOLD}Q1: Who did the suspect (Vikram) communicate with?{RESET}")
        results = client._driver.execute_query("""
            MATCH (p:Person)-[r]-(other:Person)
            WHERE p.name CONTAINS 'Vikram' OR p.name CONTAINS 'V (Boss)'
            RETURN DISTINCT other.name AS contact, type(r) AS channel, count(*) AS interactions
            ORDER BY interactions DESC
        """, database_=client._database)
        for rec in results.records:
            print(f"      {rec['contact']:30s}  via {rec['channel']:15s}  ({rec['interactions']}x)")

        # Query 2: Cross-device correlation — shared phone numbers
        print(f"\n  {BOLD}Q2: Cross-device entity overlap (shared phone numbers on both devices){RESET}")
        results = client._driver.execute_query("""
            MATCH (phone:PhoneNumber)-[:MENTIONED_IN]-(p:Page)
            WITH phone, count(DISTINCT p) AS page_count
            WHERE page_count > 2
            RETURN phone.number AS phone_number, phone.raw AS raw, page_count
            ORDER BY page_count DESC
            LIMIT 10
        """, database_=client._database)
        for rec in results.records:
            raw = rec.get('raw') or rec['phone_number']
            print(f"      {raw:25s}  found across {rec['page_count']} pages")

        # Query 3: Financial trail — search through page content stored in PageStore
        print(f"\n  {BOLD}Q3: Financial entities — pages mentioning money/crypto/hawala{RESET}")
        keywords = ['lakh', 'hawala', 'btc', 'usdt', 'commission', 'wire transfer', 'laundr']
        for p in all_pages:
            body_lower = p.body.lower()
            hits = [k for k in keywords if k in body_lower]
            if hits:
                excerpt = p.body.replace('\n', ' ')[:100]
                print(f"      [{p.artifact_type:12s}] {excerpt}...")
                print(f"        {DIM}Keywords: {', '.join(hits)}{RESET}")

        # Query 4: Organisations in the network
        print(f"\n  {BOLD}Q4: Organisations in the suspect's network{RESET}")
        results = client._driver.execute_query("""
            MATCH (o:Organization)<-[:BELONGS_TO_ORG]-(p:Person)
            RETURN o.name AS org, collect(DISTINCT p.name) AS members, count(p) AS member_count
            ORDER BY member_count DESC
        """, database_=client._database)
        for rec in results.records:
            members = [m for m in rec['members'] if m][:3]
            member_str = ", ".join(members) if members else "—"
            print(f"      {rec['org']:40s}  ({rec['member_count']} links) → {member_str}")

        # Query 5: Location timeline
        print(f"\n  {BOLD}Q5: Location timeline (GPS coordinates from devices){RESET}")
        results = client._driver.execute_query("""
            MATCH (l:Location)
            RETURN l.latitude AS lat, l.longitude AS lon
        """, database_=client._database)
        for rec in results.records:
            lat = rec.get('lat')
            lon = rec.get('lon')
            if lat and lon:
                print(f"      📍 {lat:.4f}, {lon:.4f}")
        # Also show text-based locations from page content
        for p in all_pages:
            if p.artifact_type == "location":
                for line in p.body.splitlines():
                    if "Address:" in line:
                        print(f"      📍 {line.strip()}")

        # Query 6: Email network
        print(f"\n  {BOLD}Q6: Email addresses in the network{RESET}")
        results = client._driver.execute_query("""
            MATCH (e:EmailAddress)<-[:HAS_EMAIL]-(p:Person)
            RETURN e.address AS email, collect(DISTINCT p.name) AS people
            ORDER BY e.address
        """, database_=client._database)
        seen = set()
        for rec in results.records:
            email = rec['email']
            if email in seen:
                continue
            seen.add(email)
            people = [p for p in rec['people'] if p]
            pstr = ", ".join(people[:3]) if people else "—"
            print(f"      {email:45s}  → {pstr}")

        # Query 7: URL / web evidence
        print(f"\n  {BOLD}Q7: Suspicious URLs visited{RESET}")
        results = client._driver.execute_query("""
            MATCH (u:URL)
            RETURN u.address AS url
            ORDER BY u.address
        """, database_=client._database)
        for rec in results.records:
            url = rec.get('url') or ''
            if not url:
                continue
            flag = "🚩" if any(k in url.lower() for k in ['tornado', 'binance', 'dban', 'hawala', 'tor']) else "  "
            print(f"      {flag} {url}")

        # Query 8: App evidence
        print(f"\n  {BOLD}Q8: Installed apps (privacy / crypto / security tools){RESET}")
        results = client._driver.execute_query("""
            MATCH (a:App)
            WHERE a.name CONTAINS 'Tor' OR a.name CONTAINS 'VPN' OR a.name CONTAINS 'Binance'
                  OR a.name CONTAINS 'Signal' OR a.name CONTAINS 'Vault' OR a.name CONTAINS 'Trust'
                  OR a.name CONTAINS 'Proton' OR a.name CONTAINS 'Secure'
            RETURN DISTINCT a.name AS app
        """, database_=client._database)
        for rec in results.records:
            print(f"      🔒 {rec['app']}")

        # Summary graph statistics
        header("GRAPH SUMMARY")
        label_counts = client._driver.execute_query("""
            MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC
        """, database_=client._database)
        for rec in label_counts.records:
            print(f"      {rec['label']:20s}  {rec['cnt']:4d} nodes")

        rel_counts = client._driver.execute_query("""
            MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt ORDER BY cnt DESC
        """, database_=client._database)
        print()
        for rec in rel_counts.records:
            print(f"      {rec['rel_type']:20s}  {rec['cnt']:4d} relationships")

        client.close()

    # ─── Step 5: Vector RAG status ──────────────────────
    header("STEP 5: Vector RAG (Semantic Search)")
    
    try:
        from config.settings import Settings
        settings = Settings()
        if settings.openai_api_key and settings.openai_api_key != "your-openai-key-here":
            sub("OpenAI API key found — embedding pipeline available")
            sub("Start the server and use POST /api/v1/query to run semantic searches")
        else:
            warn("OPENAI_API_KEY not set in .env — vector search unavailable")
            warn("Set it to enable semantic queries like:")
            print(f'      curl -X POST "http://localhost:8000/api/v1/query" \\')
            print(f'           -H "Content-Type: application/json" \\')
            print(f'           -d \'{{"text": "money laundering through hawala", "k": 5}}\'')
    except Exception:
        warn("Settings not loaded — vector search status unknown")

    # ─── Done ───────────────────────────────────────────
    header("DEMO COMPLETE")
    print(f"  {BOLD}What to show judges:{RESET}")
    print(f"  1. Neo4j Aura → https://console.neo4j.io  (Explore tab → Open)")
    print(f"     Run: MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100")
    print(f"  2. ForensIQ API  → http://localhost:8000/docs (Swagger UI)")
    print(f"  3. This demo script shows end-to-end pipeline")
    print()
    print(f"  {DIM}Key talking points:")
    print(f"  • Cross-device entity resolution (same phone numbers/emails merge)")
    print(f"  • Financial trail extraction (Hawala, crypto, wire transfers)")
    print(f"  • Suspicious app detection (Tor, VPN, crypto wallets, vaults)")
    print(f"  • Location timeline correlation between suspects")
    print(f"  • Evidence-grade page indexing with content hashing{RESET}")
    print()


if __name__ == "__main__":
    main()

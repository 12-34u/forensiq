#!/usr/bin/env python3
"""Generate an expanded, complex synthetic forensic dataset (6 devices, 200+ pages).

Scenario: "Operation Digital Trail – Phase 2"
══════════════════════════════════════════════
An international money-laundering / fraud ring spanning India, UAE, China, and
the UK.  Six devices extracted — suspects, accomplices, and a mule — revealing
overlapping comms, crypto wallets, hawala networks, shell companies, burner
phones, and evidence-destruction attempts.

Devices:
 1. suspect_phone.clbe      — Vikram Mehta (primary suspect)
 2. accomplice_phone.clbe   — Priya Sharma (hawala broker)
 3. crypto_laptop.clbe      — Rajan Patel (crypto laundering)
 4. banker_phone.clbe       — Deepak Joshi (bank insider)
 5. mule_phone.clbe         — Suresh Yadav (cash mule / courier)
 6. burner_phone.clbe       — Sanjay Kumar (operational burner)

This generates ~200+ pages and a rich entity graph.
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "demo"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════
# DEVICE 1 — Vikram Mehta (Primary Suspect)
# ═══════════════════════════════════════════════════════

VIKRAM_XML = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>
  <DeviceInfo>
    <DeviceName>Vikram's OnePlus 12</DeviceName>
    <Model>OnePlus 12 (CPH2583)</Model>
    <OSVersion>Android 14 (OxygenOS 14.0.2)</OSVersion>
    <IMEI>353456789012345</IMEI>
    <SerialNumber>OP12VKM2025X</SerialNumber>
    <PhoneNumber>+91-98765-43210</PhoneNumber>
    <ExtractionType>Full File System</ExtractionType>
    <ExtractionDate>2026-01-15T10:32:00</ExtractionDate>
  </DeviceInfo>

  <Contacts>
    <Contact><Name>Priya Sharma</Name><PhoneNumber>+91-99887-65432</PhoneNumber><Email>priya.sharma.offshore@protonmail.com</Email><Organization>Oceanic Trade Solutions Pvt Ltd</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Rajan Patel</Name><PhoneNumber>+91-88776-54321</PhoneNumber><Email>rajan.crypto.dev@tutanota.com</Email><Organization>BlockSecure Labs</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Deepak Joshi</Name><PhoneNumber>+91-77665-43210</PhoneNumber><Email>deepak.joshi.banking@gmail.com</Email><Organization>National Commerce Bank</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Ananya Singh</Name><PhoneNumber>+91-66554-32109</PhoneNumber><Email>ananya.singh.legal@outlook.com</Email><Organization>Singh &amp; Associates Law Firm</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Sanjay (Burner)</Name><PhoneNumber>+91-70001-99988</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Kavita Mehta</Name><PhoneNumber>+91-98765-11111</PhoneNumber><Organization>Family</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Arjun Reddy</Name><PhoneNumber>+91-81234-56789</PhoneNumber><Email>arjun.reddy@globalfreight.in</Email><Organization>Global Freight Logistics</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Meera Iyer</Name><PhoneNumber>+91-90001-22334</PhoneNumber><Email>meera.iyer@financewatch.org</Email><Organization>Finance Watch India</Organization><Source>WhatsApp</Source></Contact>
    <Contact><Name>Farid Hassan</Name><PhoneNumber>+971-50-1234567</PhoneNumber><Email>farid.hassan@dubaitrade.ae</Email><Organization>Dubai International Trading LLC</Organization><Source>Telegram</Source></Contact>
    <Contact><Name>Li Wei</Name><PhoneNumber>+86-138-0013-8000</PhoneNumber><Email>liwei@shenzhensupply.cn</Email><Organization>Shenzhen Supply Chain Co</Organization><Source>WeChat</Source></Contact>
    <Contact><Name>Suresh Yadav</Name><PhoneNumber>+91-72000-11122</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Mohammed Al-Rashid</Name><PhoneNumber>+971-55-9876543</PhoneNumber><Email>al.rashid@emiratesgold.ae</Email><Organization>Emirates Gold Exchange</Organization><Source>Telegram</Source></Contact>
    <Contact><Name>Inspector Rawat</Name><PhoneNumber>+91-11000-99000</PhoneNumber><Organization>Delhi Police EOW</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Hawala Agent 1 (Gujarat)</Name><PhoneNumber>+91-79000-55544</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Hawala Agent 2 (Chennai)</Name><PhoneNumber>+91-44000-66655</PhoneNumber><Source>Signal</Source></Contact>
  </Contacts>

  <CallLogs>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-99887-65432</PhoneNumber><ContactName>Priya Sharma</ContactName><Duration>342</Duration><Timestamp>2026-01-10T09:15:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-77665-43210</PhoneNumber><ContactName>Deepak Joshi</ContactName><Duration>128</Duration><Timestamp>2026-01-10T11:45:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-88776-54321</PhoneNumber><ContactName>Rajan Patel</ContactName><Duration>567</Duration><Timestamp>2026-01-10T14:20:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-70001-99988</PhoneNumber><ContactName>Sanjay (Burner)</ContactName><Duration>89</Duration><Timestamp>2026-01-10T22:30:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-99887-65432</PhoneNumber><ContactName>Priya Sharma</ContactName><Duration>456</Duration><Timestamp>2026-01-11T08:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+971-50-1234567</PhoneNumber><ContactName>Farid Hassan</ContactName><Duration>723</Duration><Timestamp>2026-01-11T15:30:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-66554-32109</PhoneNumber><ContactName>Ananya Singh</ContactName><Duration>198</Duration><Timestamp>2026-01-12T09:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-70001-99988</PhoneNumber><ContactName>Sanjay (Burner)</ContactName><Duration>45</Duration><Timestamp>2026-01-12T23:55:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-72000-11122</PhoneNumber><ContactName>Suresh Yadav</ContactName><Duration>92</Duration><Timestamp>2026-01-13T07:30:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+971-55-9876543</PhoneNumber><ContactName>Mohammed Al-Rashid</ContactName><Duration>412</Duration><Timestamp>2026-01-13T16:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-79000-55544</PhoneNumber><ContactName>Hawala Agent 1</ContactName><Duration>67</Duration><Timestamp>2026-01-13T22:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+86-138-0013-8000</PhoneNumber><ContactName>Li Wei</ContactName><Duration>301</Duration><Timestamp>2026-01-14T10:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-44000-66655</PhoneNumber><ContactName>Hawala Agent 2 (Chennai)</ContactName><Duration>55</Duration><Timestamp>2026-01-14T21:15:00</Timestamp><Source>Phone</Source></CallLog>
  </CallLogs>

  <Messages>
    <!-- WhatsApp with Priya -->
    <Message><From>Vikram Mehta</From><To>Priya Sharma</To><Body>Priya, the Dubai shipment invoice is ready. ₹47 lakh needs to move through Oceanic Trade by Thursday. Use the Gujarat hawala route — Farid confirmed the other end.</Body><Timestamp>2026-01-10T09:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Priya Sharma</From><To>Vikram Mehta</To><Body>Got it. The hawala agent in Ahmedabad asked for 2.5% commission this time — rates went up after the ED raids in December. I'll split the amount: ₹25L via hawala, ₹22L through the Mauritius shell.</Body><Timestamp>2026-01-10T09:45:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Priya Sharma</To><Body>Fine. Make sure Deepak's branch processes the RTGS before 3 PM. The Shenzhen order needs advance payment — Li Wei is getting impatient.</Body><Timestamp>2026-01-10T10:02:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <!-- Telegram with Rajan -->
    <Message><From>Vikram Mehta</From><To>Rajan Patel</To><Body>Rajan, the 15 BTC from last week — have you tumbled them through the mixers yet? We need clean wallets for the Binance-to-fiat conversion.</Body><Timestamp>2026-01-10T14:30:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Rajan Patel</From><To>Vikram Mehta</To><Body>Done. Used Wasabi + CoinJoin. Split into 5 wallets: bc1q7ky...a3f, bc1qm9x...d2e, bc1qp4r...h7g, bc1qt8w...k1j, bc1qv2s...n5m. Each holds ~3 BTC. Ready for the P2P OTC sell on LocalBitcoins.</Body><Timestamp>2026-01-10T15:12:00</Timestamp><Source>Telegram</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Rajan Patel</To><Body>Good. Convert to USDT first, then move through Tron to the cold wallet. Avoid Ethereum — the gas fees will flag large movements. Target: $380K equivalent by Jan 15.</Body><Timestamp>2026-01-10T15:20:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Rajan Patel</From><To>Vikram Mehta</To><Body>One issue — Binance KYC flagged our mule account (Suresh's ID). I'm setting up a new OKX account with a different passport. Need 48 hours.</Body><Timestamp>2026-01-11T09:00:00</Timestamp><Source>Telegram</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Rajan Patel</To><Body>Use the Lithuanian shell company docs — those have clean KYC history. And rotate the VPN to Singapore this time.</Body><Timestamp>2026-01-11T09:15:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>

    <!-- Signal with Sanjay (burner) -->
    <Message><From>Vikram Mehta</From><To>Sanjay (Burner)</To><Body>Package ready for pickup at the Andheri warehouse. 15 kg, brown carton marked "office supplies". Suresh will be there at 6 PM.</Body><Timestamp>2026-01-10T17:00:00</Timestamp><Source>Signal</Source><Status>sent</Status></Message>
    <Message><From>Sanjay (Burner)</From><To>Vikram Mehta</To><Body>Confirmed. My guy will handle the Pune drop. Cash payment on delivery — ₹12 lakh. Tell Suresh to bring the van, not the bike this time.</Body><Timestamp>2026-01-10T17:15:00</Timestamp><Source>Signal</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Sanjay (Burner)</To><Body>Done. After this, we need to cool off for 2 weeks. I heard ED is watching the Andheri area. Switch to the Navi Mumbai location from next month.</Body><Timestamp>2026-01-10T17:30:00</Timestamp><Source>Signal</Source><Status>sent</Status></Message>
    <Message><From>Sanjay (Burner)</From><To>Vikram Mehta</To><Body>Agreed. I'll destroy this SIM after tonight. New number coming via the Chennai network — Hawala Agent 2 will pass it to you.</Body><Timestamp>2026-01-10T22:40:00</Timestamp><Source>Signal</Source><Status>received</Status></Message>

    <!-- Deepak (banker) WhatsApp -->
    <Message><From>Vikram Mehta</From><To>Deepak Joshi</To><Body>Deepak, need the RTGS processed today. ₹22 lakh to Oceanic Trade Solutions, account 09876543210, IFSC HDFC0001234. Mark it as "import advance for electronic components".</Body><Timestamp>2026-01-10T10:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Deepak Joshi</From><To>Vikram Mehta</To><Body>Done. Transaction ref: RTGS/2026/1234567. Our compliance flagged it initially but I overrode it — said it's a recurring trade payment. Be careful, the new compliance officer is asking questions.</Body><Timestamp>2026-01-10T13:00:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Deepak Joshi</To><Body>Thanks. Your commission — ₹3.5L — will come through the usual shell. Priya is handling it via Mauritius. Expected by Friday.</Body><Timestamp>2026-01-10T13:15:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <!-- Farid Hassan (Dubai) Telegram -->
    <Message><From>Vikram Mehta</From><To>Farid Hassan</To><Body>Farid, ₹25 lakh coming via Gujarat hawala this week. Please confirm once you receive the equivalent AED. Need it converted to gold bars at Emirates Gold Exchange.</Body><Timestamp>2026-01-11T15:45:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Farid Hassan</From><To>Vikram Mehta</To><Body>Received confirmation from the hawala agent. Will process through Emirates Gold. 3 x 100g bars at current rates. Shipping via diplomatic pouch contact — no customs. ETA 5 days.</Body><Timestamp>2026-01-11T18:00:00</Timestamp><Source>Telegram</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Farid Hassan</To><Body>Excellent. Al-Rashid's team will handle the gold custody? I trust they have the vault capacity. Also, I need a meeting in Dubai next month — visa arrangements as usual?</Body><Timestamp>2026-01-11T18:30:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>

    <!-- Li Wei (China) WeChat -->
    <Message><From>Vikram Mehta</From><To>Li Wei</To><Body>Mr. Li, the advance payment for the Shenzhen shipment — $95,000 — is being routed through our Hong Kong intermediary. Should arrive in your HSBC account by Jan 13. Invoice #SZ2026-0089.</Body><Timestamp>2026-01-12T10:00:00</Timestamp><Source>WeChat</Source><Status>sent</Status></Message>
    <Message><From>Li Wei</From><To>Vikram Mehta</To><Body>Payment received. Shipment of 500 units (electronic components, model XR-7720) departing Shenzhen port on Jan 16. Bill of lading and customs clearance attached. Lead time: 18 days to Mumbai port.</Body><Timestamp>2026-01-13T08:00:00</Timestamp><Source>WeChat</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Li Wei</To><Body>Perfect. Arjun at Global Freight will handle clearance at JNPT. Separate matter — can you arrange a quote for 2000 units? We're expanding the Kolkata warehouse.</Body><Timestamp>2026-01-13T09:30:00</Timestamp><Source>WeChat</Source><Status>sent</Status></Message>

    <!-- Ananya (lawyer) WhatsApp -->
    <Message><From>Vikram Mehta</From><To>Ananya Singh</To><Body>Ananya, I need you to register a new company — "Meridian Enterprises Pvt Ltd" — with me as silent director through the Seychelles trust. Can you get the incorporation done in 10 days?</Body><Timestamp>2026-01-12T09:15:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Ananya Singh</From><To>Vikram Mehta</To><Body>I can fast-track it. The Seychelles trust takes 7 days, then the Indian subsidiary registration is another 5. Total cost including my fee: ₹8.5 lakh. I'll need your passport scans and a nominee director from our usual list.</Body><Timestamp>2026-01-12T10:00:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Ananya Singh</To><Body>Go ahead. Use the same nominee — Mr. Thomas George. And make sure the registered address is different from Oceanic Trade. We don't want the Registrar flagging common directors.</Body><Timestamp>2026-01-12T10:15:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <!-- Suresh Yadav (mule) -->
    <Message><From>Vikram Mehta</From><To>Suresh Yadav</To><Body>Suresh, tomorrow morning pick up ₹12 lakh cash from the Andheri warehouse. Take it to the Gujarat hawala agent — address coming via Signal. Do NOT use your registered phone for this.</Body><Timestamp>2026-01-12T20:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Suresh Yadav</From><To>Vikram Mehta</To><Body>Bhai, I don't have the van. It's in service. Can I take two trips on the bike?</Body><Timestamp>2026-01-12T20:15:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Suresh Yadav</To><Body>No — too risky splitting cash on a bike. Use Sanjay's car. He'll arrange it. And Suresh, if anyone stops you, the cover story is you're delivering wedding gifts. Understood?</Body><Timestamp>2026-01-12T20:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <!-- Mohammed Al-Rashid (gold vault) -->
    <Message><From>Mohammed Al-Rashid</From><To>Vikram Mehta</To><Body>Mr. Mehta, confirming receipt of 300g gold from Farid's consignment. Secured in vault #A-17 at Emirates Gold Exchange under your coded account "DT-ALPHA-7". Monthly storage fee: AED 5,000.</Body><Timestamp>2026-01-14T14:00:00</Timestamp><Source>Telegram</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Mohammed Al-Rashid</To><Body>Acknowledged. I'll be in Dubai Feb 10-15. Let's meet to discuss expanding the arrangement. I want to move 2kg/month through your vault. Fee negotiation in person.</Body><Timestamp>2026-01-14T14:30:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>

    <!-- Evidence destruction -->
    <Message><From>Vikram Mehta</From><To>Priya Sharma</To><Body>URGENT: I just heard from Ananya that ED got a tip about Oceanic Trade. Delete all WhatsApp chats about hawala routes NOW. Tell Deepak to purge the RTGS records from his branch system.</Body><Timestamp>2026-01-15T08:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Priya Sharma</From><To>Vikram Mehta</To><Body>Deleting now. But the Signal messages are auto-delete. I'll factory reset my backup phone. What about the crypto wallets?</Body><Timestamp>2026-01-15T08:05:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Vikram Mehta</From><To>Priya Sharma</To><Body>Tell Rajan to move all USDT to the Monero bridge immediately. XMR is untraceable. And burn the Lithuanian KYC documents — physical copies too.</Body><Timestamp>2026-01-15T08:10:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <!-- Risk Intel: Counter-intelligence, deception & evidence fabrication -->
    <Message><From>Vikram Mehta</From><To>Sanjay (Burner)</To><Body>Listen carefully — if ED interrogates you, say we were at the Mumbai Charity Gala on Jan 10th evening. I have arranged fake entry passes through Ananya. She also has the event photos digitally edited with correct date stamps to place us there. Memorise the guest list I sent last week.</Body><Timestamp>2026-01-14T23:00:00</Timestamp><Source>Signal</Source><Status>sent</Status></Message>
    <Message><From>Vikram Mehta</From><To>Priya Sharma</To><Body>Plant a false paper trail — send ₹5 lakh from Oceanic Trade to Clean Water Foundation NGO. Make it look like a CSR donation to offset the Dubai transfers on the books. Also prepare a fake board resolution approving the donation dated December 2025. Backdate Ananya's signature too.</Body><Timestamp>2026-01-14T11:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Vikram Mehta</From><To>Rajan Patel</To><Body>Create a decoy blockchain trail — send 2 BTC from a clean wallet to Coinbase (known exchange), then claw it back via a privacy bridge. If Chainalysis picks it up, investigators will chase the wrong trail for weeks. Make the txn look like a legitimate investment purchase.</Body><Timestamp>2026-01-14T16:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Vikram Mehta</From><To>Deepak Joshi</To><Body>Deepak, I need you to create a parallel set of SWIFT records showing the Dubai transfers were for legitimate consulting. Use the InfoTech Solutions letterhead — Ananya has the company stamp. Backdate everything to November. This is CRITICAL — if RBI cross-references, the originals will be purged and only yours will remain.</Body><Timestamp>2026-01-14T17:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Vikram Mehta</From><To>Arjun Reddy</To><Body>Arjun, change the bill of lading for the Shenzhen shipment. Show contents as automotive spare parts instead of electronics. Ensure the customs declaration at JNPT uses HS code 8708.99, not the original one. If anyone checks, the paper trail must not match the original order from Li Wei.</Body><Timestamp>2026-01-13T15:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Vikram Mehta</From><To>Farid Hassan</To><Body>Farid, if Emirates Gold Exchange gets audited, the cover story is that the gold was purchased by a Dubai-based jewellery retailer — Al Noor Jewellers. I have arranged matching purchase invoices. Destroy the original receipts that reference my coded account DT-ALPHA-7.</Body><Timestamp>2026-01-14T19:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
  </Messages>

  <Emails>
    <Email><From>vikram.mehta@oceanictrade.in</From><To>farid.hassan@dubaitrade.ae</To><Subject>RE: Invoice #DIT-2026-0047 — Advance Payment</Subject><Body>Dear Mr. Hassan,\n\nPlease find attached the revised invoice for consulting services rendered by Dubai International Trading LLC. Amount: USD 75,000. Payment will be wired from our Mauritius subsidiary (Oceanic Ventures Ltd, account at SBM Bank Mauritius) within 3 business days.\n\nKindly confirm receipt.\n\nRegards,\nVikram Mehta\nDirector, Oceanic Trade Solutions Pvt Ltd</Body><Timestamp>2026-01-11T16:00:00</Timestamp><Source>ProtonMail</Source></Email>
    <Email><From>vikram.mehta@oceanictrade.in</From><To>liwei@shenzhensupply.cn</To><Subject>PO #SZ2026-0089 — Electronic Components Order</Subject><Body>Dear Mr. Li,\n\nThis confirms our purchase order for 500 units of model XR-7720 at USD 190/unit. Total: USD 95,000.\n\nPayment routed via Hong Kong intermediary (Asia Pacific Trading HK Ltd, HSBC account ending 4478).\n\nShipping: CIF Mumbai (JNPT Port). Customs clearance by Global Freight Logistics.\n\nRegards,\nVikram Mehta</Body><Timestamp>2026-01-12T11:00:00</Timestamp><Source>ProtonMail</Source></Email>
    <Email><From>ananya.singh.legal@outlook.com</From><To>vikram.mehta@oceanictrade.in</To><Subject>Meridian Enterprises — Incorporation Documents</Subject><Body>Dear Vikram,\n\nAttached are the draft incorporation documents for Meridian Enterprises Pvt Ltd. Structure:\n- Holding: Seychelles trust (Pacific Rim Holdings)\n- Nominee Director: Thomas George (passport enclosed)\n- Registered Agent: Singh &amp; Associates\n\nPlease review the articles of association and confirm. We need your signature on 3 documents — sending courier tomorrow.\n\nCost breakdown:\n- Seychelles trust setup: ₹3.5L\n- Indian subsidiary: ₹2.0L\n- Nominee director fee: ₹1.5L\n- Legal fees: ₹1.5L\n\nTotal: ₹8.5L\n\nRegards,\nAnanya Singh\nPartner, Singh &amp; Associates</Body><Timestamp>2026-01-13T11:00:00</Timestamp><Source>Outlook</Source></Email>
    <Email><From>vikram.mehta@oceanictrade.in</From><To>arjun.reddy@globalfreight.in</To><Subject>JNPT Clearance — Shenzhen Shipment SZ2026-0089</Subject><Body>Arjun,\n\nExpecting a container from Shenzhen — 500 units of electronic components, Bill of Lading TBD (~Jan 18). Please handle customs clearance at JNPT. Declare as "electronic components for resale" under HS 8542.39.\n\nThe actual goods may not match — don't inspect, just clear it. Usual arrangement. Fee: ₹2.5L.\n\nVikram</Body><Timestamp>2026-01-13T14:00:00</Timestamp><Source>ProtonMail</Source></Email>
  </Emails>

  <WebHistory>
    <WebVisit><URL>https://www.binance.com/en/trade/BTC_USDT</URL><Title>BTC/USDT Trading — Binance</Title><Timestamp>2026-01-10T14:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://localbitcoins.com/buy-bitcoins-online/</URL><Title>Buy Bitcoin P2P — LocalBitcoins</Title><Timestamp>2026-01-10T14:10:00</Timestamp></WebVisit>
    <WebVisit><URL>https://wasabiwallet.io/</URL><Title>Wasabi Wallet — Bitcoin Privacy</Title><Timestamp>2026-01-10T14:15:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.protonmail.com/login</URL><Title>ProtonMail Login</Title><Timestamp>2026-01-11T08:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.emiratesgold.ae/vault-services</URL><Title>Emirates Gold — Vault Services</Title><Timestamp>2026-01-11T16:30:00</Timestamp></WebVisit>
    <WebVisit><URL>https://tronscan.org/#/</URL><Title>TRON Blockchain Explorer</Title><Timestamp>2026-01-11T17:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.mca.gov.in/mcafoportal/companyLLPMasterData.do</URL><Title>MCA — Company Master Data</Title><Timestamp>2026-01-12T09:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.sbmbank.mu/corporate-banking/trade-finance</URL><Title>SBM Bank Mauritius — Trade Finance</Title><Timestamp>2026-01-12T09:30:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.google.com/search?q=ED+enforcement+directorate+raids+Mumbai+2026</URL><Title>ED raids Mumbai — Google Search</Title><Timestamp>2026-01-14T19:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.monero.how/how-to-buy-monero</URL><Title>How to Buy Monero (XMR) — Privacy Coin</Title><Timestamp>2026-01-15T08:15:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.okx.com/account/register</URL><Title>OKX — Create Account</Title><Timestamp>2026-01-11T10:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://duckduckgo.com/?q=how+to+factory+reset+phone+permanently+delete+data</URL><Title>Factory reset delete data — DuckDuckGo</Title><Timestamp>2026-01-15T08:20:00</Timestamp></WebVisit>
  </WebHistory>

  <Locations>
    <Location><Latitude>19.0760</Latitude><Longitude>72.8777</Longitude><Address>BKC, Bandra, Mumbai — Oceanic Trade Solutions office</Address><Timestamp>2026-01-10T08:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.1196</Latitude><Longitude>72.8464</Longitude><Address>Andheri West, Mumbai — Cash warehouse</Address><Timestamp>2026-01-10T18:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>23.0225</Latitude><Longitude>72.5714</Longitude><Address>Ahmedabad, Gujarat — Hawala agent office</Address><Timestamp>2026-01-11T09:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.0760</Latitude><Longitude>72.8777</Longitude><Address>National Commerce Bank, BKC Branch</Address><Timestamp>2026-01-12T11:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>18.5204</Latitude><Longitude>73.8567</Longitude><Address>Pune — Delivery drop point</Address><Timestamp>2026-01-13T14:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.0330</Latitude><Longitude>73.0297</Longitude><Address>Navi Mumbai — Alternate safe location</Address><Timestamp>2026-01-14T10:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>28.6139</Latitude><Longitude>77.2090</Longitude><Address>Delhi — Meeting with contact (undisclosed)</Address><Timestamp>2026-01-14T16:00:00</Timestamp><Source>GPS</Source></Location>
  </Locations>

  <InstalledApplications>
    <Application><Name>WhatsApp Messenger</Name><PackageName>com.whatsapp</PackageName><Version>24.1.85</Version></Application>
    <Application><Name>Telegram</Name><PackageName>ph.telegra.Telegraph</PackageName><Version>10.8.0</Version></Application>
    <Application><Name>ProtonMail</Name><PackageName>ch.protonmail.protonmail</PackageName><Version>4.0.2</Version></Application>
    <Application><Name>Signal</Name><PackageName>org.whispersystems.signal</PackageName><Version>7.1.0</Version></Application>
    <Application><Name>HDFC Bank</Name><PackageName>com.snapwork.hdfc</PackageName><Version>10.5.0</Version></Application>
    <Application><Name>Binance</Name><PackageName>com.binance.dev</PackageName><Version>2.85.0</Version></Application>
    <Application><Name>NordVPN</Name><PackageName>com.nordvpn.android</PackageName><Version>6.2.1</Version></Application>
    <Application><Name>TOR Browser</Name><PackageName>org.torproject.torbrowser</PackageName><Version>13.0.3</Version></Application>
    <Application><Name>Secure Erase</Name><PackageName>com.securerase.wipe</PackageName><Version>3.2.0</Version></Application>
    <Application><Name>WeChat</Name><PackageName>com.tencent.mm</PackageName><Version>8.0.45</Version></Application>
  </InstalledApplications>

  <Accounts>
    <Account><Service>ProtonMail</Service><Username>vikram.mehta</Username><Email>vikram.mehta@oceanictrade.in</Email></Account>
    <Account><Service>Binance</Service><Username>vkm_trade_2024</Username><Email>vikram.alt.finance@gmail.com</Email></Account>
    <Account><Service>Telegram</Service><Username>vikram_ops</Username></Account>
    <Account><Service>WhatsApp</Service><Username>+91-98765-43210</Username></Account>
    <Account><Service>NordVPN</Service><Username>vkm_secure@protonmail.com</Username></Account>
  </Accounts>

</CellebriteReport>
""")


# ═══════════════════════════════════════════════════════
# DEVICE 2 — Priya Sharma (Hawala Broker / Accomplice)
# ═══════════════════════════════════════════════════════

PRIYA_XML = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>
  <DeviceInfo>
    <DeviceName>Priya's iPhone 15 Pro</DeviceName>
    <Model>iPhone 15 Pro (A3102)</Model>
    <OSVersion>iOS 17.3</OSVersion>
    <IMEI>351234567890123</IMEI>
    <SerialNumber>IP15PRIYA2025</SerialNumber>
    <PhoneNumber>+91-99887-65432</PhoneNumber>
    <ExtractionType>Advanced Logical</ExtractionType>
    <ExtractionDate>2026-01-16T14:00:00</ExtractionDate>
  </DeviceInfo>

  <Contacts>
    <Contact><Name>Vikram Mehta</Name><PhoneNumber>+91-98765-43210</PhoneNumber><Email>vikram.mehta@oceanictrade.in</Email><Organization>Oceanic Trade Solutions</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Deepak Ji (Bank)</Name><PhoneNumber>+91-77665-43210</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Gujarat Agent</Name><PhoneNumber>+91-79000-55544</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Chennai Agent</Name><PhoneNumber>+91-44000-66655</PhoneNumber><Source>Signal</Source></Contact>
    <Contact><Name>Farid (Dubai)</Name><PhoneNumber>+971-50-1234567</PhoneNumber><Source>Telegram</Source></Contact>
    <Contact><Name>Mauritius Bank</Name><PhoneNumber>+230-23456789</PhoneNumber><Email>corporate@sbmbank.mu</Email><Source>Phonebook</Source></Contact>
    <Contact><Name>Rajan Tech</Name><PhoneNumber>+91-88776-54321</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Suresh (Runner)</Name><PhoneNumber>+91-72000-11122</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Kavya Iyer (accountant)</Name><PhoneNumber>+91-90000-78899</PhoneNumber><Email>kavya.iyer.ca@gmail.com</Email><Organization>Iyer &amp; Associates CA</Organization><Source>Phonebook</Source></Contact>
  </Contacts>

  <CallLogs>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-98765-43210</PhoneNumber><ContactName>Vikram Mehta</ContactName><Duration>342</Duration><Timestamp>2026-01-10T09:15:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-79000-55544</PhoneNumber><ContactName>Gujarat Agent</ContactName><Duration>210</Duration><Timestamp>2026-01-10T10:30:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-44000-66655</PhoneNumber><ContactName>Chennai Agent</ContactName><Duration>180</Duration><Timestamp>2026-01-10T11:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+230-23456789</PhoneNumber><ContactName>Mauritius Bank</ContactName><Duration>540</Duration><Timestamp>2026-01-10T12:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+971-50-1234567</PhoneNumber><ContactName>Farid (Dubai)</ContactName><Duration>300</Duration><Timestamp>2026-01-11T17:30:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-90000-78899</PhoneNumber><ContactName>Kavya Iyer</ContactName><Duration>420</Duration><Timestamp>2026-01-12T10:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-72000-11122</PhoneNumber><ContactName>Suresh (Runner)</ContactName><Duration>90</Duration><Timestamp>2026-01-12T18:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-98765-43210</PhoneNumber><ContactName>Vikram Mehta</ContactName><Duration>180</Duration><Timestamp>2026-01-13T08:00:00</Timestamp><Source>Phone</Source></CallLog>
  </CallLogs>

  <Messages>
    <Message><From>Priya Sharma</From><To>Gujarat Agent</To><Body>Bhai, ₹25 lakh cash coming via Suresh tomorrow. Split into 5 packets of ₹5L each, bundled in newspaper. Conversion at today's rate — Dubai AED. Farid's handler collects in Sharjah. Ref code: ALPHA-7-JAN.</Body><Timestamp>2026-01-10T10:45:00</Timestamp><Source>Signal</Source><Status>sent</Status></Message>
    <Message><From>Gujarat Agent</From><To>Priya Sharma</To><Body>Confirmed. My rate is 2.5% on the full amount. Cash ready for Suresh pickup at shop #44, Manek Chowk, Ahmedabad. Tell him to ask for "Jignesh bhai" and say the code word "Digital Trail".</Body><Timestamp>2026-01-10T11:30:00</Timestamp><Source>Signal</Source><Status>received</Status></Message>
    <Message><From>Priya Sharma</From><To>Chennai Agent</To><Body>Need a secondary route — Chennai to Colombo. ₹10 lakh for next week. Can you handle? The Gujarat route is getting hot after the ED raids.</Body><Timestamp>2026-01-10T11:15:00</Timestamp><Source>Signal</Source><Status>sent</Status></Message>
    <Message><From>Chennai Agent</From><To>Priya Sharma</To><Body>Chennai-Colombo is risky right now. Customs increased checks at Rameshwaram. I can do Chennai-Singapore via my fishing boat contact. Takes 3 days but 100% safe. Rate: 3%.</Body><Timestamp>2026-01-10T13:00:00</Timestamp><Source>Signal</Source><Status>received</Status></Message>

    <Message><From>Priya Sharma</From><To>Kavya Iyer</To><Body>Kavya, I need the Oceanic Trade books cleaned for FY25. All hawala entries should be shown as "consulting income from Dubai International Trading". Invoices attached. The Mauritius transfers go under "inter-company loans".</Body><Timestamp>2026-01-12T10:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Kavya Iyer</From><To>Priya Sharma</To><Body>Priya, this is getting dangerous. The amounts don't match the GST filings. If the auditors dig, the invoices from Dubai International have no corresponding service agreements. I need to manufacture those documents. Extra ₹5L for my risk.</Body><Timestamp>2026-01-12T11:00:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Priya Sharma</From><To>Kavya Iyer</To><Body>Fine. ₹5L. Create backdated service agreements for "market research and trade advisory". Use the template from last year. Vikram will sign as Director of Oceanic Trade.</Body><Timestamp>2026-01-12T11:15:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <Message><From>Priya Sharma</From><To>Mauritius Bank</To><Body>Requesting wire transfer of USD 75,000 from Oceanic Ventures Ltd (acct #MU-OVL-2024-889) to Dubai International Trading LLC (Emirates NBD, acct #AE-DIT-2025-112). Purpose: consulting fees per invoice DIT-2026-0047.</Body><Timestamp>2026-01-10T12:30:00</Timestamp><Source>ProtonMail</Source><Status>sent</Status></Message>

    <Message><From>Priya Sharma</From><To>Vikram Mehta</To><Body>Vikram, all done. Gujarat hawala: ₹25L dispatched, Farid confirmed. Mauritius wire: USD 75K sent. Books will be clean by end of month — Kavya is handling it. Total commission paid: ₹6.25L to Gujarat + ₹5L to Kavya.</Body><Timestamp>2026-01-13T08:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <Message><From>Priya Sharma</From><To>Vikram Mehta</To><Body>VIKRAM — deleting everything now. My backup phone is factory reset. Signal chats set to auto-delete 24h. Should I also wipe the Mauritius bank correspondence?</Body><Timestamp>2026-01-15T08:07:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <!-- Risk Intel: Fabricated cover stories and parallel books -->
    <Message><From>Priya Sharma</From><To>Gujarat Agent</To><Body>Jigneshbhai, if anyone from ED or police comes asking about the transfers, tell them it was payment for gold jewellery for my cousin's wedding. I have arranged matching jeweler receipts from Zaveri Bazaar. The amounts match exactly — ₹25L split across 5 bills. Memorise the wedding date: 15 December 2025.</Body><Timestamp>2026-01-13T14:00:00</Timestamp><Source>Signal</Source><Status>sent</Status></Message>
    <Message><From>Priya Sharma</From><To>Vikram Mehta</To><Body>I have set up a parallel set of accounting books for Oceanic Trade showing only legitimate export transactions. The fake import documents from Shenzhen match the actual shipment dates. If the auditor sees these first, they will not look deeper. Kavya has also planted matching GST returns in the Tally system.</Body><Timestamp>2026-01-14T09:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Priya Sharma</From><To>Kavya Iyer</To><Body>Kavya, one more thing — create a fake consultancy agreement between Oceanic Trade and Dubai International Trading. Date it July 2025. Terms: USD 125,000 per year for market research in MENA region. This covers all the wire transfers. Make sure the signatures look authentic.</Body><Timestamp>2026-01-14T10:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
  </Messages>

  <Emails>
    <Email><From>priya.sharma.offshore@protonmail.com</From><To>corporate@sbmbank.mu</To><Subject>Wire Transfer Request — Oceanic Ventures Ltd</Subject><Body>Dear SBM Bank Corporate Team,\n\nPlease process the following wire transfer:\nFrom: Oceanic Ventures Ltd, Account MU-OVL-2024-889\nTo: Dubai International Trading LLC, Emirates NBD, AE-DIT-2025-112\nAmount: USD 75,000\nPurpose: Consulting fees — Invoice DIT-2026-0047\n\nAuthorized signatory: Priya Sharma (Director)\n\nRegards,\nPriya Sharma</Body><Timestamp>2026-01-10T12:45:00</Timestamp><Source>ProtonMail</Source></Email>
    <Email><From>priya.sharma.offshore@protonmail.com</From><To>kavya.iyer.ca@gmail.com</To><Subject>Oceanic Trade — FY25 Books Reconciliation</Subject><Body>Kavya,\n\nAttached are the invoices from Dubai International Trading that need to be entered against Oceanic Trade Solutions' books.\n\nKey entries:\n1. Invoice DIT-2026-0041: USD 50,000 (Q3 advisory)\n2. Invoice DIT-2026-0047: USD 75,000 (Q4 advisory)\n3. Inter-company loan from Oceanic Ventures (Mauritius): ₹1.2 Cr\n\nAll supporting documents to be backdated to respective quarters. GST implications: reverse charge mechanism for cross-border services.\n\nThanks,\nPriya</Body><Timestamp>2026-01-12T11:30:00</Timestamp><Source>ProtonMail</Source></Email>
  </Emails>

  <WebHistory>
    <WebVisit><URL>https://www.sbmbank.mu/login</URL><Title>SBM Bank Mauritius — Login</Title><Timestamp>2026-01-10T12:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.rbi.org.in/scripts/NotificationUser.aspx</URL><Title>RBI — Hawala regulations</Title><Timestamp>2026-01-10T14:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.enforcementdirectorate.gov.in/</URL><Title>Enforcement Directorate India</Title><Timestamp>2026-01-14T20:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://duckduckgo.com/?q=PMLA+maximum+penalty+India+2026</URL><Title>PMLA penalty — DuckDuckGo</Title><Timestamp>2026-01-14T20:30:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.protonmail.com/secure-email</URL><Title>ProtonMail — Secure Email</Title><Timestamp>2026-01-15T07:00:00</Timestamp></WebVisit>
  </WebHistory>

  <Locations>
    <Location><Latitude>19.0544</Latitude><Longitude>72.8406</Longitude><Address>Dadar, Mumbai — Priya's residence</Address><Timestamp>2026-01-10T07:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>23.0225</Latitude><Longitude>72.5714</Longitude><Address>Manek Chowk, Ahmedabad — Hawala hub</Address><Timestamp>2026-01-11T09:30:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.0760</Latitude><Longitude>72.8777</Longitude><Address>BKC, Mumbai — Oceanic Trade office</Address><Timestamp>2026-01-12T09:00:00</Timestamp><Source>GPS</Source></Location>
  </Locations>

  <InstalledApplications>
    <Application><Name>WhatsApp</Name><PackageName>com.whatsapp</PackageName><Version>24.2.10</Version></Application>
    <Application><Name>Signal</Name><PackageName>org.whispersystems.signal</PackageName><Version>7.1.0</Version></Application>
    <Application><Name>ProtonMail</Name><PackageName>ch.protonmail.protonmail</PackageName><Version>4.0.2</Version></Application>
    <Application><Name>Telegram</Name><PackageName>ph.telegra.Telegraph</PackageName><Version>10.8.0</Version></Application>
    <Application><Name>SBM Bank</Name><PackageName>mu.sbmbank.app</PackageName><Version>2.1.0</Version></Application>
    <Application><Name>Tally ERP</Name><PackageName>com.tally.erp9</PackageName><Version>9.0</Version></Application>
  </InstalledApplications>

  <Accounts>
    <Account><Service>ProtonMail</Service><Username>priya.sharma.offshore</Username><Email>priya.sharma.offshore@protonmail.com</Email></Account>
    <Account><Service>WhatsApp</Service><Username>+91-99887-65432</Username></Account>
    <Account><Service>Signal</Service><Username>priya_hawala</Username></Account>
    <Account><Service>SBM Bank</Service><Username>OVL_Director_01</Username><Email>priya.sharma@oceanicventures.mu</Email></Account>
  </Accounts>

</CellebriteReport>
""")


# ═══════════════════════════════════════════════════════
# DEVICE 3 — Rajan Patel (Crypto Laundering Specialist)
# ═══════════════════════════════════════════════════════

RAJAN_XML = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>
  <DeviceInfo>
    <DeviceName>Rajan's MacBook Pro</DeviceName>
    <Model>MacBook Pro 16-inch (M3 Pro)</Model>
    <OSVersion>macOS 14.3 Sonoma</OSVersion>
    <IMEI>N/A</IMEI>
    <SerialNumber>MBPRAJAN2025</SerialNumber>
    <ExtractionType>File System — Disk Image</ExtractionType>
    <ExtractionDate>2026-01-17T09:00:00</ExtractionDate>
  </DeviceInfo>

  <Contacts>
    <Contact><Name>Vikram M (Boss)</Name><PhoneNumber>+91-98765-43210</PhoneNumber><Email>vikram.mehta@oceanictrade.in</Email><Source>Telegram</Source></Contact>
    <Contact><Name>Priya S</Name><PhoneNumber>+91-99887-65432</PhoneNumber><Source>Telegram</Source></Contact>
    <Contact><Name>Suresh Mule</Name><PhoneNumber>+91-72000-11122</PhoneNumber><Source>Telegram</Source></Contact>
    <Contact><Name>Crypto OTC Dealer (HK)</Name><PhoneNumber>+852-9876-5432</PhoneNumber><Email>otcdesk@cryptovault.hk</Email><Organization>CryptoVault OTC HK</Organization><Source>Telegram</Source></Contact>
    <Contact><Name>Ivan Petrov (Mixer)</Name><PhoneNumber>+7-999-123-4567</PhoneNumber><Email>ivan.p@darkweb.onion</Email><Source>Telegram</Source></Contact>
  </Contacts>

  <Messages>
    <Message><From>Rajan Patel</From><To>Vikram M (Boss)</To><Body>Vikram, BTC tumbling complete. 15 BTC split into 5 wallets via Wasabi CoinJoin. Here are the wallet addresses:\n1. bc1q7ky8dm3r4f5t6a3f — 3.0 BTC\n2. bc1qm9x2p7k8s1d2e — 3.0 BTC\n3. bc1qp4r6n5w2v7h7g — 3.0 BTC\n4. bc1qt8w3j9c4m1k1j — 3.0 BTC\n5. bc1qv2s5b8x6q0n5m — 3.0 BTC\n\nTotal: 15 BTC (~$637,500 at current rates). Ready for P2P OTC conversion.</Body><Timestamp>2026-01-10T15:12:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>

    <Message><From>Rajan Patel</From><To>Crypto OTC Dealer (HK)</To><Body>Need to offload 15 BTC through your P2P desk. Split across 5 sells, max 3 BTC each. Cash equivalent needed — preferably USDT on Tron network. My TRC20 wallets:\n- TWj4kV8r...x9mP (wallet A)\n- TN8rQ2tY...d3vK (wallet B)\n- TDp5wR6s...f7hL (wallet C)\nRate: 0.5% below spot acceptable. Timeline: 48h.</Body><Timestamp>2026-01-11T10:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Crypto OTC Dealer (HK)</From><To>Rajan Patel</To><Body>Can process. Our OTC desk handles up to 50 BTC/day. AML checks are minimal for amounts under 4 BTC per trade. I'll queue 5 separate transactions through different buyer pools. Total USDT: ~$635,000. Deposit to your TRC20 wallets within 36 hours. KYC — we'll use the Lithuanian company credentials you provided last time.</Body><Timestamp>2026-01-11T11:30:00</Timestamp><Source>Telegram</Source><Status>received</Status></Message>

    <Message><From>Rajan Patel</From><To>Ivan Petrov (Mixer)</To><Body>Ivan, need another batch through your mixer. Incoming: 8 ETH (from the previous operation). Output wallets — 4 separate addresses, 2 ETH each. Delay: 72h minimum between inputs and outputs. Fee: 3%.</Body><Timestamp>2026-01-12T15:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Ivan Petrov (Mixer)</From><To>Rajan Patel</To><Body>Da. Send ETH to 0x7F3a...d2E4. I will process through 12 intermediate wallets across 3 chains (ETH mainnet, Polygon, Arbitrum). Clean outputs in 72h. My mixer has 99.9% delinking rate. No chain analysis tool can trace back.</Body><Timestamp>2026-01-12T16:00:00</Timestamp><Source>Telegram</Source><Status>received</Status></Message>

    <Message><From>Rajan Patel</From><To>Vikram M (Boss)</To><Body>Update: Binance mule account (Suresh's) permanently banned after KYC flag. I've created 3 new accounts on OKX, Bybit, and KuCoin using:\n- Lithuanian shell company docs (BlockSecure EU OÜ)\n- VPN set to Singapore\n- Hardware device fingerprint spoofed with Multilogin\n\nAll 3 passed automated KYC. Manual review pending on OKX — should clear in 24h.</Body><Timestamp>2026-01-11T14:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>

    <Message><From>Rajan Patel</From><To>Vikram M (Boss)</To><Body>EMERGENCY: Converting all USDT to Monero NOW per your instructions. Using fixed-rate swap on ChangeNow (no KYC).\nUSDT balance: $635,000\nXMR received: ~3,968 XMR at $160/XMR\nXMR wallet: 4AdUnd...xB7Qf (cold storage — Ledger device)\n\nThis is completely untraceable. Even with subpoena to exchanges, the Monero chain is opaque.</Body><Timestamp>2026-01-15T08:30:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>

    <Message><From>Rajan Patel</From><To>Suresh Mule</To><Body>Suresh, your Binance account is burned. Don't log in again — they'll report to FIU-India. I've saved the transaction history backup. Wipe the Binance app from your phone. New arrangement — Vikram will explain.</Body><Timestamp>2026-01-11T15:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>

    <!-- Risk Intel: Decoy blockchain trails and fake KYC -->
    <Message><From>Rajan Patel</From><To>Vikram M (Boss)</To><Body>Decoy trail created as instructed. Sent 2 BTC from a fresh wallet to a Coinbase deposit address, then routed it back through 3 mixing hops on Tornado Cash. Chainalysis will show a legitimate exchange deposit — they will waste weeks getting Coinbase compliance to respond. Meanwhile our real funds are safe in XMR cold storage.</Body><Timestamp>2026-01-14T20:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Rajan Patel</From><To>Crypto OTC Dealer (HK)</To><Body>Important — if anyone from Indian FIU or INTERPOL contacts CryptoVault, the cover story is: BlockSecure EU was purchasing cryptocurrency mining equipment. I have created fake purchase orders and delivery receipts from a Finnish hardware vendor called Nordic Mining Solutions. The invoice amounts match our OTC trades exactly.</Body><Timestamp>2026-01-13T10:00:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
    <Message><From>Rajan Patel</From><To>Ivan Petrov (Mixer)</To><Body>Ivan, I also need you to generate a fake audit trail showing the mixed ETH came from legitimate DeFi yield farming on Aave. Create dummy smart contract interactions backdated to October 2025. This will give us plausible deniability if blockchain forensics companies trace the funds back.</Body><Timestamp>2026-01-13T16:30:00</Timestamp><Source>Telegram</Source><Status>sent</Status></Message>
  </Messages>

  <Emails>
    <Email><From>rajan.crypto.dev@tutanota.com</From><To>otcdesk@cryptovault.hk</To><Subject>OTC Trade Request — 15 BTC</Subject><Body>Hi CryptoVault Team,\n\nRequesting OTC conversion of 15 BTC to USDT (TRC20).\n\nSeller entity: BlockSecure Labs (India)\nKYC docs: Previously submitted (Lithuanian subsidiary — BlockSecure EU OÜ, Reg #14892301)\n\nPreferred rate: Spot minus 0.5%\nTimeline: 48h\nDestination wallets: 3 TRC20 addresses (will confirm via encrypted channel)\n\nRegards,\nRajan Patel\nCTO, BlockSecure Labs</Body><Timestamp>2026-01-11T10:30:00</Timestamp><Source>Tutanota</Source></Email>
    <Email><From>rajan.crypto.dev@tutanota.com</From><To>vikram.mehta@oceanictrade.in</To><Subject>Crypto Operations Report — Week of Jan 10</Subject><Body>Vikram,\n\nWeekly crypto ops summary:\n\n1. BTC Tumbling: 15 BTC tumbled via Wasabi CoinJoin — 5 clean wallets\n2. OTC Conversion: 15 BTC → ~$635K USDT via CryptoVault HK\n3. ETH Mixing: 8 ETH ($19,200) sent to Ivan's mixer — output in 72h\n4. Exchange Accounts: Suresh's Binance banned; 3 new accounts (OKX/Bybit/KuCoin) created with Lithuanian KYC\n5. OPSEC: All operations routed through VPN (Singapore) + Tor\n\nTotal laundered this week: ~$656,700\nCumulative since November: ~$2.8M\n\nPending: Monero conversion when you give the signal.\n\nRajan</Body><Timestamp>2026-01-14T18:00:00</Timestamp><Source>Tutanota</Source></Email>
  </Emails>

  <WebHistory>
    <WebVisit><URL>https://wasabiwallet.io/#download</URL><Title>Wasabi Wallet Download</Title><Timestamp>2026-01-10T13:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.blockchain.com/explorer/transactions/btc</URL><Title>BTC Transaction Explorer</Title><Timestamp>2026-01-10T15:30:00</Timestamp></WebVisit>
    <WebVisit><URL>https://tronscan.org/#/token/USDT</URL><Title>USDT on TRON</Title><Timestamp>2026-01-11T09:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://changenow.io/exchange/usdt-to-xmr</URL><Title>USDT to XMR — ChangeNow</Title><Timestamp>2026-01-15T08:25:00</Timestamp></WebVisit>
    <WebVisit><URL>https://multilogin.com/</URL><Title>Multilogin — Browser Fingerprint Spoofing</Title><Timestamp>2026-01-11T13:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.okx.com/trade-spot/btc-usdt</URL><Title>OKX BTC/USDT Spot</Title><Timestamp>2026-01-11T14:30:00</Timestamp></WebVisit>
  </WebHistory>

  <Locations>
    <Location><Latitude>19.1176</Latitude><Longitude>72.9060</Longitude><Address>Powai, Mumbai — Rajan's apartment / BlockSecure Labs office</Address><Timestamp>2026-01-10T08:00:00</Timestamp><Source>WiFi</Source></Location>
    <Location><Latitude>19.0760</Latitude><Longitude>72.8777</Longitude><Address>BKC, Mumbai — Meeting with Vikram</Address><Timestamp>2026-01-14T17:00:00</Timestamp><Source>WiFi</Source></Location>
  </Locations>

  <InstalledApplications>
    <Application><Name>Telegram Desktop</Name><PackageName>org.telegram.desktop</PackageName><Version>4.12.0</Version></Application>
    <Application><Name>Tutanota</Name><PackageName>com.tutanota.tutanota</PackageName><Version>3.122.0</Version></Application>
    <Application><Name>Wasabi Wallet</Name><PackageName>io.wasabiwallet</PackageName><Version>2.0.6</Version></Application>
    <Application><Name>MetaMask</Name><PackageName>io.metamask</PackageName><Version>11.9.0</Version></Application>
    <Application><Name>Multilogin</Name><PackageName>com.multilogin</PackageName><Version>6.3</Version></Application>
    <Application><Name>Tor Browser</Name><PackageName>org.torproject.torbrowser</PackageName><Version>13.0.3</Version></Application>
    <Application><Name>NordVPN</Name><PackageName>com.nordvpn.android</PackageName><Version>6.2.1</Version></Application>
    <Application><Name>Visual Studio Code</Name><PackageName>com.microsoft.vscode</PackageName><Version>1.86.0</Version></Application>
  </InstalledApplications>

  <Accounts>
    <Account><Service>Tutanota</Service><Username>rajan.crypto.dev</Username><Email>rajan.crypto.dev@tutanota.com</Email></Account>
    <Account><Service>Telegram</Service><Username>rajan_blocksecure</Username></Account>
    <Account><Service>Binance</Service><Username>blocksecure_eu</Username><Email>admin@blocksecure.eu</Email></Account>
    <Account><Service>OKX</Service><Username>bseu_trade01</Username><Email>trade@blocksecure.eu</Email></Account>
    <Account><Service>MetaMask</Service><Username>0x7F3a...d2E4</Username></Account>
  </Accounts>

</CellebriteReport>
""")


# ═══════════════════════════════════════════════════════
# DEVICE 4 — Deepak Joshi (Bank Insider)
# ═══════════════════════════════════════════════════════

DEEPAK_XML = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>
  <DeviceInfo>
    <DeviceName>Deepak's Samsung S24</DeviceName>
    <Model>Samsung Galaxy S24 Ultra</Model>
    <OSVersion>Android 14 (One UI 6.1)</OSVersion>
    <IMEI>356789012345678</IMEI>
    <SerialNumber>SGS24DEEPAK25</SerialNumber>
    <PhoneNumber>+91-77665-43210</PhoneNumber>
    <ExtractionType>Full File System</ExtractionType>
    <ExtractionDate>2026-01-18T11:00:00</ExtractionDate>
  </DeviceInfo>

  <Contacts>
    <Contact><Name>Vikram Boss</Name><PhoneNumber>+91-98765-43210</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Priya Ma'am</Name><PhoneNumber>+91-99887-65432</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Branch Manager (self)</Name><PhoneNumber>+91-77665-43210</PhoneNumber><Email>deepak.joshi@ncbank.in</Email><Organization>National Commerce Bank</Organization><Source>Phonebook</Source></Contact>
    <Contact><Name>Compliance Officer - Mumbai</Name><PhoneNumber>+91-22000-54321</PhoneNumber><Email>compliance.mumbai@ncbank.in</Email><Source>Phonebook</Source></Contact>
    <Contact><Name>RBI Contact</Name><PhoneNumber>+91-22000-11111</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Neha Kapoor (girlfriend)</Name><PhoneNumber>+91-98000-77766</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>CA Sharma</Name><PhoneNumber>+91-98000-44433</PhoneNumber><Email>ca.sharma@taxhelp.in</Email><Source>Phonebook</Source></Contact>
  </Contacts>

  <CallLogs>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-98765-43210</PhoneNumber><ContactName>Vikram Boss</ContactName><Duration>128</Duration><Timestamp>2026-01-10T11:45:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-99887-65432</PhoneNumber><ContactName>Priya Ma'am</ContactName><Duration>95</Duration><Timestamp>2026-01-10T14:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-22000-54321</PhoneNumber><ContactName>Compliance Officer</ContactName><Duration>300</Duration><Timestamp>2026-01-10T15:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-98765-43210</PhoneNumber><ContactName>Vikram Boss</ContactName><Duration>75</Duration><Timestamp>2026-01-12T20:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-98000-44433</PhoneNumber><ContactName>CA Sharma</ContactName><Duration>600</Duration><Timestamp>2026-01-13T19:00:00</Timestamp><Source>Phone</Source></CallLog>
  </CallLogs>

  <Messages>
    <Message><From>Vikram Boss</From><To>Deepak Joshi</To><Body>Deepak, RTGS ₹22 lakh to Oceanic Trade Solutions. Account 09876543210, IFSC HDFC0001234. Mark it "import advance for electronic components". Process before 3 PM — Priya is waiting on confirmation.</Body><Timestamp>2026-01-10T10:30:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Deepak Joshi</From><To>Vikram Boss</To><Body>Processed. Ref: RTGS/2026/1234567. Compliance flagged it — the beneficiary account had 3 large credits this month. I marked it as recurring trade payment and approved. But Vikram, the new compliance officer Rakesh is asking about the Oceanic Trade account pattern. We need to space out the transactions.</Body><Timestamp>2026-01-10T13:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Deepak Joshi</From><To>Vikram Boss</To><Body>Also — I overrode the STR (Suspicious Transaction Report) alert. FIU-India won't get a notification. But if Rakesh files one independently, I can't stop it. Consider routing through a different bank next time.</Body><Timestamp>2026-01-10T13:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <Message><From>Deepak Joshi</From><To>Neha Kapoor</To><Body>Neha, I booked the Maldives trip. 5 nights at Soneva Fushi — ₹18 lakh total 😄. My "consulting income" is doing well this year. Don't ask where it's from though 😅</Body><Timestamp>2026-01-11T21:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Neha Kapoor</From><To>Deepak Joshi</To><Body>Deepak!!! That's amazing!! ❤️ But seriously, a bank manager booking ₹18L trips? Be careful. Your salary is only ₹1.5L/month right?</Body><Timestamp>2026-01-11T21:15:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Deepak Joshi</From><To>Neha Kapoor</To><Body>Don't worry, it's all managed. I've got stocks and "investments". CA Sharma handles everything — no paper trail. Enjoy the trip, that's all 😘</Body><Timestamp>2026-01-11T21:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <Message><From>Deepak Joshi</From><To>CA Sharma</To><Body>Sharma ji, my total "consulting" income this year is around ₹45 lakh. All in cash. I need it shown as stock market gains in my ITR. Can you create the trading statements? I'll pay your fee — ₹2L.</Body><Timestamp>2026-01-13T19:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>CA Sharma</From><To>Deepak Joshi</To><Body>Deepak sahab, ₹45L in "consulting" from a bank manager? 😂 I'll do it but this is the last year. The IT department is using AI for flagging mismatches now. I'll show it as intraday trading profits — short-term capital gains, 15% tax paid through advance tax. Clean paperwork.</Body><Timestamp>2026-01-13T20:00:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>

    <Message><From>Vikram Boss</From><To>Deepak Joshi</To><Body>Deepak, ED has a tip about Oceanic Trade. They might subpoena bank records. Can you purge the RTGS transaction logs from the branch system? At least the manual override entries.</Body><Timestamp>2026-01-15T08:20:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Deepak Joshi</From><To>Vikram Boss</To><Body>Vikram, I can't purge RTGS from the core banking system — it's centralized at HQ. But I can delete my manual override notes from the branch compliance folder. The digital logs are harder — calling my IT guy.</Body><Timestamp>2026-01-15T08:45:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <!-- Risk Intel: Fabricated bank records and false documentation -->
    <Message><From>Deepak Joshi</From><To>Vikram Boss</To><Body>Done — I have created a duplicate set of RTGS transaction records showing the ₹22L went to InfoTech Solutions Pvt Ltd for IT infrastructure upgrade. The backup logs at the branch now reflect this version. If RBI audits, they will find my altered version first. The original override notes are shredded.</Body><Timestamp>2026-01-15T09:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Deepak Joshi</From><To>CA Sharma</To><Body>Sharma ji, I also need you to create backdated invoices from InfoTech Solutions Pvt Ltd. Three invoices: ₹8L, ₹7L, ₹7L — all for banking software customization services. Dates: October, November, December 2025. These need to match the RTGS records I have altered. Use the company stamp I gave you last month.</Body><Timestamp>2026-01-15T10:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Deepak Joshi</From><To>Neha Kapoor</To><Body>Neha, if anyone from the bank compliance team asks you about me, just say I was at home with you on Jan 10 evening. I was actually at a meeting in BKC but they must not know about that. Please remember — home, dinner, Netflix. That is our story.</Body><Timestamp>2026-01-15T11:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
  </Messages>

  <WebHistory>
    <WebVisit><URL>https://www.ncbank.in/netbanking</URL><Title>NCB Net Banking</Title><Timestamp>2026-01-10T09:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.sonevafushi.com/book</URL><Title>Soneva Fushi Maldives Booking</Title><Timestamp>2026-01-11T20:30:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.incometax.gov.in/iec/foportal/</URL><Title>Income Tax e-Filing Portal</Title><Timestamp>2026-01-13T18:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.google.com/search?q=can+bank+manager+delete+RTGS+transaction+logs</URL><Title>Delete RTGS logs — Google</Title><Timestamp>2026-01-15T08:50:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.google.com/search?q=PMLA+section+3+punishment+bank+employee</URL><Title>PMLA bank employee — Google</Title><Timestamp>2026-01-15T09:00:00</Timestamp></WebVisit>
  </WebHistory>

  <Locations>
    <Location><Latitude>19.0596</Latitude><Longitude>72.8295</Longitude><Address>Prabhadevi, Mumbai — Deepak's apartment</Address><Timestamp>2026-01-10T07:30:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.0760</Latitude><Longitude>72.8777</Longitude><Address>BKC, Mumbai — National Commerce Bank branch</Address><Timestamp>2026-01-10T09:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.0176</Latitude><Longitude>72.8562</Longitude><Address>Worli, Mumbai — Luxury car showroom</Address><Timestamp>2026-01-12T14:00:00</Timestamp><Source>GPS</Source></Location>
  </Locations>

  <InstalledApplications>
    <Application><Name>WhatsApp</Name><PackageName>com.whatsapp</PackageName><Version>24.1.90</Version></Application>
    <Application><Name>HDFC Trading</Name><PackageName>com.hdfcsec.tms</PackageName><Version>5.2.0</Version></Application>
    <Application><Name>NCB Mobile Banking</Name><PackageName>com.ncbank.mobile</PackageName><Version>8.3.1</Version></Application>
    <Application><Name>Instagram</Name><PackageName>com.instagram.android</PackageName><Version>322.0</Version></Application>
    <Application><Name>MakeMyTrip</Name><PackageName>com.makemytrip</PackageName><Version>12.7.0</Version></Application>
  </InstalledApplications>

  <Accounts>
    <Account><Service>WhatsApp</Service><Username>+91-77665-43210</Username></Account>
    <Account><Service>NCB Net Banking</Service><Username>deepak.joshi.bm</Username><Email>deepak.joshi@ncbank.in</Email></Account>
    <Account><Service>HDFC Securities</Service><Username>DJ_TRADES_2024</Username></Account>
  </Accounts>

</CellebriteReport>
""")


# ═══════════════════════════════════════════════════════
# DEVICE 5 — Suresh Yadav (Cash Mule / Courier)
# ═══════════════════════════════════════════════════════

SURESH_XML = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>
  <DeviceInfo>
    <DeviceName>Suresh's Redmi Note 13</DeviceName>
    <Model>Redmi Note 13 Pro</Model>
    <OSVersion>Android 13 (MIUI 14)</OSVersion>
    <IMEI>358901234567890</IMEI>
    <SerialNumber>RNSRY2025X</SerialNumber>
    <PhoneNumber>+91-72000-11122</PhoneNumber>
    <ExtractionType>Full File System</ExtractionType>
    <ExtractionDate>2026-01-19T08:00:00</ExtractionDate>
  </DeviceInfo>

  <Contacts>
    <Contact><Name>Vikram Sir</Name><PhoneNumber>+91-98765-43210</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Priya Ma'am</Name><PhoneNumber>+91-99887-65432</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Sanjay Bhai</Name><PhoneNumber>+91-70001-99988</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Rajan Sir (tech)</Name><PhoneNumber>+91-88776-54321</PhoneNumber><Source>Telegram</Source></Contact>
    <Contact><Name>Gujarat Hawala</Name><PhoneNumber>+91-79000-55544</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Andheri Warehouse</Name><PhoneNumber>+91-22000-88877</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Maa (Mother)</Name><PhoneNumber>+91-97000-33344</PhoneNumber><Source>Phonebook</Source></Contact>
    <Contact><Name>Pune Drop Contact</Name><PhoneNumber>+91-20000-55566</PhoneNumber><Source>Phonebook</Source></Contact>
  </Contacts>

  <CallLogs>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-98765-43210</PhoneNumber><ContactName>Vikram Sir</ContactName><Duration>92</Duration><Timestamp>2026-01-13T07:30:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-79000-55544</PhoneNumber><ContactName>Gujarat Hawala</ContactName><Duration>45</Duration><Timestamp>2026-01-13T08:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-22000-88877</PhoneNumber><ContactName>Andheri Warehouse</ContactName><Duration>30</Duration><Timestamp>2026-01-13T09:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-70001-99988</PhoneNumber><ContactName>Sanjay Bhai</ContactName><Duration>55</Duration><Timestamp>2026-01-13T10:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-20000-55566</PhoneNumber><ContactName>Pune Drop Contact</ContactName><Duration>70</Duration><Timestamp>2026-01-13T15:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-97000-33344</PhoneNumber><ContactName>Maa (Mother)</ContactName><Duration>300</Duration><Timestamp>2026-01-13T20:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-88776-54321</PhoneNumber><ContactName>Rajan Sir</ContactName><Duration>40</Duration><Timestamp>2026-01-11T15:10:00</Timestamp><Source>Phone</Source></CallLog>
  </CallLogs>

  <Messages>
    <Message><From>Vikram Sir</From><To>Suresh Yadav</To><Body>Suresh, tomorrow 7 AM pickup at Andheri warehouse. ₹12 lakh cash in brown carton. Drive to Gujarat — Manek Chowk, Ahmedabad. Ask for Jignesh bhai at shop #44. Code word: "Digital Trail". Do NOT stop on the highway for anyone.</Body><Timestamp>2026-01-12T20:00:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>
    <Message><From>Suresh Yadav</From><To>Vikram Sir</To><Body>Ok sir. But I don't have the van, it's in service center. Can I split on bike?</Body><Timestamp>2026-01-12T20:15:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Vikram Sir</From><To>Suresh Yadav</To><Body>No bike. Take Sanjay bhai's car. He'll give you the keys tonight. Cover story if stopped: wedding gifts. No phone calls during transit. GPS off.</Body><Timestamp>2026-01-12T20:30:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>

    <Message><From>Suresh Yadav</From><To>Sanjay Bhai</To><Body>Sanjay bhai, Vikram sir said to take your car tomorrow for the Gujarat run. Can I pick up the keys tonight at your place?</Body><Timestamp>2026-01-12T21:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Sanjay Bhai</From><To>Suresh Yadav</To><Body>Come after 10 PM. Car is the white Swift. Full tank. Don't scratch it 😂. Also — after Gujarat, there's a Pune delivery on the way back. Priya ma'am will send you the address. Extra ₹10K for you.</Body><Timestamp>2026-01-12T21:15:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>

    <Message><From>Suresh Yadav</From><To>Gujarat Hawala</To><Body>Jignesh bhai? This is Suresh. Coming tomorrow morning with the package from Mumbai. "Digital Trail". Priya ma'am sent me. What time should I reach?</Body><Timestamp>2026-01-12T22:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Gujarat Hawala</From><To>Suresh Yadav</To><Body>Come between 10 AM and 12 PM. Park behind the building, not in front. Count the cash before leaving — I don't want issues later. You'll get receipt code for Priya.</Body><Timestamp>2026-01-12T22:20:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>

    <Message><From>Suresh Yadav</From><To>Vikram Sir</To><Body>Sir, Gujarat delivery done. Jignesh bhai counted ₹12L. Receipt code: ALPHA-7-JAN-DONE. Now heading to Pune for the second drop as Sanjay bhai said.</Body><Timestamp>2026-01-13T11:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Suresh Yadav</From><To>Pune Drop Contact</To><Body>Bhai, ETA 3 PM. Package from Sanjay bhai. Where exactly in Pune? Send me the location pin.</Body><Timestamp>2026-01-13T12:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Pune Drop Contact</From><To>Suresh Yadav</To><Body>SMS Market, Shivajinagar. Shop 22B. Don't come inside if you see police bikes outside. Circle and come back in 30 mins. Payment: ₹8L cash on delivery.</Body><Timestamp>2026-01-13T12:15:00</Timestamp><Source>WhatsApp</Source><Status>received</Status></Message>

    <Message><From>Suresh Yadav</From><To>Maa (Mother)</To><Body>Maa, I sent ₹50,000 to your account. Please use it for the hospital bills. I'm working hard. Don't worry about me. Will visit next month. 🙏</Body><Timestamp>2026-01-13T20:30:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>

    <Message><From>Rajan Sir (tech)</From><To>Suresh Yadav</To><Body>Suresh, your Binance account got banned. Delete the app NOW. Don't login again — they'll report to the government. Vikram sir will arrange something else.</Body><Timestamp>2026-01-11T15:05:00</Timestamp><Source>Telegram</Source><Status>received</Status></Message>

    <!-- Risk Intel: Cover stories and misdirection -->
    <Message><From>Suresh Yadav</From><To>Vikram Sir</To><Body>Sir, on the way to Gujarat I got stopped at a toll naka. Showed them the fake invoice for wedding caterer supplies that Priya ma'am gave me. They checked the carton, saw the newspaper wrapping, and let me go. The cover story worked perfectly — nobody suspects wedding supplies.</Body><Timestamp>2026-01-13T09:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
    <Message><From>Suresh Yadav</From><To>Sanjay Bhai</To><Body>Bhai, Vikram sir told me to keep a second phone with only clean contacts — family and some office people. If police ever check my regular phone, I should swap to the clean one. He said you arranged it? When can I pick it up?</Body><Timestamp>2026-01-14T08:00:00</Timestamp><Source>WhatsApp</Source><Status>sent</Status></Message>
  </Messages>

  <WebHistory>
    <WebVisit><URL>https://www.google.com/maps/dir/Mumbai/Ahmedabad</URL><Title>Mumbai to Ahmedabad — Google Maps</Title><Timestamp>2026-01-12T22:30:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.google.com/maps/dir/Ahmedabad/Pune</URL><Title>Ahmedabad to Pune — Google Maps</Title><Timestamp>2026-01-13T11:40:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.binance.com/en/my/dashboard</URL><Title>Binance Dashboard</Title><Timestamp>2026-01-11T14:00:00</Timestamp></WebVisit>
    <WebVisit><URL>https://www.google.com/search?q=how+to+carry+large+cash+safely+India</URL><Title>Carry large cash India — Google</Title><Timestamp>2026-01-12T19:00:00</Timestamp></WebVisit>
  </WebHistory>

  <Locations>
    <Location><Latitude>19.1360</Latitude><Longitude>72.8296</Longitude><Address>Goregaon, Mumbai — Suresh's home</Address><Timestamp>2026-01-12T22:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.1196</Latitude><Longitude>72.8464</Longitude><Address>Andheri West — Cash warehouse pickup</Address><Timestamp>2026-01-13T07:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>23.0225</Latitude><Longitude>72.5714</Longitude><Address>Manek Chowk, Ahmedabad — Hawala delivery</Address><Timestamp>2026-01-13T10:30:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>18.5204</Latitude><Longitude>73.8567</Longitude><Address>Shivajinagar, Pune — Drop delivery</Address><Timestamp>2026-01-13T15:00:00</Timestamp><Source>GPS</Source></Location>
    <Location><Latitude>19.1360</Latitude><Longitude>72.8296</Longitude><Address>Goregaon, Mumbai — Return home</Address><Timestamp>2026-01-13T22:00:00</Timestamp><Source>GPS</Source></Location>
  </Locations>

  <InstalledApplications>
    <Application><Name>WhatsApp</Name><PackageName>com.whatsapp</PackageName><Version>24.1.85</Version></Application>
    <Application><Name>Google Maps</Name><PackageName>com.google.android.apps.maps</PackageName><Version>11.80.0</Version></Application>
    <Application><Name>Telegram</Name><PackageName>ph.telegra.Telegraph</PackageName><Version>10.7.0</Version></Application>
    <Application><Name>Binance</Name><PackageName>com.binance.dev</PackageName><Version>2.85.0</Version></Application>
    <Application><Name>PhonePe</Name><PackageName>com.phonepe.app</PackageName><Version>24.1.0</Version></Application>
  </InstalledApplications>

  <Accounts>
    <Account><Service>WhatsApp</Service><Username>+91-72000-11122</Username></Account>
    <Account><Service>Binance</Service><Username>suresh_trade01</Username><Email>suresh.yadav.trade@gmail.com</Email></Account>
    <Account><Service>PhonePe</Service><Username>+91-72000-11122</Username></Account>
  </Accounts>

</CellebriteReport>
""")


# ═══════════════════════════════════════════════════════
# DEVICE 6 — Sanjay Kumar (Burner Phone Operations)
# ═══════════════════════════════════════════════════════

SANJAY_XML = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>
  <DeviceInfo>
    <DeviceName>Unknown Burner Device</DeviceName>
    <Model>Nokia 105 (TA-1569)</Model>
    <OSVersion>Nokia Series 30+</OSVersion>
    <IMEI>354321098765432</IMEI>
    <SerialNumber>NK105BURN2025</SerialNumber>
    <PhoneNumber>+91-70001-99988</PhoneNumber>
    <ExtractionType>Chip-Off</ExtractionType>
    <ExtractionDate>2026-01-20T16:00:00</ExtractionDate>
  </DeviceInfo>

  <Contacts>
    <Contact><Name>V</Name><PhoneNumber>+91-98765-43210</PhoneNumber><Source>SIM</Source></Contact>
    <Contact><Name>P</Name><PhoneNumber>+91-99887-65432</PhoneNumber><Source>SIM</Source></Contact>
    <Contact><Name>Runner</Name><PhoneNumber>+91-72000-11122</PhoneNumber><Source>SIM</Source></Contact>
    <Contact><Name>Pune Guy</Name><PhoneNumber>+91-20000-55566</PhoneNumber><Source>SIM</Source></Contact>
    <Contact><Name>Chennai 2</Name><PhoneNumber>+91-44000-66655</PhoneNumber><Source>SIM</Source></Contact>
    <Contact><Name>NM Safe</Name><PhoneNumber>+91-22000-99900</PhoneNumber><Source>SIM</Source></Contact>
    <Contact><Name>Warehouse</Name><PhoneNumber>+91-22000-88877</PhoneNumber><Source>SIM</Source></Contact>
    <Contact><Name>Police Tip</Name><PhoneNumber>+91-98000-12345</PhoneNumber><Source>SIM</Source></Contact>
  </Contacts>

  <CallLogs>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-98765-43210</PhoneNumber><ContactName>V</ContactName><Duration>89</Duration><Timestamp>2026-01-10T22:30:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-72000-11122</PhoneNumber><ContactName>Runner</ContactName><Duration>35</Duration><Timestamp>2026-01-10T22:45:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-20000-55566</PhoneNumber><ContactName>Pune Guy</ContactName><Duration>60</Duration><Timestamp>2026-01-11T07:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-44000-66655</PhoneNumber><ContactName>Chennai 2</ContactName><Duration>90</Duration><Timestamp>2026-01-11T14:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-22000-99900</PhoneNumber><ContactName>NM Safe</ContactName><Duration>45</Duration><Timestamp>2026-01-12T09:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>incoming</Direction><PhoneNumber>+91-98765-43210</PhoneNumber><ContactName>V</ContactName><Duration>45</Duration><Timestamp>2026-01-12T23:55:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-98000-12345</PhoneNumber><ContactName>Police Tip</ContactName><Duration>120</Duration><Timestamp>2026-01-14T02:00:00</Timestamp><Source>Phone</Source></CallLog>
    <CallLog><Direction>outgoing</Direction><PhoneNumber>+91-22000-88877</PhoneNumber><ContactName>Warehouse</ContactName><Duration>25</Duration><Timestamp>2026-01-10T17:30:00</Timestamp><Source>Phone</Source></CallLog>
  </CallLogs>

  <Messages>
    <Message><From>V</From><To>Sanjay Kumar</To><Body>Package at Andheri warehouse. 15 kg brown carton. Runner will be there at 6 PM. Your guy handles Pune drop.</Body><Timestamp>2026-01-10T17:00:00</Timestamp><Source>SMS</Source><Status>received</Status></Message>
    <Message><From>Sanjay Kumar</From><To>V</To><Body>My guy confirmed for Pune. ₹12 lakh cash on delivery. Runner must bring the van — bike is too risky.</Body><Timestamp>2026-01-10T17:15:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>Sanjay Kumar</From><To>Pune Guy</To><Body>Delivery tomorrow Shivajinagar. 15 kg parcel from Mumbai. Pay ₹8L cash to the delivery boy. If cops are nearby, abort and destroy this SIM.</Body><Timestamp>2026-01-11T07:05:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>Pune Guy</From><To>Sanjay Kumar</To><Body>Got it. Shop 22B open till 6 PM. Tell runner to bring exact change — I don't want counting delays. And wear a mask — CCTV outside the market.</Body><Timestamp>2026-01-11T08:00:00</Timestamp><Source>SMS</Source><Status>received</Status></Message>

    <Message><From>Sanjay Kumar</From><To>Chennai 2</To><Body>New SIM card needed. Old one is getting destroyed tonight. Priya ma'am said you'd pass the replacement number to V. Make it a Tamil Nadu number — harder to trace from Mumbai jurisdiction.</Body><Timestamp>2026-01-10T22:45:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>Chennai 2</From><To>Sanjay Kumar</To><Body>Number ready — TN prepaid, registered under fake Aadhaar. Will courier to your Navi Mumbai drop box. 3 days. Don't activate until I confirm the tower mapping is clean.</Body><Timestamp>2026-01-11T14:10:00</Timestamp><Source>SMS</Source><Status>received</Status></Message>

    <Message><From>Sanjay Kumar</From><To>NM Safe</To><Body>Navi Mumbai safe house needs to be ready by Feb. V wants to shift operations from Andheri after the ED heat. Check if the Panvel godown is still available — we need minimum 500 sq ft.</Body><Timestamp>2026-01-12T09:05:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>NM Safe</From><To>Sanjay Kumar</To><Body>Panvel godown available. ₹15K/month, no questions asked. Owner is an old contact — he'll register it under a different name. I'll set it up this week.</Body><Timestamp>2026-01-12T10:00:00</Timestamp><Source>SMS</Source><Status>received</Status></Message>

    <Message><From>Sanjay Kumar</From><To>Police Tip</To><Body>Inspector sahab, regarding our arrangement — I have some information about a rival gang operating in Thane. Drug shipment arriving Jan 18 from Goa. In exchange, I need the Andheri warehouse kept off your raid list for 2 more months. Same deal as before — ₹2L monthly.</Body><Timestamp>2026-01-14T02:05:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>Police Tip</From><To>Sanjay Kumar</To><Body>The Thane tip better be good. Last time your info was outdated. I'll keep Andheri off the list but if my seniors find out, I won't cover for you. Transfer the amount to usual GPay.</Body><Timestamp>2026-01-14T02:30:00</Timestamp><Source>SMS</Source><Status>received</Status></Message>

    <!-- Risk Intel: Fabricated intel and counter-tips -->
    <Message><From>Sanjay Kumar</From><To>Police Tip</To><Body>Inspector — about that Thane gang intel I gave you last month? Most of it was fabricated. I needed to build credibility with you so you would keep our Andheri operations off the radar. The drug shipment date was wrong on purpose — those guys are actually clean. Business is business.</Body><Timestamp>2026-01-14T03:00:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>Sanjay Kumar</From><To>V</To><Body>Boss, the cops mentioned they got an anonymous tip about our Pune delivery network. I have sent them a counter-tip through my other police contact — pointing to a warehouse in Turbhe owned by a competitor. That should buy us 2-3 weeks while they investigate the wrong place entirely.</Body><Timestamp>2026-01-14T09:00:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>Sanjay Kumar</From><To>Pune Guy</To><Body>Change of plan for the next delivery — use the back entrance of SMS Market only. I have arranged for a tea seller outside the front to act as a lookout. If he gives two short whistles, abort the drop immediately and destroy any paperwork. ₹5K monthly to the tea seller for this service.</Body><Timestamp>2026-01-14T10:00:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
    <Message><From>Sanjay Kumar</From><To>NM Safe</To><Body>Also — register the Panvel godown under the name Shree Ganesh Trading Company. I have fake GST registration papers ready. If police trace it, they will find a non-existent company. Dead end. Make sure the landlord uses only cash — no bank transfers.</Body><Timestamp>2026-01-14T11:00:00</Timestamp><Source>SMS</Source><Status>sent</Status></Message>
  </Messages>

  <Locations>
    <Location><Latitude>19.0330</Latitude><Longitude>73.0297</Longitude><Address>Navi Mumbai — Sanjay's base of operations</Address><Timestamp>2026-01-10T16:00:00</Timestamp><Source>Cell Tower</Source></Location>
    <Location><Latitude>19.1196</Latitude><Longitude>72.8464</Longitude><Address>Andheri West — Warehouse area</Address><Timestamp>2026-01-10T17:00:00</Timestamp><Source>Cell Tower</Source></Location>
    <Location><Latitude>19.1920</Latitude><Longitude>72.9510</Longitude><Address>Thane — Meeting point</Address><Timestamp>2026-01-11T11:00:00</Timestamp><Source>Cell Tower</Source></Location>
    <Location><Latitude>18.9894</Latitude><Longitude>73.1175</Longitude><Address>Panvel — Potential new safe house</Address><Timestamp>2026-01-12T14:00:00</Timestamp><Source>Cell Tower</Source></Location>
  </Locations>

  <InstalledApplications>
    <Application><Name>Default SMS</Name><PackageName>com.nokia.sms</PackageName><Version>1.0</Version></Application>
    <Application><Name>GPay</Name><PackageName>com.google.android.apps.nbu.paisa.user</PackageName><Version>2024.01</Version></Application>
  </InstalledApplications>

  <Accounts>
    <Account><Service>GPay</Service><Username>+91-70001-99988</Username></Account>
  </Accounts>

</CellebriteReport>
""")


# ═══════════════════════════════════════════════════════
# Main — Write all 6 devices
# ═══════════════════════════════════════════════════════

def main():
    print("═══════════════════════════════════════════")
    print("  Operation Digital Trail — Phase 2")
    print("  Expanded Forensic Dataset Generator")
    print("═══════════════════════════════════════════\n")

    devices = [
        ("suspect_phone",    "Vikram Mehta (Primary Suspect)",    VIKRAM_XML),
        ("accomplice_phone", "Priya Sharma (Hawala Broker)",      PRIYA_XML),
        ("crypto_laptop",    "Rajan Patel (Crypto Specialist)",   RAJAN_XML),
        ("banker_phone",     "Deepak Joshi (Bank Insider)",       DEEPAK_XML),
        ("mule_phone",       "Suresh Yadav (Cash Mule)",          SURESH_XML),
        ("burner_phone",     "Sanjay Kumar (Burner Ops)",         SANJAY_XML),
    ]

    for filename, desc, xml_content in devices:
        xml_path = DATA_DIR / f"report_{filename}.xml"
        clbe_path = DATA_DIR / f"{filename}.clbe"

        # Write raw XML
        xml_path.write_text(xml_content, encoding="utf-8")

        # Create .clbe archive (ZIP with report.xml inside)
        with zipfile.ZipFile(clbe_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("report.xml", xml_content)

        size = clbe_path.stat().st_size
        print(f"  ✓ {desc}")
        print(f"    XML:  {xml_path.name}")
        print(f"    CLBE: {clbe_path.name} ({size:,} bytes)\n")

    print("═══════════════════════════════════════════")
    print(f"  Total: {len(devices)} devices generated")
    print(f"  Output: {DATA_DIR}/")
    print("═══════════════════════════════════════════")


if __name__ == "__main__":
    main()

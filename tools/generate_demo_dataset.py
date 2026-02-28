#!/usr/bin/env python3
"""Generate a realistic synthetic Cellebrite forensic dataset (.clbe archive).

Scenario: "Operation Digital Trail"
─────────────────────────────────────
A financial fraud investigation involving a suspect (Vikram Mehta) who is
coordinating a money-laundering operation through shell companies. The phone
extraction reveals contacts, WhatsApp/Telegram messages, call logs, emails,
web history, GPS locations, and installed apps that build a compelling evidence
trail for judges to see how ForensIQ connects the dots.

Characters:
  • Vikram Mehta      — Primary suspect, runs a fake import/export firm
  • Priya Sharma      — Accomplice, handles offshore accounts (Hawala broker)
  • Rajan Patel       — IT specialist who launders crypto
  • Deepak Joshi      — Bank insider facilitating wire transfers
  • Ananya Singh      — Vikram's lawyer (possibly complicit)
  • Sanjay Kumar      — Unknown contact (burner phone comms)

Output: data/demo/suspect_phone.clbe   (ZIP archive with report.xml inside)
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path
from textwrap import dedent

# ── Resolve project root ──────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "demo"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────
# The XML report — structured like a Cellebrite extraction
# ────────────────────────────────────────────────────────

REPORT_XML = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- DEVICE INFORMATION                                 -->
  <!-- ══════════════════════════════════════════════════ -->
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

  <!-- ══════════════════════════════════════════════════ -->
  <!-- CONTACTS                                           -->
  <!-- ══════════════════════════════════════════════════ -->
  <Contacts>
    <Contact>
      <Name>Priya Sharma</Name>
      <PhoneNumber>+91-99887-65432</PhoneNumber>
      <Email>priya.sharma.offshore@protonmail.com</Email>
      <Organization>Oceanic Trade Solutions Pvt Ltd</Organization>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Rajan Patel</Name>
      <PhoneNumber>+91-88776-54321</PhoneNumber>
      <Email>rajan.crypto.dev@tutanota.com</Email>
      <Organization>BlockSecure Labs</Organization>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Deepak Joshi</Name>
      <PhoneNumber>+91-77665-43210</PhoneNumber>
      <Email>deepak.joshi.banking@gmail.com</Email>
      <Organization>National Commerce Bank</Organization>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Ananya Singh</Name>
      <PhoneNumber>+91-66554-32109</PhoneNumber>
      <Email>ananya.singh.legal@outlook.com</Email>
      <Organization>Singh &amp; Associates Law Firm</Organization>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Sanjay (Burner)</Name>
      <PhoneNumber>+91-70001-99988</PhoneNumber>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Kavita Mehta</Name>
      <PhoneNumber>+91-98765-11111</PhoneNumber>
      <Organization>Family</Organization>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Arjun Reddy</Name>
      <PhoneNumber>+91-81234-56789</PhoneNumber>
      <Email>arjun.reddy@globalfreight.in</Email>
      <Organization>Global Freight Logistics</Organization>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Meera Iyer</Name>
      <PhoneNumber>+91-90001-22334</PhoneNumber>
      <Email>meera.iyer@financewatch.org</Email>
      <Organization>Finance Watch India</Organization>
      <Source>WhatsApp</Source>
    </Contact>
    <Contact>
      <Name>Farid Hassan</Name>
      <PhoneNumber>+971-50-1234567</PhoneNumber>
      <Email>farid.hassan@dubaitrade.ae</Email>
      <Organization>Dubai International Trading LLC</Organization>
      <Source>Telegram</Source>
    </Contact>
    <Contact>
      <Name>Li Wei</Name>
      <PhoneNumber>+86-138-0013-8000</PhoneNumber>
      <Email>liwei@shenzhensupply.cn</Email>
      <Organization>Shenzhen Supply Chain Co</Organization>
      <Source>WeChat</Source>
    </Contact>
  </Contacts>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- CALL LOGS                                          -->
  <!-- ══════════════════════════════════════════════════ -->
  <CallLogs>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-99887-65432</PhoneNumber>
      <ContactName>Priya Sharma</ContactName>
      <Duration>342</Duration>
      <Timestamp>2026-01-10T09:15:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>incoming</Direction>
      <PhoneNumber>+91-77665-43210</PhoneNumber>
      <ContactName>Deepak Joshi</ContactName>
      <Duration>128</Duration>
      <Timestamp>2026-01-10T11:45:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-88776-54321</PhoneNumber>
      <ContactName>Rajan Patel</ContactName>
      <Duration>567</Duration>
      <Timestamp>2026-01-10T14:20:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-70001-99988</PhoneNumber>
      <ContactName>Sanjay (Burner)</ContactName>
      <Duration>89</Duration>
      <Timestamp>2026-01-10T22:30:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>incoming</Direction>
      <PhoneNumber>+91-99887-65432</PhoneNumber>
      <ContactName>Priya Sharma</ContactName>
      <Duration>456</Duration>
      <Timestamp>2026-01-11T08:00:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+971-50-1234567</PhoneNumber>
      <ContactName>Farid Hassan</ContactName>
      <Duration>723</Duration>
      <Timestamp>2026-01-11T15:30:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>incoming</Direction>
      <PhoneNumber>+91-66554-32109</PhoneNumber>
      <ContactName>Ananya Singh</ContactName>
      <Duration>198</Duration>
      <Timestamp>2026-01-12T09:00:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-70001-99988</PhoneNumber>
      <ContactName>Sanjay (Burner)</ContactName>
      <Duration>45</Duration>
      <Timestamp>2026-01-12T23:55:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-81234-56789</PhoneNumber>
      <ContactName>Arjun Reddy</ContactName>
      <Duration>312</Duration>
      <Timestamp>2026-01-13T10:00:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>missed</Direction>
      <PhoneNumber>+91-90001-22334</PhoneNumber>
      <ContactName>Meera Iyer</ContactName>
      <Duration>0</Duration>
      <Timestamp>2026-01-13T16:45:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>incoming</Direction>
      <PhoneNumber>+86-138-0013-8000</PhoneNumber>
      <ContactName>Li Wei</ContactName>
      <Duration>540</Duration>
      <Timestamp>2026-01-14T07:30:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
  </CallLogs>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- MESSAGES (SMS / WhatsApp / Telegram)               -->
  <!-- ══════════════════════════════════════════════════ -->
  <Messages>

    <!-- SMS -->
    <SMSMessage>
      <Direction>incoming</Direction>
      <Sender>+91-77665-43210</Sender>
      <Recipient>+91-98765-43210</Recipient>
      <Body>Wire transfer of 15L cleared to Oceanic Trade account. Ref: NCB/2026/TXN-4421. Delete this.</Body>
      <Timestamp>2026-01-10T12:00:00</Timestamp>
      <Source>SMS</Source>
    </SMSMessage>
    <SMSMessage>
      <Direction>outgoing</Direction>
      <Sender>+91-98765-43210</Sender>
      <Recipient>+91-77665-43210</Recipient>
      <Body>Good. Next batch ready on the 15th. Same routing — NCB to OTS to Dubai account. Keep it under 10L per txn.</Body>
      <Timestamp>2026-01-10T12:05:00</Timestamp>
      <Source>SMS</Source>
    </SMSMessage>
    <SMSMessage>
      <Direction>incoming</Direction>
      <Sender>+91-70001-99988</Sender>
      <Recipient>+91-98765-43210</Recipient>
      <Body>Package delivered at the warehouse. 50 units. Come collect before morning.</Body>
      <Timestamp>2026-01-10T23:00:00</Timestamp>
      <Source>SMS</Source>
    </SMSMessage>

    <!-- WhatsApp -->
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Priya Sharma</To>
      <Body>Priya, the Dubai shipment invoice is ready. I need you to route the payment through the Mauritius account first. 45 lakhs total. Split it into 3 deposits under 15L each so it doesn't flag AML systems.</Body>
      <Timestamp>2026-01-10T09:30:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_priya_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Priya Sharma</From>
      <To>Vikram Mehta</To>
      <Body>Done. I'll do the first tranche today via Hawala. The rest goes through BVI shell company — Golden Horizon Ltd. Farid's team in Dubai will confirm receipt within 48 hours.</Body>
      <Timestamp>2026-01-10T09:45:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_priya_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Priya Sharma</To>
      <Body>Perfect. Also tell Rajan to convert the remaining BTC from last month to USDT and move it to the cold wallet. I don't want it sitting on the exchange after what happened to Rajesh.</Body>
      <Timestamp>2026-01-10T10:00:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_priya_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Priya Sharma</From>
      <To>Vikram Mehta</To>
      <Body>Already told him. He's doing the swap tonight through a DEX — no KYC. Wallet address: 0x7a3B...9f2E. I'll send you the TX hash once confirmed.</Body>
      <Timestamp>2026-01-10T10:15:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_priya_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Rajan Patel</To>
      <Body>Rajan, status update on the crypto? I need the 12 BTC converted to USDT before end of week. Use the Tornado mixer for the first hop, then route through Monero before coming back to USDT.</Body>
      <Timestamp>2026-01-10T14:30:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_rajan_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Rajan Patel</From>
      <To>Vikram Mehta</To>
      <Body>On it. Already moved 5 BTC through the mixer. Using 3 intermediate wallets. Will have the full amount in USDT by Thursday. Gas fees are high so I'm batching transactions during off-peak hours (2-4 AM UTC).</Body>
      <Timestamp>2026-01-10T14:50:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_rajan_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Rajan Patel</To>
      <Body>Good. Also set up a new cold wallet — the old one is too connected to the exchange KYC. I want clean separation. Use that hardware wallet I gave you last month.</Body>
      <Timestamp>2026-01-10T15:00:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_rajan_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Deepak Joshi</To>
      <Body>Deepak, I need you to push through 3 more wire transfers this week from the NCB corporate account. Same pattern — under 10L each, beneficiary is Oceanic Trade Solutions. Can you override the compliance flag again?</Body>
      <Timestamp>2026-01-11T08:30:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_deepak_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Deepak Joshi</From>
      <To>Vikram Mehta</To>
      <Body>Getting risky. The new compliance officer is running automated checks. I can do 2 more this month max. After that we need to find another bank or use the NBFC route Ananya suggested.</Body>
      <Timestamp>2026-01-11T08:45:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_deepak_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Deepak Joshi</To>
      <Body>Fine, do the 2 transfers. I'll talk to Ananya about the NBFC shell. Also — your commission for this quarter is 8 lakhs. Priya will send it via Hawala as usual. Cash pickup at the usual spot in Andheri.</Body>
      <Timestamp>2026-01-11T09:00:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_deepak_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Ananya Singh</To>
      <Body>Ananya, we might need to set up an NBFC front. Deepak says the bank route is getting hot. Can you incorporate a new company — something in microfinance — and get NBFC registration? We need it to look completely legitimate.</Body>
      <Timestamp>2026-01-12T10:00:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_ananya_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Ananya Singh</From>
      <To>Vikram Mehta</To>
      <Body>I can set up the company through a nominee director structure. Registration takes 4-6 weeks. Name ideas: "Lakshmi Microfinance" or "Bharat Credit Solutions". I'll use the Kolkata registered office address we used before. My fee is 12L for this.</Body>
      <Timestamp>2026-01-12T10:30:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_ananya_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Ananya Singh</To>
      <Body>Go with "Bharat Credit Solutions". Also prepare backdated board resolution documents for Oceanic Trade. If ED comes asking, I want clean paper trail showing all transfers were for legitimate trade purchases.</Body>
      <Timestamp>2026-01-12T10:45:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_ananya_001</ThreadId>
    </ChatMessage>

    <!-- Telegram -->
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Farid Hassan</To>
      <Body>Farid, confirming the next consignment. 200 units of "electronics parts" shipping from Shenzhen via Dubai Free Zone. Invoice shows $180K but actual goods value is $12K. Li Wei's team handles the Chinese side. Need the over-invoiced amount ($168K) credited to our Mauritius account.</Body>
      <Timestamp>2026-01-11T16:00:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_farid_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Farid Hassan</From>
      <To>Vikram Mehta</To>
      <Body>Confirmed. Dubai Free Zone paperwork ready. I'll process the LC through Emirates Trade Bank. The over-invoiced amount will be split: 60% to Mauritius account, 40% stays in Dubai as operating capital. Shipping ETA 12 days from Shenzhen port.</Body>
      <Timestamp>2026-01-11T16:30:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_farid_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Farid Hassan</To>
      <Body>Agreed. Also — we need to rotate the shell company. Golden Horizon Ltd is getting old. Set up a new one in RAK Free Zone. Name: "Meridian Global Trading FZE". Same beneficial ownership through the BVI trust.</Body>
      <Timestamp>2026-01-11T17:00:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_farid_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Li Wei</To>
      <Body>Wei, need the next shipment BOL and customs declaration to show "industrial electronic components" worth $180,000. Real goods: mobile phone covers, value $12,000. Same Shenzhen port, same freight forwarder. Farid confirms Dubai receiving end is ready.</Body>
      <Timestamp>2026-01-14T08:00:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_liwei_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Li Wei</From>
      <To>Vikram Mehta</To>
      <Body>OK. Customs documents ready in 3 days. Using new freight company — Dragon Logistics — they don't ask questions. Payment for my commission: send to my HSBC Hong Kong account as usual. $8,500 this time.</Body>
      <Timestamp>2026-01-14T08:30:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_liwei_001</ThreadId>
    </ChatMessage>

    <!-- Group chat -->
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Priya Sharma, Rajan Patel</To>
      <Body>Team update: Q4 total throughput was 4.2 Cr through all channels combined. Crypto route handled 1.8 Cr (Rajan), Hawala/banking handled 2.4 Cr (Priya/Deepak). Target for Q1 2026 is 6 Cr. Rajan — scale the crypto route. Priya — activate the NBFC channel once Ananya finishes setup.</Body>
      <Timestamp>2026-01-13T20:00:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_group_ops</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Rajan Patel</From>
      <To>Vikram Mehta, Priya Sharma</To>
      <Body>I can do 3 Cr through crypto if we add Monero and use more DEXs. Also found a new OTC desk in Singapore — no questions asked for amounts under $50K per trade. Will test it this week.</Body>
      <Timestamp>2026-01-13T20:15:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_group_ops</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Priya Sharma</From>
      <To>Vikram Mehta, Rajan Patel</To>
      <Body>Hawala network is maxed out domestically. I'm adding 2 new agents in Gujarat and one in Kolkata. International route through Farid can handle more volume — he says 2 Cr/month is feasible through the trade invoicing scheme.</Body>
      <Timestamp>2026-01-13T20:30:00</Timestamp>
      <Source>WhatsApp</Source>
      <ThreadId>whatsapp_group_ops</ThreadId>
    </ChatMessage>

    <!-- Suspicious late-night messages -->
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Sanjay (Burner)</To>
      <Body>The Andheri warehouse — clear everything by tomorrow 6 AM. ED raid alert from my source. Move goods to the Bhiwandi unit. Burn all paper invoices.</Body>
      <Timestamp>2026-01-12T23:55:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_sanjay_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Sanjay (Burner)</From>
      <To>Vikram Mehta</To>
      <Body>On it boss. Truck arranged. Boys are loading now. Paper going into the incinerator. What about the laptops?</Body>
      <Timestamp>2026-01-13T00:10:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_sanjay_001</ThreadId>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Vikram Mehta</From>
      <To>Sanjay (Burner)</To>
      <Body>Wipe the hard drives. Use the DBAN tool I showed you — 7 pass DOD standard. Then destroy the drives physically. Take them to the Dharavi scrap dealer.</Body>
      <Timestamp>2026-01-13T00:15:00</Timestamp>
      <Source>Telegram</Source>
      <ThreadId>telegram_sanjay_001</ThreadId>
    </ChatMessage>
  </Messages>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- EMAILS                                             -->
  <!-- ══════════════════════════════════════════════════ -->
  <Emails>
    <Email>
      <From>vikram.mehta@oceanictrade.in</From>
      <To>farid.hassan@dubaitrade.ae</To>
      <CC>priya.sharma.offshore@protonmail.com</CC>
      <Subject>Invoice #OTS-2026-0042 — Electronics Consignment</Subject>
      <Body>Dear Farid,

Please find attached the commercial invoice for consignment #OTS-2026-0042.

Item: Industrial Electronic Components (PCB assemblies, microcontrollers)
Quantity: 200 units
Unit Price: $900
Total: $180,000

Payment terms: LC at sight via Emirates Trade Bank, beneficiary Oceanic Trade Solutions Pvt Ltd.

Please process the LC and share the draft for our review.

Best regards,
Vikram Mehta
Director, Oceanic Trade Solutions Pvt Ltd</Body>
      <Timestamp>2026-01-11T11:00:00</Timestamp>
      <Attachment>Invoice_OTS_2026_0042.pdf</Attachment>
      <Attachment>Packing_List_OTS_0042.xlsx</Attachment>
    </Email>
    <Email>
      <From>ananya.singh.legal@outlook.com</From>
      <To>vikram.mehta@oceanictrade.in</To>
      <Subject>RE: New Company Incorporation — Bharat Credit Solutions</Subject>
      <Body>Vikram,

As discussed, I've initiated the incorporation process for Bharat Credit Solutions Pvt Ltd.

Key details:
- Registered office: 14/2 Park Street, Kolkata 700016
- Nominee Director: Suresh Agarwal (my associate, clean record)
- Authorized capital: Rs 1 Crore
- NBFC license application will follow once incorporation is complete

I've backdated the board resolution for Oceanic Trade as requested — shows approval for "international trade purchases" of Rs 50L per quarter. Keeping original docs at my office safe.

My invoice for legal services (Rs 12L) is attached. Please arrange payment through the usual channel.

— Ananya Singh
Partner, Singh &amp; Associates</Body>
      <Timestamp>2026-01-12T14:00:00</Timestamp>
      <Attachment>BCS_Incorporation_Application.pdf</Attachment>
      <Attachment>OTS_Board_Resolution_Backdated.pdf</Attachment>
    </Email>
    <Email>
      <From>deepak.joshi.banking@gmail.com</From>
      <To>vikram.mehta@oceanictrade.in</To>
      <Subject>Transfer confirmations — Jan batch</Subject>
      <Body>Vikram,

Confirmed transfers:
1. NCB/2026/TXN-4421 — Rs 9,50,000 to Oceanic Trade Solutions (10 Jan)
2. NCB/2026/TXN-4435 — Rs 8,75,000 to Oceanic Trade Solutions (11 Jan)
3. NCB/2026/TXN-4448 — Rs 9,25,000 to Oceanic Trade Solutions (12 Jan)

All three passed through compliance without flags. I manually approved them under the "existing business relationship" exception.

Note: New compliance officer (Meera Iyer from Finance Watch) joined last week. She's sharp. I recommend reducing frequency for next month.

Expecting my commission as discussed. Andheri pickup point works, Thursday after 7 PM.

— Deepak</Body>
      <Timestamp>2026-01-12T18:00:00</Timestamp>
    </Email>
    <Email>
      <From>rajan.crypto.dev@tutanota.com</From>
      <To>vikram.mehta@oceanictrade.in</To>
      <Subject>Crypto ops report — Week 2 Jan 2026</Subject>
      <Body>V,

Weekly crypto operations summary:

Conversions completed:
- 5.2 BTC → 3,400 XMR (via Atomic swap, no intermediary)
- 3,400 XMR → 195,000 USDT (via multiple DEX trades across Uniswap, SushiSwap)
- Remaining 6.8 BTC pending — will complete by Thursday

Wallet status:
- Hot wallet (exchange): 0.5 BTC (operational buffer)
- Cold wallet (Ledger): 195,000 USDT + 6.8 BTC
- Mixer output pending: 2.1 BTC (3 more confirmations needed)

OpSec notes:
- Used Tor + VPN chain for all exchange interactions
- New hardware wallet set up as requested — seed phrase stored at secure location
- Destroyed the old Trezor (physically hammered + acid bath)

Total laundered this week: ~Rs 1.8 Cr equivalent

— R</Body>
      <Timestamp>2026-01-13T02:00:00</Timestamp>
    </Email>
    <Email>
      <From>vikram.mehta@oceanictrade.in</From>
      <To>liwei@shenzhensupply.cn</To>
      <CC>farid.hassan@dubaitrade.ae</CC>
      <Subject>Purchase Order PO-2026-CN-018</Subject>
      <Body>Dear Mr. Li Wei,

Please find enclosed our Purchase Order PO-2026-CN-018 for the following:

Description: Industrial Electronic Components
Quantity: 200 units
Declared value: $180,000 (as per attached proforma invoice)

Shipping details:
- Origin: Shenzhen Port, China
- Destination: Jebel Ali Free Zone, Dubai, UAE
- Consignee: Meridian Global Trading FZE (c/o Farid Hassan)
- Freight forwarder: Dragon Logistics Shenzhen

Please confirm production and shipping timeline.

Regards,
Vikram Mehta
Oceanic Trade Solutions</Body>
      <Timestamp>2026-01-14T09:00:00</Timestamp>
      <Attachment>PO_2026_CN_018.pdf</Attachment>
      <Attachment>Proforma_Invoice_CN018.pdf</Attachment>
    </Email>
  </Emails>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- WEB HISTORY                                        -->
  <!-- ══════════════════════════════════════════════════ -->
  <WebHistory>
    <WebVisit>
      <URL>https://www.binance.com/en/trade/BTC_USDT</URL>
      <Title>BTC/USDT Trading | Binance</Title>
      <VisitCount>47</VisitCount>
      <LastVisited>2026-01-14T03:20:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://app.uniswap.org/swap</URL>
      <Title>Uniswap DEX — Token Swap</Title>
      <VisitCount>23</VisitCount>
      <LastVisited>2026-01-13T22:00:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://www.tornadocash.io</URL>
      <Title>Tornado Cash — Privacy Solution for Ethereum</Title>
      <VisitCount>8</VisitCount>
      <LastVisited>2026-01-12T01:15:00</LastVisited>
      <Source>Tor Browser</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://www.hawalatoday.com/rates</URL>
      <Title>Hawala Exchange Rates — Live</Title>
      <VisitCount>15</VisitCount>
      <LastVisited>2026-01-11T20:00:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://www.mca.gov.in/mcafoportal/companyLLPMasterData.do</URL>
      <Title>MCA — Company/LLP Master Data</Title>
      <VisitCount>6</VisitCount>
      <LastVisited>2026-01-12T11:00:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://www.rakez.com/en/set-up-your-business</URL>
      <Title>RAK Free Zone — Set Up Your Business</Title>
      <VisitCount>4</VisitCount>
      <LastVisited>2026-01-12T15:30:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://etherscan.io/address/0x7a3B4c5D6e7F8a9B0c1D2e3F4a5B6c7D8e9f2E</URL>
      <Title>Address 0x7a3B...9f2E | Etherscan</Title>
      <VisitCount>31</VisitCount>
      <LastVisited>2026-01-14T02:55:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://www.protonmail.com/login</URL>
      <Title>Proton Mail — Login</Title>
      <VisitCount>52</VisitCount>
      <LastVisited>2026-01-14T08:00:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://web.telegram.org</URL>
      <Title>Telegram Web</Title>
      <VisitCount>38</VisitCount>
      <LastVisited>2026-01-14T07:00:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://dban.org</URL>
      <Title>DBAN — Darik's Boot and Nuke</Title>
      <VisitCount>3</VisitCount>
      <LastVisited>2026-01-13T00:20:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://www.ed.gov.in/enforcement-directorate</URL>
      <Title>Enforcement Directorate — Government of India</Title>
      <VisitCount>9</VisitCount>
      <LastVisited>2026-01-13T14:00:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
    <WebVisit>
      <URL>https://www.moneycontrol.com/commodity/gold-price.html</URL>
      <Title>Gold Price Today — Moneycontrol</Title>
      <VisitCount>18</VisitCount>
      <LastVisited>2026-01-14T06:00:00</LastVisited>
      <Source>Chrome</Source>
    </WebVisit>
  </WebHistory>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- LOCATIONS (GPS)                                    -->
  <!-- ══════════════════════════════════════════════════ -->
  <Locations>
    <Location>
      <Latitude>19.1196</Latitude>
      <Longitude>72.8464</Longitude>
      <Address>Andheri West, Mumbai — Near warehouse district</Address>
      <Timestamp>2026-01-10T22:45:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>19.1726</Latitude>
      <Longitude>72.9467</Longitude>
      <Address>Bhiwandi Industrial Area, Thane</Address>
      <Timestamp>2026-01-13T05:30:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>19.0760</Latitude>
      <Longitude>72.8777</Longitude>
      <Address>National Commerce Bank, BKC Branch, Mumbai</Address>
      <Timestamp>2026-01-11T10:00:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>19.0596</Latitude>
      <Longitude>72.8295</Longitude>
      <Address>Juhu Beach Road, Mumbai — Meeting point</Address>
      <Timestamp>2026-01-11T19:30:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>19.1400</Latitude>
      <Longitude>72.8700</Longitude>
      <Address>Andheri East, Mumbai — Hotel Orchid, Room 412</Address>
      <Timestamp>2026-01-12T14:00:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>19.0180</Latitude>
      <Longitude>72.8291</Longitude>
      <Address>Dharavi Industrial Area, Mumbai</Address>
      <Timestamp>2026-01-13T10:30:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>19.0989</Latitude>
      <Longitude>72.8736</Longitude>
      <Address>Singh &amp; Associates Law Office, Bandra, Mumbai</Address>
      <Timestamp>2026-01-12T09:30:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>28.6139</Latitude>
      <Longitude>77.2090</Longitude>
      <Address>Connaught Place, New Delhi — Airport transit</Address>
      <Timestamp>2026-01-14T14:00:00</Timestamp>
      <Source>GPS</Source>
    </Location>
  </Locations>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- INSTALLED APPLICATIONS                             -->
  <!-- ══════════════════════════════════════════════════ -->
  <InstalledApplications>
    <Application>
      <Name>WhatsApp Messenger</Name>
      <PackageName>com.whatsapp</PackageName>
      <Version>2.26.1.4</Version>
    </Application>
    <Application>
      <Name>Telegram</Name>
      <PackageName>org.telegram.messenger</PackageName>
      <Version>10.8.1</Version>
    </Application>
    <Application>
      <Name>Signal Private Messenger</Name>
      <PackageName>org.thoughtcrime.securesms</PackageName>
      <Version>7.2.3</Version>
    </Application>
    <Application>
      <Name>ProtonMail</Name>
      <PackageName>ch.protonmail.android</PackageName>
      <Version>4.1.0</Version>
    </Application>
    <Application>
      <Name>Binance</Name>
      <PackageName>com.binance.dev</PackageName>
      <Version>2.89.1</Version>
    </Application>
    <Application>
      <Name>Trust Wallet</Name>
      <PackageName>com.wallet.crypto.trustapp</PackageName>
      <Version>12.1.0</Version>
    </Application>
    <Application>
      <Name>Tor Browser</Name>
      <PackageName>org.torproject.torbrowser</PackageName>
      <Version>13.0.8</Version>
    </Application>
    <Application>
      <Name>NordVPN</Name>
      <PackageName>com.nordvpn.android</PackageName>
      <Version>6.30.1</Version>
    </Application>
    <Application>
      <Name>Orbot: Tor for Android</Name>
      <PackageName>org.torproject.android</PackageName>
      <Version>17.2.1</Version>
    </Application>
    <Application>
      <Name>Google Pay</Name>
      <PackageName>com.google.android.apps.nbu.paisa.user</PackageName>
      <Version>230.1.1</Version>
    </Application>
    <Application>
      <Name>PhonePe</Name>
      <PackageName>com.phonepe.app</PackageName>
      <Version>24.1.0</Version>
    </Application>
    <Application>
      <Name>Calculator Vault (Hidden Photos)</Name>
      <PackageName>com.enchantedcloud.calculatorvault</PackageName>
      <Version>3.8.2</Version>
    </Application>
    <Application>
      <Name>Secure File Manager</Name>
      <PackageName>com.securefilemanager.app</PackageName>
      <Version>2.1.0</Version>
    </Application>
    <Application>
      <Name>Chrome</Name>
      <PackageName>com.android.chrome</PackageName>
      <Version>121.0.6167.178</Version>
    </Application>
  </InstalledApplications>

  <!-- ══════════════════════════════════════════════════ -->
  <!-- ACCOUNTS                                           -->
  <!-- ══════════════════════════════════════════════════ -->
  <Accounts>
    <Account>
      <Service>Google</Service>
      <Username>vikram.mehta.personal</Username>
      <Email>vikram.mehta.personal@gmail.com</Email>
    </Account>
    <Account>
      <Service>ProtonMail</Service>
      <Username>vm_secure</Username>
      <Email>vm.secure.2025@protonmail.com</Email>
    </Account>
    <Account>
      <Service>Binance</Service>
      <Username>vmehta_trade</Username>
      <Email>vikram.mehta.personal@gmail.com</Email>
    </Account>
    <Account>
      <Service>Telegram</Service>
      <Username>vikram_m_private</Username>
      <Email>vm.secure.2025@protonmail.com</Email>
    </Account>
    <Account>
      <Service>WhatsApp</Service>
      <Username>+91-98765-43210</Username>
    </Account>
    <Account>
      <Service>Trust Wallet</Service>
      <Username>wallet_primary</Username>
    </Account>
    <Account>
      <Service>NordVPN</Service>
      <Username>vm_nord_2025</Username>
      <Email>vm.secure.2025@protonmail.com</Email>
    </Account>
  </Accounts>

</CellebriteReport>
""")


def main():
    print("🔧 Generating synthetic forensic dataset…")
    print(f"   Scenario: Operation Digital Trail")
    print(f"   Suspect device: Vikram Mehta's OnePlus 12")
    print()

    # Write the raw XML first (useful for debugging)
    xml_path = DATA_DIR / "report.xml"
    xml_path.write_text(REPORT_XML, encoding="utf-8")
    print(f"   ✓ XML report written: {xml_path}")
    print(f"     Size: {xml_path.stat().st_size:,} bytes")

    # Package as .clbe (ZIP archive containing the report)
    clbe_path = DATA_DIR / "suspect_phone.clbe"
    with zipfile.ZipFile(clbe_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(xml_path, "report.xml")
    print(f"   ✓ CLBE archive created: {clbe_path}")
    print(f"     Size: {clbe_path.stat().st_size:,} bytes")

    # Also create a second device for richer cross-device analysis
    print()
    print("   Creating second device extraction (Priya Sharma's phone)…")
    _generate_priya_device()

    print()
    print("✅ Demo dataset ready!")
    print(f"   Files in: {DATA_DIR}")
    print()
    print("   To ingest via API:")
    print(f'   curl -X POST "http://localhost:8000/api/v1/ingest/path?path={clbe_path}"')
    print(f'   curl -X POST "http://localhost:8000/api/v1/ingest/path?path={DATA_DIR / "accomplice_phone.clbe"}"')


def _generate_priya_device():
    """Generate a second extraction — Priya Sharma's phone — for cross-device correlation."""

    priya_xml = dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<CellebriteReport>

  <DeviceInfo>
    <DeviceName>Priya's iPhone 15 Pro</DeviceName>
    <Model>iPhone 15 Pro (A2848)</Model>
    <OSVersion>iOS 17.3.1</OSVersion>
    <IMEI>490154203237518</IMEI>
    <SerialNumber>F2LXK4NDJP</SerialNumber>
    <PhoneNumber>+91-99887-65432</PhoneNumber>
    <ExtractionType>Advanced Logical</ExtractionType>
    <ExtractionDate>2026-01-16T14:20:00</ExtractionDate>
  </DeviceInfo>

  <Contacts>
    <Contact>
      <Name>V (Boss)</Name>
      <PhoneNumber>+91-98765-43210</PhoneNumber>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Rajan Tech</Name>
      <PhoneNumber>+91-88776-54321</PhoneNumber>
      <Email>rajan.crypto.dev@tutanota.com</Email>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Deepak NCB</Name>
      <PhoneNumber>+91-77665-43210</PhoneNumber>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Farid Dubai</Name>
      <PhoneNumber>+971-50-1234567</PhoneNumber>
      <Email>farid.hassan@dubaitrade.ae</Email>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Hawala Agent 1 (Gujarat)</Name>
      <PhoneNumber>+91-94260-11122</PhoneNumber>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Hawala Agent 2 (Kolkata)</Name>
      <PhoneNumber>+91-98310-33344</PhoneNumber>
      <Source>Phonebook</Source>
    </Contact>
    <Contact>
      <Name>Ananya Legal</Name>
      <PhoneNumber>+91-66554-32109</PhoneNumber>
      <Source>Phonebook</Source>
    </Contact>
  </Contacts>

  <CallLogs>
    <CallLog>
      <Direction>incoming</Direction>
      <PhoneNumber>+91-98765-43210</PhoneNumber>
      <ContactName>V (Boss)</ContactName>
      <Duration>342</Duration>
      <Timestamp>2026-01-10T09:15:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-98765-43210</PhoneNumber>
      <ContactName>V (Boss)</ContactName>
      <Duration>456</Duration>
      <Timestamp>2026-01-11T08:00:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-94260-11122</PhoneNumber>
      <ContactName>Hawala Agent 1 (Gujarat)</ContactName>
      <Duration>234</Duration>
      <Timestamp>2026-01-10T16:00:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+91-98310-33344</PhoneNumber>
      <ContactName>Hawala Agent 2 (Kolkata)</ContactName>
      <Duration>189</Duration>
      <Timestamp>2026-01-11T12:30:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
    <CallLog>
      <Direction>outgoing</Direction>
      <PhoneNumber>+971-50-1234567</PhoneNumber>
      <ContactName>Farid Dubai</ContactName>
      <Duration>567</Duration>
      <Timestamp>2026-01-12T17:00:00</Timestamp>
      <Source>Phone</Source>
    </CallLog>
  </CallLogs>

  <Messages>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>V (Boss)</From>
      <To>Priya Sharma</To>
      <Body>Priya, the Dubai shipment invoice is ready. I need you to route the payment through the Mauritius account first. 45 lakhs total. Split it into 3 deposits under 15L each so it doesn't flag AML systems.</Body>
      <Timestamp>2026-01-10T09:30:00</Timestamp>
      <Source>WhatsApp</Source>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Priya Sharma</From>
      <To>V (Boss)</To>
      <Body>Done. I'll do the first tranche today via Hawala. The rest goes through BVI shell company — Golden Horizon Ltd. Farid's team in Dubai will confirm receipt within 48 hours.</Body>
      <Timestamp>2026-01-10T09:45:00</Timestamp>
      <Source>WhatsApp</Source>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Priya Sharma</From>
      <To>Hawala Agent 1 (Gujarat)</To>
      <Body>15L ready for pickup. Same procedure — cash to your Ahmedabad office, convert and wire to Mauritius account #MU87-BKSL-4420-1155. Complete before 5 PM today.</Body>
      <Timestamp>2026-01-10T16:15:00</Timestamp>
      <Source>WhatsApp</Source>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Priya Sharma</From>
      <To>Hawala Agent 2 (Kolkata)</To>
      <Body>Need 15L routed Kolkata → Mauritius. Account details same as last month. Use the gems dealer cover story if asked. Commission is 2.5% as agreed.</Body>
      <Timestamp>2026-01-11T12:45:00</Timestamp>
      <Source>WhatsApp</Source>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Priya Sharma</From>
      <To>Farid Dubai</To>
      <Body>Farid, 30L incoming via 2 Hawala channels to the Mauritius account. Remaining 15L comes through the BVI company wire. ETA 48-72 hours for all three tranches. Please confirm receipt on each.</Body>
      <Timestamp>2026-01-11T17:30:00</Timestamp>
      <Source>Telegram</Source>
    </ChatMessage>
    <ChatMessage>
      <Direction>incoming</Direction>
      <From>Farid Dubai</From>
      <To>Priya Sharma</To>
      <Body>First tranche received — 15L confirmed in Mauritius account. Waiting for remaining two. Will credit Meridian Global's Dubai account once all three clear. Our commission (3%) will be deducted at source.</Body>
      <Timestamp>2026-01-12T10:00:00</Timestamp>
      <Source>Telegram</Source>
    </ChatMessage>
    <ChatMessage>
      <Direction>outgoing</Direction>
      <From>Priya Sharma</From>
      <To>Deepak NCB</To>
      <Body>Deepak — V says 8 lakh commission for you this quarter. I'll send via the Gujarat agent. Cash delivery at Andheri, Thursday 7 PM as usual. Bring an empty bag.</Body>
      <Timestamp>2026-01-12T18:30:00</Timestamp>
      <Source>WhatsApp</Source>
    </ChatMessage>
  </Messages>

  <Emails>
    <Email>
      <From>priya.sharma.offshore@protonmail.com</From>
      <To>farid.hassan@dubaitrade.ae</To>
      <Subject>Transfer confirmation — Mauritius to Dubai</Subject>
      <Body>Farid,

All three tranches have been dispatched:
1. Hawala Route A (Gujarat): Rs 15,00,000 — Sent 10 Jan
2. Hawala Route B (Kolkata): Rs 15,00,000 — Sent 11 Jan
3. BVI Wire (Golden Horizon Ltd): Rs 15,00,000 — Sent 12 Jan

Total: Rs 45,00,000

Please confirm full receipt and initiate the LC for the Shenzhen shipment.

Regards,
Priya</Body>
      <Timestamp>2026-01-12T20:00:00</Timestamp>
    </Email>
  </Emails>

  <Locations>
    <Location>
      <Latitude>19.1196</Latitude>
      <Longitude>72.8464</Longitude>
      <Address>Andheri West, Mumbai — Cash handover point</Address>
      <Timestamp>2026-01-10T18:00:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>23.0225</Latitude>
      <Longitude>72.5714</Longitude>
      <Address>Ahmedabad, Gujarat — Hawala agent office</Address>
      <Timestamp>2026-01-11T09:00:00</Timestamp>
      <Source>GPS</Source>
    </Location>
    <Location>
      <Latitude>19.0760</Latitude>
      <Longitude>72.8777</Longitude>
      <Address>National Commerce Bank, BKC Branch, Mumbai</Address>
      <Timestamp>2026-01-12T11:00:00</Timestamp>
      <Source>GPS</Source>
    </Location>
  </Locations>

  <InstalledApplications>
    <Application>
      <Name>WhatsApp Messenger</Name>
      <PackageName>com.whatsapp</PackageName>
      <Version>24.1.85</Version>
    </Application>
    <Application>
      <Name>Telegram</Name>
      <PackageName>ph.telegra.Telegraph</PackageName>
      <Version>10.8.0</Version>
    </Application>
    <Application>
      <Name>ProtonMail</Name>
      <PackageName>ch.protonmail.protonmail</PackageName>
      <Version>4.0.2</Version>
    </Application>
    <Application>
      <Name>Signal</Name>
      <PackageName>org.whispersystems.signal</PackageName>
      <Version>7.1.0</Version>
    </Application>
    <Application>
      <Name>HDFC Bank</Name>
      <PackageName>com.snapwork.hdfc</PackageName>
      <Version>10.5.0</Version>
    </Application>
  </InstalledApplications>

  <Accounts>
    <Account>
      <Service>ProtonMail</Service>
      <Username>priya.sharma.offshore</Username>
      <Email>priya.sharma.offshore@protonmail.com</Email>
    </Account>
    <Account>
      <Service>WhatsApp</Service>
      <Username>+91-99887-65432</Username>
    </Account>
    <Account>
      <Service>Telegram</Service>
      <Username>priya_offshore</Username>
    </Account>
  </Accounts>

</CellebriteReport>
""")

    xml2 = DATA_DIR / "report_priya.xml"
    xml2.write_text(priya_xml, encoding="utf-8")
    print(f"   ✓ XML report written: {xml2}")

    clbe2 = DATA_DIR / "accomplice_phone.clbe"
    with zipfile.ZipFile(clbe2, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(xml2, "report.xml")
    print(f"   ✓ CLBE archive created: {clbe2}")
    print(f"     Size: {clbe2.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

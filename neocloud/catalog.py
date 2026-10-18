COMPANIES = {
 "CRWV": {"name": "CoreWeave", "base_currency": "USD", "sector": "GPU cloud", "url": "https://investors.coreweave.com"},
 "NBIS": {"name": "Nebius Group", "base_currency": "USD", "sector": "AI infrastructure", "url": "https://nebius.com"},
 "IREN": {"name": "IREN", "base_currency": "USD", "sector": "AI cloud and Bitcoin mining", "url": "https://iren.com"},
 "HUT": {"name": "Hut 8", "base_currency": "USD", "sector": "Data centers, power and Bitcoin mining; mixed segments", "url": "https://www.hut8.com"},
 "BTDR": {"name": "Bitdeer Technologies Group", "base_currency": "USD", "sector": "Bitcoin mining, ASIC manufacturing and emerging AI/HPC", "url": "https://ir.bitdeer.com"},
}
SOURCES = {
 "CRWV": [
  "https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/crwv-20260630.htm",
  "https://investors.coreweave.com/news/news-details/2026/CoreWeave-Announces-Pricing-of-1-25-Billion-of-Senior-Notes-and-2-Billion-of-Senior-Notes/default.aspx"],
 "NBIS": [
  "https://nebius.com/newsroom/nebius-raises-775-million-in-first-secured-debt-financing-to-accelerate-global-buildout",
  "https://www.sec.gov/Archives/edgar/data/1513845/000110465926100347/tm2623863d1_ex99-1.htm"],
 "IREN": ["https://www.sec.gov/Archives/edgar/data/1878848/000187884826000052/iren-20260630.htm"],
 "BTDR": ["https://ir.bitdeer.com/financial-information/sec-filings"],
}

# Official discovery roots, not financial evidence until retrieved and excerpted.
SOURCES['CRWV'] += ['https://investors.coreweave.com/financials/sec-filings/default.aspx',
                    'https://investors.coreweave.com/news/default.aspx']
SOURCES['NBIS'] += ['https://nebius.com/newsroom','https://nebius.com/financials']

SOURCES['HUT'] = [
 'https://www.sec.gov/Archives/edgar/data/1964789/000110465925122052/hut-20251217xex99d1.htm',
 'https://www.sec.gov/Archives/edgar/data/1964789/000110465926090025/hut-20260630x10q.htm',
 'https://www.hut8.com/news-insights/press-releases/hut-8-closes-usd4-25-billion-of-investment-grade-senior-secured-notes-for-beacon-point-data',
 'https://www.sec.gov/Archives/edgar/data/1964789/000110465926111154/tm2625691d1_ex99-1.htm',
]

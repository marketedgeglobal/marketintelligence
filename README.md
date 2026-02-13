# PartnerAI Intelligence Report

This repository hosts the automated **PartnerAI Intelligence Report**, a weekly publication that analyzes global development, humanitarian, funding, and procurement activity from major international organizations. The report is generated automatically using RSS data delivered from Zapier and processed through GitHub Actions.

The system identifies and scores opportunities across categories such as:

- Funding  
- Procurement  
- Humanitarian updates  
- Development programs  
- Policy changes  

The final HTML report is published to GitHub Pages on a weekly schedule.

---

## Overview

The PartnerAI Intelligence Report provides a structured, AI‑generated summary of the most relevant global development signals from the past 30 days. Zapier collects RSS items from multiple international sources and sends them directly to GitHub Actions, where the report is assembled and published.

---

## Features

- **Automated Weekly Reports**: Generated every Monday at 7:00 AM MT  
- **Multi‑Source Coverage**: Pulls from major global development and humanitarian RSS feeds  
- **Signal Classification**: Categorizes items into Funding, Procurement, Humanitarian, Development Program, or Policy Update  
- **Priority Scoring**: Ranks items using a 10‑point scoring model  
- **HTML Output**: Clean, structured report published to GitHub Pages  
- **Direct Zapier Integration**: No database or Google Sheets required  

---

## Data Flow

1. **Zapier** monitors multiple RSS feeds.  
2. When new items appear, Zapier sends a JSON payload to GitHub Actions.  
3. **GitHub Actions** receives the payload, filters and scores the items, and generates the HTML report.  
4. The report is committed to the repository and published via GitHub Pages.

---

## RSS Sources

- DevelopmentAid Funding Updates  
  https://www.developmentaid.org/api/frontend/funding/rss.xml  
- ReliefWeb Humanitarian Updates  
  https://reliefweb.int/updates/rss.xml  
- UNDP Global Development Updates  
  https://www.undp.org/rss.xml  
- Asian Development Bank (ADB) Business Opportunities  
  https://www.adb.org/rss/business-opportunities.xml  
- IFAD Rural Development & Funding Updates  
  https://www.ifad.org/en/web/latest/rss  
- World Bank Procurement & Project Tenders  
  https://projects.worldbank.org/en/projects-operations/procurement/rss  

---

## Repository Structure

# 🏛️ Oracle Database Architecture & Market Coverage
> **Generated on**: 2026-02-06
> **Version**: 2.0 (The "Great Schema")

This document details the institutional-grade data architecture built for the Oracle platform. It covers the database schema, data ingestion pipelines (ETL), and the exact market coverage statistics.

---

## 1. Core Master Data (`instrument_master`)
The central "Golden Record" for all tradeable instruments.

*   **Row Count**: ~8,779 Active Instruments (Total NSE Universe).
*   **Key Features**:
    *   **Universal Key**: `instrument_key` (e.g., `NSE_EQ|INE002A01018`) maps across all tables.
    *   **Granular Classification**:
        *   `segment`: NSE_EQ, NSE_FO, etc.
        *   `instrument_type`: EQ (Equity), BE (Book Entry), SM (SME), etc.
    *   **The Enrichment Layer (Phase 13/14)**:
        *   `sector`: Broad Category (e.g., "Technology", "Energy").
        *   `industry`: Specific Niche (e.g., "Software Infrastructure", "Oil & Gas Refining").

---

## 2. Market Data Tables (The "Big Three")
We split market data into three optimized tables based on liquidity and poller logic.

### 🦅 Table D: The Mainboard Giant (`market_quota_nse500_data`)
> *Misnomer Alert: Despite the name, this covers far more than the Nifty 500.*

*   **Coverage**: **2,508 Companies** (100% of NSE Mainboard).
*   **Filter Logic**: `segment='NSE_EQ'` AND `type IN ('EQ', 'BE')`.
*   **Content**: 
    *   Full Market Depth (Bid/Ask Top 5).
    *   OHLCV (Open, High, Low, Close, Volume).
    *   Liquidity Stats (Total Buy/Sell Qty, OI).
*   **Update Frequency**: Every 5 Minutes.

### 🚀 Table C: The SME Engine (`market_quota_sme_data`)
> *Dedicated storage for Small & Medium Enterprises.*

*   **Coverage**: **461 Companies** (100% of NSE SME Board).
*   **Filter Logic**: `segment='NSE_EQ'` AND `type='SM'`.
*   **Content**: Same high-fidelity Depth & Liquidity as Mainboard.
*   **Update Frequency**: Every 5 Minutes.

### ⚡ Table E: The F&O Radar (`market_quota_fo_data`)
> *High-performance subset for Derivatives Trading.*

*   **Coverage**: **212 F&O Stocks** (Subset of Mainboard).
*   **Purpose**: Redundant, high-speed access for Option Chain correlation.
*   **Content**: 
    *   Underlying Spot Prices.
    *   **Significance**: These 212 stocks drive the entire Derivatives market.

---

## 3. Thematic Intelligence (`index_mapping`)
Instead of duplicating data, we map instruments to their indices.

*   **Total Mapped**: ~500 Unique Instruments.
*   **Indices Covered**:
    *   `NIFTY 50` & `NIFTY NEXT 50`
    *   `NIFTY MIDCAP 150`
    *   `NIFTY SMALLCAP 250`
    *   `NIFTY MIDSMALLCAP 400` (Subset of Mid+Small)
    *   And 10+ Sectoral Indices (Auto, Bank, IT, etc.)

---

## 4. The "Leftovers" Analysis
What is NOT covered by the Main Pollers?

*   **Total Active NSE_EQ**: ~8,779.
*   **Covered (Mainboard + SME)**: ~2,970 (The "Real Companies").
*   **The Gap (~5,800)**:
    *   **Gold Bonds (SG)**: ~3,954 (Investment products, not companies).
    *   **Penny/Z-Category**: ~1,800 (Types `N0`, `N1`, `BZ`).
    *   **ETFs/Mutual Funds**: Miscellaneous.

**Conclusion**: We have achieved **100% Coverage** of all viable Operating Companies on the NSE.

---

## 5. Sector Classification System (GICS Standard)
Implements the 11-Sector Global Standard:
1.  Energy
2.  Basic Materials
3.  Industrials
4.  Consumer Cyclical
5.  Consumer Defensive
6.  Healthcare
7.  Financial Services
8.  Technology
9.  Communication Services
10. Utilities
11. Real Estate

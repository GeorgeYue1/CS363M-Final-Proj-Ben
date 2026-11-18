"""Download selected World Development Indicators from the World Bank API.

Outputs (in data/raw/worldbank/):
  wdi_long.csv        one row per (country, indicator, year)
  wdi_wide.csv        one row per (country, year), one column per indicator
  countries.csv       country metadata; region == "Aggregates" marks regional/income groups
  indicators.csv      indicator codes, names, and whether they are excluded as HDI-leaky

Usage: python3 download_worldbank.py
"""

import csv
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data" / "raw" / "worldbank"
YEARS = "1990:2024"
API = "https://api.worldbank.org/v2"

# code -> (short column name, leaky?)  "leaky" = HDI component or near-duplicate;
# kept for comparison experiments only, not as default model inputs.
INDICATORS = {
    # Demographics
    "SP.POP.TOTL": ("population", False),
    "SP.POP.GROW": ("pop_growth_pct", False),
    "EN.POP.DNST": ("pop_density", False),
    "SP.URB.TOTL.IN.ZS": ("urban_pop_pct", False),
    "SP.DYN.TFRT.IN": ("fertility_rate", False),
    "SP.DYN.CBRT.IN": ("birth_rate", False),
    "SP.ADO.TFRT": ("adolescent_fertility", False),
    "SP.POP.0014.TO.ZS": ("pop_0_14_pct", False),
    "SP.POP.65UP.TO.ZS": ("pop_65up_pct", False),
    # Infrastructure / access
    "EG.ELC.ACCS.ZS": ("electricity_access_pct", False),
    "EG.CFT.ACCS.ZS": ("clean_cooking_access_pct", False),
    "SH.H2O.BASW.ZS": ("basic_water_pct", False),
    "SH.STA.BASS.ZS": ("basic_sanitation_pct", False),
    "IT.NET.USER.ZS": ("internet_users_pct", False),
    "IT.CEL.SETS.P2": ("mobile_subs_per100", False),
    # Economy structure (not income level)
    "NV.AGR.TOTL.ZS": ("agriculture_gdp_pct", False),
    "NV.IND.TOTL.ZS": ("industry_gdp_pct", False),
    "NV.SRV.TOTL.ZS": ("services_gdp_pct", False),
    "NE.TRD.GNFS.ZS": ("trade_gdp_pct", False),
    "FP.CPI.TOTL.ZG": ("inflation_pct", False),
    "SL.AGR.EMPL.ZS": ("agri_employment_pct", False),
    "SL.TLF.CACT.FE.ZS": ("female_lfp_pct", False),
    # Health spending / environment
    "SH.XPD.CHEX.GD.ZS": ("health_exp_gdp_pct", False),
    "EN.GHG.CO2.PC.CE.AR5": ("co2_per_capita", False),
    "EG.USE.ELEC.KH.PC": ("elec_kwh_per_capita", False),
    "AG.LND.FRST.ZS": ("forest_area_pct", False),
    # Leaky / near-duplicates of HDI components (for comparison only)
    "SP.DYN.IMRT.IN": ("infant_mortality", True),
    "SH.DYN.MORT": ("under5_mortality", True),
    "SP.DYN.LE00.IN": ("life_expectancy", True),
    "NY.GDP.PCAP.PP.KD": ("gdp_pc_ppp", True),
    "NY.GNP.PCAP.PP.KD": ("gni_pc_ppp", True),
    "SE.SEC.ENRR": ("secondary_enrollment", True),
}


def get_json(url, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # network hiccups / API throttling
            if attempt == retries - 1:
                raise
            print(f"  retry {attempt + 1} after error: {e}")
            time.sleep(2 * (attempt + 1))


def fetch_paged(path):
    rows, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        data = get_json(f"{API}/{path}{sep}format=json&per_page=20000&page={page}")
        if not isinstance(data, list) or len(data) < 2:
            raise RuntimeError(f"Unexpected API response for {path}: {str(data)[:300]}")
        meta, chunk = data[0], data[1] or []
        rows.extend(chunk)
        if page >= int(meta.get("pages", 1)):
            return rows
        page += 1


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("Fetching country metadata...")
    countries = fetch_paged("country")
    pd.DataFrame(
        {
            "iso3": c["id"],
            "name": c["name"],
            "region": c["region"]["value"].strip(),
            "income_level": c["incomeLevel"]["value"].strip(),
        }
        for c in countries
    ).to_csv(OUT / "countries.csv", index=False)

    long_rows, ind_meta = [], []
    for code, (col, leaky) in INDICATORS.items():
        print(f"Fetching {code} ({col})...")
        try:
            rows = fetch_paged(f"country/all/indicator/{code}?date={YEARS}")
        except RuntimeError as e:
            print(f"  SKIPPED: {e}")
            continue
        name = rows[0]["indicator"]["value"] if rows else ""
        n = 0
        for r in rows:
            if r["value"] is None:
                continue
            long_rows.append(
                {
                    "iso3": r["countryiso3code"],
                    "country": r["country"]["value"],
                    "year": int(r["date"]),
                    "indicator": col,
                    "value": r["value"],
                }
            )
            n += 1
        ind_meta.append({"code": code, "column": col, "name": name, "leaky": leaky, "non_null": n})
        print(f"  {n} non-null values")

    long_df = pd.DataFrame(long_rows)
    long_df = long_df[long_df["iso3"] != ""]
    long_df.to_csv(OUT / "wdi_long.csv", index=False)

    wide = long_df.pivot_table(index=["iso3", "country", "year"], columns="indicator", values="value").reset_index()
    wide.columns.name = None
    wide.to_csv(OUT / "wdi_wide.csv", index=False)

    pd.DataFrame(ind_meta).to_csv(OUT / "indicators.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Done: {len(wide)} country-year rows x {len(ind_meta)} indicators -> {OUT}")


if __name__ == "__main__":
    main()

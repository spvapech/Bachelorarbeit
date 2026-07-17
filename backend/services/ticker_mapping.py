"""
Statische Ticker-Vorschläge für deutsche börsennotierte Unternehmen
(DAX/MDAX, Yahoo-Finance-Notation). Dient nur als Vorschlagsliste im
Frontend — die verbindliche Zuordnung liegt in `companies.ticker`.
"""

from typing import Dict, List

GERMAN_TICKER_MAP: Dict[str, str] = {
    "Adidas": "ADS.DE",
    "Airbus": "AIR.DE",
    "Allianz": "ALV.DE",
    "BASF": "BAS.DE",
    "Bayer": "BAYN.DE",
    "Beiersdorf": "BEI.DE",
    "BMW": "BMW.DE",
    "Brenntag": "BNR.DE",
    "Commerzbank": "CBK.DE",
    "Continental": "CON.DE",
    "Covestro": "1COV.DE",
    "Daimler Truck": "DTG.DE",
    "Deutsche Bank": "DBK.DE",
    "Deutsche Börse": "DB1.DE",
    "Deutsche Lufthansa": "LHA.DE",
    "Deutsche Post DHL": "DHL.DE",
    "Deutsche Telekom": "DTE.DE",
    "E.ON": "EOAN.DE",
    "Evonik": "EVK.DE",
    "Fresenius": "FRE.DE",
    "Fresenius Medical Care": "FME.DE",
    "Fraport": "FRA.DE",
    "GEA Group": "G1A.DE",
    "Hannover Rück": "HNR1.DE",
    "HeidelbergCement": "HEI.DE",
    "HelloFresh": "HFG.DE",
    "Henkel": "HEN3.DE",
    "Hugo Boss": "BOSS.DE",
    "Infineon": "IFX.DE",
    "K+S": "SDF.DE",
    "Lanxess": "LXS.DE",
    "Mercedes-Benz": "MBG.DE",
    "Merck": "MRK.DE",
    "MTU Aero Engines": "MTX.DE",
    "Münchener Rück": "MUV2.DE",
    "Nemetschek": "NEM.DE",
    "Porsche": "P911.DE",
    "Puma": "PUM.DE",
    "Qiagen": "QIA.DE",
    "Rheinmetall": "RHM.DE",
    "RWE": "RWE.DE",
    "SAP": "SAP.DE",
    "Sartorius": "SRT3.DE",
    "Siemens": "SIE.DE",
    "Siemens Energy": "ENR.DE",
    "Siemens Healthineers": "SHL.DE",
    "Symrise": "SY1.DE",
    "TUI": "TUI1.DE",
    "Volkswagen": "VOW3.DE",
    "Vonovia": "VNA.DE",
    "Zalando": "ZAL.DE",
}


def suggest_tickers(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """Vorschläge (Name + Ticker) für eine Teilstring-Suche über Name/Ticker."""
    q = (query or "").strip().lower()
    if not q:
        return []
    matches = [
        {"name": name, "ticker": ticker}
        for name, ticker in GERMAN_TICKER_MAP.items()
        if q in name.lower() or q in ticker.lower()
    ]
    return matches[:limit]

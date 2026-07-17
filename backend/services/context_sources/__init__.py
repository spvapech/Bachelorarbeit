"""
Quell-Adapter der Kontextsammlung (2. Design-Zyklus).

Jede externe Quelle ist als eigenes Modul gekapselt, damit Verfügbarkeit
und Brüchigkeit einzelner Quellen (z.B. EQS ohne offizielle API) den
Gesamtprozess nicht gefährden und in der Arbeit getrennt diskutiert
werden können:

- yfinance_source: Unternehmensnachrichten, Aktienkurse, Kennzahlen (Yahoo Finance)
- eqs_source:      Ad-hoc-Mitteilungen via öffentlichem EQS-News-RSS (Best Effort)
- manual_import:   CSV/JSON-Import als garantierter Fallback-Pfad
"""

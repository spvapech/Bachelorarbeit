"""
Test-Isolation: Tests laufen IMMER gegen den In-Memory-Store, nie gegen
eine echte Datenbank.

database/supabase_client.py lädt beim Import backend/.env (load_dotenv) und
verbindet sich bei gesetzten SUPABASE_*-Variablen mit der echten Supabase.
Diese conftest wird von pytest vor allen Testmodulen importiert und setzt
die Variablen auf leere Strings — load_dotenv(override=False) überschreibt
bereits gesetzte Variablen nicht, daher fällt der Client sicher auf den
In-Memory-Store zurück.
"""

import os

os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_KEY"] = ""
os.environ["SUPABASE_KEY"] = ""

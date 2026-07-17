import os
from dotenv import load_dotenv

load_dotenv()

_url = os.getenv("SUPABASE_URL", "")
# Use service_role key for server-side operations (bypasses RLS for writes).
# Falls back to anon key for local dev without a service role key.
_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")

if _url and _key:
    from supabase import create_client, Client as _Client
    _client = create_client(_url, _key)

    def get_supabase_client() -> _Client:
        return _client
else:
    from database.in_memory_store import get_in_memory_client

    def get_supabase_client():
        return get_in_memory_client()

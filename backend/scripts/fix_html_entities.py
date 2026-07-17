"""
Fix HTML entities in existing database records.
Decodes &lt; &gt; &amp; &quot; etc. in all text fields.
"""

import html
from database.supabase_client import get_supabase_client

def clean_text(text):
    """Decode HTML entities from text."""
    if not text or not isinstance(text, str):
        return text
    return html.unescape(text)


def fix_candidates_table():
    """Fix HTML entities in candidates table."""
    supabase = get_supabase_client()
    
    # Fetch all candidates
    response = supabase.table("candidates").select("*").execute()
    records = response.data
    
    print(f"📊 Found {len(records)} candidates records")
    
    updated = 0
    text_fields = ["titel", "status", "stellenbeschreibung", "verbesserungsvorschlaege"]
    
    for record in records:
        record_id = record["id"]
        updates = {}
        has_changes = False
        
        # Check each text field
        for field in text_fields:
            if field in record and record[field]:
                original = record[field]
                cleaned = clean_text(original)
                if cleaned != original:
                    updates[field] = cleaned
                    has_changes = True
                    print(f"  🔧 Candidate {record_id} - {field}: {original[:50]}... → {cleaned[:50]}...")
        
        # Update if changes found
        if has_changes:
            supabase.table("candidates").update(updates).eq("id", record_id).execute()
            updated += 1
    
    print(f"✅ Updated {updated} candidates records\n")
    return updated


def fix_employee_table():
    """Fix HTML entities in employee table."""
    supabase = get_supabase_client()
    
    # Fetch all employees
    response = supabase.table("employee").select("*").execute()
    records = response.data
    
    print(f"📊 Found {len(records)} employee records")
    
    updated = 0
    text_fields = [
        "titel", "status", 
        "jobbeschreibung",
        "gut_am_arbeitgeber_finde_ich",
        "schlecht_am_arbeitgeber_finde_ich",
        "verbesserungsvorschlaege",
        # Topic comment fields
        "arbeitsatmosphaere",
        "image",
        "work_life_balance",
        "karriere_weiterbildung",
        "gehalt_sozialleistungen",
        "kollegenzusammenhalt",
        "umwelt_sozialbewusstsein",
        "vorgesetztenverhalten",
        "kommunikation",
        "interessante_aufgaben",
        "umgang_mit_aelteren_kollegen",
        "arbeitsbedingungen",
        "gleichberechtigung"
    ]
    
    for record in records:
        record_id = record["id"]
        updates = {}
        has_changes = False
        
        # Check each text field
        for field in text_fields:
            if field in record and record[field]:
                original = record[field]
                cleaned = clean_text(original)
                if cleaned != original:
                    updates[field] = cleaned
                    has_changes = True
                    print(f"  🔧 Employee {record_id} - {field}: {original[:50]}... → {cleaned[:50]}...")
        
        # Update if changes found
        if has_changes:
            supabase.table("employee").update(updates).eq("id", record_id).execute()
            updated += 1
    
    print(f"✅ Updated {updated} employee records\n")
    return updated


def main():
    """Run the HTML entity fix for all tables."""
    print("=" * 80)
    print("🧹 Fixing HTML entities in database")
    print("=" * 80)
    print()
    
    try:
        candidates_updated = fix_candidates_table()
        employee_updated = fix_employee_table()
        
        print("=" * 80)
        print(f"🎉 Done! Total updated: {candidates_updated + employee_updated} records")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

"""
Test script for Topic Overview API
Run this to test the new endpoint locally
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
COMPANY_ID = 1  # Change this to test with different companies

def test_topic_overview():
    """Test the topic overview endpoint"""
    print(f"🧪 Testing Topic Overview API for Company {COMPANY_ID}")
    print("=" * 60)
    
    try:
        # Make request
        url = f"{BASE_URL}/api/analytics/company/{COMPANY_ID}/topic-overview"
        print(f"📡 Requesting: {url}")
        
        response = requests.get(url)
        
        # Check status
        if response.status_code == 200:
            print("✅ Request successful!")
            data = response.json()
            
            # Print summary
            print(f"\n📊 Summary:")
            print(f"   Total Topics: {data.get('total_topics', 0)}")
            print(f"   Total Reviews: {data.get('total_reviews', 0)}")
            
            # Print topics
            topics = data.get('topics', [])
            if topics:
                print(f"\n📋 Found Topics:")
                for topic in topics:
                    sentiment_emoji = {
                        "Positiv": "😊",
                        "Neutral": "😐",
                        "Negativ": "😟"
                    }.get(topic['sentiment'], "❓")
                    
                    print(f"\n   {sentiment_emoji} {topic['topic']}")
                    print(f"      Frequency: {topic['frequency']} mentions")
                    print(f"      Avg Rating: {topic['avgRating']}/5")
                    print(f"      Sentiment: {topic['sentiment']}")
                    print(f"      Example: {topic['example'][:60]}...")
                    
                    # Show timeline
                    if topic.get('timelineData'):
                        timeline = topic['timelineData']
                        print(f"      Timeline: {timeline[0]['month']}={timeline[0]['rating']} → {timeline[-1]['month']}={timeline[-1]['rating']}")
                    
                    # Show typical statements
                    if topic.get('typicalStatements') and len(topic['typicalStatements']) > 0:
                        print(f"      Statements: {len(topic['typicalStatements'])} found")
                        print(f"         - {topic['typicalStatements'][0][:60]}...")
            else:
                print("\n⚠️  No topics found")
            
            # Print full JSON (optional)
            print(f"\n📄 Full JSON Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("   Make sure the backend is running:")
        print("   cd backend && uvicorn main:app --reload")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_multiple_companies():
    """Test with multiple company IDs"""
    print("\n" + "=" * 60)
    print("🔍 Testing multiple companies")
    print("=" * 60)
    
    for company_id in [1, 2, 3]:
        print(f"\n📍 Company {company_id}:")
        try:
            url = f"{BASE_URL}/api/analytics/company/{company_id}/topic-overview"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {data.get('total_topics', 0)} topics, {data.get('total_reviews', 0)} reviews")
            else:
                print(f"   ❌ Error {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║          Topic Overview API Test Script                    ║
║                                                             ║
║  Make sure your backend is running:                        ║
║  $ cd backend && uvicorn main:app --reload                 ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    test_topic_overview()
    
    # Uncomment to test multiple companies
    # test_multiple_companies()
    
    print("\n✨ Test completed!\n")

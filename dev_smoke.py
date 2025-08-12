#!/usr/bin/env python3
"""
End-to-end smoke test for the AI Business Engine
Tests: Ideation → Research Validation → Results
"""
import sys
import time
from typing import Any

import requests

BASE = "http://127.0.0.1:8000"

def post(path: str, json_data: dict[str, Any], headers: dict[str, str] = None) -> dict[str, Any]:
    """Make a POST request and return JSON response."""
    try:
        r = requests.post(BASE + path, json=json_data, headers=headers or {})
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ POST {path} failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

def get(path: str, headers: dict[str, str] = None) -> dict[str, Any]:
    """Make a GET request and return JSON response."""
    try:
        r = requests.get(BASE + path, headers=headers or {})
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ GET {path} failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

def poll_run_status(run_id: str, max_attempts: int = 30, delay: float = 1.0) -> dict[str, Any]:
    """Poll a run until it completes or fails."""
    print(f"🔄 Polling run {run_id}...")
    
    for attempt in range(max_attempts):
        try:
            response = get(f"/automation/runs/{run_id}")
            status = response.get("status", "unknown")
            print(f"  Attempt {attempt + 1}: Status = {status}")
            
            if status in ("succeeded", "failed"):
                return response
            elif status == "running":
                print("  ⏳ Run is executing...")
            elif status == "queued":
                print("  ⏳ Run is queued...")
            else:
                print(f"  ℹ️  Unexpected status: {status}")
                
        except Exception as e:
            print(f"  ⚠️  Poll attempt {attempt + 1} failed: {e}")
        
        time.sleep(delay)
    
    print(f"❌ Run {run_id} did not complete within {max_attempts * delay} seconds")
    return {"status": "timeout", "error": "Polling timeout"}

def main():
    print("🚀 Starting AI Business Engine Smoke Test")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1️⃣ Testing API Health...")
    health = get("/health")
    print(f"✅ Health: {health}")
    
    # Test 2: Ideation Pipeline
    print("\n2️⃣ Testing Ideation Pipeline...")
    ideation_payload = {
        "intent": "ideation.generate",
        "payload": {
            "topic": "AI-driven personal finance automation",
            "count": 2,
            "include_research": False
        },
        "idempotency_key": f"smoke-ideation-{int(time.time())}"
    }
    
    ideation_response = post("/automation/submit", ideation_payload)
    print(f"✅ Ideation submitted: {ideation_response}")
    
    ideation_run_id = ideation_response["run_id"]
    ideation_result = poll_run_status(ideation_run_id, max_attempts=20, delay=1.0)
    
    if ideation_result.get("status") == "succeeded":
        print("🎉 Ideation pipeline completed successfully!")
        # The result is in the detail.result field
        ideas = ideation_result.get("detail", {}).get("result", {}).get("ideas", [])
        print(f"   Generated {len(ideas)} ideas")
        
        # Use the first idea for research validation
        if ideas:
            first_idea = ideas[0]
            print(f"   First idea: {first_idea.get('title', 'No title')}")
            
            # Test 3: Research Validation Pipeline
            print("\n3️⃣ Testing Research Validation Pipeline...")
            research_payload = {
                "intent": "research.validate_idea",
                "payload": {
                    "idea": first_idea,
                    "run_id": ideation_run_id
                },
                "idempotency_key": f"smoke-research-{int(time.time())}"
            }
            
            research_response = post("/automation/submit", research_payload)
            print(f"✅ Research validation submitted: {research_response}")
            
            research_run_id = research_response["run_id"]
            research_result = poll_run_status(research_run_id, max_attempts=60, delay=1.0)
            
            if research_result.get("status") == "succeeded":
                print("🎉 Research validation completed successfully!")
                validation = research_result.get("result", {})
                print(f"   Trend Score: {validation.get('trend_score', 'N/A')}")
                print(f"   Recommended Action: {validation.get('recommended_action', 'N/A')}")
                print(f"   Market Size: {validation.get('market_size', {}).get('notes', 'N/A')}")
            else:
                print(f"❌ Research validation failed: {research_result}")
        else:
            print("⚠️  No ideas generated, skipping research validation")
    else:
        print(f"❌ Ideation pipeline failed: {ideation_result}")
    
    # Test 4: Check Recent Runs
    print("\n4️⃣ Checking Recent Runs...")
    recent_runs = get("/automation/recent")
    print(f"✅ Recent runs: {len(recent_runs.get('items', []))} items")
    
    print("\n" + "=" * 50)
    print("🎯 Smoke Test Complete!")
    
    if ideation_result.get("status") == "succeeded":
        print("✅ Ideation pipeline: WORKING")
    else:
        print("❌ Ideation pipeline: FAILED")
    
    if 'research_result' in locals() and research_result.get("status") == "succeeded":
        print("✅ Research validation: WORKING")
    else:
        print("❌ Research validation: FAILED")
    
    print("\n🚀 AI Business Engine is ready for action!")

if __name__ == "__main__":
    main()

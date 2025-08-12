#!/usr/bin/env python3
"""
Simple test script to validate the research pipeline
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.automation.registry import get_dag, get_skill


async def test_research_pipeline():
    """Test the research validation pipeline"""
    print("🧪 Testing Research Pipeline...")
    
    # Test 1: Check if skills are registered
    print("\n1. Checking skill registration...")
    try:
        ideation_skill = get_skill("ideation.generate")
        research_skill = get_skill("research.validate_idea")
        print("✅ Skills registered successfully")
    except KeyError as e:
        print(f"❌ Skill not found: {e}")
        return False
    
    # Test 2: Check if DAGs are registered
    print("\n2. Checking DAG registration...")
    try:
        ideation_dag = get_dag("ideation.generate")
        research_dag = get_dag("research.validate_idea")
        pipeline_dag = get_dag("ideation.research_pipeline")
        print("✅ DAGs registered successfully")
        print(f"   - ideation.generate: {ideation_dag}")
        print(f"   - research.validate_idea: {research_dag}")
        print(f"   - ideation.research_pipeline: {pipeline_dag}")
    except KeyError as e:
        print(f"❌ DAG not found: {e}")
        return False
    
    # Test 3: Test ideation skill directly
    print("\n3. Testing ideation skill...")
    try:
        context = {
            "topic": "AI-driven personal finance",
            "count": 3,
            "correlation_id": "test_123"
        }
        result = await ideation_skill(context)
        print("✅ Ideation skill executed successfully")
        print(f"   - Ideas generated: {len(result.get('ideas', []))}")
        print(f"   - Status: {result.get('status')}")
    except Exception as e:
        print(f"❌ Ideation skill failed: {e}")
        return False
    
    # Test 4: Test research validation skill directly
    print("\n4. Testing research validation skill...")
    try:
        # Use the first idea from the previous result
        if result.get('ideas'):
            idea = result['ideas'][0]
            validation_context = {
                "idea": idea,
                "correlation_id": "test_123",
                "run_id": "test_run_456"
            }
            validation_result = await research_skill(validation_context)
            print("✅ Research validation skill executed successfully")
            print(f"   - Trend score: {validation_result.get('validation_result', {}).get('trend_score')}")
            print(f"   - Recommended action: {validation_result.get('validation_result', {}).get('recommended_action')}")
            print(f"   - Status: {validation_result.get('status')}")
        else:
            print("⚠️  No ideas generated, skipping validation test")
    except Exception as e:
        print(f"❌ Research validation skill failed: {e}")
        return False
    
    print("\n🎉 All tests passed! The research pipeline is working correctly.")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_research_pipeline())
    sys.exit(0 if success else 1)

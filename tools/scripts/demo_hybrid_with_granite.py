#!/usr/bin/env python3
"""
Demo hybrid approach with available models
"""

import requests
import time

def quick_test_hybrid():
    """Show hybrid approach with granite3.3:8b"""
    
    base_url = "http://localhost:11434"
    
    # Simple test cases
    test_cases = [
        {
            "name": "Simple Math",
            "prompt": "What is 15 * 23?",
            "expected": "rapid_sufficient"
        },
        {
            "name": "Code Fix",
            "prompt": "Fix SQL injection in: cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
            "expected": "needs_both"
        },
        {
            "name": "Complex Analysis",
            "prompt": "Analyze the security implications of storing passwords in plaintext and suggest best practices for password storage in web applications",
            "expected": "needs_deep"
        }
    ]
    
    print("🎯 HYBRID ANALYSIS CONCEPT DEMO")
    print("=" * 60)
    print("Using granite3.3:8b to simulate rapid vs deep analysis\n")
    
    for test in test_cases:
        print(f"\n📌 {test['name']}")
        print("-" * 40)
        print(f"Question: {test['prompt'][:80]}...")
        
        # Phase 1: Rapid (limited response)
        start = time.time()
        rapid_response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": "granite3.3:8b",
                "prompt": f"Answer in 1 sentence: {test['prompt']}",
                "options": {"num_predict": 30, "temperature": 0.3},
                "stream": False
            },
            timeout=15
        )
        rapid_time = time.time() - start
        
        if rapid_response.status_code == 200:
            rapid_text = rapid_response.json().get('response', '')
            print(f"\n⚡ Rapid ({rapid_time:.1f}s): {rapid_text.strip()}")
            
            # Decide if we need deep analysis
            needs_deep = (
                len(rapid_text.split()) < 15 or
                test['expected'] in ['needs_both', 'needs_deep'] or
                any(word in test['prompt'].lower() for word in ['analyze', 'explain', 'security', 'implications'])
            )
            
            if needs_deep:
                print("\n🔍 Triggering deep analysis...")
                
                # Phase 2: Deep (full response)
                start = time.time()
                deep_response = requests.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": "granite3.3:8b",
                        "prompt": f"Provide detailed analysis:\n{test['prompt']}",
                        "options": {"temperature": 0.7},
                        "stream": False
                    },
                    timeout=30
                )
                deep_time = time.time() - start
                
                if deep_response.status_code == 200:
                    deep_text = deep_response.json().get('response', '')
                    print(f"\n🧠 Deep ({deep_time:.1f}s): {deep_text[:300]}...")
                    print(f"\n📊 Time comparison: Rapid={rapid_time:.1f}s, Deep={deep_time:.1f}s")
                    print(f"   Deep provided {len(deep_text.split()) // len(rapid_text.split())}x more detail")
            else:
                print("\n✅ Rapid response sufficient - no deep analysis needed")
    
    print("\n\n💡 KEY INSIGHTS:")
    print("1. Rapid models (<3GB) provide instant feedback")
    print("2. Deep models analyze only when complexity demands it")
    print("3. Total time = rapid_time + (deep_time if needed)")
    print("4. User gets immediate answer + optional detailed follow-up")

if __name__ == "__main__":
    quick_test_hybrid()
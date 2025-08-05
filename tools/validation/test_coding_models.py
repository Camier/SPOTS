#!/usr/bin/env python3
"""
Test different coding models for specific tasks
"""

import subprocess
import time
import json
from typing import Dict, List

def test_model(model: str, prompt: str, max_tokens: int = 200) -> Dict:
    """Test a single model with a prompt"""
    print(f"\n🔍 Testing {model}...")
    
    start = time.time()
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed = time.time() - start
        
        if result.returncode == 0:
            return {
                "model": model,
                "success": True,
                "response": result.stdout.strip(),
                "time": elapsed,
                "tokens": len(result.stdout.split())
            }
        else:
            return {
                "model": model,
                "success": False,
                "error": result.stderr,
                "time": elapsed
            }
    except subprocess.TimeoutExpired:
        return {
            "model": model,
            "success": False,
            "error": "Timeout after 30s",
            "time": 30.0
        }
    except Exception as e:
        return {
            "model": model,
            "success": False,
            "error": str(e),
            "time": time.time() - start
        }

def compare_models_for_task(task_name: str, prompt: str, models: List[str]) -> Dict:
    """Compare multiple models on the same task"""
    print(f"\n{'='*60}")
    print(f"📋 Task: {task_name}")
    print(f"{'='*60}")
    
    results = []
    for model in models:
        result = test_model(model, prompt)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {model}: {result['time']:.1f}s ({result['tokens']} tokens)")
            print(f"   Response preview: {result['response'][:100]}...")
        else:
            print(f"❌ {model}: {result['error']}")
    
    return {
        "task": task_name,
        "prompt": prompt,
        "results": results
    }

def main():
    """Test various coding models"""
    
    # Define test cases
    test_cases = [
        {
            "name": "SQL Injection Fix",
            "prompt": "Fix this SQL injection vulnerability: cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
            "models": ["starcoder2:3b", "granite3.3:8b", "phi3:mini"]
        },
        {
            "name": "Python Bug Fix", 
            "prompt": "Fix this Python bug: def factorial(n): return n * factorial(n)",
            "models": ["starcoder2:3b", "granite3.3:8b", "codellama-gpu:7b"]
        },
        {
            "name": "Code Explanation",
            "prompt": "Explain this code: lambda x: x if x <= 1 else x * (lambda f: f(x-1))",
            "models": ["starcoder2:3b", "phi3:mini", "mistral-small3.1-gpu:latest"]
        },
        {
            "name": "SQL Query Generation",
            "prompt": "Write SQL to find top 5 customers by total order value",
            "models": ["starcoder2:3b", "granite3.3:8b", "phi3:mini"]
        }
    ]
    
    all_results = []
    
    print("🚀 CODING MODEL COMPARISON TEST")
    print("=" * 60)
    
    for test_case in test_cases:
        # Check which models are available
        available_models = []
        for model in test_case["models"]:
            check = subprocess.run(
                ["ollama", "show", model],
                capture_output=True,
                stderr=subprocess.DEVNULL
            )
            if check.returncode == 0:
                available_models.append(model)
            else:
                print(f"⚠️  Model {model} not available, skipping...")
        
        if available_models:
            result = compare_models_for_task(
                test_case["name"],
                test_case["prompt"],
                available_models
            )
            all_results.append(result)
    
    # Summary
    print("\n\n📊 SUMMARY REPORT")
    print("=" * 60)
    
    for task_result in all_results:
        print(f"\n📌 {task_result['task']}")
        
        # Find fastest successful model
        successful = [r for r in task_result['results'] if r['success']]
        if successful:
            fastest = min(successful, key=lambda x: x['time'])
            print(f"   🏆 Fastest: {fastest['model']} ({fastest['time']:.1f}s)")
            
            # Show performance comparison
            for r in successful:
                speed_ratio = r['time'] / fastest['time']
                print(f"   • {r['model']}: {r['time']:.1f}s ({speed_ratio:.1f}x)")
    
    # Save detailed results
    with open("coding_models_comparison.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\n✅ Full results saved to coding_models_comparison.json")

if __name__ == "__main__":
    main()
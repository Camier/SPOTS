#!/usr/bin/env python3
"""
Automated benchmark runner for coding models
Tests performance, accuracy, and resource usage
"""

import json
import time
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import statistics

class ModelBenchmark:
    def __init__(self):
        self.models = {
            "codegemma:2b": {"size": "1.6GB", "type": "ultra-fast"},
            "starcoder2:3b": {"size": "1.7GB", "type": "rapid"},
            "starcoder2:7b": {"size": "3.8GB", "type": "balanced"},
            "deepseek-coder:6.7b": {"size": "3.8GB", "type": "python"},
            "sqlcoder:7b": {"size": "4.1GB", "type": "sql"}
        }
        
        self.test_cases = {
            "bug_fix": {
                "prompt": "Fix this JavaScript error: TypeError: Cannot read property 'user' of undefined in req.session.user.id",
                "expected_patterns": ["null check", "optional chaining", "if statement", "guard clause"]
            },
            "code_review": {
                "prompt": "Review this authentication code for security issues:\n```\nfunction login(username, password) {\n  const user = db.query(`SELECT * FROM users WHERE username='${username}' AND password='${password}'`);\n  if (user) { session.user = user; return true; }\n  return false;\n}\n```",
                "expected_patterns": ["SQL injection", "password hashing", "parameterized query", "bcrypt"]
            },
            "sql_generation": {
                "prompt": "Generate SQL to find top 5 customers by total order value with their order count",
                "expected_patterns": ["GROUP BY", "ORDER BY", "COUNT", "SUM", "JOIN", "LIMIT"]
            },
            "explain_code": {
                "prompt": "Explain this Python code:\n```python\ndef fib(n, memo={}):\n    if n in memo: return memo[n]\n    if n <= 1: return n\n    memo[n] = fib(n-1, memo) + fib(n-2, memo)\n    return memo[n]\n```",
                "expected_patterns": ["memoization", "recursion", "dynamic programming", "cache", "fibonacci"]
            },
            "refactor": {
                "prompt": "Refactor this function to follow SOLID principles:\n```\ndef process_data(data):\n    # Validate\n    if not data: return None\n    # Parse JSON\n    parsed = json.loads(data)\n    # Transform\n    result = {k.upper(): v for k,v in parsed.items()}\n    # Save to file\n    with open('output.json', 'w') as f:\n        json.dump(result, f)\n    # Send email\n    send_email('admin@example.com', 'Data processed')\n    return result\n```",
                "expected_patterns": ["separate", "single responsibility", "class", "method", "dependency"]
            }
        }
    
    def measure_performance(self, model: str, prompt: str) -> Dict[str, Any]:
        """Measure model performance metrics"""
        start_time = time.time()
        
        # Memory before
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run model
        cmd = ["ollama", "run", model, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Timing
        total_time = time.time() - start_time
        
        # Memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "model": model,
            "total_time": round(total_time, 2),
            "memory_delta": round(mem_after - mem_before, 2),
            "output_length": len(result.stdout),
            "output": result.stdout[:500]  # First 500 chars
        }
    
    def evaluate_quality(self, output: str, expected_patterns: List[str]) -> float:
        """Evaluate output quality based on expected patterns"""
        found = sum(1 for pattern in expected_patterns if pattern.lower() in output.lower())
        return found / len(expected_patterns) * 100
    
    def run_benchmark(self, iterations: int = 3) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        results = {"models": {}, "summary": {}}
        
        for model in self.models:
            print(f"\n🔄 Testing {model}...")
            model_results = {
                "performance": {},
                "quality": {},
                "metrics": []
            }
            
            for test_name, test_case in self.test_cases.items():
                print(f"  📝 Running {test_name}...")
                
                # Skip SQL test for non-SQL models
                if test_name == "sql_generation" and self.models[model]["type"] != "sql":
                    continue
                
                # Run multiple iterations
                perf_results = []
                for i in range(iterations):
                    perf = self.measure_performance(model, test_case["prompt"])
                    perf_results.append(perf)
                    time.sleep(2)  # Cool down between runs
                
                # Average performance
                avg_time = statistics.mean([r["total_time"] for r in perf_results])
                avg_memory = statistics.mean([r["memory_delta"] for r in perf_results])
                
                # Quality evaluation (use last output)
                quality = self.evaluate_quality(
                    perf_results[-1]["output"], 
                    test_case["expected_patterns"]
                )
                
                model_results["performance"][test_name] = {
                    "avg_time": round(avg_time, 2),
                    "avg_memory": round(avg_memory, 2),
                    "quality_score": round(quality, 1)
                }
            
            results["models"][model] = model_results
        
        # Generate summary
        results["summary"] = self.generate_summary(results["models"])
        
        return results
    
    def generate_summary(self, model_results: Dict) -> Dict:
        """Generate benchmark summary"""
        summary = {
            "fastest_model": None,
            "best_quality": None,
            "most_efficient": None,
            "recommendations": {}
        }
        
        # Find fastest
        avg_times = {}
        for model, results in model_results.items():
            times = [r["avg_time"] for r in results["performance"].values()]
            avg_times[model] = statistics.mean(times) if times else float('inf')
        
        summary["fastest_model"] = min(avg_times, key=avg_times.get)
        
        # Find best quality
        avg_quality = {}
        for model, results in model_results.items():
            scores = [r["quality_score"] for r in results["performance"].values()]
            avg_quality[model] = statistics.mean(scores) if scores else 0
        
        summary["best_quality"] = max(avg_quality, key=avg_quality.get)
        
        # Recommendations
        summary["recommendations"] = {
            "quick_fixes": "codegemma:2b" if "codegemma:2b" in model_results else "starcoder2:3b",
            "production_code": "starcoder2:7b",
            "python_tasks": "deepseek-coder:6.7b",
            "sql_queries": "sqlcoder:7b"
        }
        
        return summary
    
    def save_results(self, results: Dict, filename: str = "benchmark_results.json"):
        """Save benchmark results to file"""
        output_path = Path("tools") / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {output_path}")
    
    def print_summary(self, results: Dict):
        """Print formatted summary"""
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY")
        print("="*60)
        
        summary = results["summary"]
        print(f"\n🏃 Fastest Model: {summary['fastest_model']}")
        print(f"🏆 Best Quality: {summary['best_quality']}")
        print(f"\n📌 Recommendations:")
        for use_case, model in summary['recommendations'].items():
            print(f"  • {use_case.replace('_', ' ').title()}: {model}")
        
        print("\n📈 Detailed Scores:")
        for model, data in results["models"].items():
            print(f"\n{model}:")
            for test, metrics in data["performance"].items():
                print(f"  {test}: {metrics['quality_score']}% quality, {metrics['avg_time']}s")

def main():
    print("🚀 Starting Coding Model Benchmarks...")
    print("This will take several minutes per model...\n")
    
    benchmark = ModelBenchmark()
    
    # Quick test mode
    print("Run quick test (1 iteration) or full benchmark (3 iterations)?")
    mode = input("Enter 'quick' or 'full' [quick]: ").strip() or "quick"
    iterations = 1 if mode == "quick" else 3
    
    # Run benchmarks
    results = benchmark.run_benchmark(iterations=iterations)
    
    # Save and display results
    benchmark.save_results(results)
    benchmark.print_summary(results)
    
    print("\n✅ Benchmark complete!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Ollama Hybrid Analyzer - Rapid insights + Deep analysis
"""

import requests
import time
import json
from typing import Dict, Tuple, Optional
from ollama_model_manager import OllamaModelManager

class HybridAnalyzer:
    """Two-tier analysis: Quick insights followed by deep analysis"""
    
    def __init__(self):
        self.manager = OllamaModelManager()
        self.base_url = "http://localhost:11434"
        
    def rapid_insight(self, prompt: str, task: str = "general") -> Tuple[str, float]:
        """Get quick insight with small, fast model"""
        
        models = self.manager.get_tiered_models(task)
        rapid_model = models.get('rapid')
        
        if not rapid_model:
            return "No rapid model available", 0.0
        
        start_time = time.time()
        
        # Check if model is installed
        installed = self.manager.get_installed_models()
        if rapid_model not in installed:
            return f"Model {rapid_model} not installed", elapsed
        
        # Quick analysis with short response
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": rapid_model,
                "prompt": f"Quick answer (1-2 sentences): {prompt}",
                "options": {"num_predict": 50, "temperature": 0.3},
                "stream": False
            },
            timeout=10
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return response.json().get('response', ''), elapsed
        else:
            return f"Error: {response.status_code}", elapsed
    
    def deep_analysis(self, prompt: str, task: str = "general") -> Tuple[str, float]:
        """Get comprehensive analysis with larger model"""
        
        models = self.manager.get_tiered_models(task)
        deep_model = models.get('deep')
        
        if not deep_model:
            return "No deep model available", 0.0
        
        start_time = time.time()
        
        # Detailed analysis
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": deep_model,
                "prompt": f"Detailed analysis:\n{prompt}",
                "options": {"temperature": 0.7},
                "stream": False
            },
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return response.json().get('response', ''), elapsed
        else:
            return f"Error: {response.status_code}", elapsed
    
    def hybrid_analyze(self, prompt: str, task: str = "general", verbose: bool = True) -> Dict:
        """Perform both rapid and deep analysis"""
        
        models = self.manager.get_tiered_models(task)
        
        if verbose:
            print(f"🚀 Rapid Model: {models['rapid']} (speed: {models['rapid_specs']['speed']}/10)")
            print(f"🧠 Deep Model: {models['deep']} (quality: {models['deep_specs']['quality']}/10)")
            print("-" * 60)
        
        # Phase 1: Rapid insight
        if verbose:
            print("⚡ Getting rapid insight...")
        rapid_result, rapid_time = self.rapid_insight(prompt, task)
        
        result = {
            "prompt": prompt,
            "rapid": {
                "model": models['rapid'],
                "response": rapid_result,
                "time": rapid_time,
                "tokens_per_sec": len(rapid_result.split()) / rapid_time if rapid_time > 0 else 0
            }
        }
        
        if verbose:
            print(f"✓ Rapid insight ({rapid_time:.1f}s): {rapid_result[:150]}...")
            
        # Decision: Should we do deep analysis?
        needs_deep = self._needs_deep_analysis(prompt, rapid_result)
        
        if needs_deep:
            if verbose:
                print("\n🔍 Proceeding with deep analysis...")
            deep_result, deep_time = self.deep_analysis(prompt, task)
            
            result["deep"] = {
                "model": models['deep'],
                "response": deep_result,
                "time": deep_time,
                "tokens_per_sec": len(deep_result.split()) / deep_time if deep_time > 0 else 0
            }
            
            if verbose:
                print(f"✓ Deep analysis complete ({deep_time:.1f}s)")
        else:
            if verbose:
                print("\n✅ Rapid insight sufficient - skipping deep analysis")
            result["deep"] = None
        
        result["total_time"] = sum(r["time"] for r in [result["rapid"], result.get("deep", {})] if r)
        
        return result
    
    def _needs_deep_analysis(self, prompt: str, rapid_response: str) -> bool:
        """Determine if deep analysis is needed"""
        
        # Simple heuristics
        complex_keywords = ['explain', 'analyze', 'compare', 'why', 'how does', 'architecture', 'design']
        simple_keywords = ['what is', 'define', 'list', 'name', 'count', 'yes/no']
        
        prompt_lower = prompt.lower()
        
        # Check for simple questions
        if any(keyword in prompt_lower for keyword in simple_keywords):
            return False
        
        # Check for complex questions
        if any(keyword in prompt_lower for keyword in complex_keywords):
            return True
        
        # If rapid response is very short or seems incomplete
        if len(rapid_response.split()) < 20 or rapid_response.endswith('...'):
            return True
        
        return False

def demonstrate_hybrid_analysis():
    """Show hybrid analysis in action"""
    
    analyzer = HybridAnalyzer()
    
    # Test cases showing when to use rapid vs deep
    test_cases = [
        {
            "prompt": "What is 2+2?",
            "task": "general",
            "expected": "rapid_only"
        },
        {
            "prompt": "Fix this SQL injection: cursor.execute(f'SELECT * FROM users WHERE id={id}')",
            "task": "code",
            "expected": "rapid_only"
        },
        {
            "prompt": "Explain the architecture of a microservices system and compare it with monolithic architecture",
            "task": "general",
            "expected": "needs_deep"
        },
        {
            "prompt": "Analyze this code for security vulnerabilities and suggest improvements:\n\n@app.route('/login')\ndef login():\n    username = request.args.get('username')\n    password = request.args.get('password')\n    query = f\"SELECT * FROM users WHERE username='{username}' AND password='{password}'\"\n    user = db.execute(query).fetchone()\n    if user:\n        session['user'] = username\n        return 'Success'\n    return 'Failed'",
            "task": "code",
            "expected": "needs_deep"
        }
    ]
    
    print("🔬 HYBRID ANALYSIS DEMONSTRATION\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test['expected'].replace('_', ' ').title()}")
        print(f"Task: {test['task']}")
        print(f"Prompt: {test['prompt'][:100]}...")
        print("-" * 80)
        
        result = analyzer.hybrid_analyze(test['prompt'], test['task'], verbose=True)
        
        print(f"\n📊 Summary:")
        print(f"- Total time: {result['total_time']:.1f}s")
        print(f"- Rapid model: {result['rapid']['model']} ({result['rapid']['time']:.1f}s)")
        if result['deep']:
            print(f"- Deep model: {result['deep']['model']} ({result['deep']['time']:.1f}s)")
            print(f"- Deep analysis added {result['deep']['time']:.1f}s for comprehensive answer")
        else:
            print("- Deep analysis skipped (rapid was sufficient)")

def create_smart_code_analyzer():
    """Create a smart code analysis function"""
    
    analyzer = HybridAnalyzer()
    
    def analyze_code(code: str, concern: str = "general") -> Dict:
        """Analyze code with appropriate depth"""
        
        # Map concerns to prompts
        concern_prompts = {
            "security": f"Identify security vulnerabilities in this code:\n{code}",
            "performance": f"Analyze performance issues in this code:\n{code}",
            "style": f"Check code style issues:\n{code}",
            "bugs": f"Find potential bugs in this code:\n{code}",
            "general": f"Review this code:\n{code}"
        }
        
        prompt = concern_prompts.get(concern, concern_prompts["general"])
        
        # Simple style checks might only need rapid
        # Security and performance usually need deep
        if concern in ["security", "performance", "bugs"]:
            # Force deep analysis for critical concerns
            result = analyzer.hybrid_analyze(prompt, "code", verbose=False)
            if not result.get('deep'):
                # If deep was skipped, force it
                deep_response, deep_time = analyzer.deep_analysis(prompt, "code")
                result['deep'] = {
                    "model": analyzer.manager.get_tiered_models("code")['deep'],
                    "response": deep_response,
                    "time": deep_time
                }
        else:
            result = analyzer.hybrid_analyze(prompt, "code", verbose=False)
        
        return result
    
    return analyze_code

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demonstrate_hybrid_analysis()
    else:
        # Interactive mode
        analyzer = HybridAnalyzer()
        
        print("🤖 Hybrid Analyzer - Rapid + Deep Intelligence")
        print("=" * 60)
        
        models = analyzer.manager.get_tiered_models()
        print(f"Rapid: {models['rapid']} | Deep: {models['deep']}")
        print("\nEnter your prompt (or 'quit' to exit):\n")
        
        while True:
            prompt = input("> ")
            if prompt.lower() in ['quit', 'exit']:
                break
            
            print()
            result = analyzer.hybrid_analyze(prompt, verbose=True)
            
            print("\n" + "="*60)
            print("Full Rapid Response:")
            print(result['rapid']['response'])
            
            if result.get('deep'):
                print("\n" + "="*60)
                print("Full Deep Analysis:")
                print(result['deep']['response'])
            
            print("\n" + "="*60)
#!/usr/bin/env python3
"""
Ollama Model Manager - Smart model selection and management
"""

import requests
import psutil
import json
import subprocess
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class OllamaModelManager:
    """Intelligent Ollama model management"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model_registry = self._load_model_registry()
        self.performance_cache = self._load_performance_cache()
        
    def _load_model_registry(self) -> Dict:
        """Model specifications and requirements"""
        return {
            # Code models
            "deepseek-coder:6.7b": {"ram": 8, "category": "code", "quality": 9, "speed": 7},
            "codellama:7b": {"ram": 6, "category": "code", "quality": 8, "speed": 8},
            "codellama:7b-q4_K_M": {"ram": 4, "category": "code", "quality": 7, "speed": 9},
            "codegemma:2b": {"ram": 2, "category": "code", "quality": 6, "speed": 10},
            "starcoder2:3b": {"ram": 3, "category": "code", "quality": 7, "speed": 9},
            
            # General models  
            "llama3.2:latest": {"ram": 3, "category": "general", "quality": 8, "speed": 9},
            "mistral:7b": {"ram": 5, "category": "general", "quality": 9, "speed": 8},
            "mistral:7b-instruct": {"ram": 5, "category": "general", "quality": 9, "speed": 8},
            "phi3:mini": {"ram": 2, "category": "general", "quality": 7, "speed": 10},
            "phi3:medium": {"ram": 8, "category": "general", "quality": 8, "speed": 7},
            "gemma2:9b": {"ram": 7, "category": "general", "quality": 8, "speed": 7},
            "tinyllama": {"ram": 1, "category": "general", "quality": 5, "speed": 10},
            
            # Specialized
            "granite3.3:8b": {"ram": 6, "category": "enterprise", "quality": 8, "speed": 8},
            "solar:10.7b": {"ram": 8, "category": "long-context", "quality": 9, "speed": 6},
            "sqlcoder:7b": {"ram": 6, "category": "sql", "quality": 9, "speed": 8},
        }
    
    def _load_performance_cache(self) -> Dict:
        """Load cached performance data"""
        cache_file = Path("ollama_performance_cache.json")
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return {}
    
    def get_system_info(self) -> Dict:
        """Get current system resources"""
        return {
            "total_ram_gb": psutil.virtual_memory().total / (1024**3),
            "available_ram_gb": psutil.virtual_memory().available / (1024**3),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "has_gpu": self._check_gpu()
        }
    
    def _check_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True)
            return result.returncode == 0
        except:
            # Check for Apple Silicon
            import platform
            return platform.processor() == 'arm' and platform.system() == 'Darwin'
    
    def get_installed_models(self) -> List[str]:
        """Get list of installed models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return [m['name'] for m in response.json()['models']]
        except:
            pass
        return []
    
    def recommend_model(self, 
                       task: str = "general",
                       quality_preference: str = "balanced",
                       max_ram_gb: Optional[float] = None) -> Optional[str]:
        """Recommend best model for task and constraints"""
        
        system = self.get_system_info()
        available_ram = max_ram_gb or system['available_ram_gb'] - 2  # Leave 2GB buffer
        
        # Filter models by task and RAM
        suitable_models = []
        for model, specs in self.model_registry.items():
            if (task == "any" or specs['category'] == task) and specs['ram'] <= available_ram:
                suitable_models.append((model, specs))
        
        if not suitable_models:
            return None
        
        # Sort by preference
        if quality_preference == "fast":
            suitable_models.sort(key=lambda x: x[1]['speed'], reverse=True)
        elif quality_preference == "best":
            suitable_models.sort(key=lambda x: x[1]['quality'], reverse=True)
        else:  # balanced
            suitable_models.sort(key=lambda x: x[1]['quality'] * x[1]['speed'], reverse=True)
        
        return suitable_models[0][0]
    
    def get_tiered_models(self, task: str = "general") -> Dict[str, Optional[str]]:
        """Get both rapid and deep analysis models"""
        
        system = self.get_system_info()
        available_ram = system['available_ram_gb'] - 2
        
        # Find best models for each tier
        rapid_model = None
        deep_model = None
        
        # Rapid: prioritize speed (< 3GB RAM)
        for model, specs in self.model_registry.items():
            if (task == "any" or specs['category'] == task) and specs['ram'] <= 3:
                if not rapid_model or specs['speed'] > self.model_registry[rapid_model]['speed']:
                    rapid_model = model
        
        # Deep: prioritize quality (use available RAM)
        for model, specs in self.model_registry.items():
            if (task == "any" or specs['category'] == task) and specs['ram'] <= available_ram:
                if not deep_model or specs['quality'] > self.model_registry[deep_model]['quality']:
                    deep_model = model
        
        return {
            "rapid": rapid_model,
            "deep": deep_model,
            "rapid_specs": self.model_registry.get(rapid_model) if rapid_model else None,
            "deep_specs": self.model_registry.get(deep_model) if deep_model else None
        }
    
    def test_model(self, model_name: str, test_prompt: str = None) -> Dict:
        """Test model performance"""
        
        if test_prompt is None:
            test_prompt = "Write a Python function to calculate factorial"
        
        start_time = time.time()
        initial_mem = psutil.virtual_memory().used / (1024**3)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": test_prompt,
                    "options": {"num_predict": 50},
                    "stream": False
                },
                timeout=30
            )
            
            elapsed_time = time.time() - start_time
            final_mem = psutil.virtual_memory().used / (1024**3)
            
            if response.status_code == 200:
                result = response.json()
                tokens = len(result.get('response', '').split())
                
                return {
                    "success": True,
                    "model": model_name,
                    "time_seconds": elapsed_time,
                    "tokens_generated": tokens,
                    "tokens_per_second": tokens / elapsed_time if elapsed_time > 0 else 0,
                    "memory_used_gb": final_mem - initial_mem,
                    "response_preview": result.get('response', '')[:200]
                }
            else:
                return {
                    "success": False,
                    "model": model_name,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "model": model_name,
                "error": str(e)
            }
    
    def auto_select_and_run(self, prompt: str, task: str = "general") -> Tuple[str, str]:
        """Automatically select and run best available model"""
        
        # Get recommendation
        model = self.recommend_model(task)
        if not model:
            return None, "No suitable model found for available RAM"
        
        # Check if installed
        installed = self.get_installed_models()
        if model not in installed:
            print(f"Model {model} not installed. Pulling...")
            self.pull_model(model)
        
        # Run inference
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return model, response.json().get('response', '')
            else:
                return model, f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return model, f"Error: {str(e)}"
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model"""
        try:
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error pulling model: {e}")
            return False
    
    def benchmark_all_models(self, task: str = "code") -> List[Dict]:
        """Benchmark all suitable models for a task"""
        
        system = self.get_system_info()
        results = []
        
        test_prompts = {
            "code": "Write a Python function to find prime numbers",
            "general": "Explain quantum computing in simple terms",
            "sql": "Write SQL to find top 10 customers by revenue"
        }
        
        prompt = test_prompts.get(task, test_prompts["general"])
        
        for model, specs in self.model_registry.items():
            if specs['category'] == task and specs['ram'] <= system['available_ram_gb'] - 2:
                print(f"Testing {model}...")
                result = self.test_model(model, prompt)
                results.append(result)
                
                # Save to cache
                if result['success']:
                    self.performance_cache[model] = {
                        "tokens_per_second": result['tokens_per_second'],
                        "memory_used_gb": result['memory_used_gb']
                    }
        
        # Save cache
        with open("ollama_performance_cache.json", "w") as f:
            json.dump(self.performance_cache, f, indent=2)
        
        return results
    
    def suggest_models_for_system(self) -> Dict[str, List[str]]:
        """Suggest models based on current system"""
        
        system = self.get_system_info()
        available_ram = system['available_ram_gb'] - 2
        
        suggestions = {
            "code": [],
            "general": [],
            "fast": [],
            "best_quality": []
        }
        
        for model, specs in self.model_registry.items():
            if specs['ram'] <= available_ram:
                if specs['category'] == 'code':
                    suggestions['code'].append(model)
                elif specs['category'] == 'general':
                    suggestions['general'].append(model)
                
                if specs['speed'] >= 9:
                    suggestions['fast'].append(model)
                if specs['quality'] >= 8:
                    suggestions['best_quality'].append(model)
        
        return suggestions

def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama Model Manager")
    parser.add_argument("command", choices=["recommend", "test", "benchmark", "suggest", "run"])
    parser.add_argument("--task", default="general", help="Task type: code, general, sql")
    parser.add_argument("--quality", default="balanced", choices=["fast", "best", "balanced"])
    parser.add_argument("--model", help="Specific model to test")
    parser.add_argument("--prompt", help="Prompt for testing")
    
    args = parser.parse_args()
    
    manager = OllamaModelManager()
    
    if args.command == "recommend":
        model = manager.recommend_model(args.task, args.quality)
        print(f"Recommended model for {args.task}: {model}")
        
    elif args.command == "test":
        if not args.model:
            print("Please specify --model")
            return
        result = manager.test_model(args.model, args.prompt)
        print(json.dumps(result, indent=2))
        
    elif args.command == "benchmark":
        results = manager.benchmark_all_models(args.task)
        print(f"\nBenchmark Results for {args.task}:")
        for r in sorted(results, key=lambda x: x.get('tokens_per_second', 0), reverse=True):
            if r['success']:
                print(f"{r['model']}: {r['tokens_per_second']:.1f} tok/s, {r['memory_used_gb']:.1f}GB")
            else:
                print(f"{r['model']}: Failed - {r['error']}")
                
    elif args.command == "suggest":
        suggestions = manager.suggest_models_for_system()
        print("\nModel Suggestions for Your System:")
        for category, models in suggestions.items():
            print(f"\n{category.title()}:")
            for model in models[:3]:
                print(f"  - {model}")
                
    elif args.command == "run":
        prompt = args.prompt or input("Enter prompt: ")
        model, response = manager.auto_select_and_run(prompt, args.task)
        print(f"\nUsing model: {model}")
        print(f"\nResponse:\n{response}")

if __name__ == "__main__":
    main()
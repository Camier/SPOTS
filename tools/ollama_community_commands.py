#!/usr/bin/env python3
"""
Community-Inspired Ollama Commands using Hybrid Framework
Based on real usage patterns from GitHub, n8n, Reddit communities
"""

import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ollama_hybrid_analyzer import HybridAnalyzer
from ollama_model_manager import OllamaModelManager

class OllamaCommunityCommands:
    """Community-inspired commands with hybrid intelligence"""
    
    def __init__(self):
        self.analyzer = HybridAnalyzer()
        self.manager = OllamaModelManager()
        self.cache_dir = Path(".ollama_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    # ========== COMPARE COMMAND ==========
    def compare(self, prompt: str, models: Optional[List[str]] = None) -> Dict:
        """
        Compare responses from multiple models (inspired by ollama-multirun)
        Uses rapid first, then deep for interesting differences
        """
        if not models:
            # Auto-select diverse models based on available RAM
            models = self._select_comparison_models()
        
        print(f"🔄 Comparing {len(models)} models...")
        results = {}
        
        # Phase 1: Rapid comparison
        for model in models:
            start = time.time()
            response = self._run_model(model, prompt, max_tokens=50)
            results[model] = {
                "rapid": response,
                "time": time.time() - start,
                "tokens": len(response.split())
            }
        
        # Analyze differences
        responses = [r["rapid"] for r in results.values()]
        similarity = self._calculate_similarity(responses)
        
        # Phase 2: Deep dive if responses differ significantly
        if similarity < 0.8:  # Significant differences
            print("🔍 Detected significant differences - running deep analysis...")
            best_model = max(results.keys(), key=lambda m: len(results[m]["rapid"]))
            deep_response = self._run_model(best_model, prompt, max_tokens=500)
            results["deep_analysis"] = {
                "model": best_model,
                "response": deep_response,
                "reason": "Models showed different perspectives"
            }
        
        return results
    
    # ========== BATCH COMMAND ==========
    def batch(self, files: List[str], operation: str, output_dir: str = "batch_output") -> Dict:
        """
        Process multiple files with AI (document processing pattern)
        Uses rapid for triage, deep for complex files
        """
        Path(output_dir).mkdir(exist_ok=True)
        results = {}
        
        # Triage files with rapid model
        print(f"📋 Triaging {len(files)} files...")
        file_complexity = {}
        
        for file_path in files:
            content = self._read_file(file_path)[:500]  # First 500 chars
            complexity_prompt = f"Rate complexity (1-10) of this {operation} task:\n{content}"
            
            rapid_response = self.analyzer.rapid_insight(complexity_prompt, "general")[0]
            try:
                complexity = int(''.join(filter(str.isdigit, rapid_response)) or '5')
                file_complexity[file_path] = min(10, max(1, complexity))
            except:
                file_complexity[file_path] = 5
        
        # Process files based on complexity
        for file_path, complexity in file_complexity.items():
            print(f"\n📄 Processing {Path(file_path).name} (complexity: {complexity}/10)")
            
            content = self._read_file(file_path)
            prompt = self._get_operation_prompt(operation, content)
            
            if complexity <= 3:
                # Simple file - rapid only
                response, elapsed = self.analyzer.rapid_insight(prompt)
                process_type = "rapid"
            else:
                # Complex file - full hybrid
                result = self.analyzer.hybrid_analyze(prompt, verbose=False)
                response = result.get("deep", result["rapid"])["response"]
                elapsed = result["total_time"]
                process_type = "hybrid"
            
            # Save output
            output_file = Path(output_dir) / f"{Path(file_path).stem}_{operation}.txt"
            output_file.write_text(response)
            
            results[file_path] = {
                "complexity": complexity,
                "process_type": process_type,
                "time": elapsed,
                "output": str(output_file)
            }
        
        return results
    
    # ========== WATCH COMMAND ==========
    def watch(self, paths: List[str], on_change_command: str = "analyze"):
        """
        Monitor files and auto-analyze changes (automation pattern)
        Uses rapid for quick checks, deep for significant changes
        """
        print(f"👁️ Watching {len(paths)} paths...")
        file_hashes = {}
        
        # Initial hashing
        for path in paths:
            if Path(path).exists():
                file_hashes[path] = self._get_file_hash(path)
        
        try:
            while True:
                for path in paths:
                    if Path(path).exists():
                        current_hash = self._get_file_hash(path)
                        
                        if path not in file_hashes or file_hashes[path] != current_hash:
                            print(f"\n🔄 Change detected in {path}")
                            
                            # Quick assessment with rapid
                            content = self._read_file(path)[:1000]
                            change_size = abs(len(content) - len(file_hashes.get(path, "")))
                            
                            if change_size < 100:
                                # Small change - rapid analysis
                                prompt = f"Summarize this small change:\n{content}"
                                response, _ = self.analyzer.rapid_insight(prompt)
                                print(f"⚡ Rapid: {response}")
                            else:
                                # Significant change - deep analysis
                                prompt = f"Analyze these changes in {path}:\n{content}"
                                result = self.analyzer.hybrid_analyze(prompt, verbose=True)
                            
                            file_hashes[path] = current_hash
                
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print("\n✋ Watch mode stopped")
    
    # ========== SHELL COMMAND ==========
    def shell(self, command: str) -> Dict:
        """
        AI-powered shell assistance (inspired by aichat shell mode)
        Rapid for simple commands, deep for complex scripts
        """
        complexity_indicators = ['&&', '||', '|', 'for', 'while', 'if', ';', 'awk', 'sed']
        is_complex = any(ind in command for ind in complexity_indicators)
        
        if not is_complex and len(command.split()) < 5:
            # Simple command - rapid help
            prompt = f"Explain this shell command briefly: {command}"
            response, elapsed = self.analyzer.rapid_insight(prompt, "code")
            
            return {
                "command": command,
                "explanation": response,
                "suggestions": None,
                "mode": "rapid",
                "time": elapsed
            }
        else:
            # Complex command - full analysis
            prompt = f"""Analyze this shell command:
Command: {command}

Provide:
1. What it does
2. Potential issues
3. Safer alternatives
4. Performance considerations"""
            
            result = self.analyzer.hybrid_analyze(prompt, "code", verbose=False)
            
            return {
                "command": command,
                "explanation": result["rapid"]["response"],
                "detailed_analysis": result.get("deep", {}).get("response"),
                "mode": "hybrid",
                "time": result["total_time"]
            }
    
    # ========== EXPLAIN COMMAND ==========
    def explain(self, code: str, language: str = "auto") -> Dict:
        """
        Intelligent code explanation with depth control
        """
        # Detect complexity
        lines = code.strip().split('\n')
        complexity_score = (
            len(lines) +
            code.count('if') * 2 +
            code.count('for') * 3 +
            code.count('while') * 3 +
            code.count('class') * 5 +
            code.count('def') * 2
        )
        
        if complexity_score < 20:
            # Simple code - rapid explanation
            prompt = f"Explain this {language} code concisely:\n```\n{code}\n```"
            response, elapsed = self.analyzer.rapid_insight(prompt, "code")
            
            return {
                "mode": "rapid",
                "explanation": response,
                "complexity": "simple",
                "time": elapsed
            }
        else:
            # Complex code - hybrid approach
            prompt = f"""Explain this {language} code:

```{language}
{code}
```

Provide:
1. Overall purpose
2. Key components
3. How it works
4. Potential improvements"""
            
            result = self.analyzer.hybrid_analyze(prompt, "code", verbose=True)
            
            return {
                "mode": "hybrid",
                "quick_summary": result["rapid"]["response"],
                "detailed_explanation": result.get("deep", {}).get("response"),
                "complexity": "complex",
                "time": result["total_time"]
            }
    
    # ========== REFACTOR COMMAND ==========
    def refactor(self, code: str, style: str = "clean") -> Dict:
        """
        Smart code refactoring with style preferences
        """
        styles = {
            "clean": "Make the code cleaner and more readable",
            "performance": "Optimize for performance",
            "functional": "Refactor to functional programming style",
            "modern": "Modernize using latest language features",
            "secure": "Focus on security improvements"
        }
        
        # Quick assessment first
        assess_prompt = f"Rate the need for refactoring (1-10): \n{code[:200]}..."
        need_score, _ = self.analyzer.rapid_insight(assess_prompt, "code")
        
        try:
            score = int(''.join(filter(str.isdigit, need_score)) or '5')
        except:
            score = 5
        
        if score <= 3:
            return {
                "needs_refactoring": False,
                "reason": "Code is already well-written",
                "score": score
            }
        
        # Proceed with refactoring
        refactor_prompt = f"""{styles.get(style, styles['clean'])}:

```
{code}
```

Provide the refactored code with explanations for changes."""
        
        result = self.analyzer.hybrid_analyze(refactor_prompt, "code", verbose=False)
        
        return {
            "needs_refactoring": True,
            "score": score,
            "quick_improvements": result["rapid"]["response"],
            "refactored_code": result.get("deep", {}).get("response"),
            "style": style,
            "time": result.get("total_time", 0)
        }
    
    # ========== SUMMARIZE COMMAND ==========
    def summarize(self, content: str, style: str = "brief") -> Dict:
        """
        Document summarization with different styles
        """
        styles = {
            "brief": "one paragraph summary",
            "bullets": "bullet points",
            "technical": "technical summary with key details",
            "executive": "executive summary",
            "eli5": "explain like I'm 5"
        }
        
        word_count = len(content.split())
        
        if word_count < 200:
            # Short content - rapid only
            prompt = f"Provide a {styles[style]} of: {content}"
            summary, elapsed = self.analyzer.rapid_insight(prompt)
            
            return {
                "style": style,
                "summary": summary,
                "mode": "rapid",
                "original_words": word_count,
                "time": elapsed
            }
        else:
            # Long content - hybrid approach
            prompt = f"Provide a {styles[style]} of this text:\n\n{content[:2000]}..."
            
            result = self.analyzer.hybrid_analyze(prompt, verbose=False)
            
            return {
                "style": style,
                "quick_summary": result["rapid"]["response"],
                "detailed_summary": result.get("deep", {}).get("response"),
                "mode": "hybrid",
                "original_words": word_count,
                "time": result["total_time"]
            }
    
    # ========== HELPER METHODS ==========
    def _select_comparison_models(self) -> List[str]:
        """Auto-select diverse models for comparison"""
        suggestions = self.manager.suggest_models_for_system()
        selected = []
        
        # Get one from each category
        if suggestions['fast']:
            selected.append(suggestions['fast'][0])
        if suggestions['general']:
            selected.append(suggestions['general'][0])
        if suggestions['code']:
            selected.append(suggestions['code'][0])
        
        return selected[:3]  # Max 3 models
    
    def _run_model(self, model: str, prompt: str, max_tokens: int = 100) -> str:
        """Run a specific model"""
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "options": {"num_predict": max_tokens},
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('response', '')
        return f"Error: {response.status_code}"
    
    def _calculate_similarity(self, texts: List[str]) -> float:
        """Calculate similarity between responses"""
        if len(texts) < 2:
            return 1.0
        
        # Simple word overlap similarity
        word_sets = [set(text.lower().split()) for text in texts]
        intersection = set.intersection(*word_sets)
        union = set.union(*word_sets)
        
        return len(intersection) / len(union) if union else 1.0
    
    def _read_file(self, path: str) -> str:
        """Read file content safely"""
        try:
            return Path(path).read_text()
        except:
            return ""
    
    def _get_file_hash(self, path: str) -> str:
        """Get file hash for change detection"""
        content = self._read_file(path)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_operation_prompt(self, operation: str, content: str) -> str:
        """Get prompt for batch operations"""
        prompts = {
            "summarize": f"Summarize this document:\n{content}",
            "analyze": f"Analyze this content:\n{content}",
            "translate": f"Translate to Spanish:\n{content}",
            "review": f"Review this code:\n{content}",
            "test": f"Generate tests for this code:\n{content}"
        }
        return prompts.get(operation, f"{operation}: {content}")


def main():
    """Demo the commands"""
    import sys
    
    cmd = OllamaCommunityCommands()
    
    if len(sys.argv) < 2:
        print("""
🚀 Ollama Community Commands

Usage:
  python ollama_community_commands.py <command> [args]

Commands:
  compare <prompt>              - Compare responses from multiple models  
  batch <operation> <files...>  - Process multiple files
  watch <paths...>              - Monitor files for changes
  shell <command>               - Get shell command help
  explain <file>                - Explain code from file
  refactor <file> [style]       - Refactor code (clean/performance/secure)
  summarize <file> [style]      - Summarize document (brief/bullets/technical)

Examples:
  python ollama_community_commands.py compare "What is recursion?"
  python ollama_community_commands.py batch summarize *.txt
  python ollama_community_commands.py shell "find . -name '*.py' | xargs grep TODO"
  python ollama_community_commands.py explain main.py
  python ollama_community_commands.py refactor vulnerable.py secure
""")
        return
    
    command = sys.argv[1]
    
    if command == "compare" and len(sys.argv) > 2:
        prompt = ' '.join(sys.argv[2:])
        results = cmd.compare(prompt)
        
        print("\n📊 Comparison Results:")
        for model, result in results.items():
            if model != "deep_analysis":
                print(f"\n{model}: ({result['time']:.1f}s)")
                print(f"  {result['rapid'][:100]}...")
    
    elif command == "shell" and len(sys.argv) > 2:
        shell_cmd = ' '.join(sys.argv[2:])
        result = cmd.shell(shell_cmd)
        
        print(f"\n🔧 Shell Command Analysis ({result['mode']} mode)")
        print(f"Command: {result['command']}")
        print(f"\n📝 Explanation: {result['explanation']}")
        
        if result.get('detailed_analysis'):
            print(f"\n🔍 Detailed Analysis:\n{result['detailed_analysis']}")
    
    elif command == "explain" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        if Path(file_path).exists():
            code = Path(file_path).read_text()
            result = cmd.explain(code)
            
            print(f"\n📖 Code Explanation ({result['complexity']} - {result['mode']} mode)")
            if result['mode'] == 'rapid':
                print(result['explanation'])
            else:
                print(f"\nQuick Summary: {result['quick_summary']}")
                if result.get('detailed_explanation'):
                    print(f"\nDetailed Explanation:\n{result['detailed_explanation']}")
    
    else:
        print(f"Command '{command}' not fully implemented in demo. See usage above.")

if __name__ == "__main__":
    main()
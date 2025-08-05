#!/usr/bin/env python3
"""
StarCoder2 and specialized model commands
Integrates with the Ollama framework for practical usage
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
import sys

class StarCoderCommands:
    """Specialized coding commands using StarCoder2 and other models"""
    
    def __init__(self):
        self.models = {
            "rapid": "starcoder2:3b",
            "balanced": "starcoder2:7b",
            "sql": "sqlcoder:7b",
            "python": "deepseek-coder:6.7b",
            "explain": "codegemma:2b",
            "secure": "granite3.3:8b"
        }
        
    def quick_fix(self, code: str, issue: str = ""):
        """Quick syntax fix using rapid model"""
        prompt = f"Fix this code issue{f': {issue}' if issue else ''}:\n{code}"
        return self._run_ollama(self.models["rapid"], prompt)
    
    def review_code(self, file_path: str, focus: str = "all"):
        """Deep code review with focus areas"""
        if not Path(file_path).exists():
            return {"error": f"File not found: {file_path}"}
        
        code = Path(file_path).read_text()
        
        focus_prompts = {
            "security": "Review for security vulnerabilities:",
            "performance": "Review for performance issues:",
            "style": "Review for code style and best practices:",
            "bugs": "Review for potential bugs:",
            "all": "Comprehensive code review:"
        }
        
        prompt = f"{focus_prompts.get(focus, focus_prompts['all'])}\n\n{code[:2000]}"
        return self._run_ollama(self.models["balanced"], prompt)
    
    def generate_sql(self, description: str, schema: Optional[str] = None):
        """Generate SQL from natural language"""
        prompt = f"Generate SQL query for: {description}"
        if schema:
            prompt += f"\n\nSchema:\n{schema}"
        
        # Try SQL specialist first, fallback to StarCoder
        result = self._run_ollama(self.models.get("sql", self.models["balanced"]), prompt)
        if "error" in result:
            result = self._run_ollama(self.models["balanced"], prompt)
        
        return result
    
    def explain_code(self, code: str, level: str = "normal"):
        """Explain code at different levels"""
        levels = {
            "eli5": "Explain this code like I'm 5:",
            "beginner": "Explain this code for a beginner:",
            "normal": "Explain this code:",
            "expert": "Provide expert-level analysis of this code:"
        }
        
        prompt = f"{levels.get(level, levels['normal'])}\n\n{code}"
        return self._run_ollama(self.models.get("explain", self.models["rapid"]), prompt)
    
    def refactor(self, code: str, style: str = "clean"):
        """Refactor code with different styles"""
        styles = {
            "clean": "Refactor for clarity and cleanliness:",
            "performance": "Optimize for performance:",
            "functional": "Refactor to functional style:",
            "modern": "Modernize this code:",
            "secure": "Refactor for security:"
        }
        
        prompt = f"{styles.get(style, styles['clean'])}\n\n{code}"
        
        # Use specialized model for security refactoring
        model = self.models["secure"] if style == "secure" else self.models["balanced"]
        return self._run_ollama(model, prompt)
    
    def debug_error(self, error_message: str, code_context: str = ""):
        """Debug error with context"""
        prompt = f"Debug this error:\n{error_message}"
        if code_context:
            prompt += f"\n\nCode context:\n{code_context}"
        prompt += "\n\nProvide fix and explanation."
        
        return self._run_ollama(self.models["balanced"], prompt)
    
    def generate_tests(self, code: str, framework: str = "pytest"):
        """Generate unit tests for code"""
        frameworks = {
            "pytest": "Generate pytest tests",
            "unittest": "Generate unittest tests",
            "jest": "Generate Jest tests",
            "mocha": "Generate Mocha tests"
        }
        
        prompt = f"{frameworks.get(framework, 'Generate tests')} for:\n\n{code}"
        return self._run_ollama(self.models["balanced"], prompt)
    
    def convert_code(self, code: str, from_lang: str, to_lang: str):
        """Convert code between languages"""
        prompt = f"Convert this {from_lang} code to {to_lang}:\n\n{code}"
        return self._run_ollama(self.models["balanced"], prompt)
    
    def _run_ollama(self, model: str, prompt: str) -> Dict:
        """Run Ollama model and return result"""
        try:
            start = time.time()
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            elapsed = time.time() - start
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "response": result.stdout.strip(),
                    "model": model,
                    "time": elapsed
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "model": model
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout after 30s",
                "model": model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }

def main():
    """CLI interface for StarCoder commands"""
    import argparse
    
    parser = argparse.ArgumentParser(description="StarCoder2 coding commands")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Quick fix
    fix_parser = subparsers.add_parser("fix", help="Quick code fix")
    fix_parser.add_argument("code", help="Code to fix (or file path)")
    fix_parser.add_argument("-i", "--issue", help="Specific issue to fix")
    
    # Code review
    review_parser = subparsers.add_parser("review", help="Code review")
    review_parser.add_argument("file", help="File to review")
    review_parser.add_argument("-f", "--focus", choices=["security", "performance", "style", "bugs", "all"], 
                              default="all", help="Review focus")
    
    # SQL generation
    sql_parser = subparsers.add_parser("sql", help="Generate SQL")
    sql_parser.add_argument("description", help="Natural language description")
    sql_parser.add_argument("-s", "--schema", help="Database schema")
    
    # Explain code
    explain_parser = subparsers.add_parser("explain", help="Explain code")
    explain_parser.add_argument("code", help="Code to explain (or file path)")
    explain_parser.add_argument("-l", "--level", choices=["eli5", "beginner", "normal", "expert"],
                               default="normal", help="Explanation level")
    
    # Refactor
    refactor_parser = subparsers.add_parser("refactor", help="Refactor code")
    refactor_parser.add_argument("code", help="Code to refactor (or file path)")
    refactor_parser.add_argument("-s", "--style", choices=["clean", "performance", "functional", "modern", "secure"],
                                default="clean", help="Refactoring style")
    
    # Debug error
    debug_parser = subparsers.add_parser("debug", help="Debug error")
    debug_parser.add_argument("error", help="Error message")
    debug_parser.add_argument("-c", "--context", help="Code context")
    
    # Generate tests
    test_parser = subparsers.add_parser("test", help="Generate tests")
    test_parser.add_argument("code", help="Code to test (or file path)")
    test_parser.add_argument("-f", "--framework", choices=["pytest", "unittest", "jest", "mocha"],
                            default="pytest", help="Test framework")
    
    # Convert code
    convert_parser = subparsers.add_parser("convert", help="Convert between languages")
    convert_parser.add_argument("code", help="Code to convert (or file path)")
    convert_parser.add_argument("from_lang", help="Source language")
    convert_parser.add_argument("to_lang", help="Target language")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cmd = StarCoderCommands()
    
    # Handle file inputs
    def get_code_input(code_arg):
        if Path(code_arg).exists():
            return Path(code_arg).read_text()
        return code_arg
    
    # Execute commands
    if args.command == "fix":
        code = get_code_input(args.code)
        result = cmd.quick_fix(code, args.issue or "")
        
    elif args.command == "review":
        result = cmd.review_code(args.file, args.focus)
        
    elif args.command == "sql":
        result = cmd.generate_sql(args.description, args.schema)
        
    elif args.command == "explain":
        code = get_code_input(args.code)
        result = cmd.explain_code(code, args.level)
        
    elif args.command == "refactor":
        code = get_code_input(args.code)
        result = cmd.refactor(code, args.style)
        
    elif args.command == "debug":
        result = cmd.debug_error(args.error, args.context or "")
        
    elif args.command == "test":
        code = get_code_input(args.code)
        result = cmd.generate_tests(code, args.framework)
        
    elif args.command == "convert":
        code = get_code_input(args.code)
        result = cmd.convert_code(code, args.from_lang, args.to_lang)
    
    # Output results
    if result.get("success"):
        print(f"🚀 {result['model']} ({result['time']:.1f}s)")
        print("-" * 60)
        print(result["response"])
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
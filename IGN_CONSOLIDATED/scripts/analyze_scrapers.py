#!/usr/bin/env python3
"""
Analyze and compare duplicate scrapers to choose the best implementation
"""
import os
import ast
from pathlib import Path
from datetime import datetime
import json

class ScraperAnalyzer:
    def __init__(self, scraper_dir):
        self.scraper_dir = Path(scraper_dir)
        
    def analyze_file(self, filepath):
        """Analyze a single scraper file"""
        stats = {
            'file': filepath.name,
            'size': filepath.stat().st_size,
            'lines': 0,
            'functions': [],
            'classes': [],
            'imports': [],
            'error_handling': [],
            'last_modified': datetime.fromtimestamp(filepath.stat().st_mtime),
            'complexity_score': 0,
            'has_logging': False,
            'has_tests': False,
            'docstring_coverage': 0
        }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            stats['lines'] = len(content.splitlines())
            
            # Check for logging
            stats['has_logging'] = 'import logging' in content or 'from logging' in content
            
            # Parse AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, stats)
            except:
                stats['parse_error'] = True
                
        return stats
    
    def _analyze_ast(self, tree, stats):
        """Analyze AST for code quality metrics"""
        total_functions = 0
        documented_functions = 0
        
        for node in ast.walk(tree):
            # Count functions
            if isinstance(node, ast.FunctionDef):
                stats['functions'].append(node.name)
                total_functions += 1
                if ast.get_docstring(node):
                    documented_functions += 1
                    
            # Count classes  
            elif isinstance(node, ast.ClassDef):
                stats['classes'].append(node.name)
                
            # Count imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    stats['imports'].append(alias.name)
                    
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    stats['imports'].append(f"{module}.{alias.name}")
                    
            # Find exception handling
            elif isinstance(node, ast.ExceptHandler):
                if node.type:
                    exception_type = ast.unparse(node.type) if hasattr(ast, 'unparse') else 'Exception'
                else:
                    exception_type = 'bare except'
                stats['error_handling'].append(exception_type)
        
        # Calculate metrics
        stats['docstring_coverage'] = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        stats['complexity_score'] = len(stats['functions']) + len(stats['classes']) * 2
        
    def compare_scrapers(self, pattern='instagram'):
        """Compare all scrapers matching pattern"""
        scrapers = list(self.scraper_dir.glob(f'*{pattern}*.py'))
        analyses = []
        
        for scraper in scrapers:
            if scraper.name != '__init__.py':
                analysis = self.analyze_file(scraper)
                analyses.append(analysis)
                
        # Sort by quality metrics
        analyses.sort(key=lambda x: (
            x['has_logging'],  # Prefer with logging
            -x['lines'],  # Prefer concise
            x['docstring_coverage'],  # Prefer documented
            -len([e for e in x['error_handling'] if e in ['bare except', 'Exception']])  # Prefer specific exceptions
        ), reverse=True)
        
        return analyses
    
    def generate_report(self, analyses):
        """Generate comparison report"""
        print("# Scraper Comparison Report\n")
        print(f"Analyzed {len(analyses)} scrapers\n")
        
        for i, analysis in enumerate(analyses, 1):
            print(f"## {i}. {analysis['file']}")
            print(f"- **Size**: {analysis['lines']} lines ({analysis['size']} bytes)")
            print(f"- **Last Modified**: {analysis['last_modified'].strftime('%Y-%m-%d')}")
            print(f"- **Functions**: {len(analysis['functions'])}")
            print(f"- **Classes**: {len(analysis['classes'])}")
            print(f"- **Docstring Coverage**: {analysis['docstring_coverage']:.1f}%")
            print(f"- **Has Logging**: {'✅' if analysis['has_logging'] else '❌'}")
            print(f"- **Error Handling**: {len(analysis['error_handling'])} handlers")
            
            # Check for bad practices
            bad_practices = []
            if 'bare except' in analysis['error_handling']:
                bad_practices.append("Uses bare except")
            if analysis['error_handling'].count('Exception') > 2:
                bad_practices.append("Too many broad exceptions")
            if not analysis['has_logging'] and analysis['lines'] > 200:
                bad_practices.append("Large file without logging")
                
            if bad_practices:
                print(f"- **Issues**: {', '.join(bad_practices)}")
                
            print()
            
        # Recommendation
        if analyses:
            best = analyses[0]
            print(f"\n## 🏆 Recommendation: Keep `{best['file']}`")
            print("\nReasons:")
            if best['has_logging']:
                print("- Uses proper logging")
            if best['docstring_coverage'] > 50:
                print(f"- Good documentation ({best['docstring_coverage']:.1f}%)")
            if len([e for e in best['error_handling'] if e not in ['bare except', 'Exception']]) > 0:
                print("- Specific exception handling")

def main():
    # Analyze Instagram scrapers
    analyzer = ScraperAnalyzer('src/backend/scrapers')
    
    print("Analyzing Instagram scrapers...")
    instagram_analyses = analyzer.compare_scrapers('instagram')
    analyzer.generate_report(instagram_analyses)
    
    print("\n" + "="*50 + "\n")
    
    print("Analyzing OSM scrapers...")
    osm_analyses = analyzer.compare_scrapers('osm')
    analyzer.generate_report(osm_analyses)
    
    # Save detailed analysis
    with open('scraper_analysis.json', 'w') as f:
        json.dump({
            'instagram': [a for a in instagram_analyses],
            'osm': [a for a in osm_analyses]
        }, f, indent=2, default=str)
    
    print("\nDetailed analysis saved to scraper_analysis.json")

if __name__ == "__main__":
    main()
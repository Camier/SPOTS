#!/usr/bin/env python3
"""
Quick test of hybrid analysis
"""

from ollama_hybrid_analyzer import HybridAnalyzer

# Test the hybrid approach
analyzer = HybridAnalyzer()

# Simple question - should only use rapid
print("🧪 Test 1: Simple Question")
print("-" * 40)
result = analyzer.hybrid_analyze("What is Python?", verbose=True)
print(f"\nUsed deep analysis: {'Yes' if result.get('deep') else 'No'}")

print("\n" + "="*60 + "\n")

# Complex question - should trigger deep analysis
print("🧪 Test 2: Complex Question")
print("-" * 40)
result = analyzer.hybrid_analyze(
    "Explain how async/await works in Python and compare it with threading",
    verbose=True
)
print(f"\nUsed deep analysis: {'Yes' if result.get('deep') else 'Yes'}")

print("\n" + "="*60 + "\n")

# Code analysis - rapid for simple, deep for complex
print("🧪 Test 3: Code Security Check")
print("-" * 40)
code = """
@app.route('/user/<id>')
def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query).fetchone()
"""
result = analyzer.hybrid_analyze(
    f"Find security issues in this code:\n{code}",
    task="code",
    verbose=True
)

# Show timing comparison
print(f"\n📊 Performance Summary:")
print(f"- Rapid: {result['rapid']['time']:.1f}s ({result['rapid']['tokens_per_sec']:.1f} tok/s)")
if result.get('deep'):
    print(f"- Deep: {result['deep']['time']:.1f}s ({result['deep']['tokens_per_sec']:.1f} tok/s)")
    print(f"- Speedup: {result['deep']['time'] / result['rapid']['time']:.1f}x slower for deep")
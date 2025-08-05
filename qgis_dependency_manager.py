#!/usr/bin/env python3
"""
QGIS Dependency Manager - Best Practices Implementation
Based on recommendations for handling plugin dependencies
"""

import sys
import os
import subprocess
from pathlib import Path

class QGISDependencyManager:
    def __init__(self):
        self.qgis_python = sys.executable
        self.plugin_dir = Path.home() / '.local/share/QGIS/QGIS3/profiles/default/python/plugins'
        
    def check_python_environment(self):
        """Check QGIS Python environment"""
        print("=== QGIS Python Environment ===")
        print(f"Python executable: {self.qgis_python}")
        print(f"Python version: {sys.version}")
        print(f"Plugin directory: {self.plugin_dir}")
        
        # Check sys.path for conflicts
        print("\nPython paths (checking for conflicts):")
        for i, path in enumerate(sys.path[:10]):
            print(f"  {i}: {path}")
    
    def install_dependencies(self, requirements_file=None):
        """Install dependencies using QGIS Python"""
        deps = [
            'pandas>=1.3.0',
            'numpy>=1.21.0',
            'geopandas>=0.10.0',
            'requests>=2.25.0',
            'matplotlib>=3.3.0'
        ]
        
        if requirements_file and os.path.exists(requirements_file):
            with open(requirements_file) as f:
                deps = [line.strip() for line in f if line.strip()]
        
        print("\n=== Installing Dependencies ===")
        for dep in deps:
            try:
                cmd = [self.qgis_python, '-m', 'pip', 'install', '--user', dep]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✓ Installed: {dep}")
                else:
                    print(f"✗ Failed: {dep} - {result.stderr}")
            except Exception as e:
                print(f"✗ Error installing {dep}: {e}")
    
    def create_plugin_isolation(self, plugin_name):
        """Create dependency isolation for a plugin"""
        plugin_path = self.plugin_dir / plugin_name
        extlibs_path = plugin_path / 'extlibs'
        
        if not plugin_path.exists():
            print(f"Plugin {plugin_name} not found")
            return
        
        # Create extlibs directory
        extlibs_path.mkdir(exist_ok=True)
        
        # Create __init__.py for dependency isolation
        init_content = '''import sys
import os

# Add plugin's extlibs to Python path (isolated dependencies)
plugin_dir = os.path.dirname(__file__)
extlibs_dir = os.path.join(plugin_dir, 'extlibs')

if os.path.exists(extlibs_dir) and extlibs_dir not in sys.path:
    sys.path.insert(0, extlibs_dir)
'''
        
        with open(plugin_path / '__init__.py', 'w') as f:
            f.write(init_content)
        
        print(f"✓ Created dependency isolation for {plugin_name}")
        print(f"  Dependencies should be installed to: {extlibs_path}")
    
    def fix_common_conflicts(self):
        """Fix common dependency conflicts"""
        print("\n=== Fixing Common Conflicts ===")
        
        # Fix missing 'future' module for timemanager
        try:
            subprocess.run([self.qgis_python, '-m', 'pip', 'install', '--user', 'future'],
                         capture_output=True)
            print("✓ Fixed 'future' module for timemanager")
        except:
            print("✗ Could not fix 'future' module")
        
        # Clear Python cache
        cache_dir = self.plugin_dir / '__pycache__'
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            print("✓ Cleared plugin cache")
    
    def create_requirements_txt(self):
        """Create requirements.txt for QGIS plugins"""
        requirements = '''# QGIS Plugin Dependencies
# Install with: /usr/bin/python3 -m pip install --user -r requirements.txt

# Core dependencies
pandas>=1.3.0
numpy>=1.21.0
geopandas>=0.10.0
matplotlib>=3.3.0
requests>=2.25.0

# For plugin compatibility
future>=0.18.0  # Required by timemanager
pillow>=8.0.0   # Image processing
pyproj>=3.0.0   # Coordinate transformations
shapely>=1.8.0  # Geometric operations
fiona>=1.8.0    # Vector data I/O

# Optional but recommended
seaborn>=0.11.0  # Statistical plots
scipy>=1.7.0     # Scientific computing
xlsxwriter>=3.0.0  # Excel export
'''
        
        req_path = Path.home() / 'qgis_requirements.txt'
        with open(req_path, 'w') as f:
            f.write(requirements)
        
        print(f"\n✓ Created requirements.txt at: {req_path}")
        print(f"  Install with: {self.qgis_python} -m pip install --user -r {req_path}")

if __name__ == "__main__":
    manager = QGISDependencyManager()
    
    # Run all checks and fixes
    manager.check_python_environment()
    manager.create_requirements_txt()
    manager.fix_common_conflicts()
    
    # Example: Create isolation for a plugin
    # manager.create_plugin_isolation('my_plugin')
    
    print("\n=== Dependency Management Complete ===")
    print("Remember to:")
    print("1. Always use QGIS's Python for installations")
    print("2. Bundle dependencies in plugin_name/extlibs/ for isolation")
    print("3. Never modify system-wide Python packages")
    print("4. Test plugins in a clean profile when debugging")
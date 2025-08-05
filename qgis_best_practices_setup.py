#!/usr/bin/env python3
"""
QGIS Best Practices Setup Script
Following official QGIS documentation recommendations
"""

import os
import sys
import subprocess
from pathlib import Path

class QGISBestPracticesSetup:
    def __init__(self):
        self.profile_path = Path.home() / '.local/share/QGIS/QGIS3/profiles/default'
        self.plugins_path = self.profile_path / 'python/plugins'
        
    def setup_directories(self):
        """Ensure QGIS directories exist"""
        print("=== Setting up QGIS directories ===")
        directories = [
            self.profile_path,
            self.plugins_path,
            self.profile_path / 'project_templates',
            self.profile_path / 'styles',
            self.profile_path / 'svg',
            self.profile_path / 'scripts'
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created: {dir_path}")
    
    def create_startup_script(self):
        """Create QGIS startup script for custom initialization"""
        startup_script = self.profile_path / 'python/startup.py'
        startup_script.parent.mkdir(parents=True, exist_ok=True)
        
        content = '''# QGIS Startup Script - Best Practices
import os
import sys
from qgis.core import QgsApplication, QgsMessageLog, Qgis

def startup():
    """Custom QGIS startup configuration"""
    # Add custom Python paths
    custom_paths = [
        os.path.expanduser('~/.local/lib/python3.12/site-packages'),
        os.path.expanduser('~/.local/lib/python3.11/site-packages'),
    ]
    
    for path in custom_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # Log startup
    QgsMessageLog.logMessage(
        f"QGIS {Qgis.QGIS_VERSION} started with custom configuration",
        'Startup',
        Qgis.Info
    )
    
    # Set default project settings
    QgsApplication.instance().setOrganizationName('QGIS')
    QgsApplication.instance().setApplicationName('QGIS3')
    
    print("Custom startup script loaded successfully")

# Run startup
startup()
'''
        
        with open(startup_script, 'w') as f:
            f.write(content)
        
        print(f"✓ Created startup script: {startup_script}")
    
    def create_plugin_installer(self):
        """Create script to install recommended plugins"""
        installer_script = self.profile_path / 'scripts/install_plugins.py'
        installer_script.parent.mkdir(parents=True, exist_ok=True)
        
        content = '''#!/usr/bin/env python3
"""Install recommended QGIS plugins"""

# Essential plugins list based on best practices
ESSENTIAL_PLUGINS = {
    'QuickMapServices': 'Quick access to web basemaps',
    'mmqgis': 'Advanced vector operations',
    'QuickOSM': 'Download OpenStreetMap data',
    'qgis2web': 'Export maps to web format',
    'profiletool': 'Terrain profile analysis',
    'DataPlotly': 'Create interactive plots',
    'TimeManager': 'Animate temporal data',
    'QNEAT3': 'Network analysis tools',
    'firstaid': 'Fix common issues',
    'pluginbuilder3': 'Create custom plugins'
}

print("=== QGIS Plugin Installation Guide ===")
print("\\nTo install plugins manually:")
print("1. Open QGIS")
print("2. Go to Plugins → Manage and Install Plugins")
print("3. Search and install these recommended plugins:\\n")

for plugin, description in ESSENTIAL_PLUGINS.items():
    print(f"  • {plugin}: {description}")

print("\\n4. Enable 'Show experimental plugins' in settings for more options")
print("5. Restart QGIS after installing plugins")
'''
        
        with open(installer_script, 'w') as f:
            f.write(content)
        
        installer_script.chmod(0o755)
        print(f"✓ Created plugin installer: {installer_script}")
    
    def create_settings_template(self):
        """Create recommended QGIS settings template"""
        settings_file = self.profile_path / 'QGIS/QGIS3.ini'
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Don't overwrite existing settings, create template instead
        template_file = self.profile_path / 'scripts/recommended_settings.ini'
        
        content = '''[General]
# Enable multi-threaded rendering
qgis/parallel_rendering=true
qgis/max_threads=4

[cache]
# Set cache size (MB)
cache/size=512
cache/directory=@Variant(\\0\\0\\0\\x11\\0\\0\\0\\x1e/tmp/qgis3_cache)

[app]
# Check for updates
qgis/checkVersion=true
qgis/showTips=true

[plugins]
# Enable experimental plugins
qgis/showExperimentalPlugins=true
# Check for plugin updates
installer/checkOnStart=true

[digitizing]
# Default snapping
qgis/digitizing/default_snap_enabled=true
qgis/digitizing/default_snap_tolerance=12
qgis/digitizing/default_snap_units=1

[locale]
# UI language
userLocale=en_US
overrideFlag=true
'''
        
        with open(template_file, 'w') as f:
            f.write(content)
        
        print(f"✓ Created settings template: {template_file}")
    
    def create_python_requirements(self):
        """Create requirements file for Python dependencies"""
        req_file = self.profile_path / 'scripts/requirements.txt'
        
        content = '''# QGIS Python Dependencies - Best Practices
# Install with: pip install --user -r requirements.txt

# Data processing
pandas>=1.5.0
numpy>=1.23.0
geopandas>=0.12.0
shapely>=2.0.0
fiona>=1.9.0
pyproj>=3.4.0

# Visualization
matplotlib>=3.5.0
seaborn>=0.12.0
plotly>=5.0.0

# Utilities
requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0

# Database
psycopg2-binary>=2.9.0
sqlalchemy>=1.4.0

# Remote sensing (optional)
rasterio>=1.3.0
# scikit-image>=0.19.0
# opencv-python>=4.6.0

# Machine learning (optional)
# scikit-learn>=1.1.0
# tensorflow>=2.10.0
# torch>=1.12.0
'''
        
        with open(req_file, 'w') as f:
            f.write(content)
        
        print(f"✓ Created requirements file: {req_file}")
    
    def create_project_template(self):
        """Create a project template following best practices"""
        template_dir = self.profile_path / 'project_templates/standard_project'
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create template structure
        structure = {
            'data/vector': 'Vector data files',
            'data/raster': 'Raster data files',
            'data/processed': 'Processed outputs',
            'styles': 'QML style files',
            'layouts': 'Print layouts',
            'scripts': 'Processing scripts',
            'docs': 'Documentation'
        }
        
        readme_content = '''# QGIS Project Template

## Directory Structure
- `data/` - All spatial data
  - `vector/` - Shapefiles, GeoJSON, etc.
  - `raster/` - GeoTIFF, imagery, etc.
  - `processed/` - Analysis outputs
- `styles/` - Layer styling (QML files)
- `layouts/` - Print composer templates
- `scripts/` - Python processing scripts
- `docs/` - Project documentation

## Best Practices
1. Use relative paths for data sources
2. Save project as .qgz (compressed)
3. Include metadata in layer properties
4. Document processing steps
5. Version control with .gitignore for large files
'''
        
        for subdir, desc in structure.items():
            path = template_dir / subdir
            path.mkdir(parents=True, exist_ok=True)
            (path / '.gitkeep').touch()
        
        with open(template_dir / 'README.md', 'w') as f:
            f.write(readme_content)
        
        print(f"✓ Created project template: {template_dir}")
    
    def run_setup(self):
        """Run complete setup"""
        print("\n=== QGIS Best Practices Setup ===\n")
        
        self.setup_directories()
        self.create_startup_script()
        self.create_plugin_installer()
        self.create_settings_template()
        self.create_python_requirements()
        self.create_project_template()
        
        print("\n=== Setup Complete ===")
        print("\nNext steps:")
        print("1. Start QGIS 3.44.1")
        print("2. Install recommended plugins (see scripts/install_plugins.py)")
        print("3. Configure settings (see scripts/recommended_settings.ini)")
        print("4. Install Python dependencies if needed")
        print("\nFor testing, create a new profile:")
        print("  Settings → User Profiles → New Profile")

if __name__ == "__main__":
    setup = QGISBestPracticesSetup()
    setup.run_setup()
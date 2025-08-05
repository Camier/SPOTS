#!/usr/bin/env python3
"""
SPOTS Data Filtering Tool
Filter and analyze spots in the Occitanie database
"""

import sqlite3
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any

class SpotsFilter:
    """Filter and analyze spots data from the Occitanie database"""
    
    DEPARTMENT_NAMES = {
        '09': 'Ariège',
        '11': 'Aude', 
        '12': 'Aveyron',
        '30': 'Gard',
        '31': 'Haute-Garonne',
        '32': 'Gers',
        '34': 'Hérault',
        '46': 'Lot',
        '48': 'Lozère',
        '65': 'Hautes-Pyrénées',
        '66': 'Pyrénées-Orientales',
        '81': 'Tarn',
        '82': 'Tarn-et-Garonne'
    }
    
    def __init__(self, db_path: str = '/home/miko/projects/spots/data/occitanie_spots.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def get_overview(self) -> Dict[str, Any]:
        """Get database overview statistics"""
        cursor = self.conn.cursor()
        
        # Total spots
        cursor.execute("SELECT COUNT(*) FROM spots")
        total = cursor.fetchone()[0]
        
        # By department
        cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM spots 
            WHERE department IS NOT NULL 
            GROUP BY department 
            ORDER BY count DESC
        """)
        departments = [(row['department'], row['count']) for row in cursor.fetchall()]
        
        # By type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM spots 
            WHERE type IS NOT NULL 
            GROUP BY type 
            ORDER BY count DESC
        """)
        types = [(row['type'], row['count']) for row in cursor.fetchall()]
        
        # By source
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM spots 
            GROUP BY source 
            ORDER BY count DESC
        """)
        sources = [(row['source'], row['count']) for row in cursor.fetchall()]
        
        return {
            'total_spots': total,
            'departments': departments,
            'types': types,
            'sources': sources
        }

    def filter_by_department(self, departments: List[str]) -> List[Dict]:
        """Filter spots by department codes"""
        dept_list = ','.join([f"'{d}'" for d in departments])
        query = f"""
            SELECT * FROM spots 
            WHERE department IN ({dept_list})
            ORDER BY department, name
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def filter_by_type(self, types: List[str]) -> List[Dict]:
        """Filter spots by type"""
        type_list = ','.join([f"'{t}'" for t in types])
        query = f"""
            SELECT * FROM spots 
            WHERE type IN ({type_list})
            ORDER BY type, name
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def filter_by_elevation(self, min_elev: float = None, max_elev: float = None) -> List[Dict]:
        """Filter spots by elevation range"""
        conditions = ["elevation IS NOT NULL"]
        if min_elev is not None:
            conditions.append(f"elevation >= {min_elev}")
        if max_elev is not None:
            conditions.append(f"elevation <= {max_elev}")
            
        query = f"""
            SELECT * FROM spots 
            WHERE {' AND '.join(conditions)}
            ORDER BY elevation DESC
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def filter_quality_spots(self, verified_only: bool = False, 
                           min_confidence: float = None,
                           with_description: bool = False) -> List[Dict]:
        """Filter by quality indicators"""
        conditions = []
        
        if verified_only:
            conditions.append("verified = 1")
        if min_confidence is not None:
            conditions.append(f"confidence_score >= {min_confidence}")
        if with_description:
            conditions.append("description IS NOT NULL AND description != ''")
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM spots 
            WHERE {where_clause}
            ORDER BY confidence_score DESC, name
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def filter_mountain_spots(self) -> List[Dict]:
        """Filter spots in mountain areas (Pyrénées departments + high elevation)"""
        query = """
            SELECT * FROM spots 
            WHERE (department IN ('09', '31', '65', '66') OR elevation > 1000)
            AND type IN ('cave', 'waterfall', 'natural_spring', 'historical_ruins')
            ORDER BY elevation DESC
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def filter_water_activities(self) -> List[Dict]:
        """Filter spots suitable for water activities"""
        query = """
            SELECT * FROM spots 
            WHERE (type IN ('waterfall', 'natural_spring') 
                   OR name LIKE '%lac%' 
                   OR name LIKE '%cascade%'
                   OR name LIKE '%source%'
                   OR description LIKE '%baignade%')
            ORDER BY department, name
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_top_spots_by_department(self, limit: int = 5) -> Dict[str, List[Dict]]:
        """Get top spots for each department"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM spots WHERE department IS NOT NULL")
        departments = [row[0] for row in cursor.fetchall()]
        
        results = {}
        for dept in departments:
            query = f"""
                SELECT * FROM spots 
                WHERE department = '{dept}'
                AND verified = 1
                ORDER BY confidence_score DESC, elevation DESC
                LIMIT {limit}
            """
            cursor.execute(query)
            dept_name = self.DEPARTMENT_NAMES.get(dept, dept)
            results[f"{dept} - {dept_name}"] = [dict(row) for row in cursor.fetchall()]
            
        return results
    
    def search_spots(self, keyword: str) -> List[Dict]:
        """Search spots by keyword in name or description"""
        query = """
            SELECT * FROM spots 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY 
                CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
                name
        """
        search_term = f"%{keyword}%"
        cursor = self.conn.cursor()
        cursor.execute(query, (search_term, search_term, search_term))
        return [dict(row) for row in cursor.fetchall()]
    
    def export_filtered_data(self, spots: List[Dict], output_file: str):
        """Export filtered spots to JSON file"""
        # Convert datetime objects to strings
        for spot in spots:
            for key in ['created_at', 'updated_at']:
                if spot.get(key):
                    spot[key] = str(spot[key])
                    
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'export_date': datetime.now().isoformat(),
                'total_spots': len(spots),
                'spots': spots
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(spots)} spots to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Filter and analyze SPOTS data')
    parser.add_argument('--overview', action='store_true', help='Show database overview')
    parser.add_argument('--department', nargs='+', help='Filter by department codes (e.g., 09 31)')
    parser.add_argument('--type', nargs='+', help='Filter by spot types')
    parser.add_argument('--elevation-min', type=float, help='Minimum elevation')
    parser.add_argument('--elevation-max', type=float, help='Maximum elevation')
    parser.add_argument('--verified', action='store_true', help='Only verified spots')
    parser.add_argument('--mountain', action='store_true', help='Mountain spots')
    parser.add_argument('--water', action='store_true', help='Water activity spots')
    parser.add_argument('--search', help='Search keyword')
    parser.add_argument('--top', type=int, help='Top N spots per department')
    parser.add_argument('--export', help='Export results to JSON file')
    parser.add_argument('--limit', type=int, default=50, help='Limit results (default: 50)')
    
    args = parser.parse_args()
    
    # Initialize filter
    filter_tool = SpotsFilter()
    
    # Handle different filter options
    results = []
    
    if args.overview:
        overview = filter_tool.get_overview()
        print("\n=== SPOTS DATABASE OVERVIEW ===")
        print(f"Total spots: {overview['total_spots']}")
        
        print("\nBy Department:")
        for dept, count in overview['departments'][:10]:
            dept_name = filter_tool.DEPARTMENT_NAMES.get(dept, dept)
            print(f"  {dept} ({dept_name}): {count} spots")
            
        print("\nBy Type:")
        for spot_type, count in overview['types'][:10]:
            print(f"  {spot_type}: {count} spots")
            
        print("\nBy Source:")
        for source, count in overview['sources'][:10]:
            print(f"  {source}: {count} spots")
        return
    
    elif args.department:
        results = filter_tool.filter_by_department(args.department)
        print(f"\nFound {len(results)} spots in departments: {', '.join(args.department)}")
        
    elif args.type:
        results = filter_tool.filter_by_type(args.type)
        print(f"\nFound {len(results)} spots of types: {', '.join(args.type)}")
        
    elif args.elevation_min or args.elevation_max:
        results = filter_tool.filter_by_elevation(args.elevation_min, args.elevation_max)
        elev_range = f"{args.elevation_min or 0}m - {args.elevation_max or '∞'}m"
        print(f"\nFound {len(results)} spots in elevation range: {elev_range}")
        
    elif args.verified:
        results = filter_tool.filter_quality_spots(verified_only=True)
        print(f"\nFound {len(results)} verified spots")
        
    elif args.mountain:
        results = filter_tool.filter_mountain_spots()
        print(f"\nFound {len(results)} mountain spots")
        
    elif args.water:
        results = filter_tool.filter_water_activities()
        print(f"\nFound {len(results)} water activity spots")
        
    elif args.search:
        results = filter_tool.search_spots(args.search)
        print(f"\nFound {len(results)} spots matching '{args.search}'")
        
    elif args.top:
        top_spots = filter_tool.get_top_spots_by_department(args.top)
        print(f"\nTop {args.top} spots per department:")
        for dept, spots in top_spots.items():
            print(f"\n{dept}:")
            for spot in spots:
                elev = f" ({spot['elevation']}m)" if spot.get('elevation') else ""
                print(f"  - {spot['name']}{elev} [{spot['type']}]")
        return
    
    else:
        # Default: show all spots
        results = filter_tool.filter_quality_spots()
        print(f"\nShowing all {len(results)} spots")
    
    # Display results (limited)
    if results:
        print(f"\nShowing first {min(len(results), args.limit)} results:")
        for i, spot in enumerate(results[:args.limit]):
            dept_name = filter_tool.DEPARTMENT_NAMES.get(spot['department'], spot['department'])
            elev = f" ({spot['elevation']}m)" if spot.get('elevation') else ""
            verified = " ✓" if spot.get('verified') else ""
            print(f"\n{i+1}. {spot['name']}{elev} - {dept_name}{verified}")
            print(f"   Type: {spot['type']} | Source: {spot['source']}")
            if spot.get('description'):
                desc = spot['description'][:100] + "..." if len(spot['description']) > 100 else spot['description']
                print(f"   {desc}")
    
    # Export if requested
    if args.export and results:
        filter_tool.export_filtered_data(results, args.export)
    
    filter_tool.conn.close()

if __name__ == "__main__":
    main()

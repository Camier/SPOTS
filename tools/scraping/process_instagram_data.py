#!/usr/bin/env python3
"""
Process real Instagram data through the secure pipeline
"""

import json
from src.backend.data_management.instagram_data_pipeline import InstagramDataPipeline


def main():
    # Load real Instagram data we scraped
    with open('instagram_scraping_results.json', 'r', encoding='utf-8') as f:
        scraping_results = json.load(f)
    
    # Extract posts
    instagram_posts = []
    for i, post in enumerate(scraping_results['posts_collected']):
        instagram_posts.append({
            'post_id': f"real_{post['username']}_{i}",
            'location_name': post['location'],
            'caption': post['caption'],
            'hashtags': post['hashtags'],
            'source': 'instagram',
            'department': post.get('department'),
            'source_url': post.get('url', '')
        })
    
    # Process through pipeline
    pipeline = InstagramDataPipeline()
    results = pipeline.process_batch(instagram_posts)
    
    print("\n=== Instagram Data Processing Results ===")
    print(f"Total posts processed: {results['processed']}")
    print(f"Successfully stored: {results['stored']}")
    print(f"Failed: {results['failed']}")
    
    if results['errors']:
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['locations']:
        print(f"\nLocations processed: {', '.join(results['locations'])}")
    
    # Export processed data
    if results['stored'] > 0:
        export_path = pipeline.export_data('json')
        print(f"\n✅ Data exported to: {export_path}")
        
        # Show export sample
        with open(export_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
            print(f"\nExport contains {export_data['total_spots']} spots")
            for spot in export_data['spots'][:2]:
                print(f"\n📍 {spot['name']}")
                print(f"   Department: {spot['department']}")
                print(f"   Type: {spot['type']}")
                print(f"   Activities: {', '.join(spot['activities'])}")


if __name__ == "__main__":
    main()
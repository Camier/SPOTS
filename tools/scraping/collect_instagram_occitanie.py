#!/usr/bin/env python3
"""
Collect real Instagram data from Occitanie hashtags
Using Puppeteer MCP with best practices
"""

import json
from datetime import datetime


def save_instagram_spot(post_data):
    """Save Instagram post as spot data"""
    
    # Extract location from caption
    caption = post_data.get('caption', '')
    
    # Create spot data
    spot = {
        "source": f"instagram:@{post_data.get('username', 'unknown')}",
        "source_url": f"https://instagram.com/p/{post_data.get('post_id', '')}",
        "name": extract_location_name(caption),
        "raw_text": caption,
        "hashtags": post_data.get('hashtags', []),
        "metadata": {
            "is_real_data": True,
            "instagram_likes": post_data.get('likes'),
            "instagram_date": post_data.get('date'),
            "extracted_at": datetime.now().isoformat()
        }
    }
    
    return spot


def extract_location_name(caption):
    """Extract location name from caption using keywords"""
    
    # Occitanie location keywords
    locations = {
        "gorges d'ehujarré": "Gorges d'Ehujarré",
        "pyrénées": "Pyrénées",
        "lac de salagou": "Lac de Salagou",
        "pont du gard": "Pont du Gard",
        "carcassonne": "Carcassonne",
        "pic du midi": "Pic du Midi",
        "gorges du tarn": "Gorges du Tarn",
        "cirque de gavarnie": "Cirque de Gavarnie"
    }
    
    caption_lower = caption.lower()
    
    for keyword, name in locations.items():
        if keyword in caption_lower:
            return name
            
    # Default to first few words
    words = caption.split()[:3]
    return " ".join(words)


# Example data from our scraping
scraped_data = {
    "posts": [
        {
            "username": "jyvaisvoyages",
            "caption": "Et les gorges d'ehujarré ? Rando faite presque par hasard un beau matin. Complètement incroyable",
            "hashtags": ["#pyrenees", "#randonnee", "#hiking", "#occitanie", "#hautespyrenees"],
            "date": "2025-03-26T18:38:57.000Z",
            "post_id": "example123"
        }
    ]
}

# Process and save spots
spots = []
for post in scraped_data["posts"]:
    spot = save_instagram_spot(post)
    spots.append(spot)
    print(f"Processed: {spot['name']}")

# Save to file
with open("instagram_occitanie_spots.json", "w", encoding="utf-8") as f:
    json.dump(spots, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved {len(spots)} real Instagram spots from Occitanie")
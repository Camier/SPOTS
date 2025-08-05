# SPOTS Data Verification Policy

## 🚨 Important Change (August 5, 2025)

All previously bulk-imported spots have been moved to quarantine due to quality concerns.

## 📁 New Structure

```
data/
├── main/
│   ├── spots_database.json      # ONLY verified spots (currently empty)
│   └── spots_map_data.json      # ONLY verified map data (currently empty)
├── verified/                     # Individual verified spot files
├── quarantine/                   # Unverified/suspicious spots
│   ├── spots_database_unverified.json (787 spots)
│   ├── spots_map_data_unverified.json
│   └── haute_garonne_unverified.json
└── archive/                      # Historical data
```

## ✅ Verification Requirements

A spot MUST have ALL of the following to be considered verified:

1. **Real Location**: Exact GPS coordinates that correspond to an actual place
2. **Proper Name**: Specific, descriptive name (not generic like "Grotte (Ariège)")
3. **Documentation**: At least one of:
   - Recent photo (within 6 months)
   - Official tourism website link
   - Government/municipal documentation
   - Verified user report with details
4. **Accessibility Info**: Clear information about:
   - How to access the location
   - Any restrictions or permissions needed
   - Safety considerations
5. **Recent Validation**: Confirmed to exist within the last 6 months

## 🔄 Verification Process

1. **Individual Review**: Each spot must be reviewed individually
2. **Source Verification**: Original source must be credible
3. **Cross-Reference**: Check multiple sources when possible
4. **Physical Verification**: Ideally, someone has visited recently
5. **No Bulk Imports**: Never add spots in bulk without individual verification

## ⚠️ Red Flags

Spots with these characteristics should NOT be added:
- Generic names with region in parentheses
- Suspiciously uniform data patterns
- No specific address or vague locations
- All marked as "unverified" from scrapers
- Elevation data but no other details

## 📝 Adding New Verified Spots

To add a new verified spot:

1. Create a JSON file in `data/verified/` with full details
2. Include verification evidence in the file
3. Only after review, add to main `spots_database.json`
4. Update `spots_map_data.json` accordingly

Example verified spot structure:
```json
{
  "id": "verified_001",
  "name": "Cascade de Saut de l'Ours",
  "latitude": 42.9234,
  "longitude": 0.7891,
  "type": "waterfall",
  "address": "D44, 09800 Bordes-Uchentein, France",
  "description": "Beautiful 15m waterfall accessible via marked trail",
  "verification": {
    "date": "2025-08-01",
    "source": "personal_visit",
    "evidence": ["photo_link", "trail_report"],
    "verified_by": "user_id"
  },
  "access": {
    "difficulty": "easy",
    "duration": "20min walk",
    "parking": "Small parking area at trailhead"
  },
  "safety": "Slippery rocks near waterfall",
  "best_season": "May-October"
}
```

## 🗑️ Quarantine Policy

Spots in quarantine:
- Should NOT be displayed to users
- Can be reviewed individually for potential verification
- Most will likely be discarded due to poor quality
- Require complete re-verification before moving to main database

---

Remember: Quality over quantity. One well-documented, verified spot is worth more than 100 suspicious ones.
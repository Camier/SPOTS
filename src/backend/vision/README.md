# Vision Module - Image-Based Location Detection

## Overview
The Vision module uses Hugging Face models and computer vision techniques to identify and locate places in Occitanie from uploaded photos. It combines EXIF data extraction, visual landmark recognition, scene classification, and similarity search to provide comprehensive image analysis.

## Features

### 1. Image Location Detection (`image_locator.py`)
- **EXIF GPS Extraction**: Reads GPS coordinates from photo metadata
- **Visual Landmark Recognition**: Identifies known Occitanie landmarks
- **Scene Classification**: Detects scene types (waterfall, cave, ruins, etc.)
- **Department Detection**: Maps coordinates to Occitanie departments

### 2. Place Recognition (`place_recognizer.py`)
- **CLIP Zero-Shot Classification**: Recognizes places without training
- **Activity Detection**: Identifies outdoor activities in images
- **Scene Attribute Extraction**: Detects weather, season, time of day
- **Known Spot Matching**: Matches images to database spots

### 3. Visual Similarity Search (`similarity_search.py`)
- **Image Embeddings**: Creates vector representations using CLIP
- **FAISS Indexing**: Efficient similarity search at scale
- **Duplicate Detection**: Finds near-duplicate images
- **Type Filtering**: Search within specific spot categories

## Installation

### Requirements
```bash
pip install transformers torch pillow
pip install faiss-cpu  # or faiss-gpu for CUDA
pip install exifread geopy
```

### Optional for Better Performance
```bash
# For GPU acceleration
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For OCR text extraction
pip install pytesseract

# For advanced image processing
pip install opencv-python scikit-image
```

## Models Used

### Default Models
- **Vision Transformer**: `google/vit-base-patch16-224` for classification
- **CLIP**: `openai/clip-vit-base-patch32` for zero-shot recognition

### Alternative Models (Better Performance)
```python
# Larger CLIP model for better accuracy
model_name = "openai/clip-vit-large-patch14"

# French-specific model
model_name = "flaubert/flaubert_base_cased"

# Geolocation-specific model
model_name = "geolocal/im2gps"  # If available
```

## API Endpoints

### POST /api/vision/locate
Identify location from uploaded image:
```bash
curl -X POST "http://localhost:8000/api/vision/locate" \
  -F "file=@photo.jpg" \
  -F "extract_exif=true" \
  -F "recognize_landmarks=true"
```

Response:
```json
{
  "file_id": "uuid",
  "location": {
    "place_name": "Cascade de Saint-Laurent",
    "confidence": 0.85,
    "latitude": 43.6047,
    "longitude": 1.4442,
    "department": "31",
    "region": "Occitanie"
  },
  "scene": {
    "type": "waterfall",
    "confidence": 0.92
  },
  "landmarks": ["pont_neuf_toulouse"]
}
```

### POST /api/vision/recognize
Recognize place type using CLIP:
```bash
curl -X POST "http://localhost:8000/api/vision/recognize" \
  -F "file=@photo.jpg" \
  -F "include_activities=true"
```

### POST /api/vision/search/similar
Find visually similar spots:
```bash
curl -X POST "http://localhost:8000/api/vision/search/similar" \
  -F "file=@photo.jpg" \
  -F "k=10" \
  -F "filter_type=waterfall"
```

### POST /api/vision/analyze
Comprehensive image analysis:
```bash
curl -X POST "http://localhost:8000/api/vision/analyze" \
  -F "file=@photo.jpg" \
  -F "full_analysis=true"
```

## Usage Examples

### Python - Basic Location Detection
```python
from src.backend.vision import ImageLocator

locator = ImageLocator()
prediction = locator.predict_location("path/to/image.jpg")

print(f"Location: {prediction.place_name}")
print(f"Confidence: {prediction.confidence}")
print(f"Coordinates: {prediction.latitude}, {prediction.longitude}")
```

### Python - Place Recognition with CLIP
```python
from src.backend.vision import PlaceRecognizer

recognizer = PlaceRecognizer()

# Recognize place type
places = recognizer.recognize_place("path/to/image.jpg")
for place in places:
    print(f"{place['place_type']}: {place['confidence']:.2f}")

# Detect activities
activities = recognizer.identify_activities("path/to/image.jpg")
for activity in activities:
    print(f"Activity: {activity['activity']} ({activity['confidence']:.2f})")
```

### Python - Visual Similarity Search
```python
from src.backend.vision import SimilaritySearch

search = SimilaritySearch()

# Add images to index
spot_images = [
    {"spot_id": 1, "image_path": "spot1.jpg", "spot_type": "waterfall"},
    {"spot_id": 2, "image_path": "spot2.jpg", "spot_type": "cave"}
]
search.add_spot_images(spot_images)

# Search for similar spots
similar = search.search_similar("query.jpg", k=5)
for match in similar:
    print(f"Spot {match['spot_id']}: {match['similarity']:.2f}")
```

### JavaScript - Upload and Analyze
```javascript
async function analyzePhoto(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('full_analysis', 'true');
    
    const response = await fetch('/api/vision/analyze', {
        method: 'POST',
        body: formData
    });
    
    const analysis = await response.json();
    
    // Display results
    console.log('Location:', analysis.location);
    console.log('Scene type:', analysis.location.scene_type);
    console.log('Activities:', analysis.activities);
    console.log('Similar spots:', analysis.similar_spots);
}
```

## Landmarks Database

### Currently Recognized Landmarks
- **Toulouse**: Capitole, Basilique Saint-Sernin, Pont Neuf
- **Carcassonne**: Cité de Carcassonne
- **Montpellier**: Place de la Comédie, Arc de Triomphe
- **Natural**: Pic du Midi, Cirque de Gavarnie, Pont du Gard, Gorges du Tarn
- **Castles**: Château de Foix, Peyrepertuse, Quéribus

### Adding Custom Landmarks
```python
locator = ImageLocator()
locator.occitanie_landmarks["custom_landmark"] = {
    "lat": 43.123,
    "lng": 1.456,
    "dept": "31"
}
```

## Performance Optimization

### 1. Batch Processing
```python
# Process multiple images efficiently
embeddings = []
for image_path in image_paths:
    embedding = search.create_embedding(image_path)
    embeddings.append(embedding)
```

### 2. GPU Acceleration
```python
# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
```

### 3. Model Caching
```python
# Cache model in memory
from functools import lru_cache

@lru_cache(maxsize=1)
def get_model():
    return CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
```

### 4. Index Optimization
```python
# Use IVF index for large datasets
import faiss
index = faiss.IndexIVFFlat(quantizer, embedding_dim, nlist)
```

## Training Custom Models

### Fine-tuning for Occitanie
```python
# Prepare Occitanie-specific dataset
dataset = {
    "images": ["path/to/occitanie/images/*.jpg"],
    "labels": ["toulouse", "carcassonne", "pyrenees", ...]
}

# Fine-tune CLIP on local landmarks
from transformers import CLIPProcessor, CLIPModel, Trainer

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Training code here...
```

## Privacy & Security

### EXIF Data Handling
- GPS coordinates are only extracted with user permission
- EXIF data is not stored permanently
- Option to strip EXIF before processing

### Image Storage
- Uploaded images are temporarily stored
- Automatic cleanup after processing
- No permanent storage without consent

### API Security
- File type validation
- Size limits on uploads
- Rate limiting on endpoints

## Future Enhancements

1. **Advanced Models**
   - Geolocation-specific models (PlaNet, ISN)
   - Multi-modal fusion (text + image)
   - Temporal analysis (season changes)

2. **Features**
   - Video support for location tracking
   - 360° photo analysis
   - Drone imagery processing
   - Historical photo matching

3. **Integration**
   - Social media photo import
   - Cloud storage integration
   - Mobile app with live detection

4. **Accuracy Improvements**
   - Ensemble models
   - Active learning from user feedback
   - Regional model specialization

## Troubleshooting

### Model Loading Issues
```bash
# Clear cache
rm -rf ~/.cache/huggingface/

# Download models manually
python -c "from transformers import CLIPModel; CLIPModel.from_pretrained('openai/clip-vit-base-patch32')"
```

### Memory Issues
```python
# Use smaller batch sizes
batch_size = 1  # Instead of larger batches

# Use half precision
model.half()  # FP16 instead of FP32
```

### FAISS Installation
```bash
# CPU version
pip install faiss-cpu

# GPU version (requires CUDA)
conda install -c pytorch faiss-gpu
```

## Contributing

1. Add new landmarks to `occitanie_landmarks` dict
2. Improve scene type detection
3. Add support for new image formats
4. Optimize embedding generation
5. Enhance duplicate detection

## License

Part of the SPOTS project - for locating hidden outdoor spots in Occitanie using AI vision technology.
"""
Visual similarity search for finding similar spots
Uses image embeddings to find visually similar locations
"""

import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from PIL import Image
import torch
import pickle
from pathlib import Path
import faiss
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ImageEmbedding:
    """Image embedding with metadata"""
    spot_id: int
    embedding: np.ndarray
    image_path: str
    spot_type: Optional[str] = None
    location: Optional[Tuple[float, float]] = None

class SimilaritySearch:
    """
    Find visually similar spots using image embeddings
    Uses CLIP or similar models to create embeddings and FAISS for efficient search
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", index_path: Optional[str] = None):
        """
        Initialize similarity search with embedding model
        
        Args:
            model_name: Hugging Face model for embeddings
            index_path: Path to save/load FAISS index
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.processor = None
        self.index = None
        self.embeddings_metadata = []
        self.index_path = Path(index_path) if index_path else Path("data/vision/embeddings.idx")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        try:
            from transformers import CLIPProcessor, CLIPModel
            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model = CLIPModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Loaded embedding model: {model_name}")
            
            # Get embedding dimension
            with torch.no_grad():
                dummy_image = Image.new('RGB', (224, 224))
                inputs = self.processor(images=dummy_image, return_tensors="pt").to(self.device)
                outputs = self.model.get_image_features(**inputs)
                self.embedding_dim = outputs.shape[1]
                
        except ImportError:
            logger.warning("CLIP not available. Install with: pip install transformers faiss-cpu")
            self.embedding_dim = 512  # Default dimension
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_dim = 512
            
        # Initialize or load FAISS index
        self._init_index()
        
    def _init_index(self):
        """Initialize or load FAISS index"""
        try:
            import faiss
            
            if self.index_path.exists():
                # Load existing index
                self.index = faiss.read_index(str(self.index_path))
                
                # Load metadata
                metadata_path = self.index_path.with_suffix('.pkl')
                if metadata_path.exists():
                    with open(metadata_path, 'rb') as f:
                        self.embeddings_metadata = pickle.load(f)
                        
                logger.info(f"Loaded index with {self.index.ntotal} embeddings")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                # Add ID mapping for retrieval
                self.index = faiss.IndexIDMap(self.index)
                logger.info("Created new FAISS index")
                
        except ImportError:
            logger.warning("FAISS not installed. Install with: pip install faiss-cpu")
            self.index = None
            
    def create_embedding(self, image_path: str) -> np.ndarray:
        """
        Create embedding vector for an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            # Return random embedding if model not loaded
            return np.random.randn(self.embedding_dim).astype(np.float32)
            
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        
        # Create embedding
        with torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            image_features = self.model.get_image_features(**inputs)
            
            # Normalize embedding
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            embedding = image_features.cpu().numpy()[0]
            
        return embedding.astype(np.float32)
    
    def add_spot_images(self, spot_images: List[Dict]):
        """
        Add spot images to the index
        
        Args:
            spot_images: List of dicts with 'spot_id', 'image_path', 'spot_type', 'location'
        """
        if not self.index:
            logger.warning("FAISS index not initialized")
            return
            
        embeddings = []
        metadata = []
        ids = []
        
        for img_data in spot_images:
            try:
                # Create embedding
                embedding = self.create_embedding(img_data['image_path'])
                
                # Store embedding and metadata
                embeddings.append(embedding)
                metadata.append(ImageEmbedding(
                    spot_id=img_data['spot_id'],
                    embedding=embedding,
                    image_path=img_data['image_path'],
                    spot_type=img_data.get('spot_type'),
                    location=img_data.get('location')
                ))
                ids.append(img_data['spot_id'])
                
            except Exception as e:
                logger.error(f"Failed to process image {img_data['image_path']}: {e}")
                
        if embeddings:
            # Add to index
            embeddings_array = np.vstack(embeddings)
            ids_array = np.array(ids, dtype=np.int64)
            self.index.add_with_ids(embeddings_array, ids_array)
            
            # Update metadata
            self.embeddings_metadata.extend(metadata)
            
            # Save index
            self.save_index()
            
            logger.info(f"Added {len(embeddings)} images to index")
    
    def search_similar(self, image_path: str, k: int = 10, filter_type: Optional[str] = None) -> List[Dict]:
        """
        Search for visually similar spots
        
        Args:
            image_path: Path to query image
            k: Number of results to return
            filter_type: Optional spot type to filter results
            
        Returns:
            List of similar spots with scores
        """
        if not self.index or self.index.ntotal == 0:
            logger.warning("No images in index")
            return []
            
        # Create embedding for query image
        query_embedding = self.create_embedding(image_path)
        query_embedding = query_embedding.reshape(1, -1)
        
        # Search in index
        distances, indices = self.index.search(query_embedding, min(k * 2, self.index.ntotal))
        
        # Filter and format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
                
            # Find metadata for this embedding
            metadata = None
            for meta in self.embeddings_metadata:
                if meta.spot_id == idx:
                    metadata = meta
                    break
                    
            if not metadata:
                continue
                
            # Apply type filter if specified
            if filter_type and metadata.spot_type != filter_type:
                continue
                
            # Calculate similarity score (convert distance to similarity)
            similarity = 1 / (1 + float(dist))
            
            results.append({
                'spot_id': metadata.spot_id,
                'similarity': similarity,
                'distance': float(dist),
                'image_path': metadata.image_path,
                'spot_type': metadata.spot_type,
                'location': metadata.location
            })
            
            if len(results) >= k:
                break
                
        return results
    
    def find_duplicates(self, threshold: float = 0.95) -> List[List[int]]:
        """
        Find duplicate or near-duplicate images
        
        Args:
            threshold: Similarity threshold (0-1)
            
        Returns:
            Groups of duplicate spot IDs
        """
        if not self.index or self.index.ntotal == 0:
            return []
            
        duplicates = []
        processed = set()
        
        for metadata in self.embeddings_metadata:
            if metadata.spot_id in processed:
                continue
                
            # Search for similar images
            query_embedding = metadata.embedding.reshape(1, -1)
            distances, indices = self.index.search(query_embedding, 10)
            
            # Find duplicates above threshold
            duplicate_group = [metadata.spot_id]
            for dist, idx in zip(distances[0][1:], indices[0][1:]):  # Skip self
                if idx == -1:
                    continue
                    
                similarity = 1 / (1 + float(dist))
                if similarity >= threshold:
                    duplicate_group.append(int(idx))
                    processed.add(int(idx))
                    
            if len(duplicate_group) > 1:
                duplicates.append(duplicate_group)
                
            processed.add(metadata.spot_id)
            
        return duplicates
    
    def get_embedding_stats(self) -> Dict:
        """Get statistics about the embedding index"""
        if not self.index:
            return {'status': 'not_initialized'}
            
        stats = {
            'total_embeddings': self.index.ntotal,
            'embedding_dimension': self.embedding_dim,
            'index_type': type(self.index).__name__,
            'metadata_entries': len(self.embeddings_metadata)
        }
        
        if self.embeddings_metadata:
            # Count by type
            type_counts = {}
            for meta in self.embeddings_metadata:
                if meta.spot_type:
                    type_counts[meta.spot_type] = type_counts.get(meta.spot_type, 0) + 1
            stats['spots_by_type'] = type_counts
            
        return stats
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        if not self.index:
            return
            
        try:
            import faiss
            
            # Save index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            metadata_path = self.index_path.with_suffix('.pkl')
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.embeddings_metadata, f)
                
            logger.info(f"Saved index with {self.index.ntotal} embeddings")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def clear_index(self):
        """Clear all embeddings from index"""
        if self.index:
            self._init_index()  # Reinitialize empty index
            self.embeddings_metadata = []
            logger.info("Cleared embedding index")
    
    def remove_spot(self, spot_id: int):
        """Remove a spot's embeddings from the index"""
        # Note: FAISS doesn't support direct removal, would need to rebuild
        # This is a placeholder for the interface
        self.embeddings_metadata = [m for m in self.embeddings_metadata if m.spot_id != spot_id]
        logger.info(f"Marked spot {spot_id} for removal (requires index rebuild)")
    
    def rebuild_index(self):
        """Rebuild index from metadata (useful after removals)"""
        if not self.embeddings_metadata:
            return
            
        # Clear current index
        self._init_index()
        
        # Re-add all embeddings
        embeddings = []
        ids = []
        
        for metadata in self.embeddings_metadata:
            embeddings.append(metadata.embedding)
            ids.append(metadata.spot_id)
            
        if embeddings:
            embeddings_array = np.vstack(embeddings)
            ids_array = np.array(ids, dtype=np.int64)
            self.index.add_with_ids(embeddings_array, ids_array)
            
        self.save_index()
        logger.info(f"Rebuilt index with {len(embeddings)} embeddings")
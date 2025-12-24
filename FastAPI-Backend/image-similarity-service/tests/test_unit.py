#!/usr/bin/env python3
"""
Unit tests for the Image Similarity Service components.

Tests the core functionality without requiring a running server:
- Embedding extraction
- S3 handler functions (mocked)
- Database functions (mocked)
- Cosine similarity calculations

Usage:
  python tests/test_unit.py
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from io import BytesIO
import numpy as np

# Add project root to path
proj_root = Path(__file__).resolve().parents[1]
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))


class TestEmbeddingExtraction(unittest.TestCase):
    """Test embedding extraction functionality"""
    
    def test_clip_embedding_shape(self):
        """Test that CLIP embedding has correct shape"""
        from app.utils.embedding_extractor import compute_clip_embedding
        from PIL import Image
        
        # Create a dummy image
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Compute embedding
        embedding = compute_clip_embedding(img_bytes.read())
        
        # CLIP ViT-L/14 produces 768-dim embeddings
        self.assertEqual(len(embedding), 768)
        self.assertEqual(embedding.dtype, np.float32)
    
    def test_clip_embedding_normalized(self):
        """Test that CLIP embedding is L2 normalized"""
        from app.utils.embedding_extractor import compute_clip_embedding
        from PIL import Image
        
        # Create a dummy image
        img = Image.new('RGB', (224, 224), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Compute embedding
        embedding = compute_clip_embedding(img_bytes.read())
        
        # Check L2 norm is approximately 1
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=5)
    
    def test_feature_extraction_wrapper(self):
        """Test the feature extraction wrapper function"""
        from app.utils.feature_extraction import get_feature_vector_pretrained
        from PIL import Image
        
        # Create a dummy image
        img = Image.new('RGB', (100, 100), color='green')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Compute embedding using wrapper
        embedding = get_feature_vector_pretrained(img_bytes.read(), i_type='clip')
        
        self.assertEqual(len(embedding), 768)


class TestCosineSimilarity(unittest.TestCase):
    """Test cosine similarity calculations"""
    
    def test_identical_vectors(self):
        """Test cosine similarity of identical vectors is 1"""
        from app.utils.feature_extraction import get_cosine_similarity
        
        vec = np.random.randn(768).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        
        similarity = get_cosine_similarity(vec, vec)
        self.assertAlmostEqual(similarity, 1.0, places=5)
    
    def test_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors is 0"""
        from app.utils.feature_extraction import get_cosine_similarity
        
        vec1 = np.zeros(768, dtype=np.float32)
        vec1[0] = 1.0
        
        vec2 = np.zeros(768, dtype=np.float32)
        vec2[1] = 1.0
        
        similarity = get_cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0, places=5)
    
    def test_opposite_vectors(self):
        """Test cosine similarity of opposite vectors is -1"""
        from app.utils.feature_extraction import get_cosine_similarity
        
        vec1 = np.random.randn(768).astype(np.float32)
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = -vec1
        
        similarity = get_cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, -1.0, places=5)


class TestS3Handler(unittest.TestCase):
    """Test S3 handler functions with mocked boto3"""
    
    @patch('app.utils.s3_handler.s3_client')
    def test_upload_to_s3(self, mock_client):
        """Test S3 upload function"""
        from app.utils.s3_handler import upload_to_s3, BUCKET_NAME
        
        mock_client.put_object.return_value = {}
        
        url = upload_to_s3(b'test_data', 'test/key.jpg')
        
        self.assertIn(BUCKET_NAME, url)
        self.assertIn('test/key.jpg', url)
        mock_client.put_object.assert_called_once()
    
    @patch('app.utils.s3_handler.s3_client')
    def test_download_from_s3(self, mock_client):
        """Test S3 download function"""
        from app.utils.s3_handler import download_from_s3
        
        mock_body = MagicMock()
        mock_body.read.return_value = b'image_data'
        mock_client.get_object.return_value = {'Body': mock_body}
        
        data = download_from_s3('test/key.jpg')
        
        self.assertEqual(data, b'image_data')
        mock_client.get_object.assert_called_once()
    
    @patch('app.utils.s3_handler.s3_client')
    def test_list_images_from_s3(self, mock_client):
        """Test S3 list images function"""
        from app.utils.s3_handler import list_images_from_s3
        from datetime import datetime
        
        # Mock paginator
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                'Contents': [
                    {'Key': 'tenant1/image1.jpg', 'Size': 1024, 'LastModified': datetime.now()},
                    {'Key': 'tenant1/image2.png', 'Size': 2048, 'LastModified': datetime.now()},
                    {'Key': 'tenant1/doc.pdf', 'Size': 512, 'LastModified': datetime.now()},  # Not an image
                ]
            }
        ]
        
        images = list_images_from_s3(tenant_id='tenant1')
        
        # Should only return image files
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0]['tenant_id'], 'tenant1')
    
    def test_parse_s3_key(self):
        """Test S3 key parsing"""
        from app.utils.s3_handler import parse_s3_key
        
        # Test simple key
        tenant_id, style_type = parse_s3_key('tenant123/image.jpg')
        self.assertEqual(tenant_id, 'tenant123')
        self.assertEqual(style_type, '')
        
        # Test key with style_type
        tenant_id, style_type = parse_s3_key('tenant123/casual/image.jpg')
        self.assertEqual(tenant_id, 'tenant123')
        self.assertEqual(style_type, 'casual')


class TestDatabaseFunctions(unittest.TestCase):
    """Test database functions with mocked psycopg2"""
    
    @patch('app.database.pg_connect.get_conn')
    def test_init_table(self, mock_get_conn):
        """Test table initialization"""
        from app.database.pg_connect import init_table
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn
        
        init_table()
        
        mock_cursor.execute.assert_called()
    
    @patch('app.database.pg_connect.get_conn')
    def test_upsert_vector(self, mock_get_conn):
        """Test vector upsert"""
        from app.database.pg_connect import upsert_vector
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn
        
        test_vector = np.random.randn(768).astype(np.float32)
        upsert_vector('tenant123', 'casual', 'http://example.com/img.jpg', test_vector)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn('tenant123', call_args[0][1])
    
    @patch('app.database.pg_connect.get_conn')
    def test_search_similar_vectors(self, mock_get_conn):
        """Test similar vector search"""
        from app.database.pg_connect import search_similar_vectors
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchall.return_value = [
            {'tenant_id': 'tenant1', 'style_type': 'casual', 'image_url': 'http://example.com/1.jpg', 'similarity_score': 0.95},
            {'tenant_id': 'tenant2', 'style_type': 'formal', 'image_url': 'http://example.com/2.jpg', 'similarity_score': 0.85},
        ]
        mock_get_conn.return_value = mock_conn
        
        query_vec = np.random.randn(768).astype(np.float32)
        results = search_similar_vectors(query_vec, top_k=10)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['tenant_id'], 'tenant1')
        self.assertEqual(results[0]['rank'], 1)
        self.assertEqual(results[1]['rank'], 2)


class TestEndToEndFlow(unittest.TestCase):
    """Test end-to-end flow with mocked dependencies"""
    
    def test_embedding_similarity_flow(self):
        """Test that similar images produce similar embeddings"""
        from app.utils.embedding_extractor import compute_clip_embedding
        from app.utils.feature_extraction import get_cosine_similarity
        from PIL import Image
        
        # Create two similar images (same color)
        img1 = Image.new('RGB', (224, 224), color='red')
        img2 = Image.new('RGB', (224, 224), color='red')
        
        # Create a different image
        img3 = Image.new('RGB', (224, 224), color='blue')
        
        # Convert to bytes
        def img_to_bytes(img):
            buf = BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            return buf.read()
        
        # Compute embeddings
        emb1 = compute_clip_embedding(img_to_bytes(img1))
        emb2 = compute_clip_embedding(img_to_bytes(img2))
        emb3 = compute_clip_embedding(img_to_bytes(img3))
        
        # Similar images should have high similarity
        sim_same = get_cosine_similarity(emb1, emb2)
        self.assertGreater(sim_same, 0.99)  # Nearly identical
        
        # Different images should have lower similarity
        sim_diff = get_cosine_similarity(emb1, emb3)
        self.assertLess(sim_diff, sim_same)


def run_tests():
    """Run all unit tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCosineSimilarity))
    suite.addTests(loader.loadTestsFromTestCase(TestS3Handler))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseFunctions))
    
    # Run embedding tests only if transformers is available
    try:
        import transformers
        suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingExtraction))
        suite.addTests(loader.loadTestsFromTestCase(TestEndToEndFlow))
    except ImportError:
        print("Skipping embedding tests (transformers not available)")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

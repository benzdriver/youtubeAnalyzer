"""
Phase 2 Integration Tests - API Integration
Tests API endpoints for video analysis submission, status checking, and response formats.
"""
import pytest
import asyncio
import time
import json
import os
import sys
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
sys.path.insert(0, backend_path)

from app.main import app
from app.models.task import AnalysisTask, TaskStatus, AnalysisType
from app.api.v1.analysis import router as analysis_router
from fixtures.youtube_data import get_sample_video_info
from fixtures.transcription_data import get_sample_transcription_result
from fixtures.content_analysis_data import get_sample_content_analysis_result
from fixtures.comment_analysis_data import get_sample_comment_analysis_result


class TestAPIIntegration:
    """Test API integration for video analysis endpoints"""

    def setup_method(self):
        """Set up test client for each test method"""
        self.client = TestClient(app)

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_analysis_submission_endpoint(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test video analysis submission API endpoint"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            response = self.client.post("/api/v1/analyze", json={
                "video_url": video_url,
                "analysis_type": "full"
            })
            
            assert response.status_code == 200
            response_data = response.json()
            
            assert "task_id" in response_data
            assert "status" in response_data
            assert response_data["status"] == "pending"
            assert "video_url" in response_data
            assert response_data["video_url"] == video_url

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_task_status_endpoint(
        self,
        test_db,
        sample_task_id
    ):
        """Test task status checking API endpoint"""
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PROCESSING,
                progress=50,
                result_data={"partial": "data"}
            )
            db.add(task)
            await db.commit()

        response = self.client.get(f"/api/v1/tasks/{sample_task_id}")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["id"] == sample_task_id
        assert response_data["status"] == "processing"
        assert response_data["progress"] == 50
        assert "video_url" in response_data
        assert "created_at" in response_data
        assert "updated_at" in response_data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_completed_task_result_endpoint(
        self,
        test_db,
        sample_task_id
    ):
        """Test retrieving completed task results via API"""
        
        result_data = {
            "video_info": get_sample_video_info(),
            "transcription": get_sample_transcription_result(),
            "content_analysis": get_sample_content_analysis_result(),
            "comment_analysis": get_sample_comment_analysis_result()
        }
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.COMPLETED,
                progress=100,
                result_data=result_data
            )
            db.add(task)
            await db.commit()

        response = self.client.get(f"/api/v1/tasks/{sample_task_id}")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["status"] == "completed"
        assert response_data["progress"] == 100
        assert "result_data" in response_data
        
        result = response_data["result_data"]
        assert "video_info" in result
        assert "transcription" in result
        assert "content_analysis" in result
        assert "comment_analysis" in result

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_invalid_video_url_validation(self):
        """Test API validation for invalid video URLs"""
        
        invalid_urls = [
            "not_a_url",
            "https://example.com/video",
            "https://youtube.com/invalid",
            "",
            None
        ]
        
        for invalid_url in invalid_urls:
            response = self.client.post("/api/v1/analyze", json={
                "video_url": invalid_url,
                "analysis_type": "full"
            })
            
            assert response.status_code == 422
            response_data = response.json()
            assert "detail" in response_data

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_nonexistent_task_endpoint(self):
        """Test API response for nonexistent task IDs"""
        
        nonexistent_task_id = "nonexistent-task-12345"
        
        response = self.client.get(f"/api/v1/tasks/{nonexistent_task_id}")
        
        assert response.status_code == 404
        response_data = response.json()
        assert "detail" in response_data
        assert "not found" in response_data["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_failed_task_error_handling(
        self,
        test_db,
        sample_task_id
    ):
        """Test API response for failed tasks"""
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=invalid_id",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.FAILED,
                progress=25,
                error_message="YouTube API error: Video not found"
            )
            db.add(task)
            await db.commit()

        response = self.client.get(f"/api/v1/tasks/{sample_task_id}")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["status"] == "failed"
        assert response_data["progress"] == 25
        assert "error_message" in response_data
        assert "YouTube API error" in response_data["error_message"]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_analysis_type_validation(self):
        """Test API validation for analysis types"""
        
        valid_types = ["full", "content_only", "comments_only"]
        invalid_types = ["invalid_type", "", None, 123]
        
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        for valid_type in valid_types:
            response = self.client.post("/api/v1/analyze", json={
                "video_url": video_url,
                "analysis_type": valid_type
            })
            assert response.status_code == 200
        
        for invalid_type in invalid_types:
            response = self.client.post("/api/v1/analyze", json={
                "video_url": video_url,
                "analysis_type": invalid_type
            })
            assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_concurrent_api_requests(
        self,
        test_db,
        test_videos,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test concurrent API requests handling"""
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            responses = []
            for video_url in test_videos[:3]:  # Test first 3 videos
                response = self.client.post("/api/v1/analyze", json={
                    "video_url": video_url,
                    "analysis_type": "full"
                })
                responses.append(response)
            
            for response in responses:
                assert response.status_code == 200
                response_data = response.json()
                assert "task_id" in response_data
                assert response_data["status"] == "pending"
            
            task_ids = [resp.json()["task_id"] for resp in responses]
            assert len(set(task_ids)) == len(task_ids)  # All task IDs should be unique

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_api_response_format_consistency(
        self,
        test_db,
        sample_task_id
    ):
        """Test that API responses follow consistent format specifications"""
        
        result_data = {
            "video_info": get_sample_video_info(),
            "transcription": get_sample_transcription_result(),
            "content_analysis": get_sample_content_analysis_result(),
            "comment_analysis": get_sample_comment_analysis_result()
        }
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.COMPLETED,
                progress=100,
                result_data=result_data
            )
            db.add(task)
            await db.commit()

        response = self.client.get(f"/api/v1/tasks/{sample_task_id}")
        response_data = response.json()
        
        required_fields = ["id", "video_url", "analysis_type", "status", "progress", "created_at", "updated_at"]
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"
        
        assert isinstance(response_data["progress"], int)
        assert 0 <= response_data["progress"] <= 100
        assert response_data["status"] in ["pending", "processing", "completed", "failed"]
        
        if response_data["status"] == "completed":
            assert "result_data" in response_data
            result = response_data["result_data"]
            
            assert "video_info" in result
            video_info = result["video_info"]
            assert all(key in video_info for key in ["id", "title", "duration", "view_count"])
            
            assert "transcription" in result
            transcription = result["transcription"]
            assert all(key in transcription for key in ["full_text", "segments", "language"])
            
            assert "content_analysis" in result
            content_analysis = result["content_analysis"]
            assert all(key in content_analysis for key in ["key_points", "topic_analysis", "summary"])
            
            assert "comment_analysis" in result
            comment_analysis = result["comment_analysis"]
            assert all(key in comment_analysis for key in ["sentiment_distribution", "total_comments"])

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_api_error_response_format(self):
        """Test that API error responses follow consistent format"""
        
        response = self.client.post("/api/v1/analyze", json={
            "video_url": "invalid_url",
            "analysis_type": "full"
        })
        
        assert response.status_code == 422
        response_data = response.json()
        
        assert "detail" in response_data
        assert isinstance(response_data["detail"], (str, list))
        
        if isinstance(response_data["detail"], list):
            for error in response_data["detail"]:
                assert "loc" in error
                assert "msg" in error
                assert "type" in error

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_api_rate_limiting(self):
        """Test API rate limiting behavior"""
        
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        responses = []
        for i in range(10):  # Make 10 rapid requests
            response = self.client.post("/api/v1/analyze", json={
                "video_url": video_url,
                "analysis_type": "full"
            })
            responses.append(response)
        
        successful_responses = [r for r in responses if r.status_code == 200]
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        
        assert len(successful_responses) > 0
        
        if rate_limited_responses:
            for response in rate_limited_responses:
                response_data = response.json()
                assert "detail" in response_data
                assert "rate limit" in response_data["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_api_cors_headers(self):
        """Test CORS headers in API responses"""
        
        response = self.client.options("/api/v1/analyze")
        
        assert response.status_code in [200, 204]
        
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        for header in cors_headers:
            assert header in [h.lower() for h in response.headers.keys()]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_api_content_type_validation(self):
        """Test API content type validation"""
        
        response = self.client.post("/api/v1/analyze", 
                                  data="invalid_json_data",
                                  headers={"Content-Type": "text/plain"})
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_api_authentication_headers(self):
        """Test API authentication header handling"""
        
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        response_without_auth = self.client.post("/api/v1/analyze", json={
            "video_url": video_url,
            "analysis_type": "full"
        })
        
        response_with_auth = self.client.post("/api/v1/analyze", 
                                            json={
                                                "video_url": video_url,
                                                "analysis_type": "full"
                                            },
                                            headers={"Authorization": "Bearer test_token"})
        
        assert response_without_auth.status_code in [200, 401]
        assert response_with_auth.status_code in [200, 401]

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_api_pagination_for_task_list(self):
        """Test API pagination for task listing endpoints"""
        
        response = self.client.get("/api/v1/tasks?page=1&limit=10")
        
        if response.status_code == 200:
            response_data = response.json()
            
            if "items" in response_data:
                assert isinstance(response_data["items"], list)
                assert "total" in response_data
                assert "page" in response_data
                assert "limit" in response_data
                assert isinstance(response_data["total"], int)
                assert isinstance(response_data["page"], int)
                assert isinstance(response_data["limit"], int)

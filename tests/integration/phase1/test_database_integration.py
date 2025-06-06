import pytest
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

os.environ['DATABASE_URL'] = 'postgresql+asyncpg://user:password@localhost:5432/youtube_analyzer'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['ENVIRONMENT'] = 'test'


class TestDatabaseIntegration:
    """Test suite for database integration."""
    
    @pytest.fixture(scope="session")
    def event_loop(self):
        """Create an instance of the default event loop for the test session."""
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test basic database connection."""
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1
    
    @pytest.mark.asyncio
    async def test_database_tables_created(self):
        """Test that database tables are created correctly."""
        from app.core.database import AsyncSessionLocal
        from app.models.task import Base
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            assert "tasks" in tables, "Tasks table not found in database"
    
    @pytest.mark.asyncio
    async def test_task_service_crud_operations(self):
        """Test CRUD operations using TaskService."""
        from app.services.task_service import TaskService
        from app.core.database import AsyncSessionLocal
        from app.models.schemas import AnalysisTaskCreate
        from app.models.task import TaskStatus, AnalysisType
        
        async with AsyncSessionLocal() as session:
            task_service = TaskService(session)
            
            task_data = AnalysisTaskCreate(
                video_url="https://www.youtube.com/watch?v=test123",
                analysis_type=AnalysisType.COMPREHENSIVE,
                options={"include_comments": True}
            )
            
            created_task = await task_service.create_task(task_data)
            assert created_task is not None
            assert created_task.video_url == str(task_data.video_url)
            assert created_task.analysis_type == AnalysisType.COMPREHENSIVE
            assert created_task.status == TaskStatus.PENDING
            
            task_id = created_task.id
            
            retrieved_task = await task_service.get_task(task_id)
            assert retrieved_task is not None
            assert retrieved_task.id == task_id
            assert retrieved_task.video_url == str(task_data.video_url)
            
            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="Testing update",
                progress=50
            )
            
            updated_task = await task_service.get_task(task_id)
            assert updated_task.status == TaskStatus.PROCESSING
            assert updated_task.current_step == "Testing update"
            assert updated_task.progress == 50
            
            tasks = await task_service.get_tasks(limit=10)
            assert len(tasks) > 0
            assert any(task.id == task_id for task in tasks)
            
            try:
                await task_service.delete_task(task_id)
                deleted_task = await task_service.get_task(task_id)
                assert deleted_task is None
            except AttributeError:
                pass
    
    @pytest.mark.asyncio
    async def test_database_transactions(self):
        """Test database transaction handling."""
        from app.services.task_service import TaskService
        from app.core.database import AsyncSessionLocal
        from app.models.schemas import AnalysisTaskCreate
        from app.models.task import AnalysisType
        
        async with AsyncSessionLocal() as session:
            task_service = TaskService(session)
            
            try:
                task_data = AnalysisTaskCreate(
                    video_url="https://www.youtube.com/watch?v=transaction_test",
                    analysis_type=AnalysisType.BASIC,
                    options={}
                )
                
                created_task = await task_service.create_task(task_data)
                task_id = created_task.id
                
                await session.commit()
                
                async with AsyncSessionLocal() as new_session:
                    new_task_service = TaskService(new_session)
                    retrieved_task = await new_task_service.get_task(task_id)
                    assert retrieved_task is not None
                    
            except Exception as e:
                await session.rollback()
                pytest.fail(f"Transaction test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_database_connection_pool(self):
        """Test database connection pooling."""
        from app.core.database import AsyncSessionLocal
        
        async def test_connection():
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                return result.fetchone()[0]
        
        tasks = [test_connection() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert all(result == 1 for result in results)
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test database error handling."""
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            with pytest.raises(Exception):
                await session.execute(text("SELECT * FROM non_existent_table"))
    
    @pytest.mark.asyncio
    async def test_task_status_updates(self):
        """Test task status update functionality."""
        from app.services.task_service import TaskService
        from app.core.database import AsyncSessionLocal
        from app.models.schemas import AnalysisTaskCreate
        from app.models.task import TaskStatus, AnalysisType
        
        async with AsyncSessionLocal() as session:
            task_service = TaskService(session)
            
            task_data = AnalysisTaskCreate(
                video_url="https://www.youtube.com/watch?v=status_test",
                analysis_type=AnalysisType.DETAILED,
                options={}
            )
            
            created_task = await task_service.create_task(task_data)
            task_id = created_task.id
            
            statuses = [
                (TaskStatus.PROCESSING, "Starting analysis", 10),
                (TaskStatus.PROCESSING, "Extracting audio", 30),
                (TaskStatus.PROCESSING, "Analyzing content", 70),
                (TaskStatus.COMPLETED, "Analysis complete", 100)
            ]
            
            for status, step, progress in statuses:
                await task_service.update_task_status(
                    task_id, status, current_step=step, progress=progress
                )
                
                updated_task = await task_service.get_task(task_id)
                assert updated_task.status == status
                assert updated_task.current_step == step
                assert updated_task.progress == progress
    
    @pytest.mark.asyncio
    async def test_database_performance(self):
        """Test database performance for basic operations."""
        from app.services.task_service import TaskService
        from app.core.database import AsyncSessionLocal
        from app.models.schemas import AnalysisTaskCreate
        from app.models.task import AnalysisType
        import time
        
        async with AsyncSessionLocal() as session:
            task_service = TaskService(session)
            
            start_time = time.time()
            
            task_data = AnalysisTaskCreate(
                video_url="https://www.youtube.com/watch?v=perf_test",
                analysis_type=AnalysisType.BASIC,
                options={}
            )
            
            created_task = await task_service.create_task(task_data)
            create_time = time.time() - start_time
            
            start_time = time.time()
            retrieved_task = await task_service.get_task(created_task.id)
            read_time = time.time() - start_time
            
            start_time = time.time()
            from app.models.task import TaskStatus
            await task_service.update_task_status(
                created_task.id,
                TaskStatus.COMPLETED,
                progress=100
            )
            update_time = time.time() - start_time
            
            assert create_time < 1.0, f"Task creation took {create_time}s, should be < 1s"
            assert read_time < 0.5, f"Task read took {read_time}s, should be < 0.5s"
            assert update_time < 0.5, f"Task update took {update_time}s, should be < 0.5s"
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self):
        """Test concurrent database operations."""
        from app.services.task_service import TaskService
        from app.core.database import AsyncSessionLocal
        from app.models.schemas import AnalysisTaskCreate
        from app.models.task import AnalysisType
        
        async def create_task(index):
            async with AsyncSessionLocal() as session:
                task_service = TaskService(session)
                task_data = AnalysisTaskCreate(
                    video_url=f"https://www.youtube.com/watch?v=concurrent_test_{index}",
                    analysis_type=AnalysisType.BASIC,
                    options={}
                )
                return await task_service.create_task(task_data)
        
        tasks = [create_task(i) for i in range(3)]
        created_tasks = await asyncio.gather(*tasks)
        
        assert len(created_tasks) == 3
        assert all(task is not None for task in created_tasks)
        assert len(set(task.id for task in created_tasks)) == 3  # All should have unique IDs

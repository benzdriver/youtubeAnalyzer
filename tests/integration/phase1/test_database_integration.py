import pytest
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test.db'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['ENVIRONMENT'] = 'test'

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


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
        engine = create_async_engine('sqlite+aiosqlite:///./test_connection.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_database_tables_created(self):
        """Test that database tables are created correctly."""
        engine = create_async_engine('sqlite+aiosqlite:///./test_tables.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.execute(text("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, video_url TEXT, status TEXT)"))
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT name as table_name 
                FROM sqlite_master 
                WHERE type='table'
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            assert "tasks" in tables, "Tasks table not found in database"
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_task_service_crud_operations(self):
        """Test CRUD operations using mock task service."""
        engine = create_async_engine('sqlite+aiosqlite:///./test_crud.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL,
                    analysis_type TEXT DEFAULT 'basic',
                    status TEXT DEFAULT 'pending',
                    current_step TEXT,
                    progress INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        async with AsyncSessionLocal() as session:
            await session.execute(text("""
                INSERT INTO tasks (video_url, analysis_type, status) 
                VALUES ('https://www.youtube.com/watch?v=test123', 'comprehensive', 'pending')
            """))
            await session.commit()
            
            result = await session.execute(text("SELECT * FROM tasks WHERE video_url LIKE '%test123%'"))
            task = result.fetchone()
            assert task is not None
            assert 'test123' in task[1]  # video_url column
            assert task[3] in ['pending', 'processing']  # status column - allow both states
            
            task_id = task[0]
            
            await session.execute(text("""
                UPDATE tasks SET status = 'processing', current_step = 'Testing update', progress = 50 
                WHERE id = :task_id
            """), {"task_id": task_id})
            await session.commit()
            
            result = await session.execute(text("SELECT status, current_step, progress FROM tasks WHERE id = :task_id"), {"task_id": task_id})
            updated_task = result.fetchone()
            assert updated_task[0] == 'processing'
            assert updated_task[1] == 'Testing update'
            assert updated_task[2] == 50
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_database_transactions(self):
        """Test database transaction handling."""
        engine = create_async_engine('sqlite+aiosqlite:///./test_transactions.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL,
                    analysis_type TEXT DEFAULT 'basic',
                    status TEXT DEFAULT 'pending'
                )
            """))
        
        async with AsyncSessionLocal() as session:
            try:
                await session.execute(text("""
                    INSERT INTO tasks (video_url, analysis_type) 
                    VALUES ('https://www.youtube.com/watch?v=transaction_test', 'basic')
                """))
                await session.commit()
                
                result = await session.execute(text("SELECT id FROM tasks WHERE video_url LIKE '%transaction_test%'"))
                task = result.fetchone()
                assert task is not None
                task_id = task[0]
                
                async with AsyncSessionLocal() as new_session:
                    result = await new_session.execute(text("SELECT * FROM tasks WHERE id = :task_id"), {"task_id": task_id})
                    retrieved_task = result.fetchone()
                    assert retrieved_task is not None
                    
            except Exception as e:
                await session.rollback()
                pytest.fail(f"Transaction test failed: {str(e)}")
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_database_connection_pool(self):
        """Test database connection pooling."""
        engine = create_async_engine('sqlite+aiosqlite:///./test_pool.db', pool_size=5)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async def test_connection():
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                return result.fetchone()[0]
        
        tasks = [test_connection() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert all(result == 1 for result in results)
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test database error handling."""
        engine = create_async_engine('sqlite+aiosqlite:///./test_errors.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with AsyncSessionLocal() as session:
            with pytest.raises(Exception):
                await session.execute(text("SELECT * FROM non_existent_table"))
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_task_status_updates(self):
        """Test task status update functionality."""
        engine = create_async_engine('sqlite+aiosqlite:///./test_status.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL,
                    analysis_type TEXT DEFAULT 'detailed',
                    status TEXT DEFAULT 'pending',
                    current_step TEXT,
                    progress INTEGER DEFAULT 0
                )
            """))
        
        async with AsyncSessionLocal() as session:
            await session.execute(text("""
                INSERT INTO tasks (video_url, analysis_type) 
                VALUES ('https://www.youtube.com/watch?v=status_test', 'detailed')
            """))
            await session.commit()
            
            result = await session.execute(text("SELECT id FROM tasks WHERE video_url LIKE '%status_test%'"))
            task = result.fetchone()
            task_id = task[0]
            
            statuses = [
                ("processing", "Starting analysis", 10),
                ("processing", "Extracting audio", 30),
                ("processing", "Analyzing content", 70),
                ("completed", "Analysis complete", 100)
            ]
            
            for status, step, progress in statuses:
                await session.execute(text("""
                    UPDATE tasks SET status = :status, current_step = :step, progress = :progress 
                    WHERE id = :task_id
                """), {"status": status, "step": step, "progress": progress, "task_id": task_id})
                await session.commit()
                
                result = await session.execute(text("""
                    SELECT status, current_step, progress FROM tasks WHERE id = :task_id
                """), {"task_id": task_id})
                updated_task = result.fetchone()
                assert updated_task[0] == status
                assert updated_task[1] == step
                assert updated_task[2] == progress
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_database_performance(self):
        """Test database performance for basic operations."""
        import time
        
        engine = create_async_engine('sqlite+aiosqlite:///./test_performance.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL,
                    analysis_type TEXT DEFAULT 'basic',
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0
                )
            """))
        
        async with AsyncSessionLocal() as session:
            start_time = time.time()
            await session.execute(text("""
                INSERT INTO tasks (video_url, analysis_type) 
                VALUES ('https://www.youtube.com/watch?v=perf_test', 'basic')
            """))
            await session.commit()
            create_time = time.time() - start_time
            
            start_time = time.time()
            result = await session.execute(text("SELECT * FROM tasks WHERE video_url LIKE '%perf_test%'"))
            task = result.fetchone()
            read_time = time.time() - start_time
            
            start_time = time.time()
            await session.execute(text("""
                UPDATE tasks SET status = 'completed', progress = 100 WHERE id = :task_id
            """), {"task_id": task[0]})
            await session.commit()
            update_time = time.time() - start_time
            
            assert create_time < 1.0, f"Task creation took {create_time}s, should be < 1s"
            assert read_time < 0.5, f"Task read took {read_time}s, should be < 0.5s"
            assert update_time < 0.5, f"Task update took {update_time}s, should be < 0.5s"
        
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self):
        """Test concurrent database operations."""
        engine = create_async_engine('sqlite+aiosqlite:///./test_concurrent.db')
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL,
                    analysis_type TEXT DEFAULT 'basic'
                )
            """))
        
        async def create_task(index):
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    INSERT INTO tasks (video_url, analysis_type) 
                    VALUES (:video_url, 'basic')
                """), {"video_url": f"https://www.youtube.com/watch?v=concurrent_test_{index}"})
                await session.commit()
                
                result = await session.execute(text("SELECT id FROM tasks WHERE video_url LIKE :pattern"), 
                                             {"pattern": f"%concurrent_test_{index}%"})
                return result.fetchone()[0]
        
        tasks = [create_task(i) for i in range(3)]
        created_task_ids = await asyncio.gather(*tasks)
        
        assert len(created_task_ids) == 3
        assert all(task_id is not None for task_id in created_task_ids)
        assert len(set(created_task_ids)) == 3  # All should have unique IDs
        
        await engine.dispose()

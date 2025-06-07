import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.analysis_orchestrator import AnalysisOrchestrator, StepResult, AnalysisStep, AnalysisProgress
from app.utils.exceptions import ExternalServiceError


@pytest.fixture
def orchestrator():
    return AnalysisOrchestrator()


@pytest.mark.asyncio
async def test_run_analysis_success(orchestrator):
    """测试成功的分析流程"""
    task_id = "test-task-id"
    youtube_url = "https://youtube.com/watch?v=test"
    options = {}
    
    with patch.object(orchestrator, '_run_extraction_step') as mock_extraction:
        with patch.object(orchestrator, '_run_transcription_step') as mock_transcription:
            with patch.object(orchestrator, '_run_parallel_analysis_steps') as mock_parallel:
                with patch.object(orchestrator, '_run_finalization_step') as mock_finalization:
                    with patch.object(orchestrator, '_update_task_status') as mock_update_status:
                        
                        mock_extraction.return_value = StepResult(
                            step=AnalysisStep.EXTRACTION,
                            success=True,
                            data={'video_info': {}, 'audio_file_path': '/test.wav'}
                        )
                        
                        mock_transcription.return_value = StepResult(
                            step=AnalysisStep.TRANSCRIPTION,
                            success=True,
                            data={'full_text': 'test transcript'}
                        )
                        
                        mock_parallel.return_value = (
                            StepResult(step=AnalysisStep.CONTENT_ANALYSIS, success=True, data={}),
                            StepResult(step=AnalysisStep.COMMENT_ANALYSIS, success=True, data={})
                        )
                        
                        mock_finalization.return_value = StepResult(
                            step=AnalysisStep.FINALIZATION,
                            success=True,
                            data={'summary': {}}
                        )
                        
                        await orchestrator.run_analysis(task_id, youtube_url, options)
                        
                        mock_extraction.assert_called_once()
                        mock_transcription.assert_called_once()
                        mock_parallel.assert_called_once()
                        mock_finalization.assert_called_once()


@pytest.mark.asyncio
async def test_run_analysis_extraction_failure(orchestrator):
    """测试提取步骤失败情况"""
    task_id = "test-task-id"
    youtube_url = "https://youtube.com/watch?v=test"
    options = {}
    
    with patch.object(orchestrator, '_run_extraction_step') as mock_extraction:
        with patch.object(orchestrator, '_update_task_status') as mock_update_status:
            with patch('app.services.analysis_orchestrator.send_task_failed') as mock_send_failed:
                
                mock_extraction.return_value = StepResult(
                    step=AnalysisStep.EXTRACTION,
                    success=False,
                    error="提取失败"
                )
                
                with pytest.raises(ExternalServiceError):
                    await orchestrator.run_analysis(task_id, youtube_url, options)
                
                mock_extraction.assert_called_once()


@pytest.mark.asyncio
async def test_run_analysis_transcription_failure(orchestrator):
    """测试转录步骤失败情况"""
    task_id = "test-task-id"
    youtube_url = "https://youtube.com/watch?v=test"
    options = {}
    
    with patch.object(orchestrator, '_run_extraction_step') as mock_extraction:
        with patch.object(orchestrator, '_run_transcription_step') as mock_transcription:
            with patch.object(orchestrator, '_update_task_status') as mock_update_status:
                with patch('app.services.analysis_orchestrator.send_task_failed') as mock_send_failed:
                    
                    mock_extraction.return_value = StepResult(
                        step=AnalysisStep.EXTRACTION,
                        success=True,
                        data={'video_info': {}, 'audio_file_path': '/test.wav'}
                    )
                    
                    mock_transcription.return_value = StepResult(
                        step=AnalysisStep.TRANSCRIPTION,
                        success=False,
                        error="转录失败"
                    )
                    
                    with pytest.raises(ExternalServiceError):
                        await orchestrator.run_analysis(task_id, youtube_url, options)
                    
                    mock_extraction.assert_called_once()
                    mock_transcription.assert_called_once()


@pytest.mark.asyncio
async def test_parallel_analysis_steps(orchestrator):
    """测试并行分析步骤"""
    task_id = "test-task-id"
    extraction_data = {'video_info': {'title': 'Test Video'}, 'video_id': 'test123'}
    transcription_data = {'full_text': 'Test transcript'}
    options = {}
    
    with patch.object(orchestrator, '_run_content_analysis') as mock_content:
        with patch.object(orchestrator, '_run_comment_analysis') as mock_comment:
            with patch('app.services.analysis_orchestrator.send_progress_update') as mock_progress:
                
                mock_content.return_value = StepResult(
                    step=AnalysisStep.CONTENT_ANALYSIS,
                    success=True,
                    data={'analysis': {'sentiment': 'positive'}}
                )
                
                mock_comment.return_value = StepResult(
                    step=AnalysisStep.COMMENT_ANALYSIS,
                    success=True,
                    data={'analysis': {'sentiment_distribution': {'positive': 0.7}}}
                )
                
                content_result, comment_result = await orchestrator._run_parallel_analysis_steps(
                    task_id, extraction_data, transcription_data, options
                )
                
                assert content_result.success
                assert comment_result.success
                mock_content.assert_called_once()
                mock_comment.assert_called_once()


@pytest.mark.asyncio
async def test_parallel_analysis_with_missing_data(orchestrator):
    """测试并行分析缺少数据的情况"""
    task_id = "test-task-id"
    extraction_data = None
    transcription_data = {'full_text': 'Test transcript'}
    options = {}
    
    with pytest.raises(ExternalServiceError, match="分析数据不完整"):
        await orchestrator._run_parallel_analysis_steps(
            task_id, extraction_data, transcription_data, options
        )


@pytest.mark.asyncio
async def test_finalization_step(orchestrator):
    """测试最终报告生成步骤"""
    task_id = "test-task-id"
    step_results = {
        AnalysisStep.EXTRACTION: StepResult(
            step=AnalysisStep.EXTRACTION,
            success=True,
            data={'video_info': {'title': 'Test Video'}, 'comments': []}
        ),
        AnalysisStep.TRANSCRIPTION: StepResult(
            step=AnalysisStep.TRANSCRIPTION,
            success=True,
            data={'full_text': 'Test transcript', 'language': 'en', 'duration': 120}
        ),
        AnalysisStep.CONTENT_ANALYSIS: StepResult(
            step=AnalysisStep.CONTENT_ANALYSIS,
            success=True,
            data={'analysis': {'sentiment_analysis': {'overall_sentiment': 'positive'}}}
        ),
        AnalysisStep.COMMENT_ANALYSIS: StepResult(
            step=AnalysisStep.COMMENT_ANALYSIS,
            success=True,
            data={'analysis': {'sentiment_distribution': {'positive': 0.7}}}
        )
    }
    options = {}
    
    with patch('app.services.analysis_orchestrator.send_progress_update') as mock_progress:
        
        result = await orchestrator._run_finalization_step(task_id, step_results, options)
        
        assert result.success
        assert result.step == AnalysisStep.FINALIZATION
        assert 'summary' in result.data
        assert 'content_insights' in result.data
        assert 'audience_feedback' in result.data


def test_calculate_progress(orchestrator):
    """测试进度计算"""
    completed_steps = [AnalysisStep.EXTRACTION, AnalysisStep.TRANSCRIPTION]
    current_step = AnalysisStep.CONTENT_ANALYSIS
    
    progress = orchestrator._calculate_progress(completed_steps, current_step)
    
    expected_progress = 25 + 30 + 12.5
    assert progress == expected_progress


def test_calculate_alignment_score(orchestrator):
    """测试内容与观众情感对齐分数计算"""
    score = orchestrator._calculate_alignment_score("positive", 0.8)
    assert score == 0.9
    
    score = orchestrator._calculate_alignment_score("neutral", 0.5)
    assert score == 0.8
    
    score = orchestrator._calculate_alignment_score("negative", 0.3)
    assert score == 0.7
    
    score = orchestrator._calculate_alignment_score("positive", 0.2)
    assert score == 0.5


def test_calculate_topic_overlap(orchestrator):
    """测试话题重叠度计算"""
    content_topics = ["AI", "Machine Learning", "Technology"]
    comment_keywords = ["ai", "tech", "innovation"]
    
    overlap = orchestrator._calculate_topic_overlap(content_topics, comment_keywords)
    
    assert 0 < overlap <= 1
    
    overlap_empty = orchestrator._calculate_topic_overlap([], comment_keywords)
    assert overlap_empty == 0.0


def test_calculate_overall_score(orchestrator):
    """测试整体评分计算"""
    content_analysis = {
        'quality_metrics': {'overall_quality': 0.8},
        'content_structure': {'overall_structure_score': 0.7}
    }
    comment_analysis = {
        'sentiment_distribution': {'positive': 70, 'negative': 20, 'neutral': 10}
    }
    
    score = orchestrator._calculate_overall_score(content_analysis, comment_analysis)
    
    expected_score = round((0.8 + 0.7 + 0.7) / 3, 2)
    assert score == expected_score


@pytest.mark.asyncio
async def test_generate_comprehensive_report(orchestrator):
    """测试综合报告生成"""
    extraction_data = {
        'video_info': {
            'title': 'Test Video',
            'channel_title': 'Test Channel',
            'duration': 300,
            'view_count': 1000,
            'like_count': 100
        },
        'comments': [{'id': '1', 'text': 'Great video!'}]
    }
    
    transcription_data = {
        'language': 'en',
        'duration': 300,
        'full_text': 'This is a test transcript with multiple words.'
    }
    
    content_data = {
        'analysis': {
            'sentiment_analysis': {'overall_sentiment': 'positive'},
            'topic_analysis': {'main_topics': ['AI', 'Technology']},
            'quality_metrics': {'overall_quality': 0.8},
            'content_structure': {'overall_structure_score': 0.7}
        }
    }
    
    comment_data = {
        'analysis': {
            'sentiment_distribution': {'positive': 70, 'negative': 20, 'neutral': 10},
            'key_themes': ['ai', 'tech'],
            'creator_interaction': {'response_rate': 0.05}
        }
    }
    
    options = {}
    
    report = await orchestrator._generate_comprehensive_report(
        extraction_data, transcription_data, content_data, comment_data, options
    )
    
    assert 'summary' in report
    assert 'transcript_analysis' in report
    assert 'content_insights' in report
    assert 'audience_feedback' in report
    assert 'cross_analysis_insights' in report
    assert 'recommendations' in report
    assert 'metadata' in report
    
    assert report['summary']['video_title'] == 'Test Video'
    assert report['summary']['channel'] == 'Test Channel'
    assert report['summary']['comment_count'] == 1
    
    assert report['transcript_analysis']['language'] == 'en'
    assert report['transcript_analysis']['word_count'] == 9

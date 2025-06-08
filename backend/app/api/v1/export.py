from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from typing import Optional
import json
import csv
import io
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.services.task_service import TaskService
from app.models.task import TaskStatus
# from app.models.schemas import AnalysisResult # This schema might not be directly applicable anymore

router = APIRouter()

@router.get("/export/{task_id}/json")
async def export_json(
    task_id: str,
    pretty: bool = Query(False, description="Pretty print JSON"),
    db: AsyncSession = Depends(get_db_session)
):
    """Export analysis result as JSON"""
    try:
        task_service = TaskService(db)
        task = await task_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status != TaskStatus.COMPLETED or not task.result_data:
            raise HTTPException(status_code=400, detail="Analysis not completed or result data is missing")
        
        result = task.result_data # This is already a dict
        json_data = result
        
        if pretty:
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        else:
            json_str = json.dumps(json_data, ensure_ascii=False)
        
        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/{task_id}/csv")
async def export_csv(task_id: str, db: AsyncSession = Depends(get_db_session)):
    """Export analysis result as CSV"""
    try:
        task_service = TaskService(db)
        task = await task_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status != TaskStatus.COMPLETED or not task.result_data:
            raise HTTPException(status_code=400, detail="Analysis not completed or result data is missing")

        result = task.result_data # This is a dict
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Task ID", "Video Title", "Channel", "Duration", "View Count",
            "Quality Score", "Sentiment", "Key Points Count", "Topics Count"
        ])
        
        # Assuming 'summary' key in result_data contains video info and orchestrator summary
        video_info_data = result.get('summary', {})
        # Assuming 'content_insights' key in result_data contains detailed content analysis
        content_insights_data = result.get('content_insights', {})
        
        writer.writerow([
            task_id,
            video_info_data.get('title', ''),
            video_info_data.get('channel_title', ''),
            video_info_data.get('duration', 0),
            video_info_data.get('view_count', 0),
            content_insights_data.get('quality_score', 0),
            content_insights_data.get('sentiment', {}).get('overall', ''),
            len(content_insights_data.get('key_points', [])),
            len(content_insights_data.get('topics', []))
        ])
        
        key_points = content_insights_data.get('key_points', [])
        if key_points:
            writer.writerow([])
            writer.writerow(["Key Points"])
            writer.writerow(["Timestamp", "Content", "Importance"])
            
            for point in key_points:
                writer.writerow([
                    point.get('timestamp', 0),
                    point.get('content', ''),
                    point.get('importance', 0)
                ])
        
        topics = content_insights_data.get('topics', [])
        if topics:
            writer.writerow([])
            writer.writerow(["Topics"])
            writer.writerow(["Topic"])
            
            for topic in topics:
                writer.writerow([topic])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/{task_id}/summary")
async def export_summary(task_id: str, db: AsyncSession = Depends(get_db_session)):
    """Export analysis summary as plain text"""
    try:
        task_service = TaskService(db)
        task = await task_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status != TaskStatus.COMPLETED or not task.result_data:
            raise HTTPException(status_code=400, detail="Analysis not completed or result data is missing")

        result = task.result_data # This is a dict

        video_info_data = result.get('summary', {})
        content_insights_data = result.get('content_insights', {})
        
        # Use a more general summary, potentially from the orchestrator's summary part
        main_summary_text = video_info_data.get('overall_summary',
                                            content_insights_data.get('summary', 'No detailed summary available'))

        summary_lines = [
            f"YouTube Video Analysis Summary",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Task ID: {task_id}",
            "",
            "=== Video Information ===",
            f"Title: {video_info_data.get('title', 'N/A')}",
            f"Channel: {video_info_data.get('channel_title', 'N/A')}",
            f"Duration: {video_info_data.get('duration', 0)} seconds",
            f"View Count: {video_info_data.get('view_count', 0):,}",
            "",
            "=== Content Analysis ===",
            f"Quality Score: {content_insights_data.get('quality_score', 0)}/100",
            f"Overall Sentiment: {content_insights_data.get('sentiment', {}).get('overall', 'N/A')}",
            f"Sentiment Score: {content_insights_data.get('sentiment', {}).get('score', 0):.2f}",
            "",
            "=== Overall Summary ===",
            main_summary_text,
            "",
        ]
        
        key_points = content_insights_data.get('key_points', [])
        if key_points:
            summary_lines.extend([
                "=== Key Points ===",
                ""
            ])
            for i, point in enumerate(key_points[:10], 1):
                timestamp = point.get('timestamp', 0)
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                summary_lines.append(f"{i}. [{minutes:02d}:{seconds:02d}] {point.get('content', '')}")
            summary_lines.append("")
        
        topics = content_insights_data.get('topics', [])
        if topics:
            summary_lines.extend([
                "=== Topics ===",
                ", ".join(topics),
                ""
            ])
        
        summary_text = "\n".join(summary_lines)
        
        return Response(
            content=summary_text,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_summary_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/share/{task_id}")
async def share_result(
    task_id: str,
    platform: str = Query(..., description="Sharing platform (twitter, linkedin, etc.)"),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate shareable content for social media platforms"""
    try:
        task_service = TaskService(db)
        task = await task_service.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status != TaskStatus.COMPLETED or not task.result_data:
            raise HTTPException(status_code=400, detail="Analysis not completed or result data is missing")

        result = task.result_data # This is a dict

        video_info_data = result.get('summary', {})
        content_insights_data = result.get('content_insights', {})
        
        title = video_info_data.get('title', 'YouTube Video')
        quality_score = content_insights_data.get('quality_score', 0)
        sentiment = content_insights_data.get('sentiment', {}).get('overall', 'neutral')
        
        if platform.lower() == 'twitter':
            share_text = f"📊 Analyzed '{title}' - Quality: {quality_score}/100, Sentiment: {sentiment} #YouTubeAnalysis #VideoInsights"
        elif platform.lower() == 'linkedin':
            share_text = f"Just analyzed a YouTube video: '{title}'\n\n📈 Quality Score: {quality_score}/100\n😊 Sentiment: {sentiment}\n\nPowered by AI-driven video analysis."
        else:
            share_text = f"Video Analysis: {title} - Quality: {quality_score}/100, Sentiment: {sentiment}"
        
        return {
            "platform": platform,
            "share_text": share_text,
            "video_title": title,
            "quality_score": quality_score,
            "sentiment": sentiment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Share generation failed: {str(e)}")

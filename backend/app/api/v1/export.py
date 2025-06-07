from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
import json
import csv
import io
from datetime import datetime

from app.models.schemas import AnalysisResult
from app.services.analysis_service import AnalysisService

router = APIRouter()

@router.get("/export/{task_id}/json")
async def export_json(
    task_id: str,
    pretty: bool = Query(False, description="Pretty print JSON")
):
    """Export analysis result as JSON"""
    try:
        analysis_service = AnalysisService()
        result = await analysis_service.get_analysis_result(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        json_data = result.dict() if hasattr(result, 'dict') else result
        
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
async def export_csv(task_id: str):
    """Export analysis result as CSV"""
    try:
        analysis_service = AnalysisService()
        result = await analysis_service.get_analysis_result(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Task ID", "Video Title", "Channel", "Duration", "View Count",
            "Quality Score", "Sentiment", "Key Points Count", "Topics Count"
        ])
        
        video_info = getattr(result, 'video_info', {}) or getattr(result, 'summary', {})
        content_insights = getattr(result, 'content_insights', {})
        
        writer.writerow([
            task_id,
            video_info.get('title', ''),
            video_info.get('channel_title', ''),
            video_info.get('duration', 0),
            video_info.get('view_count', 0),
            content_insights.get('quality_score', 0),
            content_insights.get('sentiment', {}).get('overall', ''),
            len(content_insights.get('key_points', [])),
            len(content_insights.get('topics', []))
        ])
        
        if content_insights.get('key_points'):
            writer.writerow([])
            writer.writerow(["Key Points"])
            writer.writerow(["Timestamp", "Content", "Importance"])
            
            for point in content_insights['key_points']:
                writer.writerow([
                    point.get('timestamp', 0),
                    point.get('content', ''),
                    point.get('importance', 0)
                ])
        
        if content_insights.get('topics'):
            writer.writerow([])
            writer.writerow(["Topics"])
            writer.writerow(["Topic"])
            
            for topic in content_insights['topics']:
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
async def export_summary(task_id: str):
    """Export analysis summary as plain text"""
    try:
        analysis_service = AnalysisService()
        result = await analysis_service.get_analysis_result(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        video_info = getattr(result, 'video_info', {}) or getattr(result, 'summary', {})
        content_insights = getattr(result, 'content_insights', {})
        
        summary_lines = [
            f"YouTube Video Analysis Summary",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Task ID: {task_id}",
            "",
            "=== Video Information ===",
            f"Title: {video_info.get('title', 'N/A')}",
            f"Channel: {video_info.get('channel_title', 'N/A')}",
            f"Duration: {video_info.get('duration', 0)} seconds",
            f"View Count: {video_info.get('view_count', 0):,}",
            "",
            "=== Content Analysis ===",
            f"Quality Score: {content_insights.get('quality_score', 0)}/100",
            f"Overall Sentiment: {content_insights.get('sentiment', {}).get('overall', 'N/A')}",
            f"Sentiment Score: {content_insights.get('sentiment', {}).get('score', 0):.2f}",
            "",
            "=== Summary ===",
            content_insights.get('summary', 'No summary available'),
            "",
        ]
        
        if content_insights.get('key_points'):
            summary_lines.extend([
                "=== Key Points ===",
                ""
            ])
            for i, point in enumerate(content_insights['key_points'][:10], 1):
                timestamp = point.get('timestamp', 0)
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                summary_lines.append(f"{i}. [{minutes:02d}:{seconds:02d}] {point.get('content', '')}")
            summary_lines.append("")
        
        if content_insights.get('topics'):
            summary_lines.extend([
                "=== Topics ===",
                ", ".join(content_insights['topics']),
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
    platform: str = Query(..., description="Sharing platform (twitter, linkedin, etc.)")
):
    """Generate shareable content for social media platforms"""
    try:
        analysis_service = AnalysisService()
        result = await analysis_service.get_analysis_result(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        video_info = getattr(result, 'video_info', {}) or getattr(result, 'summary', {})
        content_insights = getattr(result, 'content_insights', {})
        
        title = video_info.get('title', 'YouTube Video')
        quality_score = content_insights.get('quality_score', 0)
        sentiment = content_insights.get('sentiment', {}).get('overall', 'neutral')
        
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

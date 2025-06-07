import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import openai

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError, ValidationError


class ContentType(str, Enum):
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    REVIEW = "review"
    TUTORIAL = "tutorial"
    DISCUSSION = "discussion"
    OTHER = "other"


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class KeyPoint:
    text: str
    importance: float
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    category: Optional[str] = None


@dataclass
class TopicAnalysis:
    main_topic: str
    sub_topics: List[str]
    keywords: List[str]
    content_type: ContentType
    confidence: float


@dataclass
class SentimentAnalysis:
    overall_sentiment: SentimentType
    sentiment_score: float
    emotional_tone: List[str]
    sentiment_progression: List[Dict[str, Any]]


@dataclass
class ContentStructure:
    introduction_end: Optional[float]
    main_content_segments: List[Dict[str, Any]]
    conclusion_start: Optional[float]
    call_to_action: Optional[str]


@dataclass
class ContentInsights:
    key_points: List[KeyPoint]
    topic_analysis: TopicAnalysis
    sentiment_analysis: SentimentAnalysis
    content_structure: ContentStructure
    summary: str
    recommendations: List[str]
    quality_score: float


class BaseContentAnalyzer(ABC):
    """Base class for content analyzers"""

    @abstractmethod
    async def analyze(
        self, transcript_data: Dict[str, Any], video_info: Dict[str, Any]
    ) -> ContentInsights:
        pass


class LLMContentAnalyzer(BaseContentAnalyzer):
    """LLM-based content analyzer using OpenAI"""

    def __init__(self):
        if not settings.openai_api_key:
            raise ValidationError("OpenAI API key is required for content analysis")

        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = getattr(settings, "openai_model", "gpt-4")
        self.max_retries = 3
        self.retry_delay = 1

    async def analyze(
        self, transcript_data: Dict[str, Any], video_info: Dict[str, Any]
    ) -> ContentInsights:
        """Execute comprehensive content analysis"""
        try:
            full_text = transcript_data.get("full_text", "")
            segments = transcript_data.get("segments", [])

            if not full_text:
                raise ValidationError("Transcript text is empty")

            logging.info(
                f"Starting content analysis for video: {video_info.get('title', 'Unknown')}"
            )

            try:
                (
                    key_points,
                    topic_analysis,
                    sentiment_analysis,
                    content_structure,
                    summary,
                    recommendations,
                ) = await asyncio.gather(
                    self._extract_key_points(full_text, segments),
                    self._analyze_topics(full_text, video_info),
                    self._analyze_sentiment(full_text, segments),
                    self._analyze_structure(full_text, segments),
                    self._generate_summary(full_text, video_info),
                    self._generate_recommendations(full_text, video_info),
                )
            except Exception as e:
                logging.error(f"Parallel analysis tasks failed: {e}")
                raise ExternalServiceError(f"Content analysis failed: {e}")

            quality_score = self._calculate_quality_score(
                key_points, topic_analysis, sentiment_analysis, len(full_text.split())
            )

            insights = ContentInsights(
                key_points=key_points,
                topic_analysis=topic_analysis,
                sentiment_analysis=sentiment_analysis,
                content_structure=content_structure,
                summary=summary,
                recommendations=recommendations,
                quality_score=quality_score,
            )

            logging.info("Content analysis completed successfully")
            return insights

        except Exception as e:
            logging.error(f"Content analysis failed: {e}")
            raise ExternalServiceError(f"Content analysis failed: {e}")

    async def _extract_key_points(
        self, text: str, segments: List[Dict]
    ) -> List[KeyPoint]:
        """Extract key points from the content"""
        prompt = f"""
        Analyze the following video transcript and extract the most important key points.
        For each key point, provide:
        1. The main text/idea
        2. Importance score (0.0 to 1.0)
        3. Category if applicable
        
        Transcript: {text[:4000]}
        
        Return a JSON array with this structure:
        {{
            "key_points": [
                {{
                    "text": "Key point description",
                    "importance": 0.8,
                    "category": "main_concept"
                }}
            ]
        }}
        """

        try:
            response = await self._make_api_call(prompt, max_tokens=1000)
            result = json.loads(response)

            key_points = []
            for kp_data in result.get("key_points", []):
                start_time, end_time = self._find_timestamp_for_text(
                    kp_data["text"], segments
                )

                key_point = KeyPoint(
                    text=kp_data["text"],
                    importance=float(kp_data["importance"]),
                    timestamp_start=start_time,
                    timestamp_end=end_time,
                    category=kp_data.get("category"),
                )
                key_points.append(key_point)

            return key_points

        except Exception as e:
            logging.error(f"Key points extraction failed: {e}")
            return []

    async def _analyze_topics(
        self, text: str, video_info: Dict[str, Any]
    ) -> TopicAnalysis:
        """Analyze topics and content classification"""
        title = video_info.get("title", "")
        description = video_info.get("description", "")[:500]

        prompt = f"""
        Analyze the following video content and classify it:
        
        Title: {title}
        Description: {description}
        Transcript: {text[:3000]}
        
        Provide analysis in this JSON format:
        {{
            "main_topic": "Primary topic of the video",
            "sub_topics": ["subtopic1", "subtopic2", "subtopic3"],
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "content_type": "educational|entertainment|news|review|tutorial|discussion|other",
            "confidence": 0.85
        }}
        """

        try:
            response = await self._make_api_call(prompt, max_tokens=800)
            result = json.loads(response)

            return TopicAnalysis(
                main_topic=result.get("main_topic", "Unknown"),
                sub_topics=result.get("sub_topics", []),
                keywords=result.get("keywords", []),
                content_type=ContentType(result.get("content_type", "other")),
                confidence=float(result.get("confidence", 0.5)),
            )

        except Exception as e:
            logging.error(f"Topic analysis failed: {e}")
            return TopicAnalysis(
                main_topic="Unknown",
                sub_topics=[],
                keywords=[],
                content_type=ContentType.OTHER,
                confidence=0.0,
            )

    async def _analyze_sentiment(
        self, text: str, segments: List[Dict]
    ) -> SentimentAnalysis:
        """Analyze sentiment and emotional tone"""
        prompt = f"""
        Analyze the sentiment and emotional tone of this video transcript:
        
        Transcript: {text[:3000]}
        
        Provide analysis in this JSON format:
        {{
            "overall_sentiment": "positive|negative|neutral|mixed",
            "sentiment_score": 0.2,
            "emotional_tone": ["enthusiastic", "informative", "calm"],
            "sentiment_progression": [
                {{"timestamp": 0, "sentiment": "neutral", "score": 0.0}},
                {{"timestamp": 60, "sentiment": "positive", "score": 0.3}}
            ]
        }}
        
        Sentiment score should be between -1.0 (very negative) and 1.0 (very positive).
        """

        try:
            response = await self._make_api_call(prompt, max_tokens=800)
            result = json.loads(response)

            return SentimentAnalysis(
                overall_sentiment=SentimentType(
                    result.get("overall_sentiment", "neutral")
                ),
                sentiment_score=float(result.get("sentiment_score", 0.0)),
                emotional_tone=result.get("emotional_tone", []),
                sentiment_progression=result.get("sentiment_progression", []),
            )

        except Exception as e:
            logging.error(f"Sentiment analysis failed: {e}")
            return SentimentAnalysis(
                overall_sentiment=SentimentType.NEUTRAL,
                sentiment_score=0.0,
                emotional_tone=[],
                sentiment_progression=[],
            )

    async def _analyze_structure(
        self, text: str, segments: List[Dict]
    ) -> ContentStructure:
        """Analyze content structure and organization"""
        prompt = f"""
        Analyze the structure of this video transcript:
        
        Transcript: {text[:3000]}
        
        Identify key structural elements in this JSON format:
        {{
            "introduction_end": 45.0,
            "main_content_segments": [
                {{"start": 45.0, "end": 180.0, "topic": "Main concept explanation"}},
                {{"start": 180.0, "end": 300.0, "topic": "Examples and demonstrations"}}
            ],
            "conclusion_start": 300.0,
            "call_to_action": "Subscribe for more content"
        }}
        
        Times should be in seconds. Use null if sections are not clearly identifiable.
        """

        try:
            response = await self._make_api_call(prompt, max_tokens=600)
            result = json.loads(response)

            return ContentStructure(
                introduction_end=result.get("introduction_end"),
                main_content_segments=result.get("main_content_segments", []),
                conclusion_start=result.get("conclusion_start"),
                call_to_action=result.get("call_to_action"),
            )

        except Exception as e:
            logging.error(f"Structure analysis failed: {e}")
            return ContentStructure(
                introduction_end=None,
                main_content_segments=[],
                conclusion_start=None,
                call_to_action=None,
            )

    async def _generate_summary(self, text: str, video_info: Dict[str, Any]) -> str:
        """Generate a concise summary of the content"""
        title = video_info.get("title", "")

        prompt = f"""
        Create a concise, informative summary of this video content:
        
        Title: {title}
        Transcript: {text[:3000]}
        
        Provide a 2-3 sentence summary that captures the main points and value of the content.
        Return only the summary text, no JSON formatting.
        """

        try:
            summary = await self._make_api_call(prompt, max_tokens=200)
            return summary.strip()

        except Exception as e:
            logging.error(f"Summary generation failed: {e}")
            return "Summary generation failed"

    async def _generate_recommendations(
        self, text: str, video_info: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        prompt = f"""
        Based on this video content, provide 3-5 actionable recommendations for viewers:
        
        Title: {video_info.get('title', '')}
        Transcript: {text[:2000]}
        
        Return recommendations in this JSON format:
        {{
            "recommendations": [
                "Specific actionable recommendation 1",
                "Specific actionable recommendation 2"
            ]
        }}
        """

        try:
            response = await self._make_api_call(prompt, max_tokens=400)
            result = json.loads(response)
            return result.get("recommendations", [])

        except Exception as e:
            logging.error(f"Recommendations generation failed: {e}")
            return []

    async def _make_api_call(
        self, prompt: str, max_tokens: int = 500, temperature: float = 0.3
    ) -> str:
        """Make API call to OpenAI with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                content = response.choices[0].message.content
                if content is None:
                    raise ExternalServiceError("OpenAI API returned empty response")
                return content

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ExternalServiceError(
                        f"OpenAI API call failed after {self.max_retries} attempts: {e}"
                    )

                logging.warning(f"OpenAI API call attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.retry_delay * (2**attempt))

        raise ExternalServiceError("OpenAI API call failed - should not reach here")

    def _find_timestamp_for_text(self, text: str, segments: List[Dict]) -> tuple:
        """Find timestamp range for given text in segments"""
        text_lower = text.lower()
        for segment in segments:
            segment_text = segment.get("text", "").lower()
            if any(word in segment_text for word in text_lower.split()[:3]):
                return segment.get("start"), segment.get("end")
        return None, None

    def _calculate_quality_score(
        self,
        key_points: List[KeyPoint],
        topic_analysis: TopicAnalysis,
        sentiment_analysis: SentimentAnalysis,
        word_count: int,
    ) -> float:
        """Calculate content quality score"""
        score = 0.0

        if key_points:
            avg_importance = sum(kp.importance for kp in key_points) / len(key_points)
            score += avg_importance * 0.3

        score += topic_analysis.confidence * 0.2

        if 500 <= word_count <= 3000:
            score += 0.2
        elif word_count > 100:
            score += 0.1

        if abs(sentiment_analysis.sentiment_score) > 0.1:
            score += 0.15

        score += 0.15

        return min(score, 1.0)


content_analyzer = LLMContentAnalyzer()

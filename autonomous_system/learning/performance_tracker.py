"""
Performance Tracking and Learning System

This module provides comprehensive performance tracking and learning capabilities:
- Success rate monitoring and analysis
- Cost tracking and optimization
- Quality metrics and improvement tracking
- Pattern recognition and learning
- Performance prediction and optimization
- Automated improvement recommendations
"""

import asyncio
import json
import logging
import sqlite3
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of performance metrics"""
    SUCCESS_RATE = "success_rate"
    EXECUTION_TIME = "execution_time"
    COST = "cost"
    QUALITY_SCORE = "quality_score"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    USER_SATISFACTION = "user_satisfaction"

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_id: str
    metric_type: MetricType
    value: float
    task_category: str
    model_used: str
    agent_used: str
    timestamp: datetime
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceAnalysis:
    """Analysis of performance metrics"""
    metric_type: MetricType
    task_category: str
    current_value: float
    historical_average: float
    trend: str  # improving, declining, stable
    confidence: float
    recommendations: list[str]
    insights: list[str]
    timestamp: datetime

@dataclass
class LearningInsight:
    """Insight derived from performance analysis"""
    insight_id: str
    insight_type: str
    description: str
    confidence: float
    supporting_data: dict[str, Any]
    recommendations: list[str]
    impact_score: float
    timestamp: datetime

class PerformanceTracker:
    """Comprehensive performance tracking and learning system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get("database", {}).get("path", "performance_tracker.db"))
        self._init_database()

        # Performance tracking
        self.metrics_buffer = []
        self.analysis_cache = {}
        self.insights_history = []

        # Learning parameters
        self.learning_rate = config.get("learning_rate", 0.1)
        self.min_data_points = config.get("min_data_points", 10)
        self.analysis_interval = config.get("analysis_interval", 300)  # 5 minutes

        # Start background learning
        self._start_background_learning()

    def _init_database(self):
        """Initialize performance tracking database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id TEXT PRIMARY KEY,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    task_category TEXT NOT NULL,
                    model_used TEXT,
                    agent_used TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context TEXT,
                    metadata TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    task_category TEXT NOT NULL,
                    current_value REAL,
                    historical_average REAL,
                    trend TEXT,
                    confidence REAL,
                    recommendations TEXT,
                    insights TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    insight_id TEXT PRIMARY KEY,
                    insight_type TEXT NOT NULL,
                    description TEXT,
                    confidence REAL,
                    supporting_data TEXT,
                    recommendations TEXT,
                    impact_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT,
                    confidence REAL,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    frequency INTEGER DEFAULT 1
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Performance tracker database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize performance tracker database: {e}")
            raise

    def _start_background_learning(self):
        """Start background learning processes"""
        asyncio.create_task(self._continuous_analysis())
        asyncio.create_task(self._pattern_recognition())
        asyncio.create_task(self._insight_generation())
        asyncio.create_task(self._performance_optimization())

    async def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        try:
            # Add to buffer
            self.metrics_buffer.append(metric)

            # Store in database
            await self._store_metric(metric)

            # Trigger analysis if buffer is full
            if len(self.metrics_buffer) >= self.min_data_points:
                await self._analyze_metrics()

            logger.debug(f"Recorded metric: {metric.metric_type.value} = {metric.value}")

        except Exception as e:
            logger.error(f"Failed to record metric: {e}")

    async def _store_metric(self, metric: PerformanceMetric):
        """Store metric in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO performance_metrics
                (metric_id, metric_type, value, task_category, model_used, agent_used, timestamp, context, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.metric_id,
                metric.metric_type.value,
                metric.value,
                metric.task_category,
                metric.model_used,
                metric.agent_used,
                metric.timestamp,
                json.dumps(metric.context),
                json.dumps(metric.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store metric: {e}")

    async def _analyze_metrics(self):
        """Analyze collected metrics for insights"""
        try:
            if not self.metrics_buffer:
                return

            # Group metrics by type and category
            metrics_by_group = defaultdict(list)
            for metric in self.metrics_buffer:
                key = (metric.metric_type, metric.task_category)
                metrics_by_group[key].append(metric)

            # Analyze each group
            for (metric_type, task_category), metrics in metrics_by_group.items():
                if len(metrics) >= self.min_data_points:
                    analysis = await self._analyze_metric_group(metric_type, task_category, metrics)
                    if analysis:
                        await self._store_analysis(analysis)
                        await self._generate_insights(analysis)

            # Clear buffer after analysis
            self.metrics_buffer.clear()

        except Exception as e:
            logger.error(f"Metrics analysis failed: {e}")

    async def _analyze_metric_group(self, metric_type: MetricType, task_category: str,
                                  metrics: list[PerformanceMetric]) -> PerformanceAnalysis | None:
        """Analyze a group of metrics for a specific type and category"""
        try:
            values = [m.value for m in metrics]
            current_value = values[-1] if values else 0.0
            historical_average = statistics.mean(values) if values else 0.0

            # Calculate trend
            if len(values) >= 3:
                recent_values = values[-3:]
                trend = self._calculate_trend(recent_values)
            else:
                trend = "stable"

            # Calculate confidence
            confidence = self._calculate_confidence(values)

            # Generate recommendations
            recommendations = self._generate_recommendations(metric_type, current_value, historical_average, trend)

            # Generate insights
            insights = self._generate_insights_for_analysis(metric_type, current_value, historical_average, trend)

            return PerformanceAnalysis(
                metric_type=metric_type,
                task_category=task_category,
                current_value=current_value,
                historical_average=historical_average,
                trend=trend,
                confidence=confidence,
                recommendations=recommendations,
                insights=insights,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to analyze metric group: {e}")
            return None

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend from a list of values"""
        if len(values) < 2:
            return "stable"

        # Simple linear regression
        x = np.arange(len(values))
        y = np.array(values)

        try:
            slope = np.polyfit(x, y, 1)[0]

            if slope > 0.05:  # Threshold for improvement
                return "improving"
            elif slope < -0.05:  # Threshold for decline
                return "declining"
            else:
                return "stable"
        except:
            return "stable"

    def _calculate_confidence(self, values: list[float]) -> float:
        """Calculate confidence in the analysis"""
        if len(values) < 2:
            return 0.0

        # Confidence based on sample size and variance
        sample_size_factor = min(1.0, len(values) / 50.0)  # Max confidence at 50+ samples

        try:
            variance = statistics.variance(values)
            mean = statistics.mean(values)
            if mean == 0:
                variance_factor = 1.0
            else:
                coefficient_of_variation = variance / (mean ** 2)
                variance_factor = max(0.0, 1.0 - coefficient_of_variation)
        except:
            variance_factor = 0.5

        confidence = (sample_size_factor + variance_factor) / 2
        return min(1.0, max(0.0, confidence))

    def _generate_recommendations(self, metric_type: MetricType, current_value: float,
                                historical_average: float, trend: str) -> list[str]:
        """Generate recommendations based on metric analysis"""
        recommendations = []

        if metric_type == MetricType.SUCCESS_RATE:
            if current_value < 0.8:
                recommendations.append("Investigate recent failures and implement preventive measures")
            if trend == "declining":
                recommendations.append("Review recent changes that may have caused performance degradation")

        elif metric_type == MetricType.EXECUTION_TIME:
            if current_value > historical_average * 1.2:
                recommendations.append("Optimize workflow steps or allocate more resources")
            if trend == "improving":
                recommendations.append("Current optimizations are effective, consider applying to similar tasks")

        elif metric_type == MetricType.COST:
            if current_value > historical_average * 1.1:
                recommendations.append("Review model selection strategy for cost optimization")
            if trend == "declining":
                recommendations.append("Cost optimization measures are working well")

        elif metric_type == MetricType.QUALITY_SCORE:
            if current_value < 0.7:
                recommendations.append("Improve validation criteria or enhance model selection")
            if trend == "improving":
                recommendations.append("Quality improvements are effective, maintain current approach")

        # General recommendations
        if trend == "declining":
            recommendations.append("Monitor closely and implement corrective actions")
        elif trend == "improving":
            recommendations.append("Continue current optimization strategies")

        return recommendations

    def _generate_insights_for_analysis(self, metric_type: MetricType, current_value: float,
                                      historical_average: float, trend: str) -> list[str]:
        """Generate insights for performance analysis"""
        insights = []

        # Performance comparison insights
        if current_value > historical_average * 1.1:
            insights.append(f"Current {metric_type.value} is above historical average")
        elif current_value < historical_average * 0.9:
            insights.append(f"Current {metric_type.value} is below historical average")

        # Trend insights
        if trend == "improving":
            insights.append(f"{metric_type.value} is showing positive trend")
        elif trend == "declining":
            insights.append(f"{metric_type.value} is showing negative trend")
        elif trend == "stable":
            insights.append(f"{metric_type.value} is stable")

        # Threshold insights
        if metric_type == MetricType.SUCCESS_RATE and current_value < 0.8:
            insights.append("Success rate below acceptable threshold")
        elif metric_type == MetricType.COST and current_value > 1.0:
            insights.append("Cost per task above budget threshold")
        elif metric_type == MetricType.QUALITY_SCORE and current_value < 0.7:
            insights.append("Quality score below acceptable threshold")

        return insights

    async def _store_analysis(self, analysis: PerformanceAnalysis):
        """Store performance analysis in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO performance_analysis
                (metric_type, task_category, current_value, historical_average, trend,
                 confidence, recommendations, insights, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.metric_type.value,
                analysis.task_category,
                analysis.current_value,
                analysis.historical_average,
                analysis.trend,
                analysis.confidence,
                json.dumps(analysis.recommendations),
                json.dumps(analysis.insights),
                analysis.timestamp
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")

    async def _generate_insights(self, analysis: PerformanceAnalysis):
        """Generate learning insights from performance analysis"""
        try:
            # Create insight based on analysis
            insight = await self._create_insight_from_analysis(analysis)
            if insight:
                self.insights_history.append(insight)
                await self._store_insight(insight)

                # Check if insight should trigger action
                if insight.impact_score > 0.7:
                    await self._trigger_optimization_action(insight)

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")

    async def _create_insight_from_analysis(self, analysis: PerformanceAnalysis) -> LearningInsight | None:
        """Create a learning insight from performance analysis"""
        try:
            insight_id = f"insight_{int(datetime.now().timestamp())}_{analysis.metric_type.value}"

            # Determine insight type
            if analysis.trend == "declining":
                insight_type = "performance_degradation"
                description = f"Performance degradation detected in {analysis.metric_type.value} for {analysis.task_category}"
                impact_score = 0.8
            elif analysis.trend == "improving":
                insight_type = "performance_improvement"
                description = f"Performance improvement detected in {analysis.metric_type.value} for {analysis.task_category}"
                impact_score = 0.6
            else:
                insight_type = "performance_stable"
                description = f"Performance stable in {analysis.metric_type.value} for {analysis.task_category}"
                impact_score = 0.3

            # Generate recommendations
            recommendations = analysis.recommendations.copy()

            # Add specific recommendations based on insight type
            if insight_type == "performance_degradation":
                recommendations.append("Implement immediate corrective actions")
                recommendations.append("Review recent system changes")
            elif insight_type == "performance_improvement":
                recommendations.append("Document successful optimization strategies")
                recommendations.append("Apply similar optimizations to other areas")

            insight = LearningInsight(
                insight_id=insight_id,
                insight_type=insight_type,
                description=description,
                confidence=analysis.confidence,
                supporting_data={
                    'metric_type': analysis.metric_type.value,
                    'task_category': analysis.task_category,
                    'current_value': analysis.current_value,
                    'historical_average': analysis.historical_average,
                    'trend': analysis.trend
                },
                recommendations=recommendations,
                impact_score=impact_score,
                timestamp=datetime.now()
            )

            return insight

        except Exception as e:
            logger.error(f"Failed to create insight: {e}")
            return None

    async def _store_insight(self, insight: LearningInsight):
        """Store learning insight in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO learning_insights
                (insight_id, insight_type, description, confidence, supporting_data,
                 recommendations, impact_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                insight.insight_id,
                insight.insight_type,
                insight.description,
                insight.confidence,
                json.dumps(insight.supporting_data),
                json.dumps(insight.recommendations),
                insight.impact_score,
                insight.timestamp
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store insight: {e}")

    async def _trigger_optimization_action(self, insight: LearningInsight):
        """Trigger optimization action based on high-impact insight"""
        try:
            logger.info(f"Triggering optimization action for insight: {insight.insight_id}")

            # This would integrate with the decision engine
            # For now, just log the action
            if insight.insight_type == "performance_degradation":
                logger.warning(f"High-impact performance degradation detected: {insight.description}")
                # Would trigger system optimization decision
            elif insight.insight_type == "performance_improvement":
                logger.info(f"High-impact performance improvement detected: {insight.description}")
                # Would document successful strategies

        except Exception as e:
            logger.error(f"Failed to trigger optimization action: {e}")

    # Background learning processes
    async def _continuous_analysis(self):
        """Continuous performance analysis"""
        while True:
            try:
                # Analyze any buffered metrics
                if self.metrics_buffer:
                    await self._analyze_metrics()

                # Perform periodic analysis
                await self._perform_periodic_analysis()

                await asyncio.sleep(self.analysis_interval)

            except Exception as e:
                logger.error(f"Continuous analysis failed: {e}")
                await asyncio.sleep(60)

    async def _perform_periodic_analysis(self):
        """Perform periodic analysis of stored metrics"""
        try:
            # Get recent metrics from database
            recent_metrics = await self._get_recent_metrics(hours=24)

            # Group by metric type and category
            metrics_by_group = defaultdict(list)
            for metric in recent_metrics:
                key = (metric.metric_type, metric.task_category)
                metrics_by_group[key].append(metric)

            # Analyze each group
            for (metric_type, task_category), metrics in metrics_by_group.items():
                if len(metrics) >= self.min_data_points:
                    analysis = await self._analyze_metric_group(metric_type, task_category, metrics)
                    if analysis:
                        await self._store_analysis(analysis)
                        await self._generate_insights(analysis)

        except Exception as e:
            logger.error(f"Periodic analysis failed: {e}")

    async def _pattern_recognition(self):
        """Recognize patterns in performance data"""
        while True:
            try:
                # Analyze patterns in recent data
                await self._identify_performance_patterns()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Pattern recognition failed: {e}")
                await asyncio.sleep(1800)

    async def _identify_performance_patterns(self):
        """Identify patterns in performance data"""
        try:
            # Get recent metrics
            recent_metrics = await self._get_recent_metrics(hours=48)

            # Look for patterns
            patterns = self._find_performance_patterns(recent_metrics)

            # Store identified patterns
            for pattern in patterns:
                await self._store_performance_pattern(pattern)

        except Exception as e:
            logger.error(f"Pattern identification failed: {e}")

    def _find_performance_patterns(self, metrics: list[PerformanceMetric]) -> list[dict[str, Any]]:
        """Find patterns in performance metrics"""
        patterns = []

        # Group metrics by various dimensions
        by_time = defaultdict(list)
        by_category = defaultdict(list)
        by_model = defaultdict(list)

        for metric in metrics:
            hour = metric.timestamp.hour
            by_time[hour].append(metric)
            by_category[metric.task_category].append(metric)
            by_model[metric.model_used].append(metric)

        # Time-based patterns
        for hour, hour_metrics in by_time.items():
            if len(hour_metrics) >= 5:
                avg_success = statistics.mean([m.value for m in hour_metrics if m.metric_type == MetricType.SUCCESS_RATE])
                if avg_success < 0.7:
                    patterns.append({
                        'pattern_type': 'time_based_degradation',
                        'pattern_data': {'hour': hour, 'avg_success': avg_success},
                        'confidence': 0.7,
                        'description': f'Performance degradation detected at {hour}:00'
                    })

        # Category-based patterns
        for category, cat_metrics in by_category.items():
            if len(cat_metrics) >= 10:
                success_metrics = [m for m in cat_metrics if m.metric_type == MetricType.SUCCESS_RATE]
                if success_metrics:
                    avg_success = statistics.mean([m.value for m in success_metrics])
                    if avg_success < 0.6:
                        patterns.append({
                            'pattern_type': 'category_performance_issue',
                            'pattern_data': {'category': category, 'avg_success': avg_success},
                            'confidence': 0.8,
                            'description': f'Performance issues detected in {category} tasks'
                        })

        return patterns

    async def _store_performance_pattern(self, pattern: dict[str, Any]):
        """Store performance pattern in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            pattern_id = f"pattern_{int(datetime.now().timestamp())}_{pattern['pattern_type']}"

            cursor.execute("""
                INSERT OR REPLACE INTO performance_patterns
                (pattern_id, pattern_type, pattern_data, confidence, first_seen, last_seen, frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_id,
                pattern['pattern_type'],
                json.dumps(pattern['pattern_data']),
                pattern['confidence'],
                datetime.now(),
                datetime.now(),
                1
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store performance pattern: {e}")

    async def _insight_generation(self):
        """Generate insights from patterns and analysis"""
        while True:
            try:
                # Generate insights from recent patterns
                await self._generate_pattern_insights()

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Insight generation failed: {e}")
                await asyncio.sleep(3600)

    async def _generate_pattern_insights(self):
        """Generate insights from performance patterns"""
        try:
            # Get recent patterns
            recent_patterns = await self._get_recent_patterns(hours=24)

            for pattern in recent_patterns:
                insight = await self._create_insight_from_pattern(pattern)
                if insight:
                    self.insights_history.append(insight)
                    await self._store_insight(insight)

        except Exception as e:
            logger.error(f"Pattern insight generation failed: {e}")

    async def _create_insight_from_pattern(self, pattern: dict[str, Any]) -> LearningInsight | None:
        """Create insight from performance pattern"""
        try:
            insight_id = f"pattern_insight_{int(datetime.now().timestamp())}"

            insight = LearningInsight(
                insight_id=insight_id,
                insight_type=f"pattern_{pattern['pattern_type']}",
                description=pattern.get('description', f"Pattern detected: {pattern['pattern_type']}"),
                confidence=pattern.get('confidence', 0.5),
                supporting_data=pattern.get('pattern_data', {}),
                recommendations=self._generate_pattern_recommendations(pattern),
                impact_score=pattern.get('confidence', 0.5),
                timestamp=datetime.now()
            )

            return insight

        except Exception as e:
            logger.error(f"Failed to create pattern insight: {e}")
            return None

    def _generate_pattern_recommendations(self, pattern: dict[str, Any]) -> list[str]:
        """Generate recommendations based on pattern"""
        recommendations = []

        if pattern['pattern_type'] == 'time_based_degradation':
            recommendations.append("Investigate system load during affected hours")
            recommendations.append("Consider resource scaling during peak hours")
        elif pattern['pattern_type'] == 'category_performance_issue':
            recommendations.append("Review task processing for affected category")
            recommendations.append("Consider model or agent reassignment")

        return recommendations

    async def _performance_optimization(self):
        """Continuous performance optimization"""
        while True:
            try:
                # Check for optimization opportunities
                await self._identify_optimization_opportunities()

                await asyncio.sleep(7200)  # Check every 2 hours

            except Exception as e:
                logger.error(f"Performance optimization failed: {e}")
                await asyncio.sleep(7200)

    async def _identify_optimization_opportunities(self):
        """Identify opportunities for performance optimization"""
        try:
            # Get recent insights
            recent_insights = await self._get_recent_insights(hours=6)

            # Look for high-impact insights
            high_impact_insights = [i for i in recent_insights if i.impact_score > 0.7]

            if high_impact_insights:
                logger.info(f"Found {len(high_impact_insights)} high-impact optimization opportunities")

                # This would trigger optimization actions
                for insight in high_impact_insights:
                    await self._trigger_optimization_action(insight)

        except Exception as e:
            logger.error(f"Optimization opportunity identification failed: {e}")

    # Utility methods
    async def _get_recent_metrics(self, hours: int) -> list[PerformanceMetric]:
        """Get recent metrics from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(hours=hours)

            cursor.execute("""
                SELECT * FROM performance_metrics
                WHERE timestamp > ? ORDER BY timestamp DESC
            """, (cutoff_time,))

            rows = cursor.fetchall()
            metrics = []

            for row in rows:
                metric = PerformanceMetric(
                    metric_id=row[0],
                    metric_type=MetricType(row[1]),
                    value=row[2],
                    task_category=row[3],
                    model_used=row[4],
                    agent_used=row[5],
                    timestamp=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                    context=json.loads(row[7]) if row[7] else {},
                    metadata=json.loads(row[8]) if row[8] else {}
                )
                metrics.append(metric)

            conn.close()
            return metrics

        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return []

    async def _get_recent_patterns(self, hours: int) -> list[dict[str, Any]]:
        """Get recent performance patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(hours=hours)

            cursor.execute("""
                SELECT * FROM performance_patterns
                WHERE last_seen > ? ORDER BY last_seen DESC
            """, (cutoff_time,))

            rows = cursor.fetchall()
            patterns = []

            for row in rows:
                pattern = {
                    'pattern_id': row[0],
                    'pattern_type': row[1],
                    'pattern_data': json.loads(row[2]) if row[2] else {},
                    'confidence': row[3],
                    'first_seen': row[4],
                    'last_seen': row[5],
                    'frequency': row[6]
                }
                patterns.append(pattern)

            conn.close()
            return patterns

        except Exception as e:
            logger.error(f"Failed to get recent patterns: {e}")
            return []

    async def _get_recent_insights(self, hours: int) -> list[LearningInsight]:
        """Get recent learning insights"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(hours=hours)

            cursor.execute("""
                SELECT * FROM learning_insights
                WHERE timestamp > ? ORDER BY timestamp DESC
            """, (cutoff_time,))

            rows = cursor.fetchall()
            insights = []

            for row in rows:
                insight = LearningInsight(
                    insight_id=row[0],
                    insight_type=row[1],
                    description=row[2],
                    confidence=row[3],
                    supporting_data=json.loads(row[4]) if row[4] else {},
                    recommendations=json.loads(row[5]) if row[5] else [],
                    impact_score=row[6],
                    timestamp=datetime.fromisoformat(row[7]) if row[7] else datetime.now()
                )
                insights.append(insight)

            conn.close()
            return insights

        except Exception as e:
            logger.error(f"Failed to get recent insights: {e}")
            return []

    # Public API methods
    async def get_performance_summary(self, task_category: str | None = None,
                                    hours: int = 24) -> dict[str, Any]:
        """Get performance summary for specified period"""
        try:
            metrics = await self._get_recent_metrics(hours)

            if task_category:
                metrics = [m for m in metrics if m.task_category == task_category]

            if not metrics:
                return {"error": "No metrics found for specified criteria"}

            # Calculate summary statistics
            summary = {
                'total_metrics': len(metrics),
                'time_period_hours': hours,
                'task_category': task_category or 'all',
                'metrics_by_type': {},
                'overall_trends': {}
            }

            # Group by metric type
            by_type = defaultdict(list)
            for metric in metrics:
                by_type[metric.metric_type.value].append(metric.value)

            # Calculate statistics for each metric type
            for metric_type, values in by_type.items():
                if values:
                    summary['metrics_by_type'][metric_type] = {
                        'count': len(values),
                        'average': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'trend': self._calculate_trend(values)
                    }

            return summary

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}

    async def get_optimization_recommendations(self) -> list[dict[str, Any]]:
        """Get current optimization recommendations"""
        try:
            # Get recent insights
            recent_insights = await self._get_recent_insights(hours=24)

            # Filter high-impact insights
            high_impact = [i for i in recent_insights if i.impact_score > 0.6]

            recommendations = []
            for insight in high_impact:
                recommendations.append({
                    'insight_id': insight.insight_id,
                    'description': insight.description,
                    'confidence': insight.confidence,
                    'impact_score': insight.impact_score,
                    'recommendations': insight.recommendations,
                    'timestamp': insight.timestamp.isoformat()
                })

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get optimization recommendations: {e}")
            return []

    def get_learning_metrics(self) -> dict[str, Any]:
        """Get learning system metrics"""
        return {
            'total_insights': len(self.insights_history),
            'recent_insights': len([i for i in self.insights_history
                                  if (datetime.now() - i.timestamp).total_seconds() < 3600]),
            'learning_rate': self.learning_rate,
            'min_data_points': self.min_data_points,
            'analysis_interval': self.analysis_interval
        }


# Example usage
async def main():
    """Example usage of the performance tracker"""
    config = {
        "database": {"path": "test_performance_tracker.db"},
        "learning_rate": 0.1,
        "min_data_points": 5,
        "analysis_interval": 60
    }

    tracker = PerformanceTracker(config)

    # Record some metrics
    for i in range(10):
        metric = PerformanceMetric(
            metric_id=f"metric_{i}",
            metric_type=MetricType.SUCCESS_RATE,
            value=0.8 + (i * 0.02),  # Improving trend
            task_category="research",
            model_used="gpt-4",
            agent_used="research_agent",
            timestamp=datetime.now() - timedelta(minutes=i*10),
            context={"source": "email", "priority": "high"},
            metadata={"user_feedback": "positive"}
        )

        await tracker.record_metric(metric)

    # Wait for analysis
    await asyncio.sleep(2)

    # Get performance summary
    summary = await tracker.get_performance_summary(task_category="research", hours=1)
    print("Performance Summary:", json.dumps(summary, indent=2, default=str))

    # Get optimization recommendations
    recommendations = await tracker.get_optimization_recommendations()
    print("Optimization Recommendations:", json.dumps(recommendations, indent=2, default=str))

    # Get learning metrics
    learning_metrics = tracker.get_learning_metrics()
    print("Learning Metrics:", json.dumps(learning_metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

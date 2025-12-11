"""
AI Monitoring & Observability Service

Comprehensive monitoring for AI operations:
- Request/response logging
- Performance metrics tracking
- Cost monitoring and alerts
- Quality metrics
- A/B testing framework
- Error tracking

EPIC-009: US-009.7 AI Monitoring & Observability
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import logging
import hashlib
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class AIRequestType(str, Enum):
    """Types of AI requests."""
    CHAT_COMPLETION = "chat_completion"
    STREAMING = "streaming"
    EMBEDDING = "embedding"
    NER = "ner"
    CLASSIFICATION = "classification"
    TRIAGE = "triage"
    DOCUMENTATION = "documentation"
    SEMANTIC_SEARCH = "semantic_search"
    FUNCTION_CALL = "function_call"


class AIProvider(str, Enum):
    """AI service providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"


class QualityRating(str, Enum):
    """Quality rating for AI responses."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class AIRequestLog:
    """Log entry for an AI request."""
    request_id: str
    tenant_id: str
    timestamp: datetime

    # Request details
    request_type: AIRequestType
    provider: AIProvider
    model: str

    # Input
    prompt_hash: str  # Hashed for privacy
    input_tokens: int = 0

    # Output
    output_tokens: int = 0
    finish_reason: str = ""

    # Performance
    latency_ms: float = 0
    time_to_first_token_ms: Optional[float] = None  # For streaming

    # Quality
    quality_rating: Optional[QualityRating] = None
    confidence_score: Optional[float] = None

    # Cost
    estimated_cost_usd: float = 0

    # Status
    success: bool = True
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    feature: Optional[str] = None  # e.g., "triage", "documentation"

    # A/B testing
    experiment_id: Optional[str] = None
    variant: Optional[str] = None


@dataclass
class AIMetrics:
    """Aggregated AI metrics."""
    period_start: datetime
    period_end: datetime

    # Request counts
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Token usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Latency
    avg_latency_ms: float = 0
    p50_latency_ms: float = 0
    p95_latency_ms: float = 0
    p99_latency_ms: float = 0

    # Cost
    total_cost_usd: float = 0
    avg_cost_per_request_usd: float = 0

    # Quality
    avg_confidence_score: Optional[float] = None
    quality_distribution: Dict[str, int] = field(default_factory=dict)

    # By type
    by_request_type: Dict[str, int] = field(default_factory=dict)
    by_provider: Dict[str, int] = field(default_factory=dict)
    by_model: Dict[str, int] = field(default_factory=dict)

    # Error analysis
    error_rate: float = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)


@dataclass
class CostAlert:
    """Cost alert definition."""
    alert_id: str
    name: str
    threshold_usd: float
    period: str  # "hourly", "daily", "monthly"
    tenant_id: Optional[str] = None
    callback: Optional[Callable] = None
    triggered: bool = False
    last_triggered: Optional[datetime] = None


@dataclass
class ABExperiment:
    """A/B testing experiment definition."""
    experiment_id: str
    name: str
    description: str

    # Variants
    variants: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # e.g., {"control": {"model": "gpt-3.5-turbo"}, "treatment": {"model": "gpt-4"}}

    # Traffic allocation (must sum to 1.0)
    traffic_split: Dict[str, float] = field(default_factory=dict)

    # Status
    status: str = "draft"  # draft, running, paused, completed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Results
    results: Dict[str, Any] = field(default_factory=dict)


# Cost per 1K tokens (approximate)
MODEL_COSTS = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
    "text-embedding-ada-002": {"input": 0.0001, "output": 0},
    "text-embedding-3-small": {"input": 0.00002, "output": 0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
}


class AIMonitoringService:
    """
    AI Monitoring and Observability Service.

    Provides comprehensive monitoring for AI operations including:
    - Request logging
    - Performance metrics
    - Cost tracking
    - Quality monitoring
    - A/B testing
    - Alerting
    """

    def __init__(
        self,
        max_log_retention: int = 10000,
        metrics_window_minutes: int = 60,
    ):
        self.max_log_retention = max_log_retention
        self.metrics_window_minutes = metrics_window_minutes

        # In-memory storage (in production, use database)
        self._request_logs: List[AIRequestLog] = []
        self._metrics_cache: Dict[str, AIMetrics] = {}
        self._cost_alerts: Dict[str, CostAlert] = {}
        self._experiments: Dict[str, ABExperiment] = {}

        # Real-time counters
        self._hourly_costs: Dict[str, float] = defaultdict(float)
        self._daily_costs: Dict[str, float] = defaultdict(float)

        # Latency tracking for percentiles
        self._latencies: List[float] = []

    async def log_request(
        self,
        tenant_id: str,
        request_type: AIRequestType,
        provider: AIProvider,
        model: str,
        prompt: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool = True,
        finish_reason: str = "stop",
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        confidence_score: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        feature: Optional[str] = None,
        time_to_first_token_ms: Optional[float] = None,
        experiment_id: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> AIRequestLog:
        """
        Log an AI request.

        Args:
            tenant_id: Tenant identifier
            request_type: Type of AI request
            provider: AI provider used
            model: Model name
            prompt: Input prompt (will be hashed)
            input_tokens: Input token count
            output_tokens: Output token count
            latency_ms: Request latency in milliseconds
            success: Whether request succeeded
            finish_reason: Completion finish reason
            error_message: Error message if failed
            error_type: Error classification
            confidence_score: AI confidence score
            user_id: User identifier
            session_id: Session identifier
            conversation_id: Conversation identifier
            feature: Feature name (triage, documentation, etc.)
            time_to_first_token_ms: Time to first token for streaming
            experiment_id: A/B experiment ID
            variant: Experiment variant

        Returns:
            AIRequestLog entry
        """
        # Calculate cost
        estimated_cost = self._calculate_cost(model, input_tokens, output_tokens)

        # Hash prompt for privacy
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        log_entry = AIRequestLog(
            request_id=str(uuid4()),
            tenant_id=tenant_id,
            timestamp=datetime.now(timezone.utc),
            request_type=request_type,
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            success=success,
            error_message=error_message,
            error_type=error_type,
            confidence_score=confidence_score,
            estimated_cost_usd=estimated_cost,
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id,
            feature=feature,
            time_to_first_token_ms=time_to_first_token_ms,
            experiment_id=experiment_id,
            variant=variant,
        )

        # Store log
        self._request_logs.append(log_entry)

        # Maintain log retention limit
        if len(self._request_logs) > self.max_log_retention:
            self._request_logs = self._request_logs[-self.max_log_retention:]

        # Update latency tracking
        self._latencies.append(latency_ms)
        if len(self._latencies) > 10000:
            self._latencies = self._latencies[-10000:]

        # Update cost tracking
        hour_key = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
        day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._hourly_costs[f"{tenant_id}:{hour_key}"] += estimated_cost
        self._daily_costs[f"{tenant_id}:{day_key}"] += estimated_cost

        # Check cost alerts
        await self._check_cost_alerts(tenant_id)

        logger.debug(
            f"Logged AI request {log_entry.request_id}: "
            f"{request_type.value} with {model}, "
            f"tokens: {input_tokens}+{output_tokens}, "
            f"latency: {latency_ms:.0f}ms, "
            f"cost: ${estimated_cost:.6f}"
        )

        return log_entry

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate estimated cost for a request."""
        model_key = model.lower()

        # Find matching model in costs
        cost_info = None
        for key, costs in MODEL_COSTS.items():
            if key in model_key:
                cost_info = costs
                break

        if not cost_info:
            # Default to GPT-3.5 costs if unknown
            cost_info = MODEL_COSTS["gpt-3.5-turbo"]

        input_cost = (input_tokens / 1000) * cost_info["input"]
        output_cost = (output_tokens / 1000) * cost_info["output"]

        return input_cost + output_cost

    async def _check_cost_alerts(self, tenant_id: str):
        """Check and trigger cost alerts."""
        now = datetime.now(timezone.utc)
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")

        for alert_id, alert in self._cost_alerts.items():
            if alert.tenant_id and alert.tenant_id != tenant_id:
                continue

            # Determine current cost based on period
            if alert.period == "hourly":
                current_cost = self._hourly_costs.get(f"{tenant_id}:{hour_key}", 0)
            elif alert.period == "daily":
                current_cost = self._daily_costs.get(f"{tenant_id}:{day_key}", 0)
            else:
                continue

            # Check threshold
            if current_cost >= alert.threshold_usd and not alert.triggered:
                alert.triggered = True
                alert.last_triggered = now

                logger.warning(
                    f"Cost alert triggered: {alert.name} "
                    f"(${current_cost:.2f} >= ${alert.threshold_usd:.2f})"
                )

                if alert.callback:
                    try:
                        await alert.callback(alert, current_cost, tenant_id)
                    except Exception as e:
                        logger.error(f"Error in cost alert callback: {e}")

    async def get_metrics(
        self,
        tenant_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        request_type: Optional[AIRequestType] = None,
        provider: Optional[AIProvider] = None,
        model: Optional[str] = None,
    ) -> AIMetrics:
        """
        Get aggregated AI metrics.

        Args:
            tenant_id: Filter by tenant
            start_time: Start of period
            end_time: End of period
            request_type: Filter by request type
            provider: Filter by provider
            model: Filter by model

        Returns:
            Aggregated AIMetrics
        """
        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or (end_time - timedelta(minutes=self.metrics_window_minutes))

        # Filter logs
        filtered_logs = [
            log for log in self._request_logs
            if start_time <= log.timestamp <= end_time
            and (tenant_id is None or log.tenant_id == tenant_id)
            and (request_type is None or log.request_type == request_type)
            and (provider is None or log.provider == provider)
            and (model is None or model in log.model)
        ]

        if not filtered_logs:
            return AIMetrics(
                period_start=start_time,
                period_end=end_time,
            )

        # Calculate metrics
        total_requests = len(filtered_logs)
        successful_requests = sum(1 for log in filtered_logs if log.success)
        failed_requests = total_requests - successful_requests

        # Token usage
        total_input_tokens = sum(log.input_tokens for log in filtered_logs)
        total_output_tokens = sum(log.output_tokens for log in filtered_logs)

        # Latency
        latencies = [log.latency_ms for log in filtered_logs]
        latencies.sort()

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p50_latency = latencies[len(latencies) // 2] if latencies else 0
        p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
        p99_latency = latencies[int(len(latencies) * 0.99)] if latencies else 0

        # Cost
        total_cost = sum(log.estimated_cost_usd for log in filtered_logs)
        avg_cost = total_cost / total_requests if total_requests > 0 else 0

        # Quality
        confidence_scores = [
            log.confidence_score for log in filtered_logs
            if log.confidence_score is not None
        ]
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else None
        )

        quality_distribution = defaultdict(int)
        for log in filtered_logs:
            if log.quality_rating:
                quality_distribution[log.quality_rating.value] += 1

        # Breakdowns
        by_request_type = defaultdict(int)
        by_provider = defaultdict(int)
        by_model = defaultdict(int)
        errors_by_type = defaultdict(int)

        for log in filtered_logs:
            by_request_type[log.request_type.value] += 1
            by_provider[log.provider.value] += 1
            by_model[log.model] += 1

            if not log.success and log.error_type:
                errors_by_type[log.error_type] += 1

        return AIMetrics(
            period_start=start_time,
            period_end=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            total_cost_usd=total_cost,
            avg_cost_per_request_usd=avg_cost,
            avg_confidence_score=avg_confidence,
            quality_distribution=dict(quality_distribution),
            by_request_type=dict(by_request_type),
            by_provider=dict(by_provider),
            by_model=dict(by_model),
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            errors_by_type=dict(errors_by_type),
        )

    async def get_cost_summary(
        self,
        tenant_id: str,
        period: str = "daily",  # hourly, daily
        lookback: int = 7,  # Number of periods
    ) -> Dict[str, float]:
        """
        Get cost summary by period.

        Args:
            tenant_id: Tenant identifier
            period: Period type (hourly, daily)
            lookback: Number of periods to look back

        Returns:
            Dictionary mapping period keys to costs
        """
        costs = {}
        now = datetime.now(timezone.utc)

        if period == "hourly":
            for i in range(lookback):
                dt = now - timedelta(hours=i)
                key = dt.strftime("%Y-%m-%d-%H")
                costs[key] = self._hourly_costs.get(f"{tenant_id}:{key}", 0)
        elif period == "daily":
            for i in range(lookback):
                dt = now - timedelta(days=i)
                key = dt.strftime("%Y-%m-%d")
                costs[key] = self._daily_costs.get(f"{tenant_id}:{key}", 0)

        return costs

    def create_cost_alert(
        self,
        name: str,
        threshold_usd: float,
        period: str = "daily",
        tenant_id: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> CostAlert:
        """
        Create a cost alert.

        Args:
            name: Alert name
            threshold_usd: Cost threshold in USD
            period: Alert period (hourly, daily, monthly)
            tenant_id: Tenant to monitor (None for all)
            callback: Async callback function

        Returns:
            Created CostAlert
        """
        alert = CostAlert(
            alert_id=str(uuid4()),
            name=name,
            threshold_usd=threshold_usd,
            period=period,
            tenant_id=tenant_id,
            callback=callback,
        )

        self._cost_alerts[alert.alert_id] = alert

        logger.info(f"Created cost alert: {name} (${threshold_usd} {period})")
        return alert

    def delete_cost_alert(self, alert_id: str) -> bool:
        """Delete a cost alert."""
        if alert_id in self._cost_alerts:
            del self._cost_alerts[alert_id]
            return True
        return False

    # ==================== A/B Testing ====================

    def create_experiment(
        self,
        name: str,
        description: str,
        variants: Dict[str, Dict[str, Any]],
        traffic_split: Dict[str, float],
    ) -> ABExperiment:
        """
        Create an A/B experiment.

        Args:
            name: Experiment name
            description: Experiment description
            variants: Variant configurations
            traffic_split: Traffic allocation per variant

        Returns:
            Created ABExperiment
        """
        # Validate traffic split sums to 1.0
        if abs(sum(traffic_split.values()) - 1.0) > 0.001:
            raise ValueError("Traffic split must sum to 1.0")

        experiment = ABExperiment(
            experiment_id=str(uuid4()),
            name=name,
            description=description,
            variants=variants,
            traffic_split=traffic_split,
        )

        self._experiments[experiment.experiment_id] = experiment

        logger.info(f"Created A/B experiment: {name}")
        return experiment

    def start_experiment(self, experiment_id: str) -> ABExperiment:
        """Start an A/B experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment.status = "running"
        experiment.started_at = datetime.now(timezone.utc)

        logger.info(f"Started experiment: {experiment.name}")
        return experiment

    def stop_experiment(self, experiment_id: str) -> ABExperiment:
        """Stop an A/B experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment.status = "completed"
        experiment.ended_at = datetime.now(timezone.utc)

        # Calculate results
        experiment.results = self._calculate_experiment_results(experiment_id)

        logger.info(f"Stopped experiment: {experiment.name}")
        return experiment

    def get_variant(
        self,
        experiment_id: str,
        user_id: str,
    ) -> Optional[tuple]:
        """
        Get the variant for a user in an experiment.

        Uses consistent hashing to ensure same user always gets same variant.

        Args:
            experiment_id: Experiment ID
            user_id: User identifier

        Returns:
            Tuple of (variant_name, variant_config) or None if experiment not running
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment or experiment.status != "running":
            return None

        # Consistent hash based on user ID
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 1000) / 1000  # 0.0 to 0.999

        # Assign to variant based on traffic split
        cumulative = 0.0
        for variant_name, allocation in experiment.traffic_split.items():
            cumulative += allocation
            if bucket < cumulative:
                return (variant_name, experiment.variants[variant_name])

        # Fallback to first variant
        first_variant = list(experiment.variants.keys())[0]
        return (first_variant, experiment.variants[first_variant])

    def _calculate_experiment_results(
        self,
        experiment_id: str,
    ) -> Dict[str, Any]:
        """Calculate experiment results from logs."""
        logs = [
            log for log in self._request_logs
            if log.experiment_id == experiment_id
        ]

        if not logs:
            return {"status": "no_data"}

        results_by_variant: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "success_count": 0,
                "total_latency": 0,
                "total_cost": 0,
                "confidence_scores": [],
            }
        )

        for log in logs:
            if not log.variant:
                continue

            v = results_by_variant[log.variant]
            v["count"] += 1
            if log.success:
                v["success_count"] += 1
            v["total_latency"] += log.latency_ms
            v["total_cost"] += log.estimated_cost_usd
            if log.confidence_score is not None:
                v["confidence_scores"].append(log.confidence_score)

        # Calculate summary metrics
        summary = {}
        for variant_name, data in results_by_variant.items():
            count = data["count"]
            if count == 0:
                continue

            summary[variant_name] = {
                "requests": count,
                "success_rate": data["success_count"] / count,
                "avg_latency_ms": data["total_latency"] / count,
                "total_cost_usd": data["total_cost"],
                "avg_cost_per_request_usd": data["total_cost"] / count,
                "avg_confidence": (
                    sum(data["confidence_scores"]) / len(data["confidence_scores"])
                    if data["confidence_scores"] else None
                ),
            }

        return summary

    async def get_experiment_results(
        self,
        experiment_id: str,
    ) -> Dict[str, Any]:
        """Get current experiment results."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        if experiment.status == "completed":
            return experiment.results

        return self._calculate_experiment_results(experiment_id)

    # ==================== Quality Tracking ====================

    async def record_quality_rating(
        self,
        request_id: str,
        rating: QualityRating,
        feedback: Optional[str] = None,
    ) -> bool:
        """
        Record quality rating for a request.

        Args:
            request_id: Request ID to rate
            rating: Quality rating
            feedback: Optional feedback text

        Returns:
            True if rating was recorded
        """
        for log in self._request_logs:
            if log.request_id == request_id:
                log.quality_rating = rating
                logger.debug(f"Recorded quality rating {rating.value} for {request_id}")
                return True

        return False

    async def get_quality_metrics(
        self,
        tenant_id: Optional[str] = None,
        feature: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get quality metrics for AI responses."""
        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or (end_time - timedelta(days=7))

        logs = [
            log for log in self._request_logs
            if start_time <= log.timestamp <= end_time
            and (tenant_id is None or log.tenant_id == tenant_id)
            and (feature is None or log.feature == feature)
        ]

        if not logs:
            return {"status": "no_data"}

        rated_logs = [log for log in logs if log.quality_rating]
        confidence_logs = [
            log for log in logs
            if log.confidence_score is not None
        ]

        quality_distribution = defaultdict(int)
        for log in rated_logs:
            quality_distribution[log.quality_rating.value] += 1

        return {
            "total_requests": len(logs),
            "rated_requests": len(rated_logs),
            "rating_rate": len(rated_logs) / len(logs) if logs else 0,
            "quality_distribution": dict(quality_distribution),
            "avg_confidence_score": (
                sum(log.confidence_score for log in confidence_logs) / len(confidence_logs)
                if confidence_logs else None
            ),
            "excellent_rate": (
                quality_distribution.get("excellent", 0) / len(rated_logs)
                if rated_logs else 0
            ),
            "poor_rate": (
                quality_distribution.get("poor", 0) / len(rated_logs)
                if rated_logs else 0
            ),
        }

    # ==================== Reporting ====================

    async def generate_daily_report(
        self,
        tenant_id: str,
        date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate a daily AI usage report.

        Args:
            tenant_id: Tenant identifier
            date: Report date (defaults to yesterday)

        Returns:
            Daily report with metrics
        """
        if date is None:
            date = datetime.now(timezone.utc) - timedelta(days=1)

        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)

        metrics = await self.get_metrics(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
        )

        quality_metrics = await self.get_quality_metrics(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
        )

        return {
            "date": date.strftime("%Y-%m-%d"),
            "tenant_id": tenant_id,
            "summary": {
                "total_requests": metrics.total_requests,
                "success_rate": (
                    metrics.successful_requests / metrics.total_requests
                    if metrics.total_requests > 0 else 0
                ),
                "total_cost_usd": metrics.total_cost_usd,
                "avg_cost_per_request_usd": metrics.avg_cost_per_request_usd,
                "total_tokens": metrics.total_tokens,
            },
            "performance": {
                "avg_latency_ms": metrics.avg_latency_ms,
                "p95_latency_ms": metrics.p95_latency_ms,
                "p99_latency_ms": metrics.p99_latency_ms,
            },
            "quality": quality_metrics,
            "breakdown": {
                "by_type": metrics.by_request_type,
                "by_model": metrics.by_model,
                "errors": metrics.errors_by_type,
            },
        }


# Global monitoring service instance
ai_monitoring_service = AIMonitoringService()

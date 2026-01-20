"""
VAP SDK Models
Pydantic models for API responses
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GenerateResult:
    """Result of image generation."""
    success: bool
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    request_id: Optional[str] = None
    aspect_ratio: Optional[str] = None
    cost: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "GenerateResult":
        """Create from API response."""
        return cls(
            success=data.get("success", False),
            image_url=data.get("image_url"),
            image_base64=data.get("image_base64"),
            request_id=data.get("request_id"),
            aspect_ratio=data.get("aspect_ratio"),
            cost=data.get("cost", 0.0),
            metadata=data.get("metadata"),
            error=data.get("error"),
        )


@dataclass
class UpscaleResult:
    """Result of image upscaling."""
    success: bool
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    scale: Optional[str] = None
    cost: float = 0.0
    error: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "UpscaleResult":
        """Create from API response."""
        return cls(
            success=data.get("success", False),
            image_url=data.get("image_url"),
            image_base64=data.get("image_base64"),
            scale=data.get("scale"),
            cost=data.get("cost", 0.0),
            error=data.get("error"),
        )


@dataclass
class ValidationCheck:
    """Individual validation check result."""
    name: str
    passed: bool
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidateResult:
    """Result of image validation."""
    success: bool
    valid: bool = False
    issues: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    format_info: Optional[Dict[str, Any]] = None
    dimensions: Optional[Dict[str, Any]] = None
    size_info: Optional[Dict[str, Any]] = None
    cost: float = 0.0
    error: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "ValidateResult":
        """Create from API response."""
        validation = data.get("validation", {})
        return cls(
            success=data.get("success", False),
            valid=validation.get("valid", False),
            issues=validation.get("issues"),
            warnings=validation.get("warnings"),
            format_info=validation.get("format"),
            dimensions=validation.get("dimensions"),
            size_info=validation.get("size"),
            cost=data.get("cost", 0.0),
            error=data.get("error"),
        )


@dataclass
class HealthStatus:
    """API health status."""
    status: str
    version: Optional[str] = None
    service: Optional[str] = None
    dependencies: Optional[Dict[str, Any]] = None

    @classmethod
    def from_response(cls, data: dict) -> "HealthStatus":
        """Create from API response."""
        return cls(
            status=data.get("status", "unknown"),
            version=data.get("version"),
            service=data.get("service"),
            dependencies=data.get("dependencies"),
        )


@dataclass
class Balance:
    """Client balance information."""
    balance: float
    currency: str = "USD"
    reserved: float = 0.0
    usable: float = 0.0

    @classmethod
    def from_response(cls, data: dict) -> "Balance":
        """Create from API response."""
        return cls(
            balance=float(data.get("balance", 0)),
            currency=data.get("currency", "USD"),
            reserved=float(data.get("reserved", 0)),
            usable=float(data.get("usable", data.get("balance", 0))),
        )


@dataclass
class VideoResult:
    """Result of video generation."""
    success: bool
    task_id: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[int] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    has_audio: bool = False
    cost: float = 0.0
    status: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "VideoResult":
        """Create from API response."""
        return cls(
            success=data.get("success", False),
            task_id=data.get("task_id"),
            video_url=data.get("video_url") or data.get("result_url"),
            duration=data.get("duration"),
            resolution=data.get("resolution"),
            aspect_ratio=data.get("aspect_ratio"),
            has_audio=data.get("has_audio", False),
            cost=data.get("cost", 0.0),
            status=data.get("status"),
            error=data.get("error"),
        )


@dataclass
class MusicResult:
    """Result of music generation."""
    success: bool
    task_id: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[int] = None
    audio_format: Optional[str] = None
    instrumental: bool = False
    cost: float = 0.0
    status: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "MusicResult":
        """Create from API response."""
        return cls(
            success=data.get("success", False),
            task_id=data.get("task_id"),
            audio_url=data.get("audio_url") or data.get("result_url"),
            duration=data.get("duration"),
            audio_format=data.get("audio_format", "mp3"),
            instrumental=data.get("instrumental", False),
            cost=data.get("cost", 0.0),
            status=data.get("status"),
            error=data.get("error"),
        )


@dataclass
class TaskResult:
    """Result of task status query."""
    task_id: str
    status: str
    task_type: Optional[str] = None
    result_url: Optional[str] = None
    cost: float = 0.0
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_response(cls, data: dict) -> "TaskResult":
        """Create from API response."""
        return cls(
            task_id=data.get("task_id", ""),
            status=data.get("status", "unknown"),
            task_type=data.get("task_type") or data.get("type"),
            result_url=data.get("result_url") or data.get("image_url") or data.get("video_url") or data.get("audio_url"),
            cost=data.get("cost", 0.0),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
            error=data.get("error"),
            metadata=data.get("metadata"),
        )


@dataclass
class TaskListResult:
    """Result of task list query."""
    tasks: List["TaskResult"]
    total: int = 0
    limit: int = 10
    offset: int = 0

    @classmethod
    def from_response(cls, data: dict) -> "TaskListResult":
        """Create from API response."""
        tasks_data = data.get("tasks", [])
        tasks = [TaskResult.from_response(t) for t in tasks_data]
        return cls(
            tasks=tasks,
            total=data.get("total", len(tasks)),
            limit=data.get("limit", 10),
            offset=data.get("offset", 0),
        )
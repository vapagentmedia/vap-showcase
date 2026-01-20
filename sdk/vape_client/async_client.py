"""
VAP Async Client
Asynchronous HTTP client for VAP API
"""

import httpx
from typing import Optional, List, Dict, Any
from .models import (
    GenerateResult,
    UpscaleResult,
    ValidateResult,
    HealthStatus,
    Balance,
    VideoResult,
    MusicResult,
    TaskResult,
    TaskListResult,
)
from .exceptions import (
    VAPEError,
    VAPEAuthenticationError,
    VAPEInsufficientBalanceError,
    VAPERateLimitError,
    VAPEValidationError,
    VAPEServerError,
    VAPEConnectionError,
    VAPETimeoutError,
)


class AsyncVAPEClient:
    """
    Asynchronous client for VAP API.

    Usage:
        async with AsyncVAPEClient(api_key="vape_xxx...") as client:
            result = await client.generate(description="A sunset")
            print(result.image_url)
    """

    DEFAULT_BASE_URL = "https://api.vapagent.com"
    DEFAULT_TIMEOUT = 60.0

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: float = None,
        max_retries: int = 3,
    ):
        """
        Initialize async VAP client.

        Args:
            api_key: Your VAP API key (starts with vape_)
            base_url: API base URL (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 60)
            max_retries: Max retry attempts for transient errors (default: 3)
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    def _default_headers(self) -> Dict[str, str]:
        """Get default request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "vap-client-python/1.0.0",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._default_headers(),
            )
        return self._client

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate exceptions."""
        try:
            data = response.json()
        except:
            data = {"error": response.text}

        if response.status_code == 200:
            return data
        elif response.status_code == 401:
            raise VAPEAuthenticationError(
                message=data.get("error", "Authentication failed"),
                status_code=401,
                response=data,
            )
        elif response.status_code == 402:
            raise VAPEInsufficientBalanceError(
                message=data.get("error", "Insufficient balance"),
                status_code=402,
                response=data,
                balance=data.get("balance"),
                required=data.get("required"),
            )
        elif response.status_code == 429:
            raise VAPERateLimitError(
                message=data.get("error", "Rate limit exceeded"),
                status_code=429,
                response=data,
                retry_after=data.get("retry_after"),
                limit_type=data.get("limit_type"),
            )
        elif response.status_code == 400:
            raise VAPEValidationError(
                message=data.get("error", "Validation error"),
                status_code=400,
                response=data,
                errors=data.get("errors"),
            )
        elif response.status_code >= 500:
            raise VAPEServerError(
                message=data.get("error", "Server error"),
                status_code=response.status_code,
                response=data,
            )
        else:
            raise VAPEError(
                message=data.get("error", f"Request failed with status {response.status_code}"),
                status_code=response.status_code,
                response=data,
            )

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: dict = None,
        params: dict = None,
    ) -> dict:
        """Make async HTTP request with retry logic."""
        client = await self._get_client()
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=json,
                    params=params,
                )
                return self._handle_response(response)

            except httpx.TimeoutException as e:
                last_error = VAPETimeoutError(f"Request timed out: {e}")
                if attempt < self.max_retries - 1:
                    continue

            except httpx.ConnectError as e:
                last_error = VAPEConnectionError(f"Connection failed: {e}")
                if attempt < self.max_retries - 1:
                    continue

            except (VAPEAuthenticationError, VAPEInsufficientBalanceError,
                    VAPEValidationError) as e:
                raise

            except VAPERateLimitError as e:
                raise

            except VAPEServerError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue

            except VAPEError:
                raise

        raise last_error

    async def close(self):
        """Close the async HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ============================================
    # API Methods
    # ============================================

    async def health(self) -> HealthStatus:
        """Check API health status."""
        data = await self._request("GET", "/v3/health")
        return HealthStatus.from_response(data)

    async def generate(
        self,
        description: str,
        aspect_ratio: str = "1:1",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GenerateResult:
        """Generate an image from description."""
        payload = {
            "description": description,
            "aspect_ratio": aspect_ratio,
        }

        if style:
            payload["style"] = style
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if metadata:
            payload["metadata"] = metadata

        data = await self._request("POST", "/v3/generate", json=payload)
        return GenerateResult.from_response(data)

    async def upscale(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        scale: str = "2x",
    ) -> UpscaleResult:
        """Upscale an image using AI enhancement."""
        if not image_url and not image_base64:
            raise VAPEValidationError("Either image_url or image_base64 is required")

        payload = {"scale": scale}
        if image_url:
            payload["image_url"] = image_url
        if image_base64:
            payload["image_base64"] = image_base64

        data = await self._request("POST", "/v3/upscale", json=payload)
        return UpscaleResult.from_response(data)

    async def validate(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        checks: Optional[List[str]] = None,
    ) -> ValidateResult:
        """Validate an image for format, size, and quality."""
        if not image_url and not image_base64:
            raise VAPEValidationError("Either image_url or image_base64 is required")

        payload = {}
        if image_url:
            payload["image_url"] = image_url
        if image_base64:
            payload["image_base64"] = image_base64
        if checks:
            payload["checks"] = checks

        data = await self._request("POST", "/v3/validate", json=payload)
        return ValidateResult.from_response(data)

    async def get_balance(self) -> Balance:
        """Get current account balance."""
        data = await self._request("GET", "/v3/balance")
        return Balance.from_response(data)

    # ============================================
    # Video Generation (Veo 3.1) - $1.96
    # ============================================

    async def generate_video(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        generate_audio: bool = True,
        resolution: str = "720p",
        negative_prompt: Optional[str] = None,
    ) -> VideoResult:
        """
        Generate a video from text prompt using Veo 3.1.

        Args:
            prompt: Visual description of the video to generate
            duration: Video duration in seconds (4, 6, or 8)
            aspect_ratio: Video aspect ratio (16:9 or 9:16)
            generate_audio: Whether to generate audio (costs more)
            resolution: Video resolution (720p or 1080p)
            negative_prompt: What to avoid in the video

        Returns:
            VideoResult with task_id for async tracking. Cost: $1.96
        """
        payload = {
            "type": "video_generation",
            "params": {
                "description": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "generate_audio": generate_audio,
                "resolution": resolution,
            }
        }

        if negative_prompt:
            payload["params"]["negative_prompt"] = negative_prompt

        data = await self._request("POST", "/v3/tasks", json=payload)
        return VideoResult.from_response(data)

    # ============================================
    # Music Generation (Suno V5) - $0.68
    # ============================================

    async def generate_music(
        self,
        prompt: str,
        duration: int = 120,
        instrumental: bool = False,
        loudness_preset: str = "streaming",
        audio_format: str = "mp3",
    ) -> MusicResult:
        """
        Generate music from text prompt using Suno V5.

        Args:
            prompt: Music description (genre, mood, instruments, tempo)
            duration: Target duration in seconds (30-480, default 120)
            instrumental: Generate without vocals
            loudness_preset: Normalization (streaming, apple, broadcast)
            audio_format: Output format (mp3 or wav)

        Returns:
            MusicResult with task_id for async tracking. Cost: $0.68
        """
        payload = {
            "type": "music_generation",
            "params": {
                "description": prompt,
                "duration": duration,
                "instrumental": instrumental,
                "loudness_preset": loudness_preset,
                "audio_format": audio_format,
            }
        }

        data = await self._request("POST", "/v3/tasks", json=payload)
        return MusicResult.from_response(data)

    # ============================================
    # Task Management
    # ============================================

    async def get_task(self, task_id: str) -> TaskResult:
        """
        Get the status and result of a generation task.

        Args:
            task_id: Task UUID from generate_image/video/music

        Returns:
            TaskResult with status and result_url when completed
        """
        data = await self._request("GET", f"/v3/tasks/{task_id}")
        return TaskResult.from_response(data)

    async def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> TaskListResult:
        """
        List recent generation tasks.

        Args:
            status: Filter by status (pending, processing, completed, failed)
            limit: Maximum number of tasks to return (1-50)

        Returns:
            TaskListResult with list of tasks
        """
        params = {"limit": limit}
        if status:
            params["status"] = status

        data = await self._request("GET", "/v3/tasks", params=params)
        return TaskListResult.from_response(data)
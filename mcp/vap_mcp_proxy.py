#!/usr/bin/env python3
"""
VAP MCP Proxy for Claude Desktop

Bridges Claude Desktop's stdio transport to VAP's HTTP MCP endpoints.
Claude Desktop communicates via JSON-RPC over stdio, this proxy translates
those requests to HTTP calls to the VAP API.

Supported Tools (10 total):
- generate_image: Generate AI images (~$0.002 each, Z-Image-Turbo)
- generate_video: Generate AI videos (Veo 3.1) - $2.40-$4.80 with audio, $1.20-$2.40 without
- generate_music: Generate AI music (Suno) - ~$0.05/song
- execute_preset: Run predefined generation presets
- get_task: Check task status and get results
- list_tasks: List recent tasks
- check_balance: Check account balance
- estimate_cost: Estimate image generation cost
- estimate_video_cost: Estimate video generation cost
- estimate_music_cost: Estimate music generation cost

Usage:
    python vap_mcp_proxy.py

Configuration:
    Set VAP_API_KEY environment variable (VAPE_API_KEY also supported for backward compatibility).

Claude Desktop config (~/.config/Claude/claude_desktop_config.json):
{
  "mcpServers": {
    "vap": {
      "command": "python",
      "args": ["/path/to/vap_mcp_proxy.py"],
      "env": {
        "VAP_API_KEY": "vap_your_api_key_here"
      }
    }
  }
}

Directive: #233 (Local MCP Proxy)
Directive: #242 (Veo 3.1 Video)
Directive: #405 (Documentation)
"""

import sys
import json
import os
import logging
from typing import Optional, Dict, Any

# Use httpx for async HTTP (pip install httpx)
try:
    import httpx
except ImportError:
    # Fallback to requests if httpx not available
    import requests as httpx

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

API_URL = os.getenv("VAP_API_URL", os.getenv("VAPE_API_URL", "https://api.vapagent.com/mcp")).strip()
API_BASE_URL = os.getenv("VAP_API_BASE_URL", os.getenv("VAPE_API_BASE_URL", "https://api.vapagent.com")).strip()
# Support both VAP_API_KEY (new) and VAPE_API_KEY (legacy) for backward compatibility
API_KEY = os.getenv("VAP_API_KEY", os.getenv("VAPE_API_KEY", "")).strip()

# Video pricing (Directive #242: Veo 3.1)
# COGS: $0.40/sec with audio, $0.20/sec without
# Sell price: 50% margin on COGS
VIDEO_COSTS_WITH_AUDIO = {4: 2.40, 6: 3.60, 8: 4.80}
VIDEO_COSTS_NO_AUDIO = {4: 1.20, 6: 1.80, 8: 2.40}

# Logging to stderr so it doesn't interfere with stdio
logging.basicConfig(
    level=logging.DEBUG if os.getenv("VAP_DEBUG", os.getenv("VAPE_DEBUG")) else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# HTTP CLIENT
# ═══════════════════════════════════════════════════════════════════════════

def make_request(endpoint: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP request to VAP MCP API."""
    url = f"{API_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
    }
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    logger.debug(f"Request: POST {url}")
    logger.debug(f"Payload: {json.dumps(payload)}")

    try:
        if hasattr(httpx, 'Client'):
            # httpx
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload or {}, headers=headers)
                response.raise_for_status()
                return response.json()
        else:
            # requests fallback
            response = httpx.post(url, json=payload or {}, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"HTTP error: {e}")
        return {"error": str(e)}


def make_v3_request(endpoint: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP request to VAP V3 API (Directive #240)."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
    }
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    logger.debug(f"V3 Request: POST {url}")
    logger.debug(f"Payload: {json.dumps(payload)}")

    try:
        if hasattr(httpx, 'Client'):
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload or {}, headers=headers)
                response.raise_for_status()
                return response.json()
        else:
            response = httpx.post(url, json=payload or {}, headers=headers, timeout=120)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        # D#509: Extract detailed error from response body
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_body = e.response.json()
                if isinstance(error_body, dict):
                    detail = error_body.get("detail", {})
                    if isinstance(detail, dict):
                        error_detail = detail.get("message", str(detail))
                    elif isinstance(detail, str):
                        error_detail = detail
                    else:
                        error_detail = str(error_body)
            except Exception:
                error_detail = e.response.text[:500] if e.response.text else str(e)
        logger.error(f"V3 HTTP error: {error_detail}")
        return {"error": error_detail}


# ═══════════════════════════════════════════════════════════════════════════
# MCP METHOD HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

def handle_initialize(params: Dict) -> Dict:
    """Handle initialize request."""
    response = make_request("/initialize", {
        "protocolVersion": params.get("protocolVersion"),
        "capabilities": params.get("capabilities", {}),
        "clientInfo": params.get("clientInfo", {})
    })
    return response


def handle_tools_list(params: Dict) -> Dict:
    """Handle tools/list request."""
    response = make_request("/tools/list", {})
    return response


def handle_tools_call(params: Dict) -> Dict:
    """
    Handle tools/call request.

    Directive #240: Special handlers for video tools.
    """
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    # ═══════════════════════════════════════════════════════════════════
    # VIDEO TOOL HANDLERS (Directive #240)
    # ═══════════════════════════════════════════════════════════════════

    if tool_name == "generate_video":
        return _handle_generate_video(arguments)

    if tool_name == "estimate_video_cost":
        return _handle_estimate_video_cost(arguments)

    if tool_name == "get_task":
        return _handle_get_task(arguments)

    # Default: forward to MCP API
    response = make_request("/tools/call", {
        "name": tool_name,
        "arguments": arguments
    })
    return response


def _handle_generate_video(arguments: Dict) -> Dict:
    """
    Handle generate_video tool call (Directive #242: Veo 3.1).

    Creates a video generation task via V3 API.
    """
    prompt = arguments.get("prompt", "")
    duration = arguments.get("duration", 8)
    aspect_ratio = arguments.get("aspect_ratio", "16:9")
    generate_audio = arguments.get("generate_audio", True)
    resolution = arguments.get("resolution", "720p")
    negative_prompt = arguments.get("negative_prompt", "")

    if not prompt:
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Error: prompt is required"}]
        }

    # Validate duration (Veo 3.1: 4, 6, 8 seconds)
    if duration not in (4, 6, 8):
        duration = 8

    # Validate aspect ratio (Veo 3.1: 16:9, 9:16)
    if aspect_ratio not in ("16:9", "9:16"):
        aspect_ratio = "16:9"

    # Validate resolution
    if resolution not in ("720p", "1080p"):
        resolution = "720p"

    # Create task via V3 API
    logger.info(f"Creating Veo 3.1 video task: duration={duration}s, audio={generate_audio}")

    params = {
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "generate_audio": generate_audio,
        "resolution": resolution
    }
    if negative_prompt:
        params["negative_prompt"] = negative_prompt

    response = make_v3_request("/v3/tasks", {
        "type": "video",
        "params": params
    })

    if "error" in response:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error: {response['error']}"}]
        }

    # Format success response
    task_id = response.get("task_id", "unknown")
    cost_table = VIDEO_COSTS_WITH_AUDIO if generate_audio else VIDEO_COSTS_NO_AUDIO
    estimated_cost = response.get("estimated_cost", cost_table.get(duration, 4.80))

    return {
        "content": [{
            "type": "text",
            "text": f"Video generation task created (Veo 3.1)!\n\nTask ID: {task_id}\nDuration: {duration} seconds\nAspect Ratio: {aspect_ratio}\nResolution: {resolution}\nAudio: {'Yes' if generate_audio else 'No'}\nEstimated Cost: ${estimated_cost}\n\nUse get_task with this task_id to check status and get the video URL when complete."
        }]
    }


def _handle_estimate_video_cost(arguments: Dict) -> Dict:
    """
    Handle estimate_video_cost tool call (Directive #242: Veo 3.1).

    Local calculation - no API call needed.
    """
    duration = arguments.get("duration", 8)
    generate_audio = arguments.get("generate_audio", True)

    # Validate duration (Veo 3.1: 4, 6, 8 seconds)
    if duration not in (4, 6, 8):
        duration = 8

    cost_table = VIDEO_COSTS_WITH_AUDIO if generate_audio else VIDEO_COSTS_NO_AUDIO
    cost = cost_table.get(duration, 4.80)

    return {
        "content": [{
            "type": "text",
            "text": f"Video Generation Cost Estimate (Veo 3.1):\n\nDuration: {duration} seconds\nAudio: {'Yes' if generate_audio else 'No'}\nCost: ${cost:.2f}\n\nPricing with audio:\n- 4 seconds: $2.40\n- 6 seconds: $3.60\n- 8 seconds: $4.80\n\nPricing without audio:\n- 4 seconds: $1.20\n- 6 seconds: $1.80\n- 8 seconds: $2.40"
        }]
    }


def _handle_get_task(arguments: Dict) -> Dict:
    """
    Handle get_task tool call (Directive #241).

    Fetches task status from V3 API with proper video_url extraction.
    """
    task_id = arguments.get("task_id", "")

    if not task_id:
        return {
            "isError": True,
            "content": [{"type": "text", "text": "Error: task_id is required"}]
        }

    # Fetch task from V3 API
    response = make_v3_get_request(f"/v3/tasks/{task_id}")

    if "error" in response:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error: {response['error']}"}]
        }

    # Extract fields
    status = response.get("status", "unknown")
    task_type = response.get("type", "unknown")
    estimated_cost = response.get("estimated_cost", "N/A")
    actual_cost = response.get("actual_cost", "N/A")
    error_message = response.get("error_message")
    result = response.get("result", {}) or {}

    # Extract output URL (video, image, or audio)
    video_url = result.get("video_url") or result.get("output_url")
    image_url = result.get("image_url") or result.get("output_url")

    # D#508: Music tasks have audio_url in items array
    audio_url = None
    items = result.get("items", [])
    if items and isinstance(items, list) and len(items) > 0:
        audio_url = items[0].get("audio_url")
        # Also check for image_url in items (for image tasks)
        if not image_url:
            image_url = items[0].get("image_url")

    # Build response text
    lines = [
        f"Task: {task_id}",
        f"Type: {task_type}",
        f"Status: {status}",
        f"Estimated Cost: ${estimated_cost}",
    ]

    if actual_cost and actual_cost != "N/A":
        lines.append(f"Actual Cost: ${actual_cost}")

    if status == "completed":
        if audio_url:
            lines.append(f"\n🎵 Audio URL: {audio_url}")
        elif video_url:
            lines.append(f"\n🎬 Video URL: {video_url}")
        elif image_url:
            lines.append(f"\n🖼️ Image URL: {image_url}")
    elif status == "failed" and error_message:
        lines.append(f"\n❌ Error: {error_message}")
    elif status in ("pending", "queued", "executing"):
        lines.append(f"\n⏳ Task is still {status}. Check again shortly.")

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(lines)
        }]
    }


def make_v3_get_request(endpoint: str) -> Dict[str, Any]:
    """Make HTTP GET request to VAP V3 API (Directive #241)."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
    }
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    logger.debug(f"V3 GET Request: {url}")

    try:
        if hasattr(httpx, 'Client'):
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        else:
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"V3 GET error: {e}")
        return {"error": str(e)}


def handle_resources_list(params: Dict) -> Dict:
    """Handle resources/list request."""
    response = make_request("/resources/list", {})
    return response


def handle_resources_read(params: Dict) -> Dict:
    """Handle resources/read request."""
    response = make_request("/resources/read", {
        "params": {"uri": params.get("uri")}
    })
    return response


# Method routing table
METHOD_HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "resources/list": handle_resources_list,
    "resources/read": handle_resources_read,
}


# ═══════════════════════════════════════════════════════════════════════════
# JSON-RPC PROTOCOL
# ═══════════════════════════════════════════════════════════════════════════

def create_response(id: Any, result: Any) -> Dict:
    """Create JSON-RPC success response."""
    return {
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    }


def create_error(id: Any, code: int, message: str) -> Dict:
    """Create JSON-RPC error response."""
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": {
            "code": code,
            "message": message
        }
    }


def process_request(request: Dict) -> Optional[Dict]:
    """Process a JSON-RPC request or notification.

    Returns:
        Dict for requests (with response), None for notifications (no response).
    """
    request_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params") or {}

    # Notifications have no id - don't send response
    is_notification = request_id is None

    if is_notification:
        if method == "notifications/initialized":
            logger.info("Client initialized successfully")
        elif method.startswith("notifications/"):
            logger.debug(f"Received notification: {method}")
        else:
            logger.warning(f"Unknown notification: {method}")
        return None  # DON'T SEND RESPONSE FOR NOTIFICATIONS

    logger.info(f"Processing method: {method}")

    # Find handler for requests
    handler = METHOD_HANDLERS.get(method)
    if not handler:
        logger.warning(f"Unknown method: {method}")
        return create_error(request_id, -32601, f"Method not found: {method}")

    try:
        result = handler(params)

        # Check for error in result
        if "error" in result and isinstance(result["error"], str):
            return create_error(request_id, -32000, result["error"])

        return create_response(request_id, result)

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return create_error(request_id, -32000, str(e))


# ═══════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main stdio loop."""
    logger.info("VAP MCP Proxy starting...")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"API Key: {'configured' if API_KEY else 'NOT SET'}")

    if not API_KEY:
        logger.warning("VAP_API_KEY not set! Set it via environment variable (VAPE_API_KEY also supported).")

    # Read line by line from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        logger.debug(f"Received: {line[:200]}...")

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            response = create_error(None, -32700, "Parse error")
            print(json.dumps(response), flush=True)
            continue

        # Process request
        response = process_request(request)

        # Send response only for requests (not notifications)
        if response is not None:
            response_json = json.dumps(response)
            logger.debug(f"Sending: {response_json[:200]}...")
            print(response_json, flush=True)


if __name__ == "__main__":
    main()
# VAP AI

Agent-native AI platform for AI Room, Media API, and Coding Plan API.

[Website](https://vapagent.com/) | [Developer Hub](https://vapagent.com/developer/) | [AI Room](https://vapagent.com/new) | [Dashboard](https://vapagent.com/new-dashboard/) | [Status](https://vapagent.com/status.html)

## Products

### AI Room

Conversational creative workspace where custom-trained AI agents use session context to create images, video, voice, and music.

- Product URL: https://vapagent.com/new
- Plans: Lite, Pro, and Max monthly Room plans

### Media API

Unified generation API for image, video, and music workflows. Current public model surfaces include Pimo AI-Video, Aura Image Turbo, and Pira V5.5.

- Developer Hub: https://vapagent.com/developer/
- API base URL: `https://api.vapagent.com/api/v1`
- Create generation: `POST /api/v1/generations`
- Authentication: product-scoped VAP Media API key
- MCP endpoint: `https://api.vapagent.com/mcp`

### Coding Plan API

OpenAI-compatible API for coding agents, IDEs, editors, and automation workflows. Powered by Nemesis Deep Coder with model ID `vap-code`.

- Developer Hub: https://vapagent.com/developer/
- Model page: https://vapagent.com/models/nemesis-deep-coder.html
- Harness guide: https://vapagent.com/integrations/coding-harnesses.html
- API base URL: `https://api.vapagent.com/v1`
- Model ID: `vap-code`
- Responses endpoint: `POST /v1/responses`
- Chat Completions endpoint: `POST /v1/chat/completions`
- Authentication: product-scoped VAP Coding Plan API key

## Start From The Product Surface

Use these entry points for new integrations:

| Need | Link |
| --- | --- |
| Use AI Room | https://vapagent.com/new |
| Generate a Media API key | https://vapagent.com/developer/?key=media#keys |
| Generate a Coding Plan API key | https://vapagent.com/developer/?key=code#keys |
| View Coding Plan API plans | https://vapagent.com/new-dashboard/?billing=code#plans |
| Read Developer Hub | https://vapagent.com/developer/ |
| See Nemesis Deep Coder | https://vapagent.com/models/nemesis-deep-coder.html |

## Media API Via MCP

This repository remains the public GitHub and MCP discovery surface for VAP Media API integrations. MCP is still supported for Claude Desktop, Claude Code, Cursor-compatible MCP clients, and other agent workflows that call VAP media tools.

Claude Desktop example:

```json
{
  "mcpServers": {
    "vap": {
      "url": "https://api.vapagent.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MEDIA_API_KEY"
      }
    }
  }
}
```

For clients that do not support headers directly, use the local proxy in `mcp/vap_mcp_proxy.py` and set `VAP_API_KEY`.

## API Examples

### Media API

```bash
curl -X POST https://api.vapagent.com/api/v1/generations \
  -H "Authorization: Bearer YOUR_MEDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"kind":"image","prompt":"a neon city at night"}'
```

### Coding Plan API

```bash
curl -X POST https://api.vapagent.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_CODING_PLAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"vap-code","messages":[{"role":"user","content":"Review this patch."}]}'
```

## Compatibility

Older `/v3/execute`, `/v3/tasks`, and MCP tool contracts remain available for existing integrations and registry clients. New builds should start from the current product contracts in Developer Hub:

- Media API: `https://api.vapagent.com/api/v1`
- Coding Plan API: `https://api.vapagent.com/v1`

## Discovery Files

- `server.json`: MCP Registry server metadata
- `mcp.json`: MCP package metadata
- `glama.json`: Glama MCP listing metadata
- `mcp/tools.json`: MCP tool schema metadata
- `mcp/vap_mcp_proxy.py`: local stdio/http proxy for MCP clients

## Links

- Website: https://vapagent.com/
- Developer Hub: https://vapagent.com/developer/
- AI Room: https://vapagent.com/new
- MCP guide: https://vapagent.com/mcp.html
- Webhooks: https://vapagent.com/webhooks.html
- Status: https://vapagent.com/status.html
- Support: support@vapagent.com

## License

MIT License. See [LICENSE](LICENSE).

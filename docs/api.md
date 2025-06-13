# Gitingest API Documentation

This document provides a comprehensive overview of the Gitingest API, designed to be useful for both human developers and LLMs integrating with the service.

## Table of Contents
- [API Overview](#api-overview)
- [API Endpoints](#api-endpoints)
- [Request Parameters](#request-parameters)
- [Response Formats](#response-formats)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Future Enhancements](#future-enhancements)

## API Overview

The Gitingest API allows programmatic access to the repository ingestion functionality, enabling developers to convert Git repositories into LLM-friendly text format without using the web interface. The API is designed to be simple, RESTful, and follows standard HTTP conventions.

### Core Value Proposition
- Programmatic access to repository ingestion
- Customizable output through query parameters
- Plain text responses optimized for LLM consumption
- Consistent with CLI and web interface functionality

### Key Features
- Repository URL processing
- File filtering via include/exclude patterns
- File size limitations
- Plain text responses for non-browser clients
- Rate limiting for fair usage

## API Endpoints

```mermaid
flowchart TD
    A(Client) --> B(GET /{repository_path})
    A --> C(POST /{repository_path})
    A --> D(GET /download/{digest_id})
    A --> E(GET /health)
    B --> F(Repository Processing)
    C --> F
    F --> G(Response Generation)
```

### Primary Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{repository_path}` | GET | Process a repository based on the path and query parameters |
| `/{repository_path}` | POST | Process a repository with form data parameters |
| `/download/{digest_id}` | GET | Download a previously generated digest file |
| `/health` | GET | Check API health status |

## Request Parameters

### Path Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `repository_path` | Path to the repository, typically in the format `owner/repo` | `tiangolo/fastapi` |
| `digest_id` | Unique identifier for a previously generated digest | `550e8400-e29b-41d4-a716-446655440000` |

### Query Parameters (GET /{repository_path})

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_size` | Integer | 243 | Maximum file size to include (slider position 0-500) |
| `pattern_type` | String | "exclude" | Type of pattern to use ("include" or "exclude") |
| `pattern` | String | "" | Pattern string to include or exclude files (comma or space separated) |
| `format` | String | "text" | Response format: "text" or "json" |

### Form Parameters (POST /{repository_path})

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_text` | String | Yes | Repository URL or path |
| `max_file_size` | Integer | Yes | Maximum file size to include (slider position 0-500) |
| `pattern_type` | String | Yes | Type of pattern to use ("include" or "exclude") |
| `pattern` | String | Yes | Pattern string to include or exclude files |

## Response Formats

The API detects whether the request is from a browser or another client (like a script or application) and returns the appropriate format:

### Browser Requests
- Content-Type: `text/html`
- HTML response with rendered template
- Interactive UI elements

### Non-Browser Requests

The API supports multiple response formats:

#### Plain Text (default)
- Content-Type: `text/plain`
- Plain text response with three sections:
  1. Summary (including token estimates)
  2. Directory tree structure
  3. File contents

#### JSON
- Content-Type: `application/json`
- JSON object with the following structure:
  ```json
  {
    "summary": "Summary text with token estimates",
    "tree": "Directory tree structure",
    "content": "File contents",
    "ingest_id": "Unique identifier for the digest"
  }
  ```

### Download Endpoint
- Content-Type: `text/plain`
- Content-Disposition: `attachment; filename={repository_name}.txt`
- Plain text file containing the full repository digest

## Rate Limiting

The API implements rate limiting to ensure fair usage and prevent abuse:

- Limit: 10 requests per minute per IP address
- Applies to: POST requests to `/{repository_path}` and `/`
- Response on limit exceeded: 429 Too Many Requests

```python
@router.post("/{full_path:path}", response_model=None)
@limiter.limit("10/minute")
async def process_catch_all(...)
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| 200 | OK | Successful request |
| 404 | Not Found | Repository or digest not found |
| 422 | Unprocessable Entity | Invalid parameters |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

Error responses include a descriptive message in the response body to help diagnose the issue.

## Examples

### Basic Repository Processing

```bash
# Process a GitHub repository with default settings
curl https://gitingest.com/tiangolo/fastapi
```

### Custom Pattern Filtering

```bash
# Include only Python files
curl "https://gitingest.com/tiangolo/fastapi?pattern_type=include&pattern=*.py"

# Exclude test files
curl "https://gitingest.com/tiangolo/fastapi?pattern_type=exclude&pattern=*/test_*"
```

### Custom File Size

```bash
# Set a larger maximum file size (slider position 300)
curl "https://gitingest.com/tiangolo/fastapi?max_size=300"
```

### Combined Parameters

```bash
# Combine multiple parameters
curl "https://gitingest.com/tiangolo/fastapi?max_size=300&pattern_type=include&pattern=*.py,*.md"
```

### Response Format Examples

```bash
# Request JSON format using query parameter
curl "https://gitingest.com/tiangolo/fastapi?format=json"

# Request JSON format using Accept header
curl -H "Accept: application/json" "https://gitingest.com/tiangolo/fastapi"
```

### Downloading a Digest

```bash
# Download a previously generated digest
curl -O https://gitingest.com/download/550e8400-e29b-41d4-a716-446655440000
```

## Best Practices

### Pattern Formatting

- Separate multiple patterns with commas or spaces
- Use standard glob patterns:
  - `*` matches any number of characters
  - `?` matches a single character
  - `[abc]` matches any character in the brackets
  - `[!abc]` matches any character not in the brackets

### File Size Considerations

The `max_size` parameter uses a logarithmic scale:
- 0: Minimum file size (1KB)
- 243: Default (50KB)
- 500: Maximum file size (100MB)

```python
def log_slider_to_size(position: int) -> int:
    """
    Convert a slider position to a file size in bytes using a logarithmic scale.
    """
    maxp = 500
    minv = math.log(1)
    maxv = math.log(102_400)
    return round(math.exp(minv + (maxv - minv) * pow(position / maxp, 1.5))) * 1024
```

### Efficient API Usage

1. **Use specific patterns**: Narrow down the files you need to reduce processing time and response size
2. **Adjust file size limits**: Set appropriate limits based on your use case
3. **Cache responses**: Store responses for frequently accessed repositories
4. **Respect rate limits**: Implement backoff strategies for rate limit errors

## Future Enhancements

The Gitingest API is under active development. Planned enhancements include:

1. **Authentication**: Support for API keys to increase rate limits and access private repositories
2. **Webhooks**: Notifications when repository digests are updated
3. **Custom Output Formats**: JSON and other structured output formats
4. **Pagination**: Support for large repositories with paginated responses
5. **Advanced Filtering**: More sophisticated file filtering options
6. **Caching Controls**: Options to use cached results or force fresh processing

### Implementation Status

The API is currently in beta. The current implementation includes:
- Basic repository processing
- Pattern filtering via query parameters
- File size limitations via query parameters
- Rate limiting
- Browser/non-browser response differentiation

Future versions will expand these capabilities based on user feedback and needs.

---

This API documentation provides a comprehensive overview of the Gitingest API, suitable for both human developers and LLMs to understand and work with the API effectively.

"""HTTP operation tools for agents."""

from typing import Any

import requests


def http_get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 10
) -> dict[str, Any]:
    """Make HTTP GET request.
    
    Args:
        url: URL to request
        headers: Optional headers to include
        timeout: Request timeout in seconds (default: 10)
        
    Returns:
        Dictionary with:
            - status_code: HTTP status code
            - text: Response text
            - headers: Response headers
            - json: Parsed JSON if response is JSON (optional)
            - error: Error message if request failed
    """
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return {"error": f"Invalid URL: {url}. URL must start with http:// or https://"}
    
    try:
        # Make the request
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout
        )
        
        # Build result
        result = {
            "status_code": response.status_code,
            "text": response.text,
            "headers": dict(response.headers)
        }
        
        # Try to parse JSON if content type suggests it
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/json' in content_type:
            try:
                result["json"] = response.json()
            except:
                # If JSON parsing fails, just include the text
                pass
        
        # Check for HTTP errors (but still return the response)
        try:
            response.raise_for_status()
        except:
            # Don't treat HTTP errors as failures - return the response
            pass
        
        return result
        
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout} seconds"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def http_post(
    url: str,
    data: Any | None = None,
    json: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 10
) -> dict[str, Any]:
    """Make HTTP POST request.
    
    Args:
        url: URL to request
        data: Form data to send (will be form-encoded)
        json: JSON data to send (will be JSON-encoded)
        headers: Optional headers to include
        timeout: Request timeout in seconds (default: 10)
        
    Returns:
        Dictionary with:
            - status_code: HTTP status code
            - text: Response text
            - headers: Response headers
            - json: Parsed JSON if response is JSON (optional)
            - error: Error message if request failed
    """
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return {"error": f"Invalid URL: {url}. URL must start with http:// or https://"}
    
    try:
        # Make the request
        response = requests.post(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout
        )
        
        # Build result
        result = {
            "status_code": response.status_code,
            "text": response.text,
            "headers": dict(response.headers)
        }
        
        # Try to parse JSON if content type suggests it
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/json' in content_type:
            try:
                result["json"] = response.json()
            except:
                # If JSON parsing fails, just include the text
                pass
        
        # Check for HTTP errors (but still return the response)
        try:
            response.raise_for_status()
        except:
            # Don't treat HTTP errors as failures - return the response
            pass
        
        return result
        
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout} seconds"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
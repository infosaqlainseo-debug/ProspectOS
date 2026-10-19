import aiohttp
import asyncio

async def validate_website(url: str, timeout_seconds: int = 5) -> bool:
    if not url:
        return False
        
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # We just need to check if it resolves and returns a basic HTTP response
            async with session.head(url, allow_redirects=True) as response:
                return response.status < 500
    except (aiohttp.ClientError, asyncio.TimeoutError):
        try:
            # Fallback to GET if HEAD is not allowed
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    return response.status < 500
        except Exception:
            return False
    except Exception:
        return False

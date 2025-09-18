"""
VirusTotal client for file hash and URL enrichment.
"""

import aiohttp
from typing import Optional, Dict, Any
import structlog
from ..core.config import get_settings


logger = structlog.get_logger()


async def vt_lookup_file(sha256: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    api_key = settings.virustotal_api_key
    if not api_key or not sha256:
        return None
    url = f"https://www.virustotal.com/api/v3/files/{sha256}"
    headers = {"x-apikey": api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    attr = data.get('data', {}).get('attributes', {})
                    stats = attr.get('last_analysis_stats', {})
                    result = {
                        'harmless': stats.get('harmless', 0),
                        'malicious': stats.get('malicious', 0),
                        'suspicious': stats.get('suspicious', 0),
                        'undetected': stats.get('undetected', 0),
                        'timeout': stats.get('timeout', 0),
                        'reputation': attr.get('reputation', 0),
                        'meaningful_name': attr.get('meaningful_name'),
                    }
                    return result
                else:
                    logger.warning("VT file lookup failed", status=resp.status)
                    return None
    except Exception as e:
        logger.error("VT file lookup error", error=str(e))
        return None



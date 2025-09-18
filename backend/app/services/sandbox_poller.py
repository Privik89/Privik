"""
Background poller to finalize CAPE sandbox analyses and persist results.
"""

import asyncio
import structlog
import aiohttp
from datetime import datetime
from typing import Dict, Any

from ..database import SessionLocal
from ..models.sandbox import SandboxAnalysis
from ..services.object_storage import ObjectStorage
from ..services.virustotal import vt_lookup_file


logger = structlog.get_logger()


async def run_cape_poller(cape_base_url: str, cape_api_token: str, interval_seconds: int = 30):
    storage = ObjectStorage()
    while True:
        try:
            db = SessionLocal()
            try:
                pending = db.query(SandboxAnalysis).filter(
                    SandboxAnalysis.analysis_completed.is_(None),
                    SandboxAnalysis.sandbox_id.isnot(None)
                ).limit(20).all()
                if not pending:
                    await asyncio.sleep(interval_seconds)
                    continue
                for a in pending:
                    try:
                        report = await _fetch_cape_report(cape_base_url, cape_api_token, a.sandbox_id)
                        if report is None:
                            continue
                        # Upload report
                        report_key = f"reports/cape/{a.sandbox_id}.json"
                        try:
                            storage.upload_json(report_key, report)
                        except Exception:
                            report_key = None
                        score = float(report.get('info', {}).get('score', 0.0))
                        verdict = 'malicious' if score >= 8 else 'suspicious' if score >= 4 else 'safe'
                        a.threat_score = min(score / 10.0, 1.0)
                        a.verdict = verdict
                        a.confidence = min(score / 10.0, 1.0)
                        a.network_connections = report.get('network', {})
                        a.process_created = report.get('behavior', {}).get('processes') if report.get('behavior') else None
                        a.artifacts_report_key = report_key
                        # Extract CAPE signatures/MITRE
                        sigs = report.get('signatures') or []
                        if isinstance(sigs, list):
                            a.ai_details = (a.ai_details or {})
                            a.ai_details['cape_signatures'] = [s.get('name') for s in sigs if isinstance(s, dict)]
                            a.ai_details['cape_mitre'] = list({t for s in sigs for t in (s.get('ttp', []) if isinstance(s, dict) else [])})
                        # Screenshots integration (if available)
                        try:
                            screenshots = await _fetch_cape_screenshots(cape_base_url, cape_api_token, a.sandbox_id)
                            keys = []
                            for idx, content in enumerate(screenshots):
                                key = f"reports/cape/{a.sandbox_id}/screenshots/{idx}.png"
                                try:
                                    storage.upload_bytes(key, content, content_type='image/png')
                                    keys.append(key)
                                except Exception:
                                    continue
                            a.artifacts_screenshots = keys
                        except Exception:
                            a.artifacts_screenshots = []
                        # VirusTotal enrichment if file hash available
                        try:
                            if a.file_hash:
                                vt = await vt_lookup_file(a.file_hash)
                                if vt:
                                    a.ai_details = (a.ai_details or {})
                                    a.ai_details['virustotal'] = vt
                        except Exception:
                            pass
                        a.analysis_completed = datetime.utcnow()
                        db.commit()
                        logger.info("Sandbox analysis finalized", sandbox_id=a.sandbox_id, verdict=verdict)
                    except Exception as e:
                        logger.error("Poller finalize error", sandbox_id=a.sandbox_id, error=str(e))
                        db.rollback()
                await asyncio.sleep(1)
            finally:
                db.close()
        except Exception as e:
            logger.error("Poller loop error", error=str(e))
            await asyncio.sleep(interval_seconds)


async def _fetch_cape_report(cape_base_url: str, cape_api_token: str, task_id: str):
    if not cape_base_url:
        return None
    params = {"token": cape_api_token} if cape_api_token else {}
    url = f"{cape_base_url}/tasks/report/{task_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            return None


async def _fetch_cape_screenshots(cape_base_url: str, cape_api_token: str, task_id: str):
    """Fetch screenshots as raw bytes list if CAPE exposes them under a standard path.
    This is best-effort; not all CAPE setups expose direct screenshot download.
    """
    try:
        params = {"token": cape_api_token} if cape_api_token else {}
        # Attempt list endpoint; if unavailable, return empty.
        list_url = f"{cape_base_url}/tasks/screenshots/{task_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(list_url, params=params) as resp:
                if resp.status != 200:
                    return []
                listing = await resp.json()
                files = listing.get('files', []) if isinstance(listing, dict) else []
        images = []
        async with aiohttp.ClientSession() as session:
            for fname in files:
                raw_url = f"{cape_base_url}/tasks/screenshots/{task_id}/{fname}"
                async with session.get(raw_url, params=params) as r2:
                    if r2.status == 200:
                        images.append(await r2.read())
        return images
    except Exception:
        return []



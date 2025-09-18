"""
Training Logger Service
Captures inputs/outputs from email/link/behavior analysis for future ML training
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, Optional
import structlog


logger = structlog.get_logger()


class TrainingLogger:
    """Simple JSONL file-based training data logger.

    For Phase 1, we store rich input/output records that can be used to
    bootstrap supervised and self-supervised training later.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.base_dir = self.config.get("storage_path", "./training_data")
        self.enabled = self.config.get("enabled", True)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_daily_file(self, category: str) -> str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        dir_path = os.path.join(self.base_dir, category)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"{date_str}.jsonl")

    def _write_jsonl(self, path: str, record: Dict[str, Any]):
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("Training log write failed", path=path, error=str(e))

    def log_email_sample(
        self,
        email_input: Dict[str, Any],
        ai_output: Dict[str, Any],
        combined_score: Optional[float] = None,
        action: Optional[str] = None,
    ):
        if not self.enabled:
            return
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "email",
                "input": {
                    # Only store non-sensitive subset; extend as needed
                    "message_id": email_input.get("message_id"),
                    "subject": email_input.get("subject"),
                    "sender": email_input.get("sender"),
                    "recipients": email_input.get("recipients"),
                    "body_text": email_input.get("body_text"),
                    "has_html": bool(email_input.get("body_html")),
                    "attachments_meta": [
                        {
                            "filename": a.get("filename"),
                            "mime_type": a.get("mime_type") or a.get("content_type"),
                            "size": a.get("size") or a.get("file_size"),
                        }
                        for a in (email_input.get("attachments") or [])
                    ],
                },
                "output": {
                    "threat_type": ai_output.get("threat_type"),
                    "confidence": ai_output.get("confidence"),
                    "threat_score": ai_output.get("threat_score"),
                    "indicators": ai_output.get("indicators"),
                    "model_version": ai_output.get("model_version"),
                    "combined_score": combined_score,
                    "final_action": action,
                },
            }

            # Optional label override if provided (Phase 5 feedback loop)
            if "label" in ai_output:
                record["label"] = ai_output["label"]

            path = self._get_daily_file("emails")
            self._write_jsonl(path, record)
        except Exception as e:
            logger.error("Training email log failed", error=str(e))

    def log_link_sample(
        self,
        url_input: Dict[str, Any],
        ai_output: Dict[str, Any],
        action: Optional[str] = None,
    ):
        if not self.enabled:
            return
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "link",
                "input": url_input,
                "output": ai_output | {"final_action": action},
            }
            path = self._get_daily_file("links")
            self._write_jsonl(path, record)
        except Exception as e:
            logger.error("Training link log failed", error=str(e))

    def log_behavior_sample(
        self,
        behavior_input: Dict[str, Any],
        ai_output: Dict[str, Any],
        action: Optional[str] = None,
    ):
        if not self.enabled:
            return
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "behavior",
                "input": behavior_input,
                "output": ai_output | {"final_action": action},
            }
            path = self._get_daily_file("behaviors")
            self._write_jsonl(path, record)
        except Exception as e:
            logger.error("Training behavior log failed", error=str(e))



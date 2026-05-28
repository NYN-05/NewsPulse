import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from config.settings import get

logger = logging.getLogger(__name__)


class AlertEngine:
    def __init__(self):
        self.webhook_urls = get("alerts.webhooks", {})
        self._alert_log = set()
        self._load_sent()

    def _load_sent(self):
        log_path = os.path.join("output", "logs", "alert_log.json")
        try:
            if os.path.exists(log_path):
                with open(log_path) as f:
                    self._alert_log = set(json.load(f))
        except Exception:
            self._alert_log = set()

    def _save_sent(self):
        log_path = os.path.join("output", "logs", "alert_log.json")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(list(self._alert_log)[-500:], f)

    def send_alert(self, title: str, message: str, channel: str = "telegram", link: str = ""):
        alert_key = f"{title[:50]}:{datetime.now().hour}"
        if alert_key in self._alert_log:
            return
        text = f"*{title}*\n{message[:500]}"
        if link:
            text += f"\n{link}"
        if channel == "telegram" and self.webhook_urls.get("telegram"):
            self._send_telegram(text)
        elif channel == "slack" and self.webhook_urls.get("slack"):
            self._send_slack(text)
        elif channel == "discord" and self.webhook_urls.get("discord"):
            self._send_discord(text)
        self._alert_log.add(alert_key)
        self._save_sent()
        logger.info("Alert sent [%s]: %s", channel, title[:60])

    def _send_telegram(self, text: str):
        url = self.webhook_urls["telegram"]
        try:
            requests.post(url, json={"text": text, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            logger.warning("Telegram alert failed: %s", e)

    def _send_slack(self, text: str):
        url = self.webhook_urls["slack"]
        try:
            requests.post(url, json={"text": text}, timeout=10)
        except Exception as e:
            logger.warning("Slack alert failed: %s", e)

    def _send_discord(self, text: str):
        url = self.webhook_urls["discord"]
        try:
            requests.post(url, json={"content": text}, timeout=10)
        except Exception as e:
            logger.warning("Discord alert failed: %s", e)

    def check_breaking_events(self, events: List[Dict]):
        for event in events[:3]:
            keyword = event.get("keyword") or event.get("entity", "unknown")
            score = event.get("score", 0)
            if score >= get("alerts.breaking_threshold", 20):
                self.send_alert(
                    title=f"Breaking: {keyword}",
                    message=f"Burst score: {score}, Recent mentions: {event.get('recent_count', 0)}",
                    channel="telegram",
                )

    def check_virality_alerts(self, df):
        if "virality_score" not in df.columns:
            return
        threshold = get("alerts.virality_threshold", 0.8)
        viral = df[df["virality_score"] >= threshold].head(5)
        for _, row in viral.iterrows():
            self.send_alert(
                title=f"Viral: {row.get('title', '')[:80]}",
                message=f"Virality: {row['virality_score']:.2f} | Source: {row.get('source', '')}",
                link=row.get("link", ""),
            )

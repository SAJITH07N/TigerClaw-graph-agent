"""
Groq API Client for Dynamic Fraud Investigation Narrative Synthesis.
Provides high-speed LLM generation using LLaMA-3.3-70B / LLaMA-3.1-8B models on Groq.
Falls back seamlessly to local deterministic GraphRAG templates when offline or without API key.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GroqClient:
    """Lightweight, resilient Groq API client with zero extra heavyweight dependencies."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 6.0,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "").strip()
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.timeout = timeout
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def is_available(self) -> bool:
        """Returns True if a valid-looking Groq API key is present."""
        return bool(self.api_key and len(self.api_key) > 8)

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic status for UI and health checks."""
        return {
            "provider": "Groq Cloud Inference",
            "model": self.model,
            "configured": self.is_available,
            "mode": "Active Live LLM (Groq)" if self.is_available else "Local Deterministic GraphRAG Fallback",
        }

    def generate_investigation_narrative(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Synthesizes an executive fraud investigation summary using Groq LLM.
        Returns None if API key is not configured or if any network error occurs.
        """
        if not self.is_available:
            return None

        case_id = context.get("case_id", "CASE")
        typology = context.get("typology_name", "Unknown Typology")
        risk_level = context.get("risk_level", "medium").upper()
        confidence = context.get("composite_confidence", 0.0)
        entities = context.get("entities", {})
        actions = context.get("actions", [])
        sar_status = "MANDATORY FILING (31 CFR § 1020.320)" if context.get("has_sar") else "NOT REQUIRED (Benign/Sub-threshold)"

        actions_str = ", ".join([f"{a.get('action_type')} [{a.get('permission_level')}]" for a in actions]) or "None"

        system_prompt = (
            "You are an elite Senior Financial Crime & Anti-Money Laundering (AML) Investigator "
            "at a Tier-1 Bank. Analyze the provided graph intelligence findings and write a concise, "
            "professional 2-paragraph Executive Investigation Summary. Ground your analysis strictly "
            "in the graph evidence, 4-pillar uncertainty metrics, and regulatory mandates."
        )

        user_content = f"""
Case Identifier: {case_id}
Detected Typology: {typology}
Risk Assessment: {risk_level} (Composite Confidence: {confidence:.2%})
Entities Involved:
- Target Accounts: {', '.join(entities.get('accounts', []))}
- Associated Cards: {', '.join(entities.get('cards', []))}
- Hardware Devices: {', '.join(entities.get('devices', []))}
- IP/Addresses: {', '.join(entities.get('addresses', []))}
Next-Best Actions: {actions_str}
FinCEN SAR Status: {sar_status}
Key Evidence: {context.get('what_changed', 'Initial multi-hop neighborhood traversal completed.')}

Draft a concise, rigorous 2-paragraph executive narrative for the Chief Risk Officer and BSA Compliance Officer.
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
            "max_tokens": 400,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    logger.info("Successfully generated Groq dynamic narrative for %s via %s", case_id, self.model)
                    return content.strip()
            else:
                logger.warning("Groq API returned status %d: %s", response.status_code, response.text[:200])
        except Exception as e:
            logger.warning("Groq API call skipped or failed (%s). Falling back to grounded template.", e)

        return None

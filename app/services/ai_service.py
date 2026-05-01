"""
AI Service — Voice transcript parsing & unknown product price estimation.
Uses Groq (Llama-3) via OpenAI-compatible endpoint.

Key responsibilities:
  1. Parse raw voice transcript → structured invoice JSON
  2. Estimate price/GST for products NOT in the database
  3. Return confidence scores for human review
"""
import json
import re
import requests
from flask import current_app
from typing import Any


# ─────────────────────────────────────────────────────────────
# PROMPT TEMPLATES
# ─────────────────────────────────────────────────────────────

CONVERSATION_SYSTEM_PROMPT = """You are VoiceInvoice AI, a professional billing assistant for Indian businesses.

You exclusively communicate in English (en-IN).

RESPONSE FORMAT — always reply with valid JSON only:

1. CHAT MODE — greetings, questions, small talk.
{
  "mode": "chat",
  "reply": "Hello! How can I help you today? 😊"
}

2. INVOICE MODE — ONLY when the user wants to create a bill/invoice.
{
  "mode": "invoice",
  "reply": "Sure! I'm preparing the invoice for you 👍",
  "data": {
    "customer_name": "Person Name",
    "customer_company": "Company Name",
    "customer_store": "Branch/Store",
    "customer_gst": null,
    "customer_address": null,
    "supply_type": "intra",
    "confidence": 0.95,
    "items": [
      {
        "product_name": "Item",
        "quantity": 1,
        "unit": "piece",
        "unit_price": null
      }
    ]
  }
}

PARSING RULES:
- If a user says "bill for BIRYANI" and no other items are mentioned, BIRYANI is a PRODUCT.
- Extract three distinct customer fields:
  1. "customer_company": The business/firm name (e.g., "ABC Tech", "Kirana Store").
  2. "customer_store": The specific branch or location (e.g., "Redhills", "Main Branch").
  3. "customer_name": The individual person's name (e.g., "Rahul", "Priya").
- Default these fields to null if NOT explicitly mentioned. DO NOT use "Generic User".
- Extract quantities and units if mentioned. Default quantity is 1.
- "unit_price" should be null unless explicitly mentioned.
- BE SMART: Distinguish between products, person names, and company names based on context.
"""

PRICE_ESTIMATE_PROMPT = """You are an expert Indian market pricing specialist. 
Estimate the unit price and GST details for the following product.

RULES:
- Provide a realistic Indian market price in INR (₹)
- Choose the correct GST rate: 0%, 5%, 12%, 18%, or 28%
- Provide a relevant HSN code (8-digit for goods, SAC for services)
- Base your estimate on current Indian market prices (2024)
- Never say "I don't know" — always provide your best estimate
- Set ai_estimated: true always

Product name: {product_name}
Context (company type): {company_context}
Quantity context: {quantity} {unit}

Respond ONLY with valid JSON. No explanations.

{
  "unit_price": 1499.00,
  "gst_rate": 18.0,
  "hsn_code": "8471",
  "confidence": 0.85,
  "ai_estimated": true,
  "reasoning": "Brief one-line reasoning"
}
"""


class AIService:
    """Handles all AI interactions with Groq."""

    def __init__(self):
        self._api_key = None
        self._url = "https://api.groq.com/openai/v1/chat/completions"

    def _clean_keys(self, obj: Any) -> Any:
        """Recursively clean whitespace and literal quotes from dictionary keys."""
        if isinstance(obj, dict):
            return {
                key.strip().strip('"').strip("'"): self._clean_keys(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [self._clean_keys(item) for item in obj]
        return obj

    def _call_groq(self, prompt: str, system_prompt: str = None, max_tokens: int = 2048) -> dict:
        """Helper to make a direct API call to Groq with retries."""
        import time
        api_key = current_app.config.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Use a high-quota "instant" model by default for reliability
        model = current_app.config.get("AI_MODEL", "llama-3.1-8b-instant")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        # Model pool for fallback if the primary hits a rate limit
        fallback_models = ["mixtral-8x7b-32768", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        
        max_retries = 3
        retry_delay = 1 # Start faster for instant models

        for attempt in range(max_retries + 1):
            try:
                # If this is a retry, try a different model from the pool as fallback
                if attempt > 0:
                    payload["model"] = fallback_models[attempt % len(fallback_models)]
                    print(f"Fallback active: Switching to model {payload['model']}...")

                response = requests.post(self._url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 429:
                    if attempt < max_retries:
                        print(f"Groq Rate Limit (429) for {payload['model']}. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                
                response.raise_for_status()
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]
                
                # Clean accidental markdown and normalize JSON
                clean_raw = re.sub(r"^```json\s*|```$", "", raw_content, flags=re.MULTILINE).strip()
                parsed = json.loads(clean_raw)
                return self._clean_keys(parsed)
            except Exception as e:
                # Handle connection errors or other timeouts by retrying
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                print(f"Groq API Error: {e}")
                raise e


    def parse_voice_transcript(self, transcript: str) -> dict[str, Any]:
        """Convert raw voice/text into structured invoice data or chat reply."""
        try:
            result = self._call_groq(prompt=transcript, system_prompt=CONVERSATION_SYSTEM_PROMPT)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": f"AI processing failed: {str(e)}", "data": None}

    def estimate_product_price(
        self,
        product_name: str,
        company_context: str = "general retail",
        quantity: float = 1,
        unit: str = "piece",
    ) -> dict[str, Any]:
        """Estimate price for an unknown product."""
        prompt = PRICE_ESTIMATE_PROMPT.replace("{product_name}", product_name) \
            .replace("{company_context}", company_context) \
            .replace("{quantity}", str(quantity)) \
            .replace("{unit}", unit)

        try:
            result = self._call_groq(prompt, max_tokens=512)
            return {"success": True, "data": result}
        except Exception:
            # Fallback: return a conservative estimate rather than failing
            return {
                "success": True,
                "data": {
                    "unit_price": 999.00,
                    "gst_rate": 18.0,
                    "hsn_code": "9999",
                    "confidence": 0.3,
                    "ai_estimated": True,
                    "reasoning": "Fallback estimate — AI request failed",
                }
            }


# Module-level singleton
ai_service = AIService()

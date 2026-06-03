import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

def analyze_report(report_text, filename="unknown"):
    """
    Send report text to OpenAI and extract structured defect data.
    Returns a dict with building info, defects, and executive summary.
    """
    text_sample = report_text[:3000]

    prompt = f"""You are a senior building inspector at SECO Group, an independent
technical control and engineering firm in Luxembourg.

Analyze this building inspection report and extract all defects found.
Return ONLY a valid JSON object with this exact structure, no other text:

{{
  "building_name": "name or description of building",
  "location": "address if found, otherwise Unknown",
  "inspector": "inspector name if found, otherwise Unknown",
  "date": "inspection date if found, otherwise Unknown",
  "overall_risk": "CRITICAL or HIGH or MEDIUM or LOW",
  "defects": [
    {{
      "severity": "CRITICAL or HIGH or MEDIUM or LOW",
      "title": "short defect title",
      "description": "what was observed",
      "recommendation": "what action should be taken",
      "urgency": "Immediate or Within 7 days or Within 30 days or Next maintenance cycle"
    }}
  ],
  "executive_summary": "2-3 sentences summarising findings for a non-technical manager"
}}

REPORT TEXT:
{text_sample}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def severity_rank(severity):
    """Return numeric rank for sorting (lower = more severe)."""
    return {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}.get(severity, 5)

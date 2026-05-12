# services/workflow_b.py

import os
import json
from openai import OpenAI
from prompts.evaluator_system import EVALUATOR_SYSTEM_PROMPT
from motor import MotorClient

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def build_evaluation_prompt(patient, turns, submission):
    transcript = "\n".join([
        f"Student: {t['student_message']}\nPatient: {t['patient_response']}"
        for t in turns
    ])

    return f"""
ACTUAL PATIENT DATA:
{json.dumps(patient, indent=2)}

CONVERSATION TRANSCRIPT:
{transcript}

STUDENT SUBMISSION:
Suspected disease: {submission['suspected_disease']}
Reasoning: {submission['reasoning']}
Treatment plan: {submission['treatment']}

Return ONLY valid JSON.
"""


async def evaluate_submission(patient, turns, submission):
    """
    Production evaluator using Groq
    """

    prompt = build_evaluation_prompt(patient, turns, submission)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )

        raw = response.choices[0].message.content.strip()

        # Clean JSON (LLMs sometimes wrap it)
        clean = raw.replace("```json", "").replace("```", "").strip()

        return json.loads(clean)

    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "raw_response": raw if 'raw' in locals() else None
        }
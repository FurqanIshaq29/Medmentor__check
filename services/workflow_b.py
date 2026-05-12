# services/workflow_b.py

import os
import json
from openai import OpenAI
from prompts.evaluator_system import EVALUATOR_SYSTEM_PROMPT
from motor.motor_asyncio import AsyncIOMotorClient
import re

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
def normalize_diagnosis(text: str) -> str:
    text = text.lower().strip()

    # remove brackets
    text = re.sub(r"[()]", " ", text)

    # standardize spaces
    text = re.sub(r"\s+", " ", text)

    return text


def extract_diabetes_type(text: str):
    text = text.lower()

    if re.search(r"type\s*1|type\s*i\b", text):
        return 1

    if re.search(r"type\s*2|type\s*ii\b", text):
        return 2

    return None


def is_diagnosis_correct(student_answer: str, actual_answer: str):
    student = student_answer.lower()
    actual = actual_answer.lower()

    # Extract diabetes type numbers
    student_has_1 = "1" in student
    student_has_2 = "2" in student

    actual_has_1 = "1" in actual
    actual_has_2 = "2" in actual

    # If actual diagnosis is Type 1
    if actual_has_1:
        return student_has_1

    # If actual diagnosis is Type 2
    if actual_has_2:
        return student_has_2

    # fallback generic text match
    return student.strip() in actual.strip() or actual.strip() in student.strip()

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

        result = json.loads(clean)

        student_diagnosis = submission.get("suspected_disease", "")
        correct_diagnosis = patient.get("diagnosis", "")

        diagnosis_correct = is_diagnosis_correct(
            student_diagnosis,
            correct_diagnosis
        )

        # Force deterministic correctness
        result["diagnosis_result"] = {
            "your_diagnosis": student_diagnosis,
            "correct_diagnosis": correct_diagnosis,
            "is_correct": diagnosis_correct
        }

        return result

    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "raw_response": raw if 'raw' in locals() else None
        }
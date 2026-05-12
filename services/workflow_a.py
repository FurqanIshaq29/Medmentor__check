# services/workflow_a.py

import os
from openai import OpenAI
from prompts.patient_system import build_patient_system_prompt

groq_key = os.getenv("GROQ_API_KEY")

if not groq_key:
    raise ValueError("GROQ_API_KEY is missing")

client = OpenAI(
    api_key=groq_key,
    base_url="https://api.groq.com/openai/v1"
)


# In workflow_a.py
def build_messages_from_turns(turns: list, new_message: str) -> list:
    # Use last 20 turns for context — store all in DB
    context = turns[-20:] if len(turns) > 20 else turns

    messages = []
    if len(turns) > 20:
        # Optional: single summarising injection for older context
        messages.append({
            "role": "user",
            "content": f"Earlier in this consultation the student asked about: "
                      f"{', '.join(t['student_message'][:40] for t in turns[:-20][:5])}"
        })
        messages.append({
            "role": "assistant",
            "content": "I understand, continuing our conversation."
        })

    for t in context:
        messages.append({"role": "user",      "content": t["student_message"]})
        messages.append({"role": "assistant", "content": t["patient_response"]})

    messages.append({"role": "user", "content": new_message})
    return messages


async def get_patient_response(patient, history_turns, new_message):
    """
    Production Virtual Patient using Groq
    """

    msg = new_message.lower()
    vitals = patient.get("vital_signs", {})

    # =========================
    # 🔒 HARD DETERMINISTIC LAYER
    # =========================
    if "weight" in msg:
        return f"I weigh around {vitals.get('weight_kg')} kg."

    if "height" in msg:
        return f"I'm about {vitals.get('height_cm')} cm tall."

    if "temperature" in msg or "fever" in msg:
        return f"It was around {vitals.get('temperature_celsius')}°C."

    if "blood pressure" in msg:
        return f"I think it was {vitals.get('blood_pressure')}."

    if "pulse" in msg or "heart rate" in msg:
        return f"My pulse was around {vitals.get('pulse_rate')}."

    # =========================
    # 🤖 LLM FALLBACK
    # =========================

    system_prompt = build_patient_system_prompt(patient)

    messages = [{"role": "system", "content": system_prompt}]
    messages += build_messages_from_turns(
        history_turns,
        new_message
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.3,   # 🔥 reduced for stability
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"[LLM Error: {str(e)}]"
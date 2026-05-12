import os
import json

from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

PATIENTS_DIR = os.getenv("PATIENTS_DIR", "./patients")

if not os.path.exists(PATIENTS_DIR):
    print(f"Warning: patients directory not found: {PATIENTS_DIR}")


@lru_cache(maxsize=100)
def load_patient(case_id: str) -> dict:

    path = os.path.join(
        PATIENTS_DIR,
        f"{case_id}.json"
    )

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Patient case '{case_id}' not found in {PATIENTS_DIR}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_all_cases() -> list:

    cases = []

    if not os.path.exists(PATIENTS_DIR):
        return []

    for filename in sorted(os.listdir(PATIENTS_DIR)):

        if not filename.endswith(".json"):
            continue

        case_id = filename.replace(".json", "")

        try:

            data = load_patient(case_id)

            meta = data.get("metadata", {})
            demo = data.get("demographics", {})

            cases.append({
                "case_id": case_id,
                "name": demo.get("name", "Unknown"),
                "age": demo.get("age", 0),
                "gender": demo.get("gender", "Unknown"),
                "disease_category": meta.get(
                    "disease",
                    "General Medicine"
                ),
                "difficulty": data.get(
                    "difficulty",
                    "medium"
                )
            })

        except Exception as e:

            print(
                f"Warning: could not load {filename}: {e}"
            )

    return cases
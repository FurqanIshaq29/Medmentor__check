import os, json
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()
PATIENTS_DIR = os.getenv("PATIENTS_DIR", "./patients")

@lru_cache(maxsize=100)
def load_patient(case_id: str) -> dict:
    path = os.path.join(PATIENTS_DIR, f"{case_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Patient case '{case_id}' not found in {PATIENTS_DIR}")
    with open(path, "r") as f:
        return json.load(f)

def list_all_cases() -> list[dict]:
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
                "disease_category": meta.get("disease", "General Medicine"),
                "difficulty": data.get("difficulty", "medium")
            })
        except Exception as e:
            print(f"Warning: could not load {filename}: {e}")
    return cases

"""# loads JSON, validates structure
# services/patient_loader.py
import json, os
from functools import lru_cache

PATIENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "patients")

@lru_cache(maxsize=50)
def load(case_id: str) -> dict:
    path = os.path.join(PATIENTS_DIR, f"{case_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Case {case_id} not found")
    with open(path) as f:
        return json.load(f)

def list_cases() -> list[dict]:
    cases = []
    for filename in os.listdir(PATIENTS_DIR):
        if filename.endswith(".json"):
            case_id = filename.replace(".json", "")
            data = load(case_id)
            cases.append({
                "case_id": case_id,
                "disease_hint": data["metadata"].get("disease", "Unknown"),
                "age": data["demographics"]["age"],
                "gender": data["demographics"]["gender"],
                "difficulty": "medium"  # you can add this field to your JSON
            })
    return cases


"""
from fastapi import FastAPI, HTTPException
from jsonschema import validate, ValidationError
import json

app = FastAPI(title="Ñ / NOR Canonical Intent API", version="1.0.0")

with open("schema.json") as f:
    SCHEMA = json.load(f)

def nor(x: bool, y: bool) -> bool:
    return (not x) and (not y)

def evaluate(intent: dict, context: dict) -> bool:
    def eval_node(node):
        if isinstance(node, str):
            return bool(context.get(node, False))
        if isinstance(node, dict) and "nor" in node:
            left, right = node["nor"]
            return nor(eval_node(left), eval_node(right))
        raise ValueError("Invalid Ñ structure")
    return eval_node(intent)

@app.post("/v1/validate")
def validate_intent(intent: dict):
    try:
        validate(instance=intent, schema=SCHEMA)
        return {"valid": True}
    except ValidationError as e:
        return {"valid": False, "error": e.message}

@app.post("/v1/evaluate")
def evaluate_intent(payload: dict):
    intent = payload.get("intent")
    context = payload.get("context", {})
    if intent is None:
        raise HTTPException(status_code=400, detail="Missing intent")

    try:
        validate(instance=intent, schema=SCHEMA)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)

    return {"value": evaluate(intent, context)}

@app.post("/v1/ui/toggle")
def ui_toggle(data: dict):
    action = data["actionAtom"]
    perm = data["permissionAtom"]
    toggle = bool(data["toggleValue"])

    intent = {"nor": [action, perm]}

    # Quiescent context (fixes the masking defect when v(a)=1)
    context = {action: False, perm: toggle}

    return {
        "intent": intent,
        "quiescentContext": context,
        "value": evaluate(intent, context),
    }

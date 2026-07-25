import json
import google.generativeai as genai
from pydantic import BaseModel, ValidationError

# ---------- Gemini ----------
genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel("gemini-2.5-flash")

# ---------- Constraints ----------

MAX_STEPS = 6

ALLOWED_ACTIONS = [
    "check_policy",
    "check_coverage",
    "check_documents",
    "check_fraud",
    "approve",
    "reject",
    "investigate"
]

# ---------- Schema ----------

class AgentStep(BaseModel):
    thought: str
    action: str
    final_answer: str

# ---------- Tools ----------

def execute_tool(action, claim):

    if action == "check_policy":
        return claim["policy_active"]

    if action == "check_coverage":
        return claim["claim_covered"]

    if action == "check_documents":
        return claim["documents_complete"]

    if action == "check_fraud":
        return claim["fraud_score"]

    if action == "approve":
        return "Approve Claim"

    if action == "reject":
        return "Reject Claim"

    if action == "investigate":
        return "Send Claim for Investigation"

    return "Invalid Tool"

# ---------- Agent ----------

def constrained_agent(claim):

    history = ""

    for step in range(MAX_STEPS):

        prompt = f"""
You are an insurance AI Agent.

Think step by step.

Allowed actions only:

{ALLOWED_ACTIONS}

Return ONLY JSON.

Schema:

{{
"thought":"",
"action":"",
"final_answer":""
}}

Claim:

{claim}

Previous observations:

{history}
"""

        response = model.generate_content(prompt)

        try:

            data = AgentStep.model_validate_json(response.text)

        except ValidationError:

            return "Schema Validation Failed"

        if data.action not in ALLOWED_ACTIONS:

            return "Tool Not Allowed"

        observation = execute_tool(data.action, claim)

        history += f"\nAction:{data.action}\nObservation:{observation}\n"

        if data.final_answer != "":

            return data.final_answer

    return "Escalate to Human Agent"

# ---------- Read JSON ----------

with open("claims.json", "r") as file:

    claims = json.load(file)

# ---------- Run ----------

for claim in claims:

    result = constrained_agent(claim)

    print("="*50)
    print("Claim:", claim["id"])
    print(result)
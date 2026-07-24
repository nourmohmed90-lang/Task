import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def classify_claim(claim):

    prompt = f"""
You are an insurance claim routing agent.

Your task is ONLY to classify the claim.

Return ONLY ONE of these labels:

APPROVE
REJECT
REQUEST_DOCUMENTS
INVESTIGATE

Do not explain.
Do not write anything else.

Claim:
{json.dumps(claim, indent=2)}
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    return response.text.strip()

def approve(claim):
    return "Claim Approved."
    
def reject(claim):
    return "Claim Rejected."

def request_documents(claim):
    return "Please upload the missing documents."

def investigate(claim):
    return "Claim sent for manual investigation."

actions = {
    "APPROVE": approve,
    "REJECT": reject,
    "REQUEST_DOCUMENTS": request_documents,
    "INVESTIGATE": investigate
}

with open(r"C:\Users\nourm\Downloads\Documents\claims.json", "r") as file:
    claims = json.load(file)

for claim in claims:

    route = classify_claim(claim).strip().upper()
    if route not in actions:
        print(f"Invalid route returned: {route}")
        continue

    result = actions[route](claim)

    print("-------------------")
    print("Claim:", claim["id"])
    print("Route:", route)
    print("Decision:", result)    

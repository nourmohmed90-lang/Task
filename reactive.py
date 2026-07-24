import json
def reactive_agent(policy_active,
                         claim_covered,
                         documents_complete,
                         fraud_score,
                         claim_amount):

    if not policy_active:
        return "Reject Claim: Policy is inactive."

    if not claim_covered:
        return "Reject Claim: Damage is not covered."

    if not documents_complete:
        return "Request Additional Documents."

    if fraud_score > 80:
        return "Send Claim for Investigation."

    if claim_amount <= 5000:
        return "Approve Claim."

    return "Send Claim for Investigation."

with open(r"C:\Users\nourm\Downloads\Documents\claims.json", "r") as file:
    claims = json.load(file)

for claim in claims:

    result = reactive_agent(
        claim["policy_active"],
        claim["claim_covered"],
        claim["documents_complete"],
        claim["fraud_score"],
        claim["claim_amount"]
    )

    print("-" * 20)
    print(f"Claim ID: {claim['id']}")
    print(f"Decision: {result}")


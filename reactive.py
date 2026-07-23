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

policy_active = input("Is the policy active? (yes/no): ").lower() == "yes"
claim_covered = input("Is the claim covered? (yes/no): ").lower() == "yes"
documents_complete = input("Are all required documents submitted? (yes/no): ").lower() == "yes"
fraud_score = int(input("Enter fraud risk score (0-100): "))
claim_amount = float(input("Enter claim amount ($): "))

result = reactive_agent(
    policy_active,
    claim_covered,
    documents_complete,
    fraud_score,
    claim_amount
)

print("\nDecision:", result)
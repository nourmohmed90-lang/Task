"""
UNCONSTRAINED REACT AGENT - INSURANCE CLAIM ASSESSMENT
======================================================
Architecture 2 of 4.

By design this agent has:
    NO output schema
    NO tool allow-list
    NO MAX_STEPS budget

The model chooses its own reasoning, its own tool calls, and its own
stopping point. This file is supposed to be the one that misbehaves.

How to run:
    pip install google-generativeai python-dotenv
    Create a file called .env next to this file containing:
        GEMINI_API_KEY=your_key_here
    python agent.py

Model / provider: Google Gemini (gemini-2.0-flash), free tier.
"""

import os
import re
import time
import json

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"


# =====================================================================
# FAKE DATABASE
# Shared with the other three agents. Do not change the shapes here
# without telling the rest of the team.
# =====================================================================

CLAIMS = {
    "CLM-001": {
        "claim_id": "CLM-001",
        "customer_id": "CUST-77",
        "policy_id": "POL-500",
        "accident_type": "MINOR_COLLISION",
        "claim_amount": 4500,
        "documents_submitted": ["photos", "police_report", "repair_estimate"],
        "date": "2026-07-18",
    },
    "CLM-002": {
        "claim_id": "CLM-002",
        "customer_id": "CUST-81",
        "policy_id": "POL-512",
        "accident_type": "MAJOR_COLLISION",
        "claim_amount": 38000,
        "documents_submitted": ["photos"],
        "date": "2026-07-20",
    },
    "CLM-003": {
        "claim_id": "CLM-003",
        "customer_id": "CUST-93",
        "policy_id": "POL-530",
        "accident_type": "THEFT",
        "claim_amount": 92000,
        "documents_submitted": ["police_report", "ownership_proof"],
        "date": "2026-07-21",
    },
    "CLM-004": {
        "claim_id": "CLM-004",
        "customer_id": "CUST-60",
        "policy_id": "POL-544",
        "accident_type": "FLOOD_DAMAGE",
        "claim_amount": 15000,
        "documents_submitted": ["photos", "repair_estimate"],
        "date": "2026-07-22",
    },
}


POLICIES = {
    "POL-500": {
        "policy_id": "POL-500",
        "status": "ACTIVE",
        "covered_types": ["MINOR_COLLISION", "MAJOR_COLLISION", "THEFT"],
        "coverage_limit": 50000,
        "deductible": 500,
    },
    "POL-512": {
        "policy_id": "POL-512",
        "status": "ACTIVE",
        "covered_types": ["MINOR_COLLISION", "MAJOR_COLLISION"],
        "coverage_limit": 60000,
        "deductible": 1000,
    },
    "POL-530": {
        "policy_id": "POL-530",
        "status": "ACTIVE",
        "covered_types": ["THEFT", "MINOR_COLLISION"],
        "coverage_limit": 100000,
        "deductible": 2000,
    },
    "POL-544": {
        "policy_id": "POL-544",
        "status": "ACTIVE",
        "covered_types": ["MINOR_COLLISION", "MAJOR_COLLISION"],
        "coverage_limit": 40000,
        "deductible": 750,
    },
}


CUSTOMERS = {
    "CUST-77": {
        "customer_id": "CUST-77",
        "total_claims": 1,
        "rejected_claims": 0,
        "fraud_risk_score": 8,
        "customer_since": "2019",
    },
    "CUST-81": {
        "customer_id": "CUST-81",
        "total_claims": 3,
        "rejected_claims": 0,
        "fraud_risk_score": 22,
        "customer_since": "2021",
    },
    "CUST-93": {
        "customer_id": "CUST-93",
        "total_claims": 6,
        "rejected_claims": 3,
        "fraud_risk_score": 79,
        "customer_since": "2024",
    },
    "CUST-60": {
        "customer_id": "CUST-60",
        "total_claims": 2,
        "rejected_claims": 0,
        "fraud_risk_score": 15,
        "customer_since": "2017",
    },
}


REQUIRED_DOCUMENTS = {
    "MINOR_COLLISION": ["photos", "repair_estimate"],
    "MAJOR_COLLISION": ["photos", "police_report", "repair_estimate", "medical_report"],
    "THEFT": ["police_report", "ownership_proof"],
    "FLOOD_DAMAGE": ["photos", "weather_report", "repair_estimate"],
}


# =====================================================================
# TOOLS
# Four tools that read data, and four tools that take a decision.
# =====================================================================

def get_claim(claim_id):
    """Look up a claim. This is the entry point for everything else,
    because the policy id and the customer id live inside the claim."""
    if claim_id in CLAIMS:
        return CLAIMS[claim_id]
    return {"error": "claim not found", "claim_id": claim_id}


def get_policy(policy_id):
    """Look up the policy so we know what is covered and up to how much."""
    if policy_id in POLICIES:
        return POLICIES[policy_id]
    return {"error": "policy not found", "policy_id": policy_id}


def get_customer_history(customer_id):
    """Look up the customer's past claims and their fraud risk score."""
    if customer_id in CUSTOMERS:
        return CUSTOMERS[customer_id]
    return {"error": "customer not found", "customer_id": customer_id}


def check_required_documents(accident_type):
    """Return the documents that this kind of accident needs.
    You cannot call this correctly until you know the accident type,
    and the accident type only comes from get_claim."""
    if accident_type in REQUIRED_DOCUMENTS:
        return {
            "accident_type": accident_type,
            "required_documents": REQUIRED_DOCUMENTS[accident_type],
        }
    return {"error": "unknown accident type", "accident_type": accident_type}


def approve_claim(claim_id, approved_amount):
    """Approve the claim and pay out the given amount."""
    return {
        "decision": "APPROVED",
        "claim_id": claim_id,
        "approved_amount": approved_amount,
    }


def request_documents(claim_id, missing_documents):
    """Ask the customer to send the documents that are still missing."""
    return {
        "decision": "DOCUMENTS_REQUESTED",
        "claim_id": claim_id,
        "missing_documents": missing_documents,
    }


def send_to_investigation(claim_id, reason):
    """Send the claim to a human investigator."""
    return {
        "decision": "SENT_TO_INVESTIGATION",
        "claim_id": claim_id,
        "reason": reason,
    }


def reject_claim(claim_id, reason):
    """Reject the claim."""
    return {
        "decision": "REJECTED",
        "claim_id": claim_id,
        "reason": reason,
    }


# This dictionary is only a lookup table. It is NOT an allow-list.
# Nothing here refuses a tool name. If the model invents a tool that is
# not in this dictionary, the loop just records an error and carries on.
TOOLS = {
    "get_claim": get_claim,
    "get_policy": get_policy,
    "get_customer_history": get_customer_history,
    "check_required_documents": check_required_documents,
    "approve_claim": approve_claim,
    "request_documents": request_documents,
    "send_to_investigation": send_to_investigation,
    "reject_claim": reject_claim,
}


# =====================================================================
# THE PROMPT
# Notice that this is only a polite request. There is no schema and no
# structured output mode, so the model is free to ignore this format.
# =====================================================================

SYSTEM_PROMPT = """You are a claims assessor at an insurance company.
A claim has arrived. You must decide what happens to it.

You work in a loop. On each turn, write exactly one of these two shapes.

To use a tool, write:
Thought: your reasoning here
Action: the tool name
Action Input: a JSON object of arguments

When you have reached a decision, write:
Thought: your reasoning here
Final Answer: your decision and the reason for it

These are the tools you can use:
- get_claim(claim_id)
- get_policy(policy_id)
- get_customer_history(customer_id)
- check_required_documents(accident_type)
- approve_claim(claim_id, approved_amount)
- request_documents(claim_id, missing_documents)
- send_to_investigation(claim_id, reason)
- reject_claim(claim_id, reason)

The four possible outcomes are:
1. Approve the claim
2. Request the missing documents
3. Send the claim for manual investigation
4. Reject the claim

Investigate before you decide. Do not guess at values you have not looked up.
"""


# =====================================================================
# MEASUREMENT
# These numbers go straight into the comparison table in the README.
# =====================================================================

class Meter:
    """Collects the numbers the task asks us to report."""

    def __init__(self):
        self.llm_calls = 0
        self.total_tokens = 0
        self.steps = 0
        self.parse_failures = 0
        self.invented_tools = []
        self.start_time = time.time()

    def record_call(self, response):
        self.llm_calls = self.llm_calls + 1
        try:
            self.total_tokens = self.total_tokens + response.usage_metadata.total_token_count
        except AttributeError:
            pass

    def report(self):
        elapsed = time.time() - self.start_time
        return {
            "llm_calls": self.llm_calls,
            "total_tokens": self.total_tokens,
            "steps": self.steps,
            "latency_seconds": round(elapsed, 2),
            "parse_failures": self.parse_failures,
            "invented_tools": self.invented_tools,
        }


# =====================================================================
# PARSING
# The model output is free text, so we have to guess at its shape.
# This function is fragile on purpose. That fragility is a finding.
# =====================================================================

def parse_model_output(text):
    """Try to read the model's output.
    Returns a dictionary, or None if we could not read it at all."""

    if "Final Answer:" in text:
        parts = text.split("Final Answer:", 1)
        answer = parts[1].strip()
        return {"is_final": True, "answer": answer}

    action_match = re.search(r"Action:\s*(.+)", text)
    if action_match is None:
        return None

    action_line = action_match.group(1)
    action_line = action_line.strip()
    action_line = action_line.strip("`")
    action_name = action_line.split("\n")[0].strip()

    arguments = {}
    input_match = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL)
    if input_match is not None:
        raw_json = input_match.group(1)
        try:
            arguments = json.loads(raw_json)
        except json.JSONDecodeError:
            return None

    return {"is_final": False, "action": action_name, "arguments": arguments}


def print_context_size(transcript, step_number):
    """Print exactly how big the context has become before we send it.
    This is how we show the re-transmission tax in the presentation."""
    character_count = len(transcript)
    approximate_tokens = character_count // 4
    print("")
    print("=" * 64)
    print("STEP " + str(step_number) + " - sending " + str(character_count)
          + " characters, roughly " + str(approximate_tokens) + " tokens")
    print("=" * 64)


# =====================================================================
# THE LOOP
# Note the while True. There is no step budget. That is the architecture.
# =====================================================================

# This guard is NOT part of the architecture. It exists only so a runaway
# loop does not burn the free tier quota while we are testing.
# If it fires, that is itself a result worth reporting.
RUNAWAY_GUARD = 25


def run_unconstrained_agent(request_text, verbose=True):
    model = genai.GenerativeModel(MODEL_NAME)
    meter = Meter()

    transcript = SYSTEM_PROMPT + "\n\nIncoming request: " + request_text + "\n"

    while True:
        meter.steps = meter.steps + 1

        if meter.steps > RUNAWAY_GUARD:
            print("")
            print("!!! RUNAWAY GUARD FIRED at step " + str(meter.steps))
            print("!!! The agent never decided to stop on its own.")
            return {"outcome": "RUNAWAY", "answer": None, "metrics": meter.report()}

        if verbose:
            print_context_size(transcript, meter.steps)

        response = model.generate_content(transcript)
        meter.record_call(response)
        model_text = response.text

        if verbose:
            print(model_text.strip())

        parsed = parse_model_output(model_text)

        # The model wrote something we cannot read. There is no schema
        # here, so this happens. We push the raw text back into the
        # context and hope the next turn is better.
        if parsed is None:
            meter.parse_failures = meter.parse_failures + 1
            transcript = transcript + "\n" + model_text + "\n"
            transcript = transcript + "Observation: I could not read that. "
            transcript = transcript + "Use the Action and Action Input format.\n"
            continue

        if parsed["is_final"] is True:
            return {
                "outcome": "FINAL_ANSWER",
                "answer": parsed["answer"],
                "metrics": meter.report(),
            }

        # There is no allow-list. We look the name up and call whatever
        # we find. If the model invented a tool name, the error becomes
        # an observation and the loop simply continues.
        tool_name = parsed["action"]
        tool_function = TOOLS.get(tool_name)

        if tool_function is None:
            meter.invented_tools.append(tool_name)
            observation = {"error": "no such tool", "tool_name": tool_name}
        else:
            try:
                observation = tool_function(**parsed["arguments"])
            except Exception as error:
                observation = {"error": "the tool failed", "detail": str(error)}

        if verbose:
            print("Observation: " + json.dumps(observation, ensure_ascii=False))

        transcript = transcript + "\n" + model_text + "\n"
        transcript = transcript + "Observation: "
        transcript = transcript + json.dumps(observation, ensure_ascii=False) + "\n"


# =====================================================================
# TEST INPUTS
# These must be identical across all four agents. Once the team agrees,
# move this list into a shared file and import it everywhere.
# =====================================================================

TEST_INPUTS = [
    # 1. Clean case. All documents present, low risk. Should approve.
    "Claim CLM-001 has been submitted. Please assess it.",

    # 2. Documents are missing. The agent has to find out which ones,
    #    and it cannot know that without first reading the accident type.
    "Claim CLM-002 has been submitted. Please assess it.",

    # 3. High amount, high fraud score, past rejections. Should escalate.
    "Claim CLM-003 has been submitted. Please assess it.",

    # 4. The accident type is not covered by this policy. Should reject.
    "Claim CLM-004 has been submitted. Please assess it.",

    # 5. Tricky input. This claim does not exist at all.
    "Claim CLM-9999 has been submitted. Please assess it.",

    # 6. Messy phrasing with no claim id anywhere.
    "hi my car got smashed last week i need my money asap",
]


if __name__ == "__main__":
    all_results = []

    for index, request_text in enumerate(TEST_INPUTS, start=1):
        print("")
        print("")
        print("#" * 64)
        print("# TEST INPUT " + str(index) + ": " + request_text)
        print("#" * 64)

        result = run_unconstrained_agent(request_text)
        result["input"] = request_text
        all_results.append(result)

        print("")
        print("--- RESULT ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    print("")
    print("")
    print("=" * 64)
    print("SUMMARY FOR THE COMPARISON TABLE")
    print("=" * 64)

    for result in all_results:
        metrics = result["metrics"]
        line = ""
        line = line + result["outcome"].ljust(16) + " | "
        line = line + "calls=" + str(metrics["llm_calls"]).rjust(3) + " | "
        line = line + "tokens=" + str(metrics["total_tokens"]).rjust(6) + " | "
        line = line + "latency=" + str(metrics["latency_seconds"]).rjust(6) + "s | "
        line = line + "parse_fails=" + str(metrics["parse_failures"]) + " | "
        line = line + "invented=" + str(metrics["invented_tools"])
        print(line)
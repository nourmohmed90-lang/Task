# # Insurance Claim Assessment Agent

## Company

Our company is an insurance provider that offers vehicle insurance policies. Every day, customers submit insurance claims after accidents. Each claim contains information such as the claim amount, policy details, supporting documents, and fraud risk indicators. The company must quickly decide what should happen next while ensuring that valid claims are processed efficiently and suspicious claims receive additional review.

## Problem

The problem we chose is **Insurance Claim Assessment**.

When a customer submits a claim, the system must determine one of the following actions:

* Approve the claim
* Request additional documents
* Send the claim for manual investigation
* Reject the claim

The decision depends on several factors, including:

* Whether the insurance policy is active
* Whether the claimed damage is covered by the policy
* Whether all required documents have been submitted
* The claim amount
* The fraud risk score
* The customer's previous claim history (for the more advanced agent architectures)

This is a realistic problem faced by insurance companies because incorrect decisions can lead to financial losses, delayed customer service, or undetected fraudulent claims.

## Why an Agent Instead of a Simple Script?

A simple rule-based script can only evaluate fixed conditions using predefined if/else statements. While this works for straightforward cases, it struggles when multiple pieces of information must be gathered and evaluated together.

For example, a claim may have a low amount but also belong to a customer with several previous suspicious claims. Another claim may require checking policy details, claim history, fraud indicators, and submitted documents before making a decision.

An intelligent agent can perform multiple steps, retrieve additional information when needed, and adapt its decision-making process based on previous results. This makes it more suitable for handling complex or unusual insurance claims while still allowing simpler architectures to solve basic cases.

In this project, we implement the same insurance claim assessment problem using four different agent architectures to compare their behavior, flexibility, cost, and limitations.


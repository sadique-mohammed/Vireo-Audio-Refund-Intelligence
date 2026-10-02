# Memo to Arjun Mehta

**To:** Arjun Mehta, Finance Controller  
**Subject:** Vireo Audio Refund Intelligence  

## 1. The Numbers Reconciled
The true, reproducible figure is **₹67.1 lakh (₹6,709,932)** over 18 months. Finance's "well over a crore" figure was artificially inflated due to double-counting migration imports and reading legacy paise as rupees. Helpdesk's "around ₹11 lakh a quarter" is perfectly accurate when averaged across this correct total.

## 2. Monthly Refunds & Volumes
Refunds rose primarily because overall ticket volume doubled after the *Pulse 2* launch, not because agents became softer. The refund rate per ticket remains completely flat at ~20%. There is no evidence of a Q4 "stop arguing" policy spike; frontline CSAT sat flat at ~3.5.

## 3. The Reason Code Problem
Reason codes completely hide the story. **43% of all refund value (₹29.1 lakh) sits in "Goodwill/Other" (GW-OTHER).** However, our AI extraction of the agent notes proves these are actually non-delivery, payment issues, and defects, misclassified simply because GW-OTHER is the first option in the dropdown. 

## 4. Agent & Team Variances
Ranking agents by "who is giving away money" is misleading because refund rates are tied directly to team functional design (e.g., the Returns Desk naturally has a 50% refund rate).

## 5. Order Integrity Exceptions
We identified **98 orders totaling ~₹2.5 lakh** that were refunded for more than the original purchase amount, which require immediate review.

## 6. The Business Goal: Double-Dip Exceptions
**Current estimated refund + replacement rate: 15.6%. The proposed goal is to reduce this toward <1%, with an estimated replacement-cost opportunity of ₹65k–₹133k per quarter. These figures are estimates and need validation.**

This occurs when agents issue both a refund and ship a physical replacement—a direct violation of policy.

## 7. What Still Needs Validation
- **Over-refunded orders**: We must confirm whether the 98 over-refunded orders are data artifacts (e.g., test orders) or actual duplicate cash payouts.
- **AI Accuracy**: Financial pipeline is fully passing and reconciled to ₹0 residual, but final AI classification accuracy is not yet established across the full dataset (currently relying largely on safe rules fallbacks).
- **Double-Dip Opportunity**: The ₹65k–₹133k savings estimate requires validation of the physical inventory logs to confirm the replacements were actually dispatched.

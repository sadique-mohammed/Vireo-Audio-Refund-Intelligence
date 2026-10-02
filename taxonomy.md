# Refund reason taxonomy, version 1

Pick the one label that names what went wrong for the customer. Do not pick it from how the agent resolved the ticket. A goodwill gesture, a store credit or a replacement is a resolution, not a cause.

## PAYMENT_ISSUE
Definition: The customer was charged wrongly: charged twice, debited with no order created, or a failed payment that still took money.
Include: "amount deducted but no order", "charged twice", "bank shows a debit, site shows no order", UPI success with no confirmation.
Exclude: A refund already promised but not received (REFUND_STATUS_FOLLOWUP). A coupon or discount not applied (PRICE_COUPON).
Tie-break: Money left the account and no matching order exists, or it left twice: PAYMENT_ISSUE.
Example: TK-250054

## NON_DELIVERY
Definition: The order never reached the customer: not delivered, tracking stuck, or the courier marks it delivered when it was not.
Include: "package not delivered", "order status stuck on shipped", "tracking not updating", lost in transit.
Exclude: A parcel that arrived damaged (DAMAGED_IN_TRANSIT) or with the wrong product (WRONG_ITEM). A return pickup that did not happen (RETURN_PICKUP_QC).
Tie-break: If no parcel ever reached the customer: NON_DELIVERY.
Example: TK-254485

## DAMAGED_IN_TRANSIT
Definition: The unit or its packaging arrived physically damaged.
Include: dent, crack, crushed box, "straight out of the box" damage, "transit damage" in the notes.
Exclude: A unit that arrived intact but does not work (PRODUCT_DEFECT).
Tie-break: Visible physical damage on arrival: DAMAGED_IN_TRANSIT. A functional fault with no physical damage: PRODUCT_DEFECT.
Example: TK-243653

## WRONG_ITEM
Definition: The customer received a different product, model, colour or variant from the one ordered.
Include: "got something else", "completely different thing", "wrong item delivered".
Exclude: The customer ordered the wrong thing by mistake and wants to cancel (CANCELLATION).
Tie-break: The warehouse sent the wrong thing: WRONG_ITEM. The customer chose the wrong thing: CANCELLATION.
Example: TK-249675

## PRODUCT_DEFECT
Definition: The unit does not work as it should, including dead on arrival.
Include: no power, will not pair or charge, one side silent, battery drain, microphone or touch fault, failed firmware update.
Exclude: Physical damage on arrival (DAMAGED_IN_TRANSIT). A question about the status of a warranty claim (WARRANTY_BUYBACK).
Tie-break: A functional fault with no sign of physical damage: PRODUCT_DEFECT.
Example: TK-249291

## CANCELLATION
Definition: The customer wants to cancel before dispatch, changed their mind, ordered by mistake, or could not use the cancel button.
Include: "want to cancel my order", "change of mind, stop the shipment", "ordered the wrong colour, don't ship it", "my son ordered this without asking".
Exclude: A product the customer received and does not want (RETURN_PICKUP_QC if the issue is the return).
Tie-break: Ordering error or change of mind before dispatch: CANCELLATION, even when the customer mentions a wrong colour or model.
Example: TK-241437, TK-243592

## PRICE_COUPON
Definition: A coupon, discount, offer or price was not applied or was changed at checkout, and the refund or credit adjusts the price.
Include: "discount was not applied at checkout", "coupon code not working", "the festive offer vanished".
Exclude: A charge that should not exist at all (PAYMENT_ISSUE).
Tie-break: The customer paid a different price than promised: PRICE_COUPON.
Example: TK-246028

## RETURN_PICKUP_QC
Definition: A return is in progress and the problem is the pickup or the quality check on the returned unit.
Include: "nobody came for the pickup", "packed the box a week ago and it's still here", "rescheduled pickup twice", pickup missed.
Exclude: The customer waits for money after the return was accepted (REFUND_STATUS_FOLLOWUP).
Tie-break: The pickup has not happened: RETURN_PICKUP_QC. The pickup happened and the money is missing: REFUND_STATUS_FOLLOWUP.
Example: TK-251081

## WARRANTY_BUYBACK
Definition: The ticket is about a warranty claim, an RMA, a repair status or a warranty buy-back.
Include: "status of my warranty claim", "I sent the unit in 10 days ago", RMA number quoted.
Exclude: A unit that is faulty and the customer simply wants a refund, with no claim opened (PRODUCT_DEFECT).
Tie-break: A claim or RMA exists and the question is about it: WARRANTY_BUYBACK.
Example: TK-247627

## REFUND_STATUS_FOLLOWUP
Definition: The customer is chasing a refund that was approved or promised and has not reached them.
Include: "the return was accepted but the amount is nowhere in my account", "refund was promised 9 days ago", "still waiting for my refund".
Exclude: A payment that was wrong in the first place (PAYMENT_ISSUE). A pickup that has not happened (RETURN_PICKUP_QC).
Tie-break: The message is mainly about missing refund money after a return or cancellation: REFUND_STATUS_FOLLOWUP.
Example: TK-247702

## GOODWILL
Definition: No fault is described anywhere in the ticket and the agent grants the refund as a gesture.
Include: Nothing found in the data. See the tie-break.
Exclude: Any ticket that names a concrete fault, even when the agent calls the refund goodwill or a gesture.
Tie-break: A goodwill phrase on top of a named fault never makes the label GOODWILL. Label the fault.
Example: none found as a cause. Closest case, labelled by its fault: TK-246466 (pickup not done, refund "as goodwill") is RETURN_PICKUP_QC.

## OTHER_UNCLEAR
Definition: The ticket is readable but gives no cause, or the cause fits none of the labels above.
Include: A message and notes that name no problem at all.
Exclude: Tickets where the cause can be read from the message or the notes, even if the other field is empty or says "see prev".
Tie-break: If a cause can be inferred from either field, use that label. OTHER_UNCLEAR is for tickets with nothing to infer.
Example: none found in the data

## UNCERTAIN
Definition: Two or more labels fit equally well, or the message and the notes contradict each other. This is the abstain option. Use it instead of guessing.
Include: Evidence that points to two causes with no way to rank them.
Exclude: A ticket with one clear cause and a vague second field.
Tie-break: Prefer UNCERTAIN over a low-confidence guess.
Example: none found in the data

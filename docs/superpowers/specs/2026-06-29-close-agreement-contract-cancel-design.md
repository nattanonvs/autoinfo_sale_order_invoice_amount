# Close Agreement Cancel Amount And Contract Summary Design

## Objective

Extend `autoinfo_sale_order_invoice_amount` to require a cancelled contract amount when closing an agreement, and display a clear contract-level summary on the Sale Order.

The new behavior must be safe, minimal-change, and consistent with existing Collections + Closed Agreement features.

## Existing Context

- Target module: `autoinfo_sale_order_invoice_amount`
- Odoo version: 15
- Existing features already present:
  - Dedicated `Collections` page for Sale Order
  - `Close Agreement` wizard requires reason
  - `Reopen Agreement` action exists
  - Collection metrics on `sale.order`:
    - `total_paid_amount`
    - `outstanding_amount`
    - `collection_status` (with `closed_agreement` override)
- Security model already present:
  - Sales users can close agreement only within their own department (`sale.order.department_id`)
  - Sales Manager can reopen agreement

## Functional Scope

### 1) Close Agreement Requires Cancelled Amount

When user clicks `Close Agreement`:

- Wizard must require:
  - Reason (required text)
  - Cancelled contract amount (required monetary)

On confirm:

- Mark Sale Order as closed agreement
- Save all closure data on the Sale Order
- Enforce validation rules (see section Validation)

### 2) Contract Summary On Sale Order

Sale Order must display a contract summary that includes:

- Amount collected
- Amount not yet collected (based on expected amount)
- Cancelled amount (if any)
- Full contract amount
- Expected amount for this contract

### 3) Reopen Agreement Clears Closure Data

When Sales Manager or Admin reopens:

- Set `is_closed_agreement = False`
- Clear closure fields (reason/date/by/cancel amount)
- Summary values must revert to pre-closure behavior (expected amount equals full amount)

## Business Rules (Locked)

### Definitions

- Full contract amount = `sale.order.amount_total` (original SO total)
- Cancelled amount = amount user enters at Close Agreement time
- Expected amount for this contract = `amount_total - cancelled_amount`

Constraints:

- Expected amount must not be negative (clamp to 0 if needed)

### Validation Rules

Cancelled amount must satisfy:

- `cancelled_amount >= 0`
- `cancelled_amount <= outstanding_at_close`

Where:

- `outstanding_at_close = max(amount_total - total_paid_amount, 0)`

The validation uses current computed totals at the time the wizard is confirmed.

### Collection Status Priority

Priority remains:

1. `closed_agreement`
2. `paid`
3. `partial`

Closed agreement always overrides normal payment logic and remains the indicator for the closed state.

## Data Model Design

### `sale.order`

Add new fields:

- `closed_agreement_cancel_amount`: `fields.Monetary`
  - copy=False
  - readonly for normal users (only set via wizard)

Add contract summary computed fields:

- `contract_expected_amount`: `fields.Monetary`, computed, stored
  - `max(amount_total - closed_agreement_cancel_amount, 0)`
- `contract_uncollected_amount`: `fields.Monetary`, computed, stored
  - `max(contract_expected_amount - total_paid_amount, 0)`

Reuse existing values (no new fields needed):

- Full contract amount = `amount_total`
- Collected amount = `total_paid_amount`
- Cancelled amount = `closed_agreement_cancel_amount`

Compute dependencies:

- `amount_total`
- `total_paid_amount`
- `closed_agreement_cancel_amount`

### Close Agreement Wizard

Extend existing wizard model to include:

- `cancel_amount`: `fields.Monetary` (required)
  - Use `currency_id` from the Sale Order (wizard computed/related)
  - Wizard must show currency consistent with Sale Order currency

On confirm:

- Validate reason and cancel_amount
- Validate cancel_amount does not exceed outstanding_at_close
- Write to Sale Order:
  - `is_closed_agreement = True`
  - `closed_agreement_reason`
  - `closed_agreement_date`
  - `closed_agreement_by`
  - `closed_agreement_cancel_amount = cancel_amount`

## Security Design (Updated)

### Admin Override

Users in `base.group_system` must be able to:

- Close Agreement on any Sale Order (all departments)
- Reopen Agreement on any Sale Order
- Bypass department matching rule completely

### Close Agreement Access (Non-Admin)

Allowed if:

- user is Sales user or Sales Manager
- and document department matches user department

Department logic remains the same as existing implementation:

- Document department: `sale.order.department_id` when present
- User department: from `res.users.department_id` if present, else first `employee_ids.department_id`

### Reopen Agreement Access (Non-Admin)

Allowed if:

- user is Sales Manager

Admin can always reopen regardless of Sales group membership.

## View Design

### Close Agreement Wizard View

Update wizard form to show:

- Sale Order (readonly)
- Reason (required)
- Cancelled amount (required, monetary with correct currency)

### Sale Order Form View (Main)

Existing closed agreement summary block must be expanded:

- Show:
  - Collection status badge (existing)
  - Closed reason/date/by (existing)
  - Cancelled amount (new)
  - Contract summary (new, readonly):
    - Full contract amount (amount_total)
    - Expected amount
    - Collected amount
    - Uncollected amount

### Sale Order Collections Page

Add a `Contract Summary` group (readonly) to keep the contract metrics visible during collections review:

- Full contract amount
- Expected amount
- Collected amount
- Uncollected amount
- Cancelled amount (only visible when closed agreement is active)

## Error Handling

Wizard confirm must raise `UserError` with clear message for:

- missing reason (blank after trim)
- cancel amount < 0
- cancel amount exceeds outstanding at close

## Testing Expectations

Add or extend tests to cover:

1. Close agreement requires cancel amount and reason
2. Cancel amount cannot exceed outstanding at close
3. Cancel amount can be exactly equal to outstanding at close
4. Expected amount and uncollected amount compute correctly after close
5. Reopen clears closure fields and recomputes expected/uncollected amounts
6. Admin (`base.group_system`) can close/reopen across departments

## Assumptions

- Cancel amount is in Sale Order currency
- Refunds/credit notes continue to be handled by existing invoice collection aggregation logic
- The contract summary is a business summary on Sale Order and does not perform accounting write-off postings

## Out Of Scope

- Posting accounting write-offs automatically when closing
- Keeping a multi-event history of repeated close/reopen cycles (log model)
- Introducing new record rules or broad access changes outside the close/reopen workflow


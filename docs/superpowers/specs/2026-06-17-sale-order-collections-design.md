# Sale Order Collections And Closed Agreement Design

## Objective

Extend `autoinfo_sale_order_invoice_amount` so Sale Order shows collection progress in a cleaner way, moves invoice/collection details into a dedicated page, and supports a controlled `Closed Agreement` workflow with auditability.

## Existing Context

- Target module: `autoinfo_sale_order_invoice_amount`
- Odoo version: 15
- Base functional dependencies already present:
  - `sale_order_invoice_amount`
  - `sale_margin`
- `sale.order` already has custom field `department_id`
- Existing system behavior relies on department-based visibility in Sales
- Documentation paths must use Linux-style deployment path conventions

## Functional Scope

### 1. Dedicated Collections Page

Invoice and collection details should no longer be displayed as detailed content in the main totals area of the Sale Order form.

Instead:

- Add a smart button named `Collections`
- Clicking it opens a dedicated Sale Order collections page
- The page is a separate Sale Order form action specialized for collection review

The page must show:

- Sale Order number
- Customer
- Total Sale Order amount
- Total invoiced amount
- Total paid amount
- Outstanding amount
- Collection status
- Collection percentage
- Closed Agreement alert/summary when active
- Related customer invoices list

Invoice list columns:

- Invoice number
- Invoice date
- Invoice amount
- Residual amount
- Payment status (`Paid`, `Partial`, `Unpaid`)

## Data Model Design

### `sale.order`

Add the following fields:

- `collection_status`: `fields.Selection`, computed, stored
  - `partial`
  - `paid`
  - `closed_agreement`
- `total_invoice_amount`: `fields.Monetary`, computed
- `total_paid_amount`: `fields.Monetary`, computed
- `outstanding_amount`: `fields.Monetary`, computed
- `collection_percent`: `fields.Float`, computed
- `is_closed_agreement`: `fields.Boolean`, readonly outside workflow
- `closed_agreement_reason`: `fields.Text`, readonly on form
- `closed_agreement_date`: `fields.Datetime`
- `closed_agreement_by`: `fields.Many2one('res.users')`

Optional helper:

- `collection_summary_display`: `fields.Char`, computed, for smart button text such as `120,000 / 200,000`

### Invoice Helper

Prefer not to create a persistent new business model for collection details.

Use:

- existing `sale.order.invoice_ids`
- computed helper fields on `account.move` only if needed for display clarity

If helper fields are added on `account.move`, they must be lightweight and derived from:

- `amount_total`
- `amount_residual`
- `payment_state`

## Collection Computation Rules

### Invoice Source

Use Sale Order linked customer invoices from `order.invoice_ids`, excluding canceled invoices.

Restrict to customer invoice/credit note move types as appropriate for sale collection logic.

### Currency Handling

All aggregated monetary values shown on Sale Order must be converted into `sale.order.currency_id`.

Conversion rule:

- If invoice currency differs from order currency, convert using invoice date and invoice company
- Use Odoo currency conversion APIs

### Totals

- `total_invoice_amount` = sum of linked valid invoice totals
- `total_paid_amount` = sum of invoice paid portions using `amount_total - amount_residual`
- `outstanding_amount`:
  - normally `max(amount_total - total_paid_amount, 0)`
  - if desired for accounting alignment, compare against invoice residual totals in display logic, but business status uses Sale Order target amount
- `collection_percent` = `total_paid_amount / amount_total`, clamped to `0.0..1.0`

### Collection Status Priority

Priority order:

1. `closed_agreement`
2. `paid`
3. `partial`

Rules:

- If `is_closed_agreement` is true, `collection_status = 'closed_agreement'`
- Else if `total_paid_amount >= amount_total`, `collection_status = 'paid'`
- Else `collection_status = 'partial'`

`Closed Agreement` always overrides normal payment logic.

## Closed Agreement Workflow

### Trigger

Add a button `Close Agreement` on Sale Order form.

### Wizard

Button opens a modal wizard with:

- `reason` as required `fields.Text`

Validation:

- user cannot confirm without reason

### On Confirm

Wizard writes to Sale Order:

- `is_closed_agreement = True`
- `closed_agreement_reason`
- `closed_agreement_date = fields.Datetime.now()`
- `closed_agreement_by = env.user`

### Reopen Workflow

Add button `Reopen Agreement` for Sales Manager only.

Behavior:

- set `is_closed_agreement = False`
- keep audit fields (`closed_agreement_reason`, `closed_agreement_date`, `closed_agreement_by`) intact for traceability

Rationale:

- preserves auditability
- avoids destructive loss of closure history

## Security Design

### Close Agreement

Allowed for Sales users, but only for Sale Orders in the same department as the current user.

Department matching logic:

1. Use `sale.order.department_id` as the document department
2. Determine user department using:
   - `user.department_id` if present
   - fallback to first employee department from `user.employee_ids`

Server-side validation must enforce:

- same department required
- close action denied otherwise

UI rules should support this, but Python validation is the final authority.

### Reopen Agreement

Allowed only for `Sales Manager`.

### Record Rules

Do not introduce broad new record rules unless necessary.

Rely on:

- existing department-based visibility already present in the system
- method-level permission checks for the close/reopen workflow

This avoids conflict with existing custom sales access modules.

## View Design

### Main Sale Order Form

Changes:

- remove the current detailed invoice amount table from the main totals area
- add smart button `Collections`
- add status badge/field for `collection_status`
- add `Close Agreement` button
- add `Reopen Agreement` button for Sales Manager
- when closed agreement is active, show a visible readonly section with:
  - reason
  - closed date
  - closed by

### Collections Page

Implement as a dedicated Sale Order form action using a specialized form view.

Recommended layout:

- header title with Sale Order reference
- summary group/cards:
  - Customer
  - Total SO
  - Total Invoiced
  - Total Paid
  - Outstanding
  - Collection %
  - Collection Status
- prominent closed agreement banner when active
- notebook or grouped section showing linked invoice list

### Sale Order Tree View

Add:

- `collection_status`
- optional `is_closed_agreement`
- optional `total_paid_amount` or `outstanding_amount` if view remains readable

Decorations:

- `partial` = warning
- `paid` = success
- `closed_agreement` = muted or danger

### Sale Order Search View

Add filters:

- Partial Collection
- Fully Collected
- Closed Agreement

Add group by:

- Collection Status

## Actions

### Collections Smart Button Action

Provide a model method returning an `ir.actions.act_window`:

- model: `sale.order`
- res_id: current order id
- view_mode: `form`
- target: current
- context or specific view id to open the collections-focused view

### Close Agreement Action

Open wizard action from Sale Order.

### Reopen Agreement Action

Direct object method with Sales Manager restriction and confirmation-safe implementation.

## UX Decisions

- Use native Odoo smart button patterns
- Keep the main Sale Order page lighter by removing dense collection details
- Use a dedicated page for review rather than a popup for maintainability and better space
- Keep closure fields readonly once set
- Use concise collection summary on the smart button when feasible

## Error Handling

The implementation must raise user-friendly errors for:

- missing close agreement reason
- user department mismatch on close action
- attempts to reopen without manager rights
- actions on multiple Sale Orders where single-record behavior is required

## Testing Expectations

Validate at least these scenarios:

1. Sale Order with no invoices -> status `partial`
2. Sale Order with partial payment -> status `partial`
3. Sale Order fully paid -> status `paid`
4. Sale Order closed agreement -> status `closed_agreement` regardless of payment amount
5. Sales user from same department can close agreement
6. Sales user from other department cannot close agreement
7. Sales Manager can reopen agreement
8. Collections page opens from smart button and shows linked invoices

## Assumptions

- `department_id` already exists on `sale.order`
- user department can be resolved from `res.users.department_id` or `employee_ids.department_id`
- existing department record rules already limit visibility appropriately
- credit notes, if linked, will be handled consistently with Odoo invoice relations and may need exclusion or sign-aware treatment during implementation depending on live accounting behavior

## Out Of Scope

- redesigning existing global department access modules
- changing accounting reconciliation behavior
- adding a new standalone persistent collection model unless implementation reveals a hard technical blocker

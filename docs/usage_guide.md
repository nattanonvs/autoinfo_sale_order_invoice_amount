# Usage Guide

## End Users (Basic)

### View invoice progress on a Sales Order

1) Sales → Orders → Quotations / Sales Orders
2) Open a document
3) Check the totals section

You will see:

- Invoiced Untaxed Amount
- Uninvoiced Untaxed Amount
- Invoiced Amount
- Uninvoiced Amount
- Invoiced Amount (%)

### Use the Collections page

1) Sales → Orders → Quotations / Sales Orders
2) Open a Sales Order
3) Click the `Collections` smart button
4) Review the following information on the `Collections` page:

- Collection Status
- Total Invoice Amount
- Total Paid Amount
- Outstanding Amount
- Collection Percent
- Related invoice list with payment status badge

### Close an agreement before full collection

1) Open a Sales Order
2) Click `Close Agreement`
3) Enter the required reason in the wizard
4) Enter `Cancelled Amount`
5) Click `Confirm`

After confirmation, the Sales Order will show:

- `Collection Status` = `Closed Agreement`
- Close reason
- Close date/time
- User who performed the action
- Cancelled contract amount

The Sales Order form and the `Collections` page will also show:

- Total contract amount
- Expected contract amount
- Total paid amount
- Uncollected contract amount
- Cancelled contract amount

### Reopen a closed agreement

1) Open a Sales Order that is already marked as `Closed Agreement`
2) Click `Reopen Agreement`

Note:

- This action is available to `Sales Manager` and `Settings` (`base.group_system`)
- Reopen is used when the closed agreement must be reversed and normal collection tracking should resume

## Intermediate Users

### Add columns on Tree view

1) Sales → Orders → Quotations
2) Use the list view column chooser
3) Enable optional columns:
   - Invoiced Untaxed Total
   - Uninvoiced Untaxed Total
   - Invoiced Amount (%)

### Filter Sales Orders by collection status

1) Sales → Orders → Quotations / Sales Orders
2) Open the search/filter area
3) Use one of the collection filters:

- `Partial Collection`
- `Fully Collected`
- `Closed Agreement`

4) Use `Group By` → `Collection Status` when you want to review orders by workflow status

## Administrators

### Validate computations

- Ensure invoices are not cancelled for totals to include them.
- Ensure sales order lines have correct invoiced quantities (`qty_invoiced`) to calculate uninvoiced amounts.

### Validate Close/Reopen Agreement access

- Confirm the user who closes the agreement belongs to a sales role or has the custom close-agreement permission configured in the system.
- Confirm the user's department matches the Sales Order department when department-based control is enabled, unless the user has `Settings` (`base.group_system`).
- Confirm `Sales Manager` and `Settings` users can perform `Reopen Agreement`.
- Confirm `Cancelled Amount` is not negative and does not exceed the outstanding amount at close time.

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.
AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight (e.g., suggesting code snippets and optimizations).

# Installation Guide

## Prerequisites

- Odoo 15
- Module dependency installed:
  - `sale_order_invoice_amount` (OCA)
  - `sale_margin`
  - `account`

## Installation Steps

1) Copy module folder

- Place `autoinfo_sale_order_invoice_amount/` at this Linux path:
  `/var/odoo/custom15_autoinfo/autoinfo_sale_order_invoice_amount`
- Ensure this addons root is included in `addons_path`:
  `/var/odoo/custom15_autoinfo`

2) Update Apps List

- Odoo → Apps → Update Apps List

3) Install

- Search “AutoInfo Sale Order Invoice Amount”
- Click Install

## Post-install Check

- Open Sales → Orders → Quotations
- Open a quotation and verify the extra invoice amount block is shown under totals.
- Open a Sales Order and verify the `Collections` smart button is shown.
- Open the `Collections` page and verify collection metrics render without errors.
- Test `Close Agreement` with both `reason` and `Cancelled Amount`.
- Confirm `Reopen Agreement` is available only to `Sales Manager` and `Settings` (`base.group_system`).

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.
AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight (e.g., suggesting code snippets and optimizations).

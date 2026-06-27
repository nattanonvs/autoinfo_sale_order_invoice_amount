# Installation Guide

## Prerequisites

- Odoo 15
- Module dependency installed:
  - `sale_order_invoice_amount` (OCA)

## Installation Steps

1) Copy module folder

- Place `autoinfo_sale_order_invoice_amount/` under an Odoo addons path.
- On a typical Linux server, the standard path is `/var/odoo/custom15_autoinfo` (ensure it is included in `addons_path`).

2) Update Apps List

- Odoo → Apps → Update Apps List

3) Install

- Search “AutoInfo Sale Order Invoice Amount”
- Click Install

## Post-install Check

- Open Sales → Orders → Quotations
- Open a quotation and verify the extra invoice amount block is shown under totals.

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.
AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight (e.g., suggesting code snippets and optimizations).

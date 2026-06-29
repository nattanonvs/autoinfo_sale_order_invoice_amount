# Timeline & Change Log

## 2026-05-18

- Stabilized baseline `sale_order_invoice_amount` by restoring to upstream OCA 15.0 implementation.
- Added new module `autoinfo_sale_order_invoice_amount` (separate install/uninstall) to extend invoice progress:
  - Invoiced Untaxed Amount
  - Uninvoiced Untaxed Amount
  - Invoiced Amount (%)
- Added Form and Tree view enhancements.
- Added QWeb cleanup to avoid blank “label-only” rendering from tax totals extensions when keys are missing.

## 2026-06-08

- Fixed empty values on existing Sales Orders by switching AutoInfo fields to compute at read time (non-stored) and computing invoiced/uninvoiced totals independently from the base module.

## 2026-06-17

- Moved the invoice amounts block to show right after `margin_percent` (requires `sale_margin`).
- Fixed `Invoiced Amount (%)` to be a fraction (0.00–1.00) and capped at 1.00 (= 100.00%).
- Updated documentation paths to a typical Linux addons directory: `/var/odoo/custom15_autoinfo`.
- Added a dedicated `Collections` page on Sale Order with invoice summary, paid amount, outstanding amount, and payment status badges.
- Added `Collection Status` workflow values for `Partial Collection`, `Fully Collected`, and `Closed Agreement`.
- Added `Close Agreement` with required reason capture and audit trail fields for reason, user, and datetime.
- Added `Reopen Agreement` so `Sales Manager` can reverse a closed agreement and resume normal collection tracking.
- Added collection-oriented visibility on the Sale Order form, tree, and search filters for faster follow-up work.
- Fixed collection metrics recompute to handle missing currency safely during module upgrade/recompute.
- Fixed the `Collections` invoice sub-tree by including `state` so account move field modifiers render correctly.
- Changed the `Collections` smart button to use `collection_summary_display` for clearer paid/total rendering.
- Removed collection-status row coloring from the Quotation tree and added the same collection columns to the Sales Order tree.
- Added `docs/user_guide.md` and `docs/technical_guide.md` in simple Thai based on the final module behavior.
- Rewrote `docs/troubleshooting.md` in simple Thai and validated install/uninstall on a clean database.

## 2026-06-29

- Bumped module version to `15.0.2.1.0`.
- Updated `Close Agreement` to require both a reason and a cancelled contract amount.
- Added `closed_agreement_cancel_amount`, `contract_expected_amount`, and `contract_uncollected_amount`.
- Added `Contract Summary` on the main Sale Order form and the `Collections` page.
- Allowed `base.group_system` to close and reopen agreements across departments.
- Changed `Reopen Agreement` to clear all stored close-agreement data before returning to normal collection tracking.
- Updated `README.md`, `docs/user_guide.md`, `docs/technical_guide.md`, and `docs/troubleshooting.md` to match the new workflow.

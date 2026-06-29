# Update Guide

## Upgrade via UI

1) Odoo → Apps
2) Search “AutoInfo Sale Order Invoice Amount”
3) Click Upgrade
4) Refresh the browser after the upgrade completes

## Upgrade via Command Line

```bash
python odoo-bin -c <odoo.conf> -d <db_name> -u autoinfo_sale_order_invoice_amount --stop-after-init
```

## Post-upgrade Validation

1) Open a Sales Order and check `Collections`
2) Confirm `Contract Summary` shows expected values
3) Open `Close Agreement` and confirm the wizard requires `reason` and `Cancelled Amount`
4) Confirm `Settings` (`base.group_system`) users can close/reopen across departments
5) Confirm `Reopen Agreement` clears the previous close-agreement data

## Current Release Target

- Feature release: `15.0.2.1.0`
- Scope: cancelled contract amount, contract summary, admin override, reopen data reset

## Versioning Policy

- Uses OCA-style version format: `15.0.x.y.z`
- Patch version increases for bugfixes without behavior change
- Minor version increases for new features or logic changes

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.
AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight (e.g., suggesting code snippets and optimizations).

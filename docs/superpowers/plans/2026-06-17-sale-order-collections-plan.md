# Sale Order Collections And Closed Agreement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated Collections page on Sale Order, computed collection status/totals, and a department-aware Closed Agreement workflow with audit trail and manager reopen support.

**Architecture:** Extend `sale.order` with collection summary fields and workflow state, add a lightweight `account.move` helper for invoice payment display, and move detailed invoice/collection UI into a dedicated Sale Order form action. Use a transient wizard for mandatory close reason capture and method-level permission checks so the feature respects existing department access modules without introducing risky global record rules.

**Tech Stack:** Odoo 15, Python models, XML inherited views, transient models, access CSV, Sale/Accounting relations, built-in Odoo actions and widgets

---

## File Map

### Files To Modify

- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__init__.py`
  - Load new model and wizard packages.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__manifest__.py`
  - Bump version, add dependencies if needed, and register security/views.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\sale_order.py`
  - Add collection totals, status logic, actions, close/reopen permission checks.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\sale_order_view.xml`
  - Remove old detailed totals block from main form and add button, collections page, tree/search changes.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\timeline_changelog.md`
  - Record the new feature release.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\README.md`
  - Update feature summary for the new workflow.

### Files To Create

- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\__init__.py`
  - Import `sale_order` and `account_move`.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\account_move.py`
  - Add lightweight helper fields/methods for invoice payment display status and paid amount in SO currency-aware contexts.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\__init__.py`
  - Import wizard model.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\close_agreement_wizard.py`
  - Implement mandatory-reason transient wizard.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\close_agreement_wizard_views.xml`
  - Wizard form view/action.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\security\ir.model.access.csv`
  - Access for wizard model.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\tests\test_sale_order_collections.py`
  - Focused functional tests for collection status and close/reopen workflow.

---

### Task 1: Add Failing Tests For Collection Logic

**Files:**
- Create: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\tests\test_sale_order_collections.py`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__manifest__.py`

- [ ] **Step 1: Write the failing test module**

```python
from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestSaleOrderCollections(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Collection Customer"})
        self.department_a = self.env["hr.department"].create({"name": "Dept A"})
        self.department_b = self.env["hr.department"].create({"name": "Dept B"})
        self.sales_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Sales A",
            "login": "sales_a_close_agreement",
            "email": "sales.a@example.com",
            "groups_id": [(6, 0, [
                self.env.ref("sales_team.group_sale_salesman").id,
            ])],
            "department_id": self.department_a.id if "department_id" in self.env["res.users"]._fields else False,
        })
        self.manager_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Manager A",
            "login": "manager_a_close_agreement",
            "email": "manager.a@example.com",
            "groups_id": [(6, 0, [
                self.env.ref("sales_team.group_sale_manager").id,
            ])],
            "department_id": self.department_a.id if "department_id" in self.env["res.users"]._fields else False,
        })
        self.other_sales_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Sales B",
            "login": "sales_b_close_agreement",
            "email": "sales.b@example.com",
            "groups_id": [(6, 0, [
                self.env.ref("sales_team.group_sale_salesman").id,
            ])],
            "department_id": self.department_b.id if "department_id" in self.env["res.users"]._fields else False,
        })
        self.order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "department_id": self.department_a.id,
            "order_line": [(0, 0, {
                "name": "Service",
                "product_uom_qty": 1,
                "price_unit": 1000.0,
            })],
        })

    def test_collection_status_defaults_to_partial(self):
        self.assertEqual(self.order.collection_status, "partial")
        self.assertEqual(self.order.total_paid_amount, 0.0)

    def test_close_agreement_requires_reason(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.sales_user).create({
            "sale_order_id": self.order.id,
            "reason": "",
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_close_agreement_restricted_to_same_department(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.other_sales_user).create({
            "sale_order_id": self.order.id,
            "reason": "Department mismatch test",
        })
        with self.assertRaises(AccessError):
            wizard.action_confirm()

    def test_close_agreement_sets_override_status(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.sales_user).create({
            "sale_order_id": self.order.id,
            "reason": "Accepted short collection",
        })
        wizard.action_confirm()
        self.assertTrue(self.order.is_closed_agreement)
        self.assertEqual(self.order.collection_status, "closed_agreement")
        self.assertEqual(self.order.closed_agreement_by, self.sales_user)

    def test_reopen_requires_sales_manager(self):
        self.order.write({
            "is_closed_agreement": True,
            "closed_agreement_reason": "Seeded",
            "closed_agreement_date": fields.Datetime.now(),
            "closed_agreement_by": self.sales_user.id,
        })
        with self.assertRaises(AccessError):
            self.order.with_user(self.sales_user).action_reopen_agreement()
        self.order.with_user(self.manager_user).action_reopen_agreement()
        self.assertFalse(self.order.is_closed_agreement)
```

- [ ] **Step 2: Register the test file in the module package**

```python
# c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\tests\__init__.py
from . import test_sale_order_collections
```

- [ ] **Step 3: Run the tests to verify they fail**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -i autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- FAIL because `collection_status`, `close.agreement.wizard`, and `action_reopen_agreement()` do not exist yet.

- [ ] **Step 4: Commit the red test scaffold**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/tests
git commit -m "test: add failing collection workflow tests"
```

---

### Task 2: Add Model Package Structure And Helper Invoice Status

**Files:**
- Create: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\account_move.py`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\__init__.py`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__init__.py`

- [ ] **Step 1: Update the model package imports**

```python
# c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\__init__.py
from . import account_move
from . import sale_order
```

```python
# c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__init__.py
from . import models
from . import wizard
```

- [ ] **Step 2: Write the invoice helper model**

```python
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    collection_payment_status = fields.Selection(
        selection=[
            ("unpaid", "Unpaid"),
            ("partial", "Partial"),
            ("paid", "Paid"),
        ],
        compute="_compute_collection_payment_status",
    )

    def _compute_collection_payment_status(self):
        for move in self:
            if move.state == "cancel" or move.move_type not in ("out_invoice", "out_refund"):
                move.collection_payment_status = "unpaid"
            elif not move.amount_residual:
                move.collection_payment_status = "paid"
            elif move.amount_residual < move.amount_total:
                move.collection_payment_status = "partial"
            else:
                move.collection_payment_status = "unpaid"
```

- [ ] **Step 3: Run the targeted tests again**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- Tests still FAIL because Sale Order collection fields and wizard are still missing.

- [ ] **Step 4: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/__init__.py c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/models
git commit -m "refactor: prepare model packages for collection workflow"
```

---

### Task 3: Implement Collection Totals And Status On Sale Order

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\sale_order.py`
- Test: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\tests\test_sale_order_collections.py`

- [ ] **Step 1: Replace the old invoice-only compute structure with collection-focused fields**

```python
from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_invoice_amount = fields.Monetary(
        compute="_compute_collection_metrics",
        store=True,
    )
    total_paid_amount = fields.Monetary(
        compute="_compute_collection_metrics",
        store=True,
    )
    outstanding_amount = fields.Monetary(
        compute="_compute_collection_metrics",
        store=True,
    )
    collection_percent = fields.Float(
        compute="_compute_collection_metrics",
        digits=(16, 2),
        store=True,
    )
    collection_status = fields.Selection(
        selection=[
            ("partial", "Partial Collection"),
            ("paid", "Fully Collected"),
            ("closed_agreement", "Closed Agreement"),
        ],
        compute="_compute_collection_metrics",
        store=True,
    )
    is_closed_agreement = fields.Boolean(copy=False, tracking=True)
    closed_agreement_reason = fields.Text(copy=False, tracking=True)
    closed_agreement_date = fields.Datetime(copy=False, tracking=True)
    closed_agreement_by = fields.Many2one("res.users", copy=False, tracking=True)
    collection_summary_display = fields.Char(
        compute="_compute_collection_metrics",
    )
```

- [ ] **Step 2: Add the collection metric compute and helper methods**

```python
    @api.depends(
        "amount_total",
        "currency_id",
        "invoice_ids",
        "invoice_ids.state",
        "invoice_ids.move_type",
        "invoice_ids.currency_id",
        "invoice_ids.invoice_date",
        "invoice_ids.amount_total",
        "invoice_ids.amount_residual",
        "is_closed_agreement",
    )
    def _compute_collection_metrics(self):
        for order in self:
            invoices = order._get_collection_invoices()
            total_invoice = 0.0
            total_paid = 0.0
            for invoice in invoices:
                total_invoice += order._convert_collection_amount(
                    invoice.amount_total,
                    invoice.currency_id,
                    invoice.invoice_date or fields.Date.context_today(order),
                    invoice.company_id,
                )
                total_paid += order._convert_collection_amount(
                    invoice.amount_total - invoice.amount_residual,
                    invoice.currency_id,
                    invoice.invoice_date or fields.Date.context_today(order),
                    invoice.company_id,
                )
            order.total_invoice_amount = total_invoice
            order.total_paid_amount = total_paid
            order.outstanding_amount = max(order.amount_total - total_paid, 0.0)
            ratio = total_paid / order.amount_total if order.amount_total else 0.0
            order.collection_percent = min(max(ratio, 0.0), 1.0)
            order.collection_summary_display = "%s / %s" % (
                order.currency_id.round(total_paid),
                order.currency_id.round(order.amount_total),
            )
            if order.is_closed_agreement:
                order.collection_status = "closed_agreement"
            elif total_paid >= order.amount_total and order.amount_total:
                order.collection_status = "paid"
            else:
                order.collection_status = "partial"

    def _get_collection_invoices(self):
        self.ensure_one()
        return self.invoice_ids.filtered(
            lambda move: move.state != "cancel" and move.move_type in ("out_invoice", "out_refund")
        )

    def _convert_collection_amount(self, amount, currency, conversion_date, company):
        self.ensure_one()
        if currency == self.currency_id:
            return amount
        return currency._convert(amount, self.currency_id, company, conversion_date)
```

- [ ] **Step 3: Add user department resolution and permission helpers**

```python
    def _get_user_department(self, user=None):
        user = user or self.env.user
        if "department_id" in user._fields and user.department_id:
            return user.department_id
        employee = user.employee_ids[:1]
        return employee.department_id if employee else self.env["hr.department"]

    def _check_close_agreement_access(self):
        self.ensure_one()
        if not self.env.user.has_group("sales_team.group_sale_salesman") and not self.env.user.has_group("sales_team.group_sale_manager"):
            raise AccessError(_("You do not have permission to close agreement."))
        user_department = self._get_user_department()
        if self.department_id and user_department and self.department_id != user_department:
            raise AccessError(_("You can only close agreements in your own department."))
```

- [ ] **Step 4: Run the test file**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- Fewer failures; tests still fail because wizard and reopen action are not implemented yet.

- [ ] **Step 5: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/models/sale_order.py
git commit -m "feat: add sale order collection metrics"
```

---

### Task 4: Implement Close Agreement Wizard

**Files:**
- Create: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\__init__.py`
- Create: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\close_agreement_wizard.py`
- Create: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\security\ir.model.access.csv`

- [ ] **Step 1: Add the wizard package import**

```python
# c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\__init__.py
from . import close_agreement_wizard
```

- [ ] **Step 2: Implement the transient wizard**

```python
from odoo import _, fields, models
from odoo.exceptions import UserError


class CloseAgreementWizard(models.TransientModel):
    _name = "close.agreement.wizard"
    _description = "Close Agreement Wizard"

    sale_order_id = fields.Many2one("sale.order", required=True, readonly=True)
    reason = fields.Text(required=True)

    def action_confirm(self):
        self.ensure_one()
        if not self.reason or not self.reason.strip():
            raise UserError(_("Please provide a reason before closing the agreement."))
        order = self.sale_order_id
        order._check_close_agreement_access()
        order.write({
            "is_closed_agreement": True,
            "closed_agreement_reason": self.reason.strip(),
            "closed_agreement_date": fields.Datetime.now(),
            "closed_agreement_by": self.env.user.id,
        })
        return {"type": "ir.actions.act_window_close"}
```

- [ ] **Step 3: Add wizard access control**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_close_agreement_wizard_user,access.close.agreement.wizard.user,model_close_agreement_wizard,sales_team.group_sale_salesman,1,1,1,1
access_close_agreement_wizard_manager,access.close.agreement.wizard.manager,model_close_agreement_wizard,sales_team.group_sale_manager,1,1,1,1
```

- [ ] **Step 4: Run tests**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- Wizard-related tests pass; reopen action tests still fail.

- [ ] **Step 5: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/wizard c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/security/ir.model.access.csv
git commit -m "feat: add close agreement wizard"
```

---

### Task 5: Add Reopen Action And Smart Button Actions

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\sale_order.py`

- [ ] **Step 1: Add the Sale Order action methods**

```python
from odoo.exceptions import AccessError

    def action_open_collections_page(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Collections"),
            "res_model": "sale.order",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
            "views": [(self.env.ref(
                "autoinfo_sale_order_invoice_amount.view_order_form_collections"
            ).id, "form")],
        }

    def action_open_close_agreement_wizard(self):
        self.ensure_one()
        self._check_close_agreement_access()
        return {
            "type": "ir.actions.act_window",
            "name": _("Close Agreement"),
            "res_model": "close.agreement.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_order_id": self.id,
            },
        }

    def action_reopen_agreement(self):
        self.ensure_one()
        if not self.env.user.has_group("sales_team.group_sale_manager"):
            raise AccessError(_("Only Sales Managers can reopen a closed agreement."))
        self.write({"is_closed_agreement": False})
        return True
```

- [ ] **Step 2: Add a reopen-focused test**

```python
    def test_action_open_collections_page_returns_form_action(self):
        action = self.order.action_open_collections_page()
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(action["res_id"], self.order.id)
```

- [ ] **Step 3: Run tests**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- Python tests PASS, but XML/UI is not wired yet.

- [ ] **Step 4: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/models/sale_order.py c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/tests/test_sale_order_collections.py
git commit -m "feat: add collection actions and reopen workflow"
```

---

### Task 6: Implement Main Form, Collections Page, And Wizard Views

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\sale_order_view.xml`
- Create: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\close_agreement_wizard_views.xml`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__manifest__.py`

- [ ] **Step 1: Register new XML files and bump the module version**

```python
{
    "version": "15.0.2.0.0",
    "depends": ["sale_order_invoice_amount", "sale_margin", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/close_agreement_wizard_views.xml",
        "views/sale_order_view.xml",
    ],
}
```

- [ ] **Step 2: Replace the current Sale Order view with smart button, status, close/reopen buttons, and collections-specific form view**

```xml
<odoo>
    <record id="view_order_form_collection_buttons" model="ir.ui.view">
        <field name="name">sale.order.form.autoinfo.collection.buttons</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">
            <xpath expr="//div[@name='button_box']" position="inside">
                <button name="action_open_collections_page"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-money">
                    <div class="o_stat_info">
                        <span class="o_stat_text">Collections</span>
                        <span class="o_stat_value">
                            <field name="total_paid_amount" widget="monetary" options="{'currency_field': 'currency_id'}"/>
                            /
                            <field name="amount_total" widget="monetary" options="{'currency_field': 'currency_id'}"/>
                        </span>
                    </div>
                </button>
            </xpath>
            <xpath expr="//header" position="inside">
                <button name="action_open_close_agreement_wizard"
                        string="Close Agreement"
                        type="object"
                        class="btn-secondary"
                        groups="sales_team.group_sale_salesman,sales_team.group_sale_manager"
                        attrs="{'invisible': [('is_closed_agreement', '=', True)]}"/>
                <button name="action_reopen_agreement"
                        string="Reopen Agreement"
                        type="object"
                        class="btn-secondary"
                        groups="sales_team.group_sale_manager"
                        attrs="{'invisible': [('is_closed_agreement', '=', False)]}"/>
            </xpath>
            <xpath expr="//sheet/group" position="before">
                <group attrs="{'invisible': [('is_closed_agreement', '=', False)]}">
                    <group string="Closed Agreement">
                        <field name="is_closed_agreement" readonly="1"/>
                        <field name="collection_status" widget="badge" readonly="1"/>
                        <field name="closed_agreement_reason" readonly="1"/>
                        <field name="closed_agreement_date" readonly="1"/>
                        <field name="closed_agreement_by" readonly="1"/>
                    </group>
                </group>
            </xpath>
        </field>
    </record>

    <record id="view_order_form_collections" model="ir.ui.view">
        <field name="name">sale.order.form.autoinfo.collections.page</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="priority">90</field>
        <field name="arch" type="xml">
            <xpath expr="//sheet/notebook" position="inside">
                <page string="Collections">
                    <group col="4">
                        <field name="name" readonly="1"/>
                        <field name="partner_id" readonly="1"/>
                        <field name="amount_total" readonly="1"/>
                        <field name="collection_status" widget="badge" readonly="1"/>
                        <field name="total_invoice_amount" readonly="1"/>
                        <field name="total_paid_amount" readonly="1"/>
                        <field name="outstanding_amount" readonly="1"/>
                        <field name="collection_percent" widget="percentage" readonly="1"/>
                    </group>
                    <group attrs="{'invisible': [('is_closed_agreement', '=', False)]}">
                        <field name="closed_agreement_reason" readonly="1"/>
                        <field name="closed_agreement_date" readonly="1"/>
                        <field name="closed_agreement_by" readonly="1"/>
                    </group>
                    <field name="invoice_ids" readonly="1"
                           domain="[('move_type', 'in', ('out_invoice', 'out_refund')), ('state', '!=', 'cancel')]"
                           context="{'default_move_type': 'out_invoice'}">
                        <tree>
                            <field name="name" string="Invoice Number"/>
                            <field name="invoice_date"/>
                            <field name="amount_total"/>
                            <field name="amount_residual"/>
                            <field name="collection_payment_status" widget="badge"/>
                        </tree>
                    </field>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
```

- [ ] **Step 3: Add the wizard XML**

```xml
<odoo>
    <record id="view_close_agreement_wizard_form" model="ir.ui.view">
        <field name="name">close.agreement.wizard.form</field>
        <field name="model">close.agreement.wizard</field>
        <field name="arch" type="xml">
            <form string="Close Agreement">
                <group>
                    <field name="sale_order_id" readonly="1"/>
                    <field name="reason" placeholder="Enter required closure reason..."/>
                </group>
                <footer>
                    <button name="action_confirm" string="Confirm" type="object" class="btn-primary"/>
                    <button string="Cancel" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

- [ ] **Step 4: Upgrade the module to verify XML loads**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test -u autoinfo_sale_order_invoice_amount --stop-after-init --log-level=warn
```

Expected:

- No view parse errors.

- [ ] **Step 5: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/views c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/__manifest__.py
git commit -m "feat: add sale order collection views"
```

---

### Task 7: Extend Tree And Search Views For Collection Status

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\sale_order_view.xml`

- [ ] **Step 1: Add tree columns and decorations**

```xml
<record id="view_order_tree_collection_status" model="ir.ui.view">
    <field name="name">sale.order.tree.autoinfo.collection.status</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_quotation_tree_with_onboarding"/>
    <field name="arch" type="xml">
        <xpath expr="//tree" position="attributes">
            <attribute name="decoration-success">collection_status == 'paid'</attribute>
            <attribute name="decoration-warning">collection_status == 'partial'</attribute>
            <attribute name="decoration-muted">collection_status == 'closed_agreement'</attribute>
        </xpath>
        <xpath expr="//field[@name='amount_total']" position="after">
            <field name="total_paid_amount" optional="hide"/>
            <field name="outstanding_amount" optional="hide"/>
            <field name="collection_status" widget="badge" optional="show"/>
        </xpath>
    </field>
</record>
```

- [ ] **Step 2: Add search filters and group by**

```xml
<record id="view_sales_order_filter_collection_status" model="ir.ui.view">
    <field name="name">sale.order.search.autoinfo.collection.status</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_sales_order_filter"/>
    <field name="arch" type="xml">
        <xpath expr="//filter[@name='my_sale_orders']" position="after">
            <filter name="partial_collection" string="Partial Collection" domain="[('collection_status', '=', 'partial')]"/>
            <filter name="paid_collection" string="Fully Collected" domain="[('collection_status', '=', 'paid')]"/>
            <filter name="closed_agreement" string="Closed Agreement" domain="[('collection_status', '=', 'closed_agreement')]"/>
        </xpath>
        <xpath expr="//group[@expand='0']" position="inside">
            <filter name="group_by_collection_status" string="Collection Status" context="{'group_by': 'collection_status'}"/>
        </xpath>
    </field>
</record>
```

- [ ] **Step 3: Upgrade module and verify**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test -u autoinfo_sale_order_invoice_amount --stop-after-init --log-level=warn
```

Expected:

- No XML parse errors and new search/tree fields load.

- [ ] **Step 4: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/views/sale_order_view.xml
git commit -m "feat: add collection status tree and search filters"
```

---

### Task 8: Update Docs And Release Metadata

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\README.md`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\usage_guide.md`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\troubleshooting.md`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\timeline_changelog.md`

- [ ] **Step 1: Update README feature summary**

```markdown
- Dedicated `Collections` page on Sale Order with invoice/payment summary
- `Collection Status` on form, tree, and search filters
- `Close Agreement` workflow with mandatory reason and audit trail
- `Reopen Agreement` reserved for Sales Manager
```

- [ ] **Step 2: Add usage notes**

```markdown
## Collections Workflow

1. Open a Sale Order.
2. Click `Collections` to review invoice and payment progress.
3. If an agreement must be closed without full collection, click `Close Agreement`.
4. Enter the required reason and confirm.
5. Sales Managers can use `Reopen Agreement` if the closure must be reversed.
```

- [ ] **Step 3: Add troubleshooting entries**

```markdown
### Close Agreement button is visible but confirmation fails

- Confirm the Sale Order `department_id` matches the current user's department.
- Confirm the user belongs to a Sales group.

### Reopen Agreement is not available

- Only `Sales Manager` can reopen a closed agreement.
```

- [ ] **Step 4: Add changelog entry**

```markdown
## 2026-06-17

- Added dedicated `Collections` Sale Order page with invoice payment summary.
- Added computed collection totals and `collection_status`.
- Added `Close Agreement` wizard with mandatory reason and audit trail.
- Added `Reopen Agreement` for Sales Manager.
```

- [ ] **Step 5: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/README.md c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/docs
git commit -m "docs: describe collections and close agreement workflow"
```

---

### Task 9: Run Full Verification And Package

**Files:**
- Verify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount`
- Output: `c:\odoo\APPreadytouse\backup\autoinfo_sale_order_invoice_amount_15.0.2.0.0_20260617.zip`

- [ ] **Step 1: Run the module tests**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- PASS for the new collection workflow tests.

- [ ] **Step 2: Run an upgrade-only validation**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test -u autoinfo_sale_order_invoice_amount --stop-after-init --log-level=warn
```

Expected:

- No module parse errors.

- [ ] **Step 3: Create the release zip**

Run:

```powershell
$py='C:\odoo\odoo-15.0\.venv\Scripts\python.exe'
$dst='C:\odoo\APPreadytouse\backup\autoinfo_sale_order_invoice_amount_15.0.2.0.0_20260617.zip'
$code=@'
import os
import zipfile

src = r"""C:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount"""
dst = r"""C:\odoo\APPreadytouse\backup\autoinfo_sale_order_invoice_amount_15.0.2.0.0_20260617.zip"""

with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(src):
        for f in files:
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, os.path.dirname(src))
            z.write(fp, rel)

print(dst)
'@
$code | & $py -
```

Expected:

- ZIP path printed successfully.

- [ ] **Step 4: Commit release-ready state**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount
git commit -m "feat: add sale order collections workflow"
```

---

## Self-Review

### Spec Coverage

- Dedicated collections page: covered in Tasks 5-7
- Collection status and totals: covered in Task 3
- Smart button and status indicator: covered in Tasks 5-6
- Close Agreement wizard with required reason: covered in Task 4
- Closed Agreement display on form: covered in Task 6
- Tree/search/filter/group support: covered in Task 7
- Auditability and manager reopen: covered in Tasks 3 and 5
- Packaging and docs: covered in Tasks 8-9

### Placeholder Scan

- No `TODO` or `TBD`
- All commands, files, and target code snippets are specified

### Type Consistency

- `collection_status`, `total_invoice_amount`, `total_paid_amount`, `outstanding_amount`, `collection_percent`
- `close.agreement.wizard`
- `action_open_collections_page`, `action_open_close_agreement_wizard`, `action_reopen_agreement`


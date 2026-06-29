# Close Agreement Cancel Amount And Contract Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add required cancel amount capture to `Close Agreement`, show contract summary on Sale Order/Collections, allow `base.group_system` to bypass department limits, and clear closure data on reopen.

**Architecture:** Extend the existing `sale.order` collection model with two new stored summary fields plus one stored cancel amount field, then reuse the current close-agreement wizard by adding a monetary input and server-side validation. Keep all security enforcement at method level so the module stays compatible with existing department visibility customizations and does not introduce risky new record rules.

**Tech Stack:** Odoo 15, Python models, TransientModel wizard, XML inherited views, Odoo access CSV, TransactionCase tests, existing Sale/Account relations

---

## File Map

### Files To Modify

- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\sale_order.py`
  - Add cancel amount field, contract summary fields, admin override, reopen clear logic.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\close_agreement_wizard.py`
  - Add cancel amount input, currency field, and validation before close.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\sale_order_view.xml`
  - Show cancel amount and contract summary on Sale Order and Collections page; allow Settings users to see/action buttons.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\close_agreement_wizard_views.xml`
  - Add cancel amount field to wizard form.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\security\ir.model.access.csv`
  - Grant wizard access to `base.group_system`.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\tests\test_sale_order_collections.py`
  - Add red/green regression tests for cancel amount, admin override, reopen clear, and summary display.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__manifest__.py`
  - Bump version for the feature release.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\README.md`
  - Add summary of the new close/cancel workflow.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\user_guide.md`
  - Explain the new fields and Close Agreement flow in simple Thai.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\technical_guide.md`
  - Document new fields, validation, and admin override.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\troubleshooting.md`
  - Add cancel amount validation and admin access notes.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\timeline_changelog.md`
  - Record the feature release.

### Files To Verify Only

- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\account_move.py`
  - No change expected unless tests reveal display dependencies.
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\__init__.py`
  - Already loads the wizard; verify no change needed.

---

### Task 1: Add Failing Tests For Cancel Amount And Admin Override

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\tests\test_sale_order_collections.py`

- [ ] **Step 1: Add an admin test user in `setUpClass`**

```python
        cls.admin_user = cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "System Admin Close Agreement",
                "login": "system_admin_close_agreement",
                "email": "system.admin.close.agreement@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_system").id,
                        ],
                    )
                ],
            }
        )
```

- [ ] **Step 2: Add the failing tests for the new business rules**

```python
    def test_close_agreement_requires_cancel_amount(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.sales_user).create(
            {
                "sale_order_id": self.order.id,
                "reason": "Close with zero outstanding validation",
                "cancel_amount": False,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_close_agreement_rejects_cancel_amount_above_outstanding(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.sales_user).create(
            {
                "sale_order_id": self.order.id,
                "reason": "Too much cancel amount",
                "cancel_amount": 1500.0,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_close_agreement_accepts_cancel_amount_equal_outstanding(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.sales_user).create(
            {
                "sale_order_id": self.order.id,
                "reason": "Cancel remaining balance",
                "cancel_amount": 1000.0,
            }
        )
        wizard.action_confirm()
        self.assertEqual(self.order.closed_agreement_cancel_amount, 1000.0)
        self.assertEqual(self.order.contract_expected_amount, 0.0)
        self.assertEqual(self.order.contract_uncollected_amount, 0.0)

    def test_reopen_clears_close_agreement_fields(self):
        self.order.write(
            {
                "is_closed_agreement": True,
                "closed_agreement_reason": "Seeded",
                "closed_agreement_date": fields.Datetime.now(),
                "closed_agreement_by": self.sales_user.id,
                "closed_agreement_cancel_amount": 250.0,
            }
        )
        self.order.with_user(self.manager_user).action_reopen_agreement()
        self.assertFalse(self.order.is_closed_agreement)
        self.assertFalse(self.order.closed_agreement_reason)
        self.assertFalse(self.order.closed_agreement_date)
        self.assertFalse(self.order.closed_agreement_by)
        self.assertEqual(self.order.closed_agreement_cancel_amount, 0.0)
        self.assertEqual(self.order.contract_expected_amount, self.order.amount_total)

    def test_admin_can_close_agreement_across_departments(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.admin_user).create(
            {
                "sale_order_id": self.order.id,
                "reason": "Admin override close",
                "cancel_amount": 100.0,
            }
        )
        wizard.action_confirm()
        self.assertTrue(self.order.is_closed_agreement)
        self.assertEqual(self.order.closed_agreement_by, self.admin_user)

    def test_admin_can_reopen_agreement(self):
        self.order.write(
            {
                "is_closed_agreement": True,
                "closed_agreement_reason": "Seeded",
                "closed_agreement_date": fields.Datetime.now(),
                "closed_agreement_by": self.sales_user.id,
                "closed_agreement_cancel_amount": 300.0,
            }
        )
        self.order.with_user(self.admin_user).action_reopen_agreement()
        self.assertFalse(self.order.is_closed_agreement)
```

- [ ] **Step 3: Add two view regression tests so XML requirements stay covered**

```python
    def test_close_agreement_wizard_view_contains_cancel_amount(self):
        view = self.env.ref(
            "autoinfo_sale_order_invoice_amount.view_close_agreement_wizard_form"
        )
        arch = self.env["close.agreement.wizard"].fields_view_get(
            view_id=view.id, view_type="form"
        )["arch"]
        root = etree.fromstring(arch.encode())
        self.assertTrue(root.xpath("//field[@name='cancel_amount']"))

    def test_collections_view_contains_contract_summary_fields(self):
        view = self.env.ref(
            "autoinfo_sale_order_invoice_amount.view_order_form_collections"
        )
        arch = self.env["sale.order"].fields_view_get(view_id=view.id, view_type="form")[
            "arch"
        ]
        root = etree.fromstring(arch.encode())
        self.assertTrue(root.xpath("//field[@name='contract_expected_amount']"))
        self.assertTrue(root.xpath("//field[@name='contract_uncollected_amount']"))
        self.assertTrue(root.xpath("//field[@name='closed_agreement_cancel_amount']"))
```

- [ ] **Step 4: Run the focused test file to confirm RED**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- FAIL with missing fields such as `cancel_amount`, `closed_agreement_cancel_amount`, `contract_expected_amount`, and access behavior not matching tests.

- [ ] **Step 5: Commit the red tests**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/tests/test_sale_order_collections.py
git commit -m "test: add close agreement cancel amount regressions"
```

---

### Task 2: Implement Sale Order Contract Summary And Admin Access

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\sale_order.py`

- [ ] **Step 1: Add the new stored fields on `sale.order`**

```python
    closed_agreement_cancel_amount = fields.Monetary(
        copy=False,
        tracking=True,
    )
    contract_expected_amount = fields.Monetary(
        compute="_compute_contract_summary",
        compute_sudo=False,
        store=True,
    )
    contract_uncollected_amount = fields.Monetary(
        compute="_compute_contract_summary",
        compute_sudo=False,
        store=True,
    )
```

- [ ] **Step 2: Add the new contract summary compute method**

```python
    @api.depends(
        "amount_total",
        "total_paid_amount",
        "closed_agreement_cancel_amount",
    )
    def _compute_contract_summary(self):
        for order in self:
            cancel_amount = max(order.closed_agreement_cancel_amount, 0.0)
            expected_amount = max(order.amount_total - cancel_amount, 0.0)
            order.contract_expected_amount = expected_amount
            order.contract_uncollected_amount = max(
                expected_amount - order.total_paid_amount,
                0.0,
            )
```

- [ ] **Step 3: Update the close-agreement access helper with admin override**

```python
    def _check_close_agreement_access(self):
        self.ensure_one()
        user = self.env.user
        if user.has_group("base.group_system"):
            return True
        is_sales_user = user.has_group("sales_team.group_sale_salesman")
        is_sales_manager = user.has_group("sales_team.group_sale_manager")
        in_group_257 = "in_group_257" in user._fields and bool(user.in_group_257)
        if not (is_sales_user or is_sales_manager or in_group_257):
            raise AccessError(_("You do not have permission to close agreement."))
        user_department = self._get_user_department(user=user)
        order_department = (
            self.department_id
            if "department_id" in self._fields and self.department_id
            else False
        )
        if order_department and user_department and order_department != user_department:
            raise AccessError(_("You can only close agreements in your own department."))
        return True
```

- [ ] **Step 4: Update reopen so Sales Manager or Admin can reopen and all close data is cleared**

```python
    def action_reopen_agreement(self):
        self.ensure_one()
        user = self.env.user
        if not (
            user.has_group("sales_team.group_sale_manager")
            or user.has_group("base.group_system")
        ):
            raise AccessError(_("Only Sales Managers or Administrators can reopen a closed agreement."))
        self.write(
            {
                "is_closed_agreement": False,
                "closed_agreement_reason": False,
                "closed_agreement_date": False,
                "closed_agreement_by": False,
                "closed_agreement_cancel_amount": 0.0,
            }
        )
        return True
```

- [ ] **Step 5: Run the targeted tests again**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- Some tests still FAIL because the wizard and XML views do not yet contain `cancel_amount` or the new summary fields.

- [ ] **Step 6: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/models/sale_order.py
git commit -m "feat: add contract summary and admin agreement access"
```

---

### Task 3: Extend The Close Agreement Wizard With Cancel Amount Validation

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\close_agreement_wizard.py`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\security\ir.model.access.csv`

- [ ] **Step 1: Add the wizard currency and cancel amount fields**

```python
class CloseAgreementWizard(models.TransientModel):
    _name = "close.agreement.wizard"
    _description = "Close Agreement Wizard"

    sale_order_id = fields.Many2one("sale.order", required=True, readonly=True)
    currency_id = fields.Many2one(
        "res.currency",
        related="sale_order_id.currency_id",
        readonly=True,
    )
    reason = fields.Text(required=True)
    cancel_amount = fields.Monetary(
        currency_field="currency_id",
        required=True,
    )
```

- [ ] **Step 2: Replace `action_confirm()` with the validated implementation**

```python
    def action_confirm(self):
        self.ensure_one()
        reason = (self.reason or "").strip()
        if not reason:
            raise UserError(_("Please provide a reason before closing the agreement."))
        if self.cancel_amount is False:
            raise UserError(_("Please provide the cancelled contract amount before closing the agreement."))
        if self.cancel_amount < 0:
            raise UserError(_("Cancelled contract amount must be zero or greater."))
        order = self.sale_order_id
        order._check_close_agreement_access()
        outstanding_at_close = max(order.amount_total - order.total_paid_amount, 0.0)
        if self.cancel_amount > outstanding_at_close:
            raise UserError(
                _("Cancelled contract amount cannot be greater than the outstanding amount.")
            )
        order.sudo().write(
            {
                "is_closed_agreement": True,
                "closed_agreement_reason": reason,
                "closed_agreement_date": fields.Datetime.now(),
                "closed_agreement_by": self.env.user.id,
                "closed_agreement_cancel_amount": self.cancel_amount,
            }
        )
        return {"type": "ir.actions.act_window_close"}
```

- [ ] **Step 3: Add wizard access for system administrators**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_close_agreement_wizard_user,access.close.agreement.wizard.user,model_close_agreement_wizard,sales_team.group_sale_salesman,1,1,1,1
access_close_agreement_wizard_manager,access.close.agreement.wizard.manager,model_close_agreement_wizard,sales_team.group_sale_manager,1,1,1,1
access_close_agreement_wizard_admin,access.close.agreement.wizard.admin,model_close_agreement_wizard,base.group_system,1,1,1,1
```

- [ ] **Step 4: Run the focused tests**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- Python workflow tests PASS except for view assertions that still depend on XML changes.

- [ ] **Step 5: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/wizard/close_agreement_wizard.py c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/security/ir.model.access.csv
git commit -m "feat: validate close agreement cancel amount"
```

---

### Task 4: Update Wizard And Sale Order Views

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\close_agreement_wizard_views.xml`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\sale_order_view.xml`

- [ ] **Step 1: Add `cancel_amount` to the wizard form**

```xml
<form string="Close Agreement">
    <group>
        <field name="sale_order_id" readonly="1" />
        <field
            name="reason"
            placeholder="Enter the required closure reason..."
        />
        <field
            name="cancel_amount"
            widget="monetary"
            options="{'currency_field': 'currency_id'}"
        />
    </group>
    <footer>
        <button
            name="action_confirm"
            string="Confirm"
            type="object"
            class="btn-primary"
        />
        <button
            string="Cancel"
            class="btn-secondary"
            special="cancel"
        />
    </footer>
</form>
```

- [ ] **Step 2: Expand the main Sale Order closed-agreement block**

```xml
            <xpath expr="//group[@name='sale_header']" position="after">
                <group attrs="{'invisible': [('is_closed_agreement', '=', False)]}">
                    <group string="Closed Agreement">
                        <field name="collection_status" widget="badge" readonly="1" />
                        <field name="closed_agreement_reason" readonly="1" />
                        <field name="closed_agreement_date" readonly="1" />
                        <field name="closed_agreement_by" readonly="1" />
                        <field
                            name="closed_agreement_cancel_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                    </group>
                    <group string="Contract Summary">
                        <field
                            name="amount_total"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                        <field
                            name="contract_expected_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                        <field
                            name="total_paid_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                        <field
                            name="contract_uncollected_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                    </group>
                </group>
            </xpath>
```

- [ ] **Step 3: Expand the Collections page with contract summary**

```xml
                    <group string="Contract Summary" col="4">
                        <field
                            name="amount_total"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                        <field
                            name="contract_expected_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                        <field
                            name="total_paid_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                        <field
                            name="contract_uncollected_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                        />
                        <field
                            name="closed_agreement_cancel_amount"
                            readonly="1"
                            widget="monetary"
                            options="{'currency_field': 'currency_id'}"
                            attrs="{'invisible': [('is_closed_agreement', '=', False)]}"
                        />
                    </group>
```

- [ ] **Step 4: Let Settings users see and run the header buttons from the form**

```xml
                <button
                    name="action_open_close_agreement_wizard"
                    string="Close Agreement"
                    type="object"
                    class="btn-secondary"
                    groups="sales_team.group_sale_salesman,sales_team.group_sale_manager,base.group_system"
                    attrs="{'invisible': [('is_closed_agreement', '=', True)]}"
                />
                <button
                    name="action_reopen_agreement"
                    string="Reopen Agreement"
                    type="object"
                    class="btn-secondary"
                    groups="sales_team.group_sale_manager,base.group_system"
                    attrs="{'invisible': [('is_closed_agreement', '=', False)]}"
                />
```

- [ ] **Step 5: Upgrade the module to verify XML loads**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test -u autoinfo_sale_order_invoice_amount --stop-after-init --log-level=warn
```

Expected:

- No view parse errors and both new fields render in the form definitions.

- [ ] **Step 6: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/views/close_agreement_wizard_views.xml c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/views/sale_order_view.xml
git commit -m "feat: show contract summary in close agreement views"
```

---

### Task 5: Bump Version And Update Docs

**Files:**
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\__manifest__.py`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\README.md`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\user_guide.md`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\technical_guide.md`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\troubleshooting.md`
- Modify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\docs\timeline_changelog.md`

- [ ] **Step 1: Bump the module version**

```python
{
    "version": "15.0.2.1.0",
}
```

- [ ] **Step 2: Add README summary bullets**

```markdown
- Close Agreement now requires both a reason and a cancelled contract amount.
- Sale Order shows a contract summary with full amount, expected amount, collected amount, uncollected amount, and cancelled amount.
- System Administrators (`base.group_system`) can close and reopen agreements across all departments.
```

- [ ] **Step 3: Add a simple Thai user-guide section**

```markdown
## ปิดสัญญาแบบใหม่

1. เปิดใบขายที่ต้องการ
2. กดปุ่ม `Close Agreement`
3. ใส่เหตุผล
4. ใส่ยอดตามสัญญาที่ต้องการยกเลิก
5. กด `Confirm`
6. ระบบจะเก็บข้อมูลการปิดไว้ในใบขาย

## ดูสรุปสัญญา

ในใบขายและหน้า `Collections` จะมีสรุปดังนี้

- ยอดเต็มของสัญญา
- ยอดที่ต้องได้รับ
- ยอดที่เก็บแล้ว
- ยอดที่ยังไม่ได้เก็บ
- ยอดที่ยกเลิก
```

- [ ] **Step 4: Add technical/troubleshooting/changelog entries**

```markdown
## Technical Notes

- New field: `closed_agreement_cancel_amount`
- New stored summary fields: `contract_expected_amount`, `contract_uncollected_amount`
- Validation: cancel amount must be between `0` and current outstanding amount
- Admin override group: `base.group_system`
```

```markdown
## ปัญหาที่อาจเจอ

### กรอกยอดยกเลิกแล้วบันทึกไม่ได้

- ตรวจว่ากรอกตัวเลขมากกว่ายอดค้างหรือไม่
- ตรวจว่าใส่ค่าติดลบหรือไม่

### Admin เห็นปุ่มแต่กดไม่ได้

- ตรวจว่าผู้ใช้มีสิทธิ `Settings` (`base.group_system`) จริง
```

```markdown
## 2026-06-29

- Added required cancel amount in `Close Agreement`.
- Added contract summary fields on Sale Order and Collections page.
- Added `base.group_system` override for close/reopen agreement.
- Changed reopen behavior to clear all close-agreement data.
```

- [ ] **Step 5: Commit**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/__manifest__.py c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/README.md c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount/docs
git commit -m "docs: describe contract cancel summary workflow"
```

---

### Task 6: Full Validation, Diagnostics, And Packaging

**Files:**
- Verify: `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount`
- Output: `c:\odoo\APPreadytouse\backup\autoinfo_sale_order_invoice_amount_15.0.2.1.0_20260629.zip`

- [ ] **Step 1: Run the full module test set**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test --test-enable -u autoinfo_sale_order_invoice_amount --stop-after-init --test-tags /autoinfo_sale_order_invoice_amount
```

Expected:

- PASS for all tests in `test_sale_order_collections.py`.

- [ ] **Step 2: Run upgrade-only validation**

Run:

```bash
"C:\odoo\odoo-15.0\.venv\Scripts\python.exe" "C:\odoo\odoo-15.0\odoo-bin" -c "C:\odoo\odoo-15.0\odoo.conf" -d autoinfo_soia_test -u autoinfo_sale_order_invoice_amount --stop-after-init --log-level=warn
```

Expected:

- No Python traceback and no XML parse errors.

- [ ] **Step 3: Check edited files for diagnostics**

Run the editor diagnostics on:

- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\models\sale_order.py`
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\wizard\close_agreement_wizard.py`
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\sale_order_view.xml`
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\views\close_agreement_wizard_views.xml`
- `c:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount\tests\test_sale_order_collections.py`

Expected:

- No new linter or parser errors.

- [ ] **Step 4: Create the release ZIP**

Run:

```powershell
$py='C:\odoo\odoo-15.0\.venv\Scripts\python.exe'
$dst='C:\odoo\APPreadytouse\backup\autoinfo_sale_order_invoice_amount_15.0.2.1.0_20260629.zip'
$code=@'
import os
import zipfile

src = r"""C:\odoo\APPreadytouse\autoinfo_sale_order_invoice_amount"""
dst = r"""C:\odoo\APPreadytouse\backup\autoinfo_sale_order_invoice_amount_15.0.2.1.0_20260629.zip"""

with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, os.path.dirname(src))
            z.write(fp, rel)

print(dst)
'@
$code | & $py -
```

Expected:

- ZIP path prints successfully and the archive contains the module root folder.

- [ ] **Step 5: Commit the release-ready state**

```bash
git add c:/odoo/APPreadytouse/autoinfo_sale_order_invoice_amount
git commit -m "feat: add contract cancel amount and summary workflow"
```

---

## Self-Review

### Spec Coverage

- Required cancel amount in Close Agreement: covered in Tasks 1 and 3
- Contract summary on Sale Order: covered in Tasks 2 and 4
- Reopen clears close data: covered in Tasks 1 and 2
- Admin override with `base.group_system`: covered in Tasks 1, 2, 3, and 4
- View updates on wizard and Collections page: covered in Task 4
- Versioning/docs/package: covered in Tasks 5 and 6

### Placeholder Scan

- No `TODO`, `TBD`, or “implement later”
- Commands, files, fields, and methods are concrete
- Code snippets align with current module structure

### Type Consistency

- `closed_agreement_cancel_amount`
- `contract_expected_amount`
- `contract_uncollected_amount`
- `cancel_amount`
- `action_reopen_agreement()`
- `base.group_system`


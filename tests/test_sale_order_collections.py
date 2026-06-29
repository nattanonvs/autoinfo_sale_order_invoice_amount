from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged
from lxml import etree


@tagged("-at_install", "post_install")
class TestSaleOrderCollections(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Collection Customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Collection Service",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 1000.0,
            }
        )
        cls.department_model = None
        cls.department_a = None
        cls.department_b = None
        if "department_id" in cls.env["sale.order"]._fields and "hr.department" in cls.env:
            cls.department_model = cls.env["hr.department"]
            cls.department_a = cls.department_model.create({"name": "Dept A"})
            cls.department_b = cls.department_model.create({"name": "Dept B"})
        cls.sales_user = cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sales A",
                "login": "sales_a_close_agreement",
                "email": "sales.a@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("sales_team.group_sale_salesman").id]),
                ],
                **cls._optional_user_department_vals(cls.department_a),
            }
        )
        cls.manager_user = cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Manager A",
                "login": "manager_a_close_agreement",
                "email": "manager.a@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("sales_team.group_sale_manager").id]),
                ],
                **cls._optional_user_department_vals(cls.department_a),
            }
        )
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
        cls.other_sales_user = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {
                "name": "Sales B",
                "login": "sales_b_close_agreement",
                "email": "sales.b@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("sales_team.group_sale_salesman").id]),
                ],
                **cls._optional_user_department_vals(cls.department_b),
            }
        )
        order_vals = {
            "partner_id": cls.partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": cls.product.id,
                        "name": "Collection Service",
                        "product_uom_qty": 1.0,
                        "price_unit": 1000.0,
                    },
                )
            ],
        }
        if "department_id" in cls.env["sale.order"]._fields and cls.department_a:
            order_vals["department_id"] = cls.department_a.id
        cls.order = cls.env["sale.order"].create(order_vals)

    @classmethod
    def _optional_user_department_vals(cls, department):
        if department and "department_id" in cls.env["res.users"]._fields:
            return {"department_id": department.id}
        return {}

    def test_collection_status_defaults_to_partial(self):
        self.assertEqual(self.order.collection_status, "partial")
        self.assertEqual(self.order.total_paid_amount, 0.0)

    def test_total_paid_amount_updates_after_register_payment(self):
        order = self.env["sale.order"].new(
            {
                "partner_id": self.partner.id,
                "amount_total": 1000.0,
                "company_id": self.order.company_id.id,
                "currency_id": self.order.currency_id.id,
            }
        )
        invoice = self.env["account.move"].new(
            {
                "move_type": "out_invoice",
                "state": "posted",
                "amount_total": 1000.0,
                "amount_residual": 600.0,
                "currency_id": self.order.currency_id.id,
                "company_id": self.order.company_id.id,
                "invoice_date": fields.Date.today(),
            }
        )
        order.invoice_ids = invoice
        order._compute_collection_metrics()
        self.assertEqual(order.total_paid_amount, 400.0)

    def test_close_agreement_requires_reason(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.sales_user).create(
            {
                "sale_order_id": self.order.id,
                "reason": "",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

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

    def test_close_agreement_restricted_to_same_department(self):
        if not (
            self.department_a
            and self.department_b
            and "department_id" in self.env["sale.order"]._fields
            and "department_id" in self.env["res.users"]._fields
        ):
            self.skipTest("Department fields are not available in this database")
        wizard = self.env["close.agreement.wizard"].with_user(
            self.other_sales_user
        ).create(
            {
                "sale_order_id": self.order.id,
                "reason": "Department mismatch test",
            }
        )
        with self.assertRaises(AccessError):
            wizard.action_confirm()

    def test_close_agreement_sets_override_status(self):
        wizard = self.env["close.agreement.wizard"].with_user(self.sales_user).create(
            {
                "sale_order_id": self.order.id,
                "reason": "Accepted short collection",
            }
        )
        wizard.action_confirm()
        self.assertTrue(self.order.is_closed_agreement)
        self.assertEqual(self.order.collection_status, "closed_agreement")
        self.assertEqual(self.order.closed_agreement_by, self.sales_user)

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

    def test_action_open_collections_page_returns_form_action(self):
        action = self.order.action_open_collections_page()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(action["res_id"], self.order.id)
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "current")

    def test_collections_button_uses_summary_display_field(self):
        view = self.env.ref("sale.view_order_form")
        arch = self.env["sale.order"].fields_view_get(view_id=view.id, view_type="form")[
            "arch"
        ]
        root = etree.fromstring(arch.encode())
        summary_fields = root.xpath(
            "//button[@name='action_open_collections_page']//field[@name='collection_summary_display']"
        )
        self.assertTrue(
            summary_fields,
            "Collections smart button should render collection_summary_display instead of hardcoded monetary fragments",
        )

    def test_action_open_close_agreement_wizard_returns_modal_action(self):
        action = self.order.with_user(self.sales_user).action_open_close_agreement_wizard()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "close.agreement.wizard")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["context"]["default_sale_order_id"], self.order.id)

    def test_collection_metrics_handle_missing_currency(self):
        order = self.env["sale.order"].new(
            {
                "partner_id": self.partner.id,
                "amount_total": 500.0,
            }
        )
        order.currency_id = self.env["res.currency"]
        order._compute_collection_metrics()
        self.assertEqual(order.total_paid_amount, 0.0)
        self.assertEqual(order.outstanding_amount, 500.0)
        self.assertEqual(order.collection_status, "partial")

    def test_collections_invoice_tree_includes_state_field_for_modifiers(self):
        view = self.env.ref(
            "autoinfo_sale_order_invoice_amount.view_order_form_collections"
        )
        result = self.env["sale.order"].fields_view_get(view_id=view.id, view_type="form")
        tree_arch = result["fields"]["invoice_ids"]["views"]["tree"]["arch"]
        invoice_tree = etree.fromstring(tree_arch.encode())
        state_fields = invoice_tree.xpath("./field[@name='state']")
        self.assertTrue(
            state_fields,
            "invoice_ids tree must include state field so account.move modifiers parse correctly",
        )

    def test_quotation_tree_has_no_collection_row_decorations(self):
        view = self.env.ref("sale.view_quotation_tree_with_onboarding")
        arch = self.env["sale.order"].fields_view_get(view_id=view.id, view_type="tree")[
            "arch"
        ]
        root = etree.fromstring(arch.encode())
        tree = root.xpath("//tree")[0]
        for attr_name in ("decoration-success", "decoration-warning", "decoration-muted"):
            self.assertNotIn(
                "collection_status",
                tree.attrib.get(attr_name, ""),
                "Quotation tree rows should not be recolored by collection status",
            )

    def test_sale_order_tree_shows_collection_columns(self):
        view = self.env.ref("sale.view_order_tree")
        arch = self.env["sale.order"].fields_view_get(view_id=view.id, view_type="tree")[
            "arch"
        ]
        root = etree.fromstring(arch.encode())
        self.assertTrue(root.xpath("//field[@name='total_paid_amount']"))
        self.assertTrue(root.xpath("//field[@name='outstanding_amount']"))
        self.assertTrue(root.xpath("//field[@name='collection_status']"))

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

    def test_reopen_requires_sales_manager(self):
        if {
            "is_closed_agreement",
            "closed_agreement_reason",
            "closed_agreement_date",
            "closed_agreement_by",
        }.issubset(self.env["sale.order"]._fields):
            self.order.write(
                {
                    "is_closed_agreement": True,
                    "closed_agreement_reason": "Seeded",
                    "closed_agreement_date": fields.Datetime.now(),
                    "closed_agreement_by": self.sales_user.id,
                }
            )
        with self.assertRaises(AccessError):
            self.order.with_user(self.sales_user).action_reopen_agreement()
        self.order.with_user(self.manager_user).action_reopen_agreement()
        self.assertFalse(self.order.is_closed_agreement)

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

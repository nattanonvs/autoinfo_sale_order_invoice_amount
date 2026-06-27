from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_invoice_amount = fields.Monetary(
        compute="_compute_collection_metrics",
        compute_sudo=False,
        store=True,
    )
    total_paid_amount = fields.Monetary(
        compute="_compute_collection_metrics",
        compute_sudo=False,
        store=True,
    )
    outstanding_amount = fields.Monetary(
        compute="_compute_collection_metrics",
        compute_sudo=False,
        store=True,
    )
    collection_percent = fields.Float(
        compute="_compute_collection_metrics",
        compute_sudo=False,
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
        compute_sudo=False,
        store=True,
    )
    is_closed_agreement = fields.Boolean(copy=False, tracking=True)
    closed_agreement_reason = fields.Text(copy=False, tracking=True)
    closed_agreement_date = fields.Datetime(copy=False, tracking=True)
    closed_agreement_by = fields.Many2one("res.users", copy=False, tracking=True)
    collection_summary_display = fields.Char(
        compute="_compute_collection_metrics",
        compute_sudo=False,
    )
    autoinfo_invoiced_amount = fields.Monetary(
        compute="_compute_autoinfo_invoice_amounts",
        store=False,
    )
    autoinfo_uninvoiced_amount = fields.Monetary(
        compute="_compute_autoinfo_invoice_amounts",
        store=False,
    )
    invoiced_untaxed_amount = fields.Monetary(
        compute="_compute_autoinfo_invoice_amounts",
        store=False,
    )
    uninvoiced_untaxed_amount = fields.Monetary(
        compute="_compute_autoinfo_invoice_amounts",
        store=False,
    )
    invoiced_amount_percent = fields.Float(
        compute="_compute_autoinfo_invoice_amounts",
        digits=(16, 2),
        store=False,
    )

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
        "invoice_ids.company_id",
        "is_closed_agreement",
    )
    def _compute_collection_metrics(self):
        for order in self:
            invoices = order._get_collection_invoices()
            display_currency = order._get_collection_currency()
            total_invoice = 0.0
            total_paid = 0.0
            for invoice in invoices:
                conversion_date = invoice.invoice_date or fields.Date.context_today(
                    order
                )
                total_invoice += order._convert_collection_amount(
                    invoice.amount_total,
                    invoice.currency_id,
                    conversion_date,
                    invoice.company_id,
                )
                total_paid += order._convert_collection_amount(
                    invoice.amount_total - invoice.amount_residual,
                    invoice.currency_id,
                    conversion_date,
                    invoice.company_id,
                )
            order.total_invoice_amount = total_invoice
            order.total_paid_amount = total_paid
            order.outstanding_amount = max(order.amount_total - total_paid, 0.0)
            ratio = total_paid / order.amount_total if order.amount_total else 0.0
            order.collection_percent = min(max(ratio, 0.0), 1.0)
            if display_currency:
                paid_display = display_currency.round(total_paid)
                total_display = display_currency.round(order.amount_total)
            else:
                paid_display = total_paid
                total_display = order.amount_total
            order.collection_summary_display = "%s / %s" % (
                paid_display,
                total_display,
            )
            if order.is_closed_agreement:
                order.collection_status = "closed_agreement"
            elif total_paid >= order.amount_total and order.amount_total:
                order.collection_status = "paid"
            else:
                order.collection_status = "partial"

    @api.depends(
        "state",
        "invoice_ids",
        "invoice_ids.amount_total_signed",
        "invoice_ids.amount_untaxed_signed",
        "invoice_ids.currency_id",
        "invoice_ids.invoice_date",
        "invoice_ids.state",
        "amount_total",
        "amount_untaxed",
        "currency_id",
        "order_line.product_uom_qty",
        "order_line.qty_invoiced",
        "order_line.price_total",
        "order_line.price_subtotal",
        "order_line.display_type",
    )
    def _compute_autoinfo_invoice_amounts(self):
        for order in self:
            if order.state != "cancel" and order.invoice_ids:
                invoiced_total = 0.0
                invoiced_untaxed = 0.0
                for invoice in order.invoice_ids:
                    if invoice.state == "cancel":
                        continue
                    invoice_date = invoice.invoice_date or fields.Date.today()
                    if (
                        invoice.currency_id != order.currency_id
                        and order.currency_id != invoice.company_currency_id
                    ):
                        invoiced_total += invoice.currency_id._convert(
                            invoice.amount_total_signed,
                            order.currency_id,
                            invoice.company_id,
                            invoice_date,
                        )
                        invoiced_untaxed += invoice.currency_id._convert(
                            invoice.amount_untaxed_signed,
                            order.currency_id,
                            invoice.company_id,
                            invoice_date,
                        )
                    else:
                        invoiced_total += invoice.amount_total_signed
                        invoiced_untaxed += invoice.amount_untaxed_signed
                order.autoinfo_invoiced_amount = invoiced_total
                order.invoiced_untaxed_amount = invoiced_untaxed
                lines = order.order_line.filtered(
                    lambda sl: sl.product_uom_qty > 0
                    and not sl.display_type
                    and sl.product_uom_qty > sl.qty_invoiced
                )
                order.autoinfo_uninvoiced_amount = max(
                    0,
                    sum(
                        (line.product_uom_qty - line.qty_invoiced)
                        * (line.price_total / line.product_uom_qty)
                        for line in lines
                    ),
                )
                order.uninvoiced_untaxed_amount = max(
                    0,
                    sum(
                        (line.product_uom_qty - line.qty_invoiced)
                        * (line.price_subtotal / line.product_uom_qty)
                        for line in lines
                    ),
                )
            else:
                order.autoinfo_invoiced_amount = 0.0
                order.invoiced_untaxed_amount = 0.0
                if order.state in ["draft", "sent", "cancel"]:
                    order.autoinfo_uninvoiced_amount = 0.0
                    order.uninvoiced_untaxed_amount = 0.0
                else:
                    order.autoinfo_uninvoiced_amount = order.amount_total
                    order.uninvoiced_untaxed_amount = order.amount_untaxed
            if order.amount_total:
                ratio = order.autoinfo_invoiced_amount / order.amount_total
                order.invoiced_amount_percent = min(max(ratio, 0.0), 1.0)
            else:
                order.invoiced_amount_percent = 0.0

    def _get_collection_invoices(self):
        self.ensure_one()
        return self.invoice_ids.filtered(
            lambda move: move.state != "cancel"
            and move.move_type in ("out_invoice", "out_refund")
        )

    def _convert_collection_amount(self, amount, currency, conversion_date, company):
        self.ensure_one()
        target_currency = self._get_collection_currency()
        if not currency or not target_currency or currency == target_currency:
            return amount
        return currency._convert(amount, target_currency, company, conversion_date)

    def _get_collection_currency(self):
        self.ensure_one()
        if self.currency_id:
            return self.currency_id
        if self.pricelist_id and self.pricelist_id.currency_id:
            return self.pricelist_id.currency_id
        if self.company_id and self.company_id.currency_id:
            return self.company_id.currency_id
        return self.env["res.currency"]

    def _get_user_department(self, user=None):
        user = user or self.env.user
        if "department_id" in user._fields and user.department_id:
            return user.department_id
        if "employee_ids" in user._fields and user.employee_ids:
            return user.employee_ids[:1].department_id
        return False

    def _check_close_agreement_access(self):
        self.ensure_one()
        user = self.env.user
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
            raise AccessError(
                _("You can only close agreements in your own department.")
            )

    def action_open_collections_page(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": _("Collections"),
            "res_model": "sale.order",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }
        collections_view = self.env.ref(
            "autoinfo_sale_order_invoice_amount.view_order_form_collections",
            raise_if_not_found=False,
        )
        if collections_view:
            action["views"] = [(collections_view.id, "form")]
        return action

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

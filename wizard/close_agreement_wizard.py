from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    cancel_amount_provided = fields.Boolean(default=False)
    cancel_amount = fields.Monetary(
        currency_field="currency_id",
        default=0.0,
    )

    @api.model_create_multi
    def create(self, vals_list):
        normalized_vals_list = []
        for vals in vals_list:
            normalized_vals = dict(vals)
            if "cancel_amount" in normalized_vals:
                normalized_vals["cancel_amount_provided"] = (
                    normalized_vals.get("cancel_amount") is not False
                )
            else:
                normalized_vals["cancel_amount"] = 0.0
                normalized_vals["cancel_amount_provided"] = True
            normalized_vals_list.append(normalized_vals)
        return super().create(normalized_vals_list)

    def action_confirm(self):
        self.ensure_one()
        reason = (self.reason or "").strip()
        if not reason:
            raise UserError(_("Please provide a reason before closing the agreement."))
        if not self.cancel_amount_provided:
            raise UserError(
                _("Please provide the cancelled contract amount before closing the agreement.")
            )
        if self.cancel_amount < 0:
            raise UserError(_("Cancelled contract amount must be zero or greater."))
        order = self.sale_order_id
        order._check_close_agreement_access()
        outstanding_at_close = max(order.amount_total - order.total_paid_amount, 0.0)
        if self.cancel_amount > outstanding_at_close:
            raise UserError(
                _(
                    "Cancelled contract amount cannot be greater than the outstanding amount."
                )
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

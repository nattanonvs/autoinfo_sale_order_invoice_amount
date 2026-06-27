from odoo import _, fields, models
from odoo.exceptions import UserError


class CloseAgreementWizard(models.TransientModel):
    _name = "close.agreement.wizard"
    _description = "Close Agreement Wizard"

    sale_order_id = fields.Many2one("sale.order", required=True, readonly=True)
    reason = fields.Text(required=True)

    def action_confirm(self):
        self.ensure_one()
        reason = (self.reason or "").strip()
        if not reason:
            raise UserError(_("Please provide a reason before closing the agreement."))
        order = self.sale_order_id
        order._check_close_agreement_access()
        order.sudo().write(
            {
                "is_closed_agreement": True,
                "closed_agreement_reason": reason,
                "closed_agreement_date": fields.Datetime.now(),
                "closed_agreement_by": self.env.user.id,
            }
        )
        return {"type": "ir.actions.act_window_close"}

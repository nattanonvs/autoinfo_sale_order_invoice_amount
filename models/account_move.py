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

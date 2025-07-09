from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    contract_line_id = fields.Many2one(
        "contract.line", string="Contract Line", index=True
    )

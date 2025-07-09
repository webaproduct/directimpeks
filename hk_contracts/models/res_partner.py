from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_contract_required = fields.Boolean(
        default="True",
        string="Contract Required",
    )

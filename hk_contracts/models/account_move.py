from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    contract_id = fields.Many2one(
        string="Contract",
        comodel_name="contract.contract",
        domain="[('partner_id', '=', partner_id)]",
    )

    is_contract_required = fields.Boolean(
        related="partner_id.is_contract_required",
    )

    @api.onchange("partner_id")
    def _onchange_partner_id_contracts(self):
        for record in self:
            record.contract_id = False

from odoo import api, fields, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    contragent_id = fields.Many2one(
        'res.partner',
        string='Counterparty'
    )

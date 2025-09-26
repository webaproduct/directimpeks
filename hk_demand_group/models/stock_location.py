from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    internal_owner_id = fields.Many2one(
        'res.partner',
        string='Location Owner'
    )

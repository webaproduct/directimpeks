from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    internal_owner_id = fields.Many2one('res.partner', string='Product Owner')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
    buyer_id = fields.Many2one(
        'res.partner', 
        string='Recipient', 
        related='demand_group_id.partner_id',
        store=True
    )

from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    internal_owner_id = fields.Many2one('res.partner', string='Власник товару')
    purchase_order_id = fields.Many2one('purchase.order', string='Замовлення на купівлю')
    demand_group_id = fields.Many2one('demand.group', string='Група попиту')
    buyer_id = fields.Many2one(
        'res.partner', 
        string='Отримувач', 
        related='demand_group_id.partner_id',
        store=True
    )

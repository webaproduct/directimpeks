from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    demand_group_id = fields.Many2one(
        'demand.group', 
        string='Група попиту',
        related='purchase_line_id.demand_group_id',         store=True
    )
    
    buyer_id = fields.Many2one(
        'res.partner', 
        string='Отримувач', 
        related='demand_group_id.partner_id'
    )

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    demand_group_id = fields.Many2one('demand.group', string='Група отримання')
    demand_partner_id = fields.Many2one(related='demand_group_id.partner_id', string='Партнер групи', store=True, readonly=True)

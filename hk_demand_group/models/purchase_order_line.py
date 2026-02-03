from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    demand_group_id = fields.Many2one('demand.group', string='Receiving Group')
    demand_partner_id = fields.Many2one(related='demand_group_id.partner_id', string='Group Partner', store=True, readonly=True)
    source_purchase_order_id = fields.Many2one('purchase.order', string='Source Purchase Order')
    source_purchase_order_line_id = fields.Many2one('purchase.order.line', string='Source Purchase Order Line')

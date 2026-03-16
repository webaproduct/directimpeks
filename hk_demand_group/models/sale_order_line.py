from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    delivery_date = fields.Date(string='Дата доставки')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    purshase_ref = fields.Char(string='Purchase reference')

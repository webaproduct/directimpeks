from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    delivery_date = fields.Date(string='Дата доставки')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    purshase_ref = fields.Char(string='Purchase reference')
    amount_delivered = fields.Monetary(string='Вартість доставленого товару', compute='_compute_amount_delivered', store=True, readonly=True)
    remain_qty = fields.Float(string='Залишилось доставити кількість', compute='_compute_remain_qty', store=True, readonly=True)
    remain_amount = fields.Monetary(string='Залишилось доставити Вартість', compute='_compute_remain_amount', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Покупець', related='order_id.partner_id', store=True, readonly=True)

    @api.depends('qty_delivered', 'price_unit')
    def _compute_amount_delivered(self):
        for line in self:
            line.amount_delivered = line.qty_delivered * line.price_unit

    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_remain_qty(self):
        for line in self:
            diff = line.product_uom_qty - line.qty_delivered
            line.remain_qty = diff if diff > 0 else 0.0

    @api.depends('product_uom_qty', 'qty_delivered', 'price_total', 'amount_delivered')
    def _compute_remain_amount(self):
        for line in self:
            diff = line.product_uom_qty - line.qty_delivered
            if diff > 0:
                line.remain_amount = line.price_total - line.amount_delivered
            else:
                line.remain_amount = 0.0

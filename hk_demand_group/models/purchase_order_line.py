from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    demand_group_id = fields.Many2one('demand.group', string='Receiving Group')
    demand_partner_id = fields.Many2one(related='demand_group_id.partner_id', string='Group Partner', store=True, readonly=True)
    source_purchase_order_id = fields.Many2one('purchase.order', string='Source Purchase Order')
    source_purchase_order_line_id = fields.Many2one('purchase.order.line', string='Source Purchase Order Line')
    amount_received = fields.Monetary(string='Вартість отриманого товару', compute='_compute_amount_received', store=True, readonly=True)
    remain_qty = fields.Float(string='Залишилось отримати кількість', compute='_compute_remain_qty', store=True, readonly=True)
    remain_amount = fields.Monetary(string='Залишилось отримати Вартість', compute='_compute_remain_amount', store=True, readonly=True)
    partner_ref = fields.Char(string='Референс постачальника', related='order_id.partner_ref', store=True, readonly=True)

    @api.depends('qty_received', 'price_unit', 'discount')
    def _compute_amount_received(self):
        for line in self:
            price_unit_discounted = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.amount_received = line.qty_received * price_unit_discounted

    @api.depends('product_qty', 'qty_received')
    def _compute_remain_qty(self):
        for line in self:
            diff = line.product_qty - line.qty_received
            line.remain_qty = diff if diff > 0 else 0.0

    @api.depends('product_qty', 'qty_received', 'price_total', 'amount_received')
    def _compute_remain_amount(self):
        for line in self:
            diff = line.product_qty - line.qty_received
            if diff > 0:
                line.remain_amount = line.price_total - line.amount_received
            else:
                line.remain_amount = 0.0

    @api.onchange('product_id', 'order_id')
    def _onchange_product_date_planned(self):
        if self.product_id and self.order_id:
            # Якщо це дозамовлення та не фактична закупівля
            if self.order_id.additional_purchase and not self.order_id.fact_purchase:
                # Дата з поля "Очікуване прибуття" замовлення
                if self.order_id.date_planned:
                    self.date_planned = self.order_id.date_planned
            # Якщо це НЕ дозамовлення та не фактична закупівля
            elif not self.order_id.additional_purchase and not self.order_id.fact_purchase:
                # Дата з картки товару
                if self.product_id.date_planned:
                    self.date_planned = self.product_id.date_planned

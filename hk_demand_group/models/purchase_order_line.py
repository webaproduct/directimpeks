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
    partner_ref = fields.Char(string='Референс постачальника', related='source_purchase_order_id.partner_ref', store=True, readonly=True)
    brand_id = fields.Many2one('product.brand', string='Бренд', related='product_id.brand_id', store=True, readonly=True)
    number_line = fields.Char(string='№ лінії', related='product_id.number_line', store=True, readonly=True)
    season_base = fields.Char(string='Сезон/база', related='product_id.season_base', store=True, readonly=True)
    category_one = fields.Char(string='Категорія 1', related='product_id.category_one', store=True, readonly=True)
    category_two = fields.Char(string='Категорія 2', related='product_id.category_two', store=True, readonly=True)
    form = fields.Char(string='Форма', related='product_id.form', store=True, readonly=True)
    attribute_line_ids = fields.Many2many(
        comodel_name='product.template.attribute.value',
        relation='purchase_order_line_attribute_value',
        string="Атрибути",
        compute='_compute_attr', store=True)
    delivery_date = fields.Date(string='Delivery date', compute='_compute_delivery_date', store=True)

    @api.depends('product_id', 'product_id.product_template_attribute_value_ids')
    def _compute_attr(self):
        for line in self:
            if line.product_id and line.product_id.product_tmpl_id:
                line.attribute_line_ids = line.product_id.product_template_attribute_value_ids
            else:
                line.attribute_line_ids = False

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

    @api.depends('order_id.date_planned', 'order_id.fact_purchase', 'order_id.additional_purchase', 'product_id', 'product_id.date_planned')
    def _compute_delivery_date(self):

        for line in self:
            if not line.order_id.fact_purchase and line.qty_received == 0:
                if line.product_id and line.order_id:
                    # Якщо це дозамовлення та не фактична закупівля
                    if line.order_id.additional_purchase:
                        # Дата з поля "Очікуване прибуття" замовлення
                        if line.order_id.date_planned:
                            line.delivery_date = line.order_id.date_planned
                    # Якщо це НЕ дозамовлення та не фактична закупівля
                    elif not line.order_id.additional_purchase:
                        # Дата з картки товару
                        if line.product_id.date_planned:
                            line.delivery_date = line.product_id.date_planned

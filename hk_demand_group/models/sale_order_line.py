from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    delivery_date = fields.Date(string='Дата доставки', copy=False)
    vendor_id = fields.Many2one('res.partner', string='Vendor', copy=False)
    purshase_ref = fields.Char(string='Purchase reference', copy=False)
    amount_delivered = fields.Monetary(string='Вартість доставленого товару', compute='_compute_amount_delivered', store=True, readonly=True)
    remain_qty = fields.Float(string='Залишилось доставити кількість', compute='_compute_remain_qty', store=True, readonly=True)
    remain_amount = fields.Monetary(string='Залишилось доставити Вартість', compute='_compute_remain_amount', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Покупець', related='order_id.partner_id', store=True, readonly=True)
    brand_id = fields.Many2one('product.brand', string='Бренд', related='product_id.brand_id', store=True, readonly=True)
    number_line = fields.Char(string='№ лінії', related='product_id.number_line', store=True, readonly=True)
    season_base = fields.Char(string='Сезон/база', related='product_id.season_base', store=True, readonly=True)
    category_one = fields.Char(string='Категорія 1', related='product_id.category_one', store=True, readonly=True)
    category_two = fields.Char(string='Категорія 2', related='product_id.category_two', store=True, readonly=True)
    form = fields.Char(string='Форма', related='product_id.form', store=True, readonly=True)
    attribute_line_value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        relation='sale_order_line_attribute_value_',
        string="Атрибути",
        compute='_compute_attr_value', store=True)


    @api.depends('product_id', 'product_id.product_template_attribute_value_ids')
    def _compute_attr_value(self):
        for line in self:
            if line.product_id:
                line.attribute_line_value_ids = line.product_id.attribute_line_ids.value_ids
            else:
                line.attribute_line_value_ids = False

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

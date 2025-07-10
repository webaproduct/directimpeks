from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DemandGroup(models.Model):
    _name = 'demand.group'
    _description = 'Група замовлень'
    _order = 'id desc'

    name = fields.Char(string='Назва', required=True, copy=False, default=lambda self: _('Нова'))
    active = fields.Boolean(default=True)
    
    # Зв'язки з sale.order або stock.request
    sale_order_id = fields.Many2one('sale.order', string='Замовлення на продаж')
    stock_request_id = fields.Many2one('stock.request', string='Запит на склад')
    partner_id = fields.Many2one('res.partner', string='Партнер')
    
    
    # @api.constrains('sale_order_id', 'stock_request_id')
    # def _check_relation_type(self):
    #     """Перевірка, що група пов'язана або з sale.order, або з stock.request, але не з обома одночасно"""
    #     for record in self:
    #         if record.sale_order_id and record.stock_request_id:
    #             raise ValidationError(_('Група може бути пов\'язана або з замовленням на продаж, або з запитом на склад, але не з обома одночасно.'))
    #         if not record.sale_order_id and not record.stock_request_id:
    #             raise ValidationError(_('Група повинна бути пов\'язана або з замовленням на продаж, або з запитом на склад.'))
    

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DemandGroup(models.Model):
    _name = 'demand.group'
    _description = 'Order Group'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True, copy=False, default=lambda self: _('New'), store=True, compute='_compute_name')
    active = fields.Boolean(default=True)
    
    # Relations with sale.order or stock.request
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    stock_request_id = fields.Many2one('stock.request', string='Stock Request')
    partner_id = fields.Many2one('res.partner', string='Partner')

    def _compute_name(self):
        self.name =  f'{self.partner_id}/{self.sale_order_id.name if self.sale_order_id else self.stock_request_id.name if self.stock_request_id else ""}'
    
    # @api.constrains('sale_order_id', 'stock_request_id')
    # def _check_relation_type(self):
    #     """Check that the group is associated with either sale.order or stock.request, but not both at the same time"""
    #     for record in self:
    #         if record.sale_order_id and record.stock_request_id:
    #             raise ValidationError(_('The group can be associated with either a sales order or a stock request, but not both at the same time.'))
    #         if not record.sale_order_id and not record.stock_request_id:
    #             raise ValidationError(_('The group must be associated with either a sales order or a stock request.'))
    

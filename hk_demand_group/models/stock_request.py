from odoo import api, fields, models, _


class StockRequest(models.Model):
    _inherit = 'stock.request'

    demand_group_id = fields.Many2one('demand.group', string='Група попиту')
    
    def action_confirm(self):
        """Розширення стандартного методу підтвердження для створення групи попиту"""
        res = super(StockRequest, self).action_confirm()
        
        for request in self:
            if not request.demand_group_id:
                # Створюємо новий запис demand.group
                vals = {
                    'name': request.name,
                    'partner_id': request.partner_id.id,
                    'stock_request_id': request.id,
                }
                demand_group = self.env['demand.group'].create(vals)
                
                # Зберігаємо посилання на створену групу
                request.demand_group_id = demand_group.id
        
        return res

    def action_create_picking(self):
        """Розширення стандартного методу створення переміщення"""
        if self.env.user.has_group('stock.group_stock_manager'):
            for record in self:
                picking_line = []
                picking_data = {
                    'partner_id': record.partner_id.id,
                    'picking_type_id': record.picking_type_id.id,
                    'origin': self.name,
                    'location_id': record.delivery_location_id.id,
                    'location_dest_id': record.stock_location_id.id,
                    'move_ids_without_package': picking_line,
                    #додаємо групу
                    'demand_group_id': record.demand_group_id.id,
                }
                for lines in self.stock_line_ids:
                    picking_line.append(((0, 0, {
                        'product_id': lines.product_id.id,
                        'name': lines.description,
                        'product_uom_qty': lines.product_qty,
                        'location_id': record.delivery_location_id.id,
                        'location_dest_id': record.stock_location_id.id,
                        'product_uom': lines.product_id.uom_id.id,
                        # додаємо групу
                        'demand_group_id': record.demand_group_id.id,
                    })))

                picking_id = self.env['stock.picking'].create(picking_data)
                record.write({
                    'states': 'approve',
                    'approved_by': self.env.user,
                })


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    demand_group_id = fields.Many2one('demand.group', string='Група попиту')
    
    def action_confirm(self):
        """Розширення стандартного методу підтвердження для створення групи попиту"""
        # Викликаємо оригінальний метод
        res = super(SaleOrder, self).action_confirm()
        
        for order in self:
            # Якщо група попиту не встановлена, створюємо нову
            if not order.demand_group_id:
                # Створюємо новий запис demand.group
                vals = {
                    'name': f'{order.partner_id.name}/{order.name}',
                    'partner_id': order.partner_id.id,
                    'sale_order_id': order.id,
                }
                demand_group = self.env['demand.group'].create(vals)
                
                # Зберігаємо посилання на створену групу
                order.demand_group_id = demand_group.id
                
                # Оновлюємо поля у переміщеннях, створених на підставі цього замовлення
                for picking in order.picking_ids:
                    picking.demand_group_id = demand_group.id
                    # Оновлюємо поля у пов'язаних stock.move
                    for move in picking.move_ids_without_package:
                        move.demand_group_id = demand_group.id
        
        return res

    def copy(self, default=None):
        """При копіюванні замовлення не копіюємо значення demand_group_id"""
        default = dict(default or {})
        default['demand_group_id'] = False
        return super(SaleOrder, self).copy(default)
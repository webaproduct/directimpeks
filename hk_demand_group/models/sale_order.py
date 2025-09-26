from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
    
    def action_confirm(self):
        """Extension of the standard confirm method to create a demand group"""
        # Call original method
        res = super(SaleOrder, self).action_confirm()
        
        for order in self:
            # If a demand group is not set, create a new one
            if not order.demand_group_id:
                # Create a new demand.group record
                vals = {
                    'name': f'{order.partner_id.name}/{order.name}',
                    'partner_id': order.partner_id.id,
                    'sale_order_id': order.id,
                }
                demand_group = self.env['demand.group'].create(vals)
                
                # Save a reference to the created group
                order.demand_group_id = demand_group.id
                
                # Update fields in pickings created from this order
                for picking in order.picking_ids:
                    picking.demand_group_id = demand_group.id
                    # Update fields in related stock.move
                    for move in picking.move_ids_without_package:
                        move.demand_group_id = demand_group.id
        
        return res

    def copy(self, default=None):
        """When copying the order, do not copy demand_group_id"""
        default = dict(default or {})
        default['demand_group_id'] = False
        return super(SaleOrder, self).copy(default)
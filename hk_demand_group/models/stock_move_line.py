from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    demand_group_id = fields.Many2one(
        'demand.group', 
        string='Demand Group',
        related='move_id.demand_group_id',         store=True
    )
    
    buyer_id = fields.Many2one(
        'res.partner', 
        string='Recipient', 
        related='demand_group_id.partner_id'
    )
    def _prepare_new_lot_vals(self):
        """Extension of the lot creation method to populate additional fields"""
        vals = super(StockMoveLine, self)._prepare_new_lot_vals()
        
        # Add internal_owner_id, group_purchase and group_demand fields
        if self.picking_id and self.picking_id.internal_owner_id:
            vals['internal_owner_id'] = self.picking_id.internal_owner_id.id
        elif self.move_id and self.move_id.picking_id and self.move_id.picking_id.internal_owner_id:
            vals['internal_owner_id'] = self.move_id.picking_id.internal_owner_id.id
        
        if self.move_id and self.move_id.purchase_line_id and self.move_id.purchase_line_id.order_id:
            vals['purchase_order_id'] = self.move_id.purchase_line_id.order_id.id
        
        if self.move_id and self.move_id.demand_group_id:
            vals['demand_group_id'] = self.move_id.demand_group_id.id
        # elif self.picking_id and self.picking_id.demand_group_id:
        #     vals['demand_group_id'] = self.picking_id.demand_group_id.id
        
        return vals

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _prepare_new_lot_vals(self):
        """Розширення методу створення лотів для заповнення додаткових полів"""
        vals = super(StockMoveLine, self)._prepare_new_lot_vals()
        
        # Додаємо поля internal_owner_id, group_purchase та group_demand
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

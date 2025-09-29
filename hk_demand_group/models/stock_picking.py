from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
    internal_owner_id = fields.Many2one('res.partner', string='Product Owner')
    
    @api.model
    def create(self, vals):
        """Extension of the create method to populate internal_owner_id and demand_group_id fields"""
        # If the picking is created from a purchase order
        if vals.get('purchase_id'):
            purchase_order = self.env['purchase.order'].browse(vals['purchase_id'])
            if purchase_order.internal_owner_id:
                vals['internal_owner_id'] = purchase_order.internal_owner_id.id
            if purchase_order.demand_group_id:
                vals['demand_group_id'] = purchase_order.demand_group_id.id

        return super(StockPicking, self).create(vals)

    def write(self, vals):
        """Extension of the write method to populate fields on related stock.move lines"""
        res = super(StockPicking, self).write(vals)

        # If demand_group_id is changed, update it on all related stock.move lines
        if 'demand_group_id' in vals:
            for picking in self:
                for move in picking.move_ids_without_package:
                    move.demand_group_id = picking.demand_group_id.id

        return res

    def button_validate(self):
        """
        Extension of the standard picking validation method to populate
        demand_group_id and buyer_id fields on the stock.move model
        """
        # Before validation, populate fields on related stock.move records
        for picking in self:
            # Guard: incoming pickings must have an internal owner set before validation
            if picking.picking_type_code == 'incoming' and not picking.internal_owner_id:
                raise UserError(_("Для вхідного переміщення потрібно заповнити поле 'Власник' (internal_owner_id) перед підтвердженням."))
            if picking.demand_group_id:
                for move in picking.move_ids_without_package:
                    move.demand_group_id = picking.demand_group_id.id
        
        return super(StockPicking, self).button_validate()
        
    def copy(self, default=None):
        """
        Extension of the standard copy method to ensure the demand_group_id field
        is copied on stock.move lines
        """
        self.ensure_one()
        default = dict(default or {})
        
        # Create a copy of the picking
        new_picking = super(StockPicking, self).copy(default)
        
        # Copy demand_group_id into stock.move lines
        if self.demand_group_id and new_picking.demand_group_id:
            for move in new_picking.move_ids_without_package:
                move.demand_group_id = new_picking.demand_group_id.id
        
        # Copy internal_owner_id into stock.move lines
        if self.internal_owner_id and new_picking.internal_owner_id:
            for move in new_picking.move_ids_without_package:
                if hasattr(move, 'internal_owner_id'):
                    move.internal_owner_id = new_picking.internal_owner_id.id
        
        return new_picking

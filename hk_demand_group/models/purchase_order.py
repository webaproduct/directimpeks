from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    internal_owner_id = fields.Many2one('res.partner', string='Product Owner')
    demand_group_id = fields.Many2one('demand.group', string='Demand Group')

    def _prepare_picking(self):
        """
        Extension of the standard method to add fields demand_group_id and internal_owner_id
        when creating a picking
        """
        res = super(PurchaseOrder, self)._prepare_picking()
        # if self.demand_group_id:
        #     res['demand_group_id'] = self.demand_group_id.id
        if self.internal_owner_id:
            res['internal_owner_id'] = self.internal_owner_id.id
        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        # After confirming the order, ensure that all created pickings
        # have correct values for demand_group_id and internal_owner_id
        for order in self:
            for picking in order.picking_ids:
                # if order.demand_group_id and not picking.demand_group_id:
                #     picking.demand_group_id = order.demand_group_id.id
                if order.internal_owner_id and not picking.internal_owner_id:
                    picking.internal_owner_id = order.internal_owner_id.id
                # Update related stock moves
                # for move in picking.move_ids_without_package:
                #     if order.demand_group_id:
                #         move.demand_group_id = order.demand_group_id.id

        return res

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    internal_owner_id = fields.Many2one('res.partner', string='Власник товару')
    demand_group_id = fields.Many2one('demand.group', string='Група попиту')

    def _prepare_picking(self):
        """
        Розширення стандартного методу для додавання полів demand_group_id та internal_owner_id
        при створенні переміщення
        """
        res = super(PurchaseOrder, self)._prepare_picking()
        # if self.demand_group_id:
        #     res['demand_group_id'] = self.demand_group_id.id
        if self.internal_owner_id:
            res['internal_owner_id'] = self.internal_owner_id.id
        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        # Після підтвердження замовлення, переконуємося, що всі створені переміщення
        # мають правильні значення demand_group_id та internal_owner_id
        for order in self:
            for picking in order.picking_ids:
                # if order.demand_group_id and not picking.demand_group_id:
                #     picking.demand_group_id = order.demand_group_id.id
                if order.internal_owner_id and not picking.internal_owner_id:
                    picking.internal_owner_id = order.internal_owner_id.id
                # Оновлюємо пов'язані переміщення товарів
                # for move in picking.move_ids_without_package:
                #     if order.demand_group_id:
                #         move.demand_group_id = order.demand_group_id.id

        return res

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    demand_group_id = fields.Many2one('demand.group', string='Група попиту')
    internal_owner_id = fields.Many2one('res.partner', string='Власник товару')
    
    @api.model
    def create(self, vals):
        """Розширення методу створення для заповнення полів internal_owner_id та demand_group_id"""
        # Якщо переміщення створюється з замовлення на купівлю
        if vals.get('purchase_id'):
            purchase_order = self.env['purchase.order'].browse(vals['purchase_id'])
            if purchase_order.internal_owner_id:
                vals['internal_owner_id'] = purchase_order.internal_owner_id.id
            if purchase_order.demand_group_id:
                vals['demand_group_id'] = purchase_order.demand_group_id.id

        return super(StockPicking, self).create(vals)

    def write(self, vals):
        """Розширення методу запису для заповнення полів у пов'язаних stock.move"""
        res = super(StockPicking, self).write(vals)

        # Якщо змінюється поле demand_group_id, оновлюємо його у всіх пов'язаних stock.move
        if 'demand_group_id' in vals:
            for picking in self:
                for move in picking.move_ids_without_package:
                    move.demand_group_id = picking.demand_group_id.id

        return res

    def button_validate(self):
        """
        Розширення стандартного методу підтвердження переміщення для заповнення полів
        demand_group_id та buyer_id у моделі stock.move
        """
        # Перед підтвердженням переміщення заповнюємо поля у пов'язаних stock.move
        for picking in self:
            if picking.demand_group_id:
                for move in picking.move_ids_without_package:
                    move.demand_group_id = picking.demand_group_id.id
        
        return super(StockPicking, self).button_validate()

from odoo import api, fields, models, _
from collections import defaultdict
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    demand_group_id = fields.Many2one(
        'demand.group',
        string='Demand Group',
        related='lot_id.demand_group_id',         store=True
    )
    
    internal_owner_id = fields.Many2one(
        'res.partner',
        string='Product Owner',
        related='lot_id.internal_owner_id',
        store=True
    )
    
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        related='lot_id.purchase_order_id',
        store=True
    )
    
    buyer_id = fields.Many2one(
        'res.partner',
        string='Recipient',
        related='lot_id.buyer_id',
        store=True
    )

    def _get_reserve_quantity(self, product_id, location_id, quantity, product_packaging_id=None, uom_id=None, lot_id=None, package_id=None, owner_id=None, strict=False):
        """Extension of the standard method to consider demand_group_id when reserving inventory.
        
        If demand_group_id is in the context, inventory will be reserved taking this parameter into account.
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        
        # Get demand_group_id from context if it exists
        demand_group_id = self.env.context.get('demand_group_id', False)
        
        # Call the standard method to get inventory
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, qty=quantity)
        
        # If there is demand_group_id in the context, filter inventory
        if not (demand_group_id and quants):
            return []
        # Get all lots associated with this demand group
        demand_group_lots = self.env['stock.lot'].search([('demand_group_id', '=', demand_group_id)])

        if not (demand_group_lots):
            return []
        # Filter inventory to first use those associated with this demand group
        priority_quants = quants.filtered(lambda q: q.lot_id in demand_group_lots)

        # If there are priority quants, use them first
        if not (priority_quants):
            return []
        # Check if there are enough priority quants
        priority_available = priority_quants._get_available_quantity(product_id, location_id, lot_id, package_id, owner_id, strict)

        if float_compare(priority_available, quantity, precision_rounding=rounding) >= 0:
            # If there are enough priority quants, use only them
            quants = priority_quants
        else:
            # If there are not enough priority quants, sort all quants so that priority ones are first
            other_quants = quants - priority_quants
            # Create a new recordset with priority quants first
            sorted_quants = self.env['stock.quant']
            sorted_quants |= priority_quants
            sorted_quants |= other_quants
            quants = sorted_quants
        
        # Continue with standard reservation logic
        available_quantity = quants._get_available_quantity(product_id, location_id, lot_id, package_id, owner_id, strict)

        # do full packaging reservation when it's needed
        if product_packaging_id and product_id.product_tmpl_id.categ_id.packaging_reserve_method == "full":
            available_quantity = product_packaging_id._check_qty(available_quantity, product_id.uom_id, "DOWN")

        quantity = min(quantity, available_quantity)

        # Unit conversion if needed
        if not strict and uom_id and product_id.uom_id != uom_id:
            quantity_move_uom = product_id.uom_id._compute_quantity(quantity, uom_id, rounding_method='DOWN')
            quantity = uom_id._compute_quantity(quantity_move_uom, product_id.uom_id, rounding_method='HALF-UP')

        if quants.product_id.tracking == 'serial':
            if float_compare(quantity, int(quantity), precision_rounding=rounding) != 0:
                quantity = 0

        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = sum(quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.', product_id.display_name))
        else:
            return reserved_quants

        negative_reserved_quantity = defaultdict(float)
        for quant in quants:
            if float_compare(quant.quantity - quant.reserved_quantity, 0, precision_rounding=rounding) < 0:
                negative_reserved_quantity[(quant.location_id, quant.lot_id, quant.package_id, quant.owner_id)] += quant.quantity - quant.reserved_quantity
        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                negative_quantity = negative_reserved_quantity[(quant.location_id, quant.lot_id, quant.package_id, quant.owner_id)]
                if negative_quantity:
                    negative_qty_to_remove = min(abs(negative_quantity), max_quantity_on_quant)
                    negative_reserved_quantity[(quant.location_id, quant.lot_id, quant.package_id, quant.owner_id)] += negative_qty_to_remove
                    max_quantity_on_quant -= negative_qty_to_remove
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
                break
        return reserved_quants

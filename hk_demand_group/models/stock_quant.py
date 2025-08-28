from odoo import api, fields, models, _
from collections import defaultdict
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    demand_group_id = fields.Many2one(
        'demand.group',
        string='Група попиту',
        related='lot_id.demand_group_id',         store=True
    )

    def _get_reserve_quantity(self, product_id, location_id, quantity, product_packaging_id=None, uom_id=None, lot_id=None, package_id=None, owner_id=None, strict=False):
        """Розширення стандартного методу для врахування demand_group_id при резервуванні запасів.
        
        Якщо в контексті є demand_group_id, то запаси будуть резервуватися з урахуванням цього параметру.
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        
        # Отримуємо demand_group_id з контексту, якщо він є
        demand_group_id = self.env.context.get('demand_group_id', False)
        
        # Виклик стандартного методу для отримання запасів
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, qty=quantity)
        
        # Якщо є demand_group_id в контексті, фільтруємо запаси
        if not (demand_group_id and quants):
            return []
        # Отримуємо всі партії (lots), які пов'язані з цією групою попиту
        demand_group_lots = self.env['stock.lot'].search([('demand_group_id', '=', demand_group_id)])

        if not (demand_group_lots):
            return []
        # Фільтруємо запаси, щоб спочатку використовувати ті, що пов'язані з цією групою попиту
        priority_quants = quants.filtered(lambda q: q.lot_id in demand_group_lots)

        # Якщо є пріоритетні запаси, використовуємо їх першими
        if not (priority_quants):
            return []
            # Перевіряємо, чи достатньо пріоритетних запасів
            priority_available = priority_quants._get_available_quantity(product_id, location_id, lot_id, package_id, owner_id, strict)

            if float_compare(priority_available, quantity, precision_rounding=rounding) >= 0:
                # Якщо пріоритетних запасів достатньо, використовуємо тільки їх
                quants = priority_quants
            else:
                # Якщо пріоритетних запасів недостатньо, сортуємо всі запаси так, щоб пріоритетні були першими
                other_quants = quants - priority_quants
                # Створюємо новий recordset з пріоритетними запасами спочатку
                sorted_quants = self.env['stock.quant']
                sorted_quants |= priority_quants
                sorted_quants |= other_quants
                quants = sorted_quants
        
        # Продовжуємо стандартну логіку резервування
        available_quantity = quants._get_available_quantity(product_id, location_id, lot_id, package_id, owner_id, strict)

        # do full packaging reservation when it's needed
        if product_packaging_id and product_id.product_tmpl_id.categ_id.packaging_reserve_method == "full":
            available_quantity = product_packaging_id._check_qty(available_quantity, product_id.uom_id, "DOWN")

        quantity = min(quantity, available_quantity)

        # Конвертація одиниць виміру, якщо потрібно
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

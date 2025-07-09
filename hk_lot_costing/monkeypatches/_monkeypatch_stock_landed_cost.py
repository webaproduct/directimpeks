from odoo import _
from odoo.exceptions import UserError

from odoo.addons.stock_landed_costs.models.stock_landed_cost import StockLandedCost


def get_valuation_lines(self):
    """Overwrite: if cost_method not in 'real' -> continue"""
    self.ensure_one()
    lines = []

    for move in self._get_targeted_move_ids():
        # it doesn't make sense to make a landed cost for a product that isn't set
        # as being valuated in real time at real cost
        if (
            move.product_id.cost_method not in self.get_valued_methods()
            or move.state == "cancel"
            or not move.quantity
        ):
            continue
        qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
        vals = {
            "product_id": move.product_id.id,
            "move_id": move.id,
            "quantity": qty,
            "former_cost": sum(move.stock_valuation_layer_ids.mapped("value")),
            "weight": move.product_id.weight * qty,
            "volume": move.product_id.volume * qty,
        }
        lines.append(vals)

    if not lines:
        target_model_descriptions = dict(
            self._fields["target_model"]._description_selection(self.env)
        )
        raise UserError(
            _(
                "You cannot apply landed costs on the chosen %s(s). Landed costs can "
                "only be applied for products with FIFO or average costing method.",
                target_model_descriptions[self.target_model],
            )
        )
    return lines


def _get_patchable_methods():
    return [
        {
            "class": StockLandedCost,
            "method_name": "get_valuation_lines",
            "new_method": get_valuation_lines,
        },
    ]

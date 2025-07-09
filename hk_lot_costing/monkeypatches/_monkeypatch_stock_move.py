from odoo.tools.float_utils import float_is_zero

from odoo.addons.stock_account.models.stock_move import StockMove


def _get_out_svl_vals(self, forced_quantity):
    svl_vals_list = []
    for move in self:
        move = move.with_company(move.company_id)
        valued_move_lines = move._get_out_move_lines()
        valued_quantity = 0
        for valued_move_line in valued_move_lines:
            valued_quantity += valued_move_line.product_uom_id._compute_quantity(
                valued_move_line.quantity, move.product_id.uom_id
            )
        if float_is_zero(
            forced_quantity or valued_quantity,
            precision_rounding=move.product_id.uom_id.rounding,
        ):
            continue
        svl_vals = move.product_id._prepare_out_svl_vals(
            forced_quantity or valued_quantity, move.company_id, move
        )
        svl_vals.update(move._prepare_common_svl_vals())
        if forced_quantity:
            svl_vals["description"] = "Correction of %s (modification of past move)" % (
                move.picking_id.name or move.name
            )
        svl_vals["description"] += svl_vals.pop("rounding_adjustment", "")
        svl_vals_list.append(svl_vals)
    return svl_vals_list


def _get_patchable_methods():
    return [
        {
            "class": StockMove,
            "method_name": "_get_out_svl_vals",
            "new_method": _get_out_svl_vals,
        },
    ]

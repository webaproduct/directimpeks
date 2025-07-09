from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_common_svl_vals(self):
        vals = super()._prepare_common_svl_vals()
        if self.lot_ids:
            vals["lot_ids"] = [(6, 0, self.lot_ids.ids)]
            if self._is_in():
                unit_cost = abs(self._get_price_unit())
                self.lot_ids.write(
                    {
                        "unit_real_cost": unit_cost,
                        "stock_move_in_id": self.id,
                    }
                )
        return vals

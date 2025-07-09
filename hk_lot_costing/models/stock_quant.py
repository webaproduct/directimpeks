from odoo import api, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.depends("company_id", "location_id", "owner_id", "product_id", "quantity")
    def _compute_value(self):
        quant_with_real_categ = self.filtered(
            lambda q: q.product_id.cost_method == "real"
        )

        for quant in quant_with_real_categ:
            if quant.product_id.cost_method == "real":
                svl = self.env["stock.valuation.layer"].search(
                    [
                        ("product_id", "=", quant.product_id.id),
                        ("company_id", "=", quant.company_id.id),
                        ("lot_ids", "in", quant.lot_id.ids),
                    ]
                )
                value = sum(
                    s.remaining_qty * lot.unit_real_cost
                    for s, lot in zip(svl, svl.lot_ids, strict=False)
                )
                quant.value = value
                quant.currency_id = quant.company_id.currency_id
        return super(StockQuant, self - quant_with_real_categ)._compute_value()

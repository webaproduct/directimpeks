from odoo import fields, api, models
from odoo.tools import float_compare


class ProductionLot(models.Model):
    _inherit = "stock.lot"

    @api.model
    def get_available_lots_for_pos(self, vals):
        lots = self.sudo().search(
            [
                "&",
                ["product_id", "=", vals.get("product_id")],
                "|",
                ["company_id", "=", vals.get("company_id")],
                ["company_id", "=", False],
            ]
        )

        lots = lots.filtered(lambda l: float_compare(l.product_qty, 0, precision_digits=l.product_uom_id.rounding) > 0)
        return lots.mapped("name")


class PosConfig(models.Model):
    _inherit = "pos.config"

    lot_serial_no_restrict = fields.Boolean("Allow Lot/Serial No Restrict")

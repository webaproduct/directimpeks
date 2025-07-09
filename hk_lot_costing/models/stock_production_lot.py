from odoo import fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    # for real cost in lot
    unit_real_cost = fields.Float()
    stock_move_in_id = fields.Many2one(
        comodel_name="stock.move",
        string="Stock move (IN)",
        copy=False,
    )

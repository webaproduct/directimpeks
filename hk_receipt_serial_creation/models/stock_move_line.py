from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    serial_number = fields.Char()

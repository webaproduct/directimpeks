from odoo import models


class LandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def get_valued_methods(self):
        return ["fifo", "average", "real"]

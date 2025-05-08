from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    size_original_manufacturer = fields.Char(
        string="Size original (manufacturer)", translate=True)
    color_manufacturer = fields.Char(string="Color manufacturer", translate=True)
    palette_colors = fields.Char(string="Palette colors", translate=True)

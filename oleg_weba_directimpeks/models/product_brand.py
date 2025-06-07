from odoo import models, fields


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product brand"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True, translate=True)

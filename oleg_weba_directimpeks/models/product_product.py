from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    size_original_manufacturer = fields.Char(
        string="Size original (manufacturer)", translate=True)
    color_manufacturer = fields.Char(string="Color manufacturer", translate=True)
    palette_colors = fields.Char(string="Palette colors", translate=True)

    # <---------For customization pricelist----------->

    def _compute_variant_item_count(self):
        for product in self:
            domain = [
                ('pricelist_id.active', '=', True),
                '|',
                '|',  # Custom
                '&',
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('applied_on', '=', '1_product'),
                '&',
                ('product_id', '=', product.id),
                ('applied_on', '=', '0_product_variant'),
                '&',  # Custom
                ('brand_id', '=', self.brand_id.id),  # Custom
                ('applied_on', '=', '4_brand'),  # Custom
            ]
            product.pricelist_item_count = self.env[
                'product.pricelist.item'].search_count(domain)

    def open_pricelist_rules(self):
        res = super().open_pricelist_rules()
        res["domain"] = [
            '|',
            '|',  # Custom
            '&',
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('applied_on', '=', '1_product'),
            '&',
            ('product_id', '=', self.id),
            ('applied_on', '=', '0_product_variant'),
            '&',  # Custom
            ('brand_id', '=', self.brand_id.id),  # Custom
            ('applied_on', '=', '4_brand'),  # Custom
        ]
        return res
    # <---------For customization pricelist----------->

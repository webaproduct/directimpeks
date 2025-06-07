from odoo import models, fields, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(comodel_name="product.brand", string="Brand")
    number_line = fields.Char(string="Number Line", translate=True)
    name_line = fields.Char(string="Name Line", translate=True)
    season_base = fields.Char(string="Season/Base", translate=True)
    chemical_composition = fields.Char(string="Chemical composition", translate=True)
    code_2 = fields.Char(string="Code", translate=True)

    category_one = fields.Char(string="Category 1", translate=True)
    sub_category_one = fields.Char(string="Sub category 1", translate=True)
    sub_lower_category_one = fields.Char(string="Sub lower category 1", translate=True)

    category_two = fields.Char(string="Category 2", translate=True)
    sub_category_two = fields.Char(string="Sub category 2", translate=True)
    sub_lower_category_two = fields.Char(string="Sub lower category 2", translate=True)

    form = fields.Char(string="Form", translate=True)
    processing = fields.Char(string="Processing", translate=True)
    purpose_one = fields.Char(string="Purpose 1", translate=True)
    purpose_two = fields.Char(string="Purpose 2", translate=True)
    gender = fields.Char(string="Gender", translate=True)
    streak = fields.Char(string="Streak", translate=True)
    drying = fields.Char(string="Drying", translate=True)
    iron = fields.Char(string="Iron", translate=True)
    whitening = fields.Char(string="Whitening", translate=True)
    professional_cleaning = fields.Char(string="Professional cleaning", translate=True)
    meta_title = fields.Char(string="Meta title", translate=True)
    meta_description = fields.Char(string="Meta description", translate=True)
    short_description = fields.Char(string="Short description", translate=True)
    description = fields.Char(string="Description", translate=True)

    # <---------For customization pricelist----------->
    def _compute_item_count(self):
        for template in self:
            # Pricelist item count counts the rules applicable on current template or on
            # its variants.
            domain = [
                '&',
                '|',
                ('product_tmpl_id', '=', template.id),
                '|',  # Custom
                ('product_id', 'in', template.product_variant_ids.ids),
                ("brand_id", "=", self.brand_id.id),  # Custom

                ('pricelist_id.active', '=', True),
            ]
            template.pricelist_item_count = template.env[
                "product.pricelist.item"].search_count(domain)

    def open_pricelist_rules(self):
        res = super().open_pricelist_rules()
        res["domain"] = [
            "|",
            ("product_tmpl_id", "=", self.id),
            "|",  # Custom
            ("product_id", "in", self.product_variant_ids.ids),
            ("brand_id", "=", self.brand_id.id),  # Custom
        ]
        return res
    # <---------For customization pricelist----------->

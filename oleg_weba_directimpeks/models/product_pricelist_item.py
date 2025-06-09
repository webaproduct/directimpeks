from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    applied_on = fields.Selection(
        selection_add=[("4_brand", "Brand"),], ondelete={'4_brand': 'cascade'})
    brand_id = fields.Many2one(comodel_name="product.brand", string="Brand")

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id',
                 'compute_price', 'fixed_price', 'pricelist_id', 'percent_price',
                 'price_discount', 'price_surcharge', 'brand_id')
    def _compute_name_and_price(self):
        super()._compute_name_and_price()
        for item in self:
            if item.brand_id and item.applied_on == "4_brand":
                item.name = _("Brand: %s", item.brand_id.display_name)

    @api.constrains('product_id', 'product_tmpl_id', 'categ_id', 'brand_id')
    def _check_product_consistency(self):
        super()._check_product_consistency()
        for item in self:
            if item.applied_on == "4_brand" and not item.brand_id:
                raise ValidationError(
                    _("Please specify the brand for which this rule should be applied")
                )

    @api.onchange('product_id', 'product_tmpl_id', 'categ_id', 'brand_id')
    def _onchange_rule_content(self):
        if not self.user_has_groups(
                'product.group_sale_pricelist') and not self.env.context.get(
                'default_applied_on', False):
            # If advanced pricelists are disabled (applied_on field is not visible)
            # AND we aren't coming from a specific product template/variant.
            variants_rules = self.filtered('product_id')
            template_rules = (self - variants_rules).filtered('product_tmpl_id')

            brand_rules = (
                    self - variants_rules - template_rules).filtered("brand_id")  # Custom
            categ_rules = (
                    self - variants_rules - template_rules - brand_rules).filtered(
                "categ_id")  # Custom

            variants_rules.update({'applied_on': '0_product_variant'})
            template_rules.update({'applied_on': '1_product'})

            brand_rules.update({"applied_on": "4_brand"})  # Custom
            categ_rules.update({"applied_on": "2_product_category"})  # Custom

            (self - variants_rules - template_rules - brand_rules - categ_rules).update(
                {"applied_on": "3_global"})  # Custom

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        for values in vals_list:
            if (values.get("applied_on") and values["applied_on"] == "3_global" and
                    values.get("4_brand")):
                values["applied_on"] = "4_brand"

            # Ensure item consistency for later searches.
            applied_on = values["applied_on"]
            if applied_on == "3_global":
                values.update(dict(
                    product_id=None, product_tmpl_id=None, categ_id=None, brand_id=None))
            elif applied_on == "2_product_category":
                values.update(dict(product_id=None, product_tmpl_id=None, brand_id=None))
            elif applied_on == "4_brand":
                values.update(dict(product_id=None, product_tmpl_id=None, categ_id=None))
            elif applied_on == "1_product":
                values.update(dict(product_id=None, categ_id=None, brand_id=None))
            elif applied_on == "0_product_variant":
                values.update(dict(categ_id=None, brand_id=None))
        return res

    def write(self, values):
        res = super().write(values)

        # Ensure item consistency for later searches.
        if values.get('applied_on', False) and values["applied_on"] == "4_brand":
            values.update(dict(product_id=None, product_tmpl_id=None, categ_id=None))

        return res

    def _is_applicable_for(self, product, qty_in_product_uom):
        res = super()._is_applicable_for(product, qty_in_product_uom)

        is_product_template = product._name == "product.template"

        if self.applied_on == "2_brand":
            product_brand = product.brand_id if not is_product_template else False
            if product_brand != self.brand_id:
                res = False

        return res

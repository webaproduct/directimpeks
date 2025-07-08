from odoo import models, fields
from odoo.osv.expression import OR


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products, quantity, currency=None, uom=None,
                            date=False, compute_price=True, **kwargs):
        result = super()._compute_price_rule(products, quantity, currency, uom, date,
                                             compute_price, **kwargs)

        for product_id, (price, rule_id) in result.items():
            product = self.env["product.product"].browse(product_id)
            if rule_id and self._check_product_in_current_pricelist(product):
                continue  # оставляем как есть — найдено правило и товар есть в текущем
                # прайсе

            # Правило не найдено — берем lst_price
            result[product_id] = (product.lst_price, False)

        return result

    def _check_product_in_current_pricelist(self, product):
        self.ensure_one()
        date = fields.Date.today()

        # Основной фильтр: только текущий прайс
        base_domain = [
            ("pricelist_id", "=", self.id),
            "|",
                ("date_start", "=", False),
                ("date_start", "<=", date),
            "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
        ]

        domains = []

        # По product_id
        domains.append([
            ("applied_on", "=", "0_product_variant"),
            ("product_id", "=", product.id)
        ])

        # По product_tmpl_id
        domains.append([
            ("applied_on", "=", "1_product"),
            ("product_tmpl_id", "=", product.product_tmpl_id.id)
        ])

        # По бренду
        if product.brand_id:
            domains.append([
                ("applied_on", "=", "4_brand"),
                ("brand_id", "=", product.brand_id.id)
            ])

        # По категории (включая родительские)
        if product.categ_id:
            domains.append([
                ("applied_on", "=", "2_product_category"),
                ("categ_id", "child_of", product.categ_id.id)
            ])

        # Глобальные правила
        domains.append([("applied_on", "=", "3_global")])

        full_domain = base_domain + OR(domains)

        return bool(self.env["product.pricelist.item"].search_count(full_domain))

from odoo import models


class ContractLine(models.Model):
    _inherit = "contract.line"

    def _prepare_purchase_line_vals(self, dates, order_id=False):
        purchase_line_vals = {
            "product_id": self.product_id.id,
            "product_uom_qty": self._get_quantity_to_invoice(*dates),
            "product_uom": self.uom_id.id,
            "discount": self.discount,
            "contract_line_id": self.id,
            "display_type": self.display_type,
            "analytic_distribution": self.analytic_distribution,
        }
        if order_id:
            purchase_line_vals["order_id"] = order_id.id
        return purchase_line_vals

    def _prepare_purchase_line(self, order_id=False, purchase_values=False):
        self.ensure_one()
        dates = self._get_period_to_invoice(
            self.last_date_invoiced, self.recurring_next_date
        )
        purchase_line_vals = self._prepare_purchase_line_vals(dates, order_id=order_id)

        order_line = (
            self.env["purchase.order.line"]
            .with_company(self.contract_id.company_id.id)
            .new(purchase_line_vals)
        )
        if purchase_values and not order_id:
            purchase = (
                self.env["purchase.order"]
                .with_company(self.contract_id.company_id.id)
                .new(purchase_values)
            )
            order_line.order_id = purchase
        # Get other order line values from product onchange
        # order_line._onchange_product_id_warning()
        purchase_line_vals = order_line._convert_to_write(order_line._cache)
        # Insert markers
        name = self._insert_markers(dates[0], dates[1])
        purchase_line_vals.update(
            {
                "sequence": self.sequence,
                "name": name,
                "price_unit": self.price_unit,
            }
        )
        return purchase_line_vals

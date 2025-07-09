from odoo import fields, models
from odoo.tools import float_is_zero


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_in_svl_vals(self, quantity, unit_cost):
        vals = super()._prepare_in_svl_vals(quantity, unit_cost)
        if self.cost_method == "real":
            vals["remaining_qty"] = quantity
            vals["remaining_value"] = vals["value"]
        return vals

    def _prepare_out_svl_vals(self, quantity, company, move=None):
        """Overwrite: takes 'move' arg, added functionality for 'real' cost method"""
        if self.cost_method != "real":
            return super()._prepare_out_svl_vals(quantity, company)

        self.ensure_one()
        # Quantity is negative for out valuation layers.
        quantity = -1 * quantity
        vals = {
            "product_id": self.id,
            "value": quantity * self.standard_price,
            "unit_cost": self.standard_price,
            "quantity": quantity,
        }
        company_id = self.env.context.get("force_company", self.env.company.id)
        company = self.env["res.company"].browse(company_id)
        currency = company.currency_id
        # Quantity is negative for out valuation layers.
        quantity = -1 * quantity
        vals = {
            "product_id": self.id,
            "value": currency.round(quantity * self.standard_price),
            "unit_cost": self.standard_price,
            "quantity": quantity,
        }
        real_vals = self._run_real(abs(quantity), company, move)
        vals.update(real_vals)

        return vals

    def _run_real(self, quantity, company, move):
        """
        Copy from _run_fifo except selecting candidates
        (stock.valuation.layer) by lot from stock move lines
        """
        qty_to_take_on_candidates = quantity
        new_standard_price = 0
        tmp_value = 0  # to accumulate the value taken on the candidates

        if move:
            for move_line in move.move_line_ids.filtered(lambda line: line.lot_id):
                candidates = (
                    self.env["stock.valuation.layer"]
                    .sudo()
                    .search(
                        [
                            ("product_id", "=", self.id),
                            ("remaining_qty", ">", 0),
                            ("company_id", "=", company.id),
                            ("lot_ids", "in", move_line.lot_id.ids),
                        ]
                    )
                )
                for candidate in candidates:
                    qty_taken_on_candidate = min(
                        move_line.quantity, candidate.remaining_qty
                    )

                    candidate_unit_cost = (
                        candidate.remaining_value / candidate.remaining_qty
                    )
                    new_standard_price = candidate_unit_cost
                    value_taken_on_candidate = (
                        qty_taken_on_candidate * candidate_unit_cost
                    )
                    value_taken_on_candidate = candidate.currency_id.round(
                        value_taken_on_candidate
                    )
                    new_remaining_value = (
                        candidate.remaining_value - value_taken_on_candidate
                    )

                    candidate_vals = {
                        "remaining_qty": candidate.remaining_qty
                        - qty_taken_on_candidate,
                        "remaining_value": new_remaining_value,
                    }

                    candidate.write(candidate_vals)

                    qty_to_take_on_candidates -= qty_taken_on_candidate
                    tmp_value += value_taken_on_candidate

                    if float_is_zero(
                        qty_to_take_on_candidates,
                        precision_rounding=self.uom_id.rounding,
                    ):
                        if float_is_zero(
                            candidate.remaining_qty,
                            precision_rounding=self.uom_id.rounding,
                        ):
                            next_candidates = candidates.filtered(
                                lambda svl: svl.remaining_qty > 0
                            )
                            new_standard_price = (
                                next_candidates
                                and next_candidates[0].unit_cost
                                or new_standard_price
                            )
                        break

        vals = {}
        if float_is_zero(
            qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding
        ):
            vals = {
                "value": -tmp_value,
                "unit_cost": tmp_value / quantity,
            }
        else:
            if qty_to_take_on_candidates > 0:
                last_fifo_price = new_standard_price or self.standard_price
                negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
                tmp_value += abs(negative_stock_value)
                vals = {
                    "remaining_qty": -qty_to_take_on_candidates,
                    "value": -tmp_value,
                    "unit_cost": last_fifo_price,
                }
        return vals


class ProductCategory(models.Model):
    _inherit = "product.category"

    property_cost_method = fields.Selection(
        selection_add=[("real", "Real Lot Cost")],
        help="""Standard Price: The products are valued at their standard cost defined
        on the product. Average Cost (AVCO): The products are valued at weighted
        average cost. First In First Out (FIFO): The products are valued supposing
        those that enter the company first will also leave it first. Real Lot Cost:
        The products values depending on lot cost or by FIFO if lot not found""",
        ondelete={"real": "set default"},
    )

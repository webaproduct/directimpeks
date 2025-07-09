from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    contract_id = fields.Many2one(
        string="Contract",
        comodel_name="contract.contract",
        domain="[('partner_id', '=', partner_id), ('contract_type', '=', 'purchase')]",
    )
    is_contract_product = fields.Boolean(
        compute="_compute_is_contract_product",
    )

    is_contract_required = fields.Boolean(
        related="partner_id.is_contract_required",
    )

    @api.onchange("partner_id")
    def _onchange_partner_id_contracts(self):
        for record in self:
            record.contract_id = False

    @api.onchange("contract_id")
    def _onchange_contract_id(self):
        vals = {}
        analytic_account_id = self.contract_id.group_id.id
        if analytic_account_id:
            analytic_account_id = str(analytic_account_id)
            for line in self.order_line:
                if line.analytic_distribution:
                    vals["analytic_distribution"] = line.analytic_distribution
                if "analytic_distribution" in vals:
                    vals["analytic_distribution"][analytic_account_id] = (
                        vals["analytic_distribution"].get(analytic_account_id, 0) + 100
                    )
                else:
                    vals["analytic_distribution"] = {analytic_account_id: 100}
                line.update(vals)

    @api.depends("contract_id")
    def _compute_is_contract_product(self):
        for so in self:
            so.is_contract_product = len(so.contract_id.contract_line_ids) > 0

    def action_refresh_lines(self):
        self.ensure_one()
        self.write({"order_line": [(5, 0, 0)]})
        new_lines = []
        for line in self.contract_id.contract_line_ids:
            dates = line._get_period_to_invoice(
                line.last_date_invoiced, line.recurring_next_date
            )
            line_vals = line._prepare_sale_line_vals(dates, order_id=self)
            line_vals.update(
                {
                    "sequence": line.sequence,
                    "price_unit": line.price_unit,
                    "analytic_distribution": line.analytic_distribution,
                }
            )
            new_lines.append((0, 0, line_vals))
        return self.write({"order_line": new_lines})

    def _get_invoice_grouping_keys(self):
        res = super()._get_invoice_grouping_keys()
        res.append("contract_id")
        return res

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals["contract_id"] = self.contract_id.id
        return invoice_vals

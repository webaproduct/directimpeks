from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _validate_analytic_distribution(self):
        res = super()._validate_analytic_distribution()
        for line in self:
            if line.display_type:
                continue
            vals = {}
            analytic_account_id = line.order_id.contract_id.group_id.id
            if line.analytic_distribution:
                vals["analytic_distribution"] = line.analytic_distribution
            if analytic_account_id:
                analytic_account_id = str(analytic_account_id)
                if "analytic_distribution" in vals:
                    vals["analytic_distribution"][analytic_account_id] = (
                        vals["analytic_distribution"].get(analytic_account_id, 0) + 100
                    )
                else:
                    vals["analytic_distribution"] = {analytic_account_id: 100}
                line.update(vals)
        return res

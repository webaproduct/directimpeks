from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    contract_plan_id = fields.Many2one("account.analytic.plan")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    contract_plan_id = fields.Many2one(
        comodel_name="account.analytic.plan",
        related="company_id.contract_plan_id",
        readonly=False,
    )

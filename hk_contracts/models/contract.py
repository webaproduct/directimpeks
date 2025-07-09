from odoo import api, fields, models


class ContractContract(models.Model):
    _inherit = "contract.contract"

    contract_number = fields.Char()
    printable_title = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for contract in records:
            if contract.group_id:
                continue
            if not self.env.company.contract_plan_id:
                continue

            analytic_account_id = self.env["account.analytic.account"].create(
                {
                    "name": contract.name,
                    "partner_id": contract.partner_id.id,
                    "plan_id": self.env.company.contract_plan_id.id,
                }
            )
            # + "/" + contract.name
            if analytic_account_id:
                vals = {"group_id": analytic_account_id.id}
                super(ContractContract, contract).write(vals)

        return records

    @api.model
    def _get_contracts_to_invoice_domain(self, date_ref=None):
        """
        This method builds the domain to use to find all
        contracts (contract.contract) to invoice.
        :param date_ref: optional reference date to use instead of today
        :return: list (domain) usable on contract.contract
        """
        domain = []
        if not date_ref:
            date_ref = fields.Date.context_today(self)
        domain.extend([("recurring_next_date", "<=", date_ref)])
        domain.extend([("is_not_recurrence", "=", False)])
        return domain

    def _prepare_invoice(self, date_invoice, journal=None):
        invoice_vals = super()._prepare_invoice(date_invoice, journal=journal)
        invoice_vals["contract_id"] = self.id
        return invoice_vals

    # def _prepare_purchase(self, date_ref):
    #     self.ensure_one()
    #     purchase = self.env["purchase.order"].new(
    #         {
    #             "partner_id": self.partner_id,
    #             "date_order": fields.Date.to_string(date_ref),
    #             "origin": self.name,
    #             "company_id": self.company_id.id,
    #             "user_id": self.partner_id.user_id.id,
    #             "contract_id": self.id,
    #             # "analytic_account_id": self.group_id.id,
    #         }
    #     )
    #     if self.payment_term_id:
    #         purchase.payment_term_id = self.payment_term_id.id
    #     if self.fiscal_position_id:
    #         purchase.fiscal_position_id = self.fiscal_position_id.id
    #     return purchase._convert_to_write(purchase._cache)

    def _prepare_sale(self, date_ref):
        self.ensure_one()
        sale_values = super()._prepare_sale(date_ref)
        sale_values["contract_id"] = self.id
        return sale_values

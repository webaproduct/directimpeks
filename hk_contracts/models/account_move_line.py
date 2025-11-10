from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    contract_id = fields.Many2one(
        string="Contract",
        comodel_name="contract.contract",
        domain="[('partner_id', '=', partner_id)]",
    )
    contract_required = fields.Boolean(compute="_compute_contract_required")

    def write(self, vals):
        """Propagate up to the move the contract if applies."""
        result = super().write(vals)

        if self.env.context.get("skip_contract_compute"):
            return result

        for record in self.with_context(skip_contract_compute=True):
            move_id = self.env["account.move"].browse(
                vals.get("move_id", 0) or record.move_id.id
            )

            account_id = self.env["account.account"].browse(
                vals.get("account_id", 0) or record.account_id.id
            )
            if record.contract_required:
                record.update({"contract_id": move_id.contract_id.id})
            # else:
            #     record.update({"contract_id": False})

        return result

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)

        for record in lines:
            if record.contract_required:
                record.update({"contract_id": record.move_id.contract_id.id})
            # else:
            #     record.update({"contract_id": False})

        return lines

    @api.depends("move_id.move_type", "account_id")
    def _compute_contract_required(self):
        for rec in self:
            rec.contract_required = (
                rec.move_type
                in ["out_invoice", "out_refund", "in_invoice", "in_refund"]
                and rec.account_id.l10n_ua_track_by_contract
            )

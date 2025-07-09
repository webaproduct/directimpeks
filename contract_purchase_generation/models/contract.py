from odoo import _, api, fields, models


class ContractContract(models.Model):
    _inherit = "contract.contract"

    purchase_count = fields.Integer(compute="_compute_purchase_count")

    def _recurring_create_purchase(self, date_ref=False):
        purchases_values = self._prepare_recurring_purchases_values(date_ref)
        purchase_orders = self.env["purchase.order"].create(purchases_values)
        purchase_orders_to_confirm = purchase_orders.filtered(
            lambda purchase: purchase.contract_auto_confirm
        )
        purchase_orders_to_confirm.button_confirm()
        self._compute_recurring_next_date()
        return purchase_orders

    def _prepare_purchase(self, date_ref):
        self.ensure_one()
        purchase = self.env["purchase.order"].new(
            {
                "partner_id": self.partner_id,
                "date_order": fields.Date.to_string(date_ref),
                "origin": self.name,
                "company_id": self.company_id.id,
                "user_id": self.partner_id.user_id.id,
                # "analytic_account_id": self.group_id.id,
                "contract_id": self.id,
            }
        )
        if self.payment_term_id:
            purchase.payment_term_id = self.payment_term_id.id
        if self.fiscal_position_id:
            purchase.fiscal_position_id = self.fiscal_position_id.id
        return purchase._convert_to_write(purchase._cache)

    def _get_related_purchases(self):
        self.ensure_one()
        purchases = (
            self.env["purchase.order.line"]
            .search([("contract_line_id", "in", self.contract_line_ids.ids)])
            .mapped("order_id")
        )
        return purchases

    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec._get_related_purchases())

    def action_show_purchases(self):
        self.ensure_one()
        tree_view = self.env.ref(
            "purchase.purchase_order_view_tree", raise_if_not_found=False
        )
        form_view = self.env.ref(
            "purchase.purchase_order_form", raise_if_not_found=False
        )
        action = {
            "type": "ir.actions.act_window",
            "name": "Purchases Orders",
            "res_model": "purchase.order",
            "view_type": "form",
            "view_mode": "tree,kanban,form,calendar,pivot,graph,activity",
            "domain": [("id", "in", self._get_related_purchases().ids)],
        }
        if tree_view and form_view:
            action["views"] = [(tree_view.id, "tree"), (form_view.id, "form")]
        return action

    def recurring_create_purchase(self):
        """
        This method triggers the creation of the next purchase order of the
        contracts even if their next purchase order date is in the future.
        """
        purchases = self._recurring_create_purchase()
        for purchase_rec in purchases:
            self.message_post(
                body=_(
                    "Contract manually purchase order: "
                    '<a href="#" data-oe-model="%(model)s" data-oe-id="%(id)s">'
                    "Purchase Order"
                    "</a>"
                )
                % {"model": purchase_rec._name, "id": purchase_rec.id}
            )
        return purchases

    def _prepare_recurring_purchases_values(self, date_ref=False):
        """
        This method builds the list of purchases values to create, based on
        the lines to purchase of the contracts in self.
        !!! The date of next invoice (recurring_next_date) is updated here !!!
        :return: list of dictionaries (invoices values)
        """
        purchases_values = []
        for contract in self:
            if not date_ref:
                date_ref = contract.recurring_next_date
            if not date_ref:
                # this use case is possible when recurring_create_invoice is
                # called for a finished contract
                continue
            contract_lines = contract._get_lines_to_invoice(date_ref)
            if not contract_lines:
                continue
            purchase_values = contract._prepare_purchase(date_ref)
            for line in contract_lines:
                purchase_values.setdefault("order_line", [])
                invoice_line_values = line._prepare_purchase_line(
                    purchase_values=purchase_values,
                )
                if invoice_line_values:
                    purchase_values["order_line"].append((0, 0, invoice_line_values))
            purchases_values.append(purchase_values)
            contract_lines._update_recurring_next_date()
        return purchases_values

    @api.model
    def cron_recurring_create_purchase(self, date_ref=None):
        return self._cron_recurring_create(date_ref, create_type="sale")

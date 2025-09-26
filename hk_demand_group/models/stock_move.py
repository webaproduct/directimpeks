from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    demand_group_id = fields.Many2one(
        'demand.group', 
        string='Demand Group',
        related='purchase_line_id.demand_group_id',         store=True
    )
    
    buyer_id = fields.Many2one(
        'res.partner', 
        string='Recipient', 
        related='demand_group_id.partner_id'
    )
    
    def _update_reserved_quantity(self, need, location_id, quant_ids=None, lot_id=None, package_id=None, owner_id=None, strict=True):
        """Extension of the standard method to pass demand_group_id in the context when reserving inventory"""
        # If there is demand_group_id, pass it in the context
        if self.demand_group_id:
            return super(StockMove, self.with_context(demand_group_id=self.demand_group_id.id))._update_reserved_quantity(
                need, location_id, quant_ids=quant_ids, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict
            )
        return super()._update_reserved_quantity(
            need, location_id, quant_ids=quant_ids, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict
        )
    
    def _action_done(self, cancel_backorder=False):
        """Extension of the standard method to create accounting entries
        when transferring stock.move to Done status"""
        # Call the original method
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        
        # Create accounting entries for movements that meet the conditions
        for move in moves:
            # Check if the destination location is a customer location
            if move.location_dest_id.usage == 'customer':
                # Check for lot_ids
                for move_line in move.move_line_ids:
                    if move_line.lot_id and move_line.lot_id.internal_owner_id:
                        lot = move_line.lot_id
                        # Check the condition of different owners
                        if move.location_id.internal_owner_id and lot.internal_owner_id != move.location_id.internal_owner_id:
                            # Look for the corresponding contract
                            contract_sale = self.env['contract.contract'].search([
                                ('contragent_id', '=', move.location_id.internal_owner_id.id),
                                ('partner_id', '=', lot.internal_owner_id.id)
                            ], limit=1)
                            contract_purchase = self.env['contract.contract'].search([
                                ('partner_id', '=', move.location_id.internal_owner_id.id),
                                ('contragent_id', '=', lot.internal_owner_id.id)
                            ], limit=1)

                            if not contract_sale or not contract_purchase:
                                continue  # Skip if contract not found
                            
                            # Get settings for intercompany settlements
                            company = self.env.company
                            intercompany_account = company.intercompany_account_id
                            intercompany_price_list = company.intercompany_price_list_id
                            
                            if not intercompany_account or not intercompany_price_list:
                                continue  # Skip if account or price list not configured
                            
                            # Get price from price list
                            price_unit = intercompany_price_list._get_product_price(
                                product=lot.product_id,
                                quantity=move_line.quantity,
                                partner=move.location_id.internal_owner_id,
                                date=fields.Date.today(),
                                uom=move.product_uom
                            )
                            
                            # Calculate amount
                            amount = price_unit * move_line.quantity
                            
                            # Create accounting entry
                            move_vals = {
                                'move_type': 'entry',
                                'stock_move_id': move.id,
                                'date': fields.Date.today(),
                                'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                                'ref': f'Intercompany Movement: {move.name}, Lot: {lot.name}',
                                'line_ids': [
                                    # Entry 1 - credit
                                    (0, 0, {
                                        'product_id': lot.product_id.id,
                                        'partner_id': move.location_id.internal_owner_id.id,
                                        'account_id': intercompany_account.id,
                                        'contract_id': contract_purchase.id,
                                        'quantity': move_line.quantity,
                                        'price_unit': price_unit,
                                        'credit': amount,
                                        'debit': 0.0,
                                        'name': f'Intercompany Movement: {move.name}, Lot: {lot.name}',
                                    }),
                                    # Entry 2 - debit
                                    (0, 0, {
                                        'product_id': lot.product_id.id,
                                        'partner_id': lot.internal_owner_id.id,
                                        'account_id': intercompany_account.id,
                                        'contract_id': contract_sale.id,
                                        'quantity': move_line.quantity,
                                        'price_unit': price_unit,
                                        'debit': amount,
                                        'credit': 0.0,
                                        'name': f'Intercompany Movement: {move.name}, Lot: {lot.name}',
                                    })
                                ]
                            }
                            
                            # Create entry
                            account_move = self.env['account.move'].create(move_vals)
                            account_move.action_post()  # Confirm entry
        
        return moves

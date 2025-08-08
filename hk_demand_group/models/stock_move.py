from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    demand_group_id = fields.Many2one(
        'demand.group', 
        string='Група попиту',
        related='purchase_line_id.demand_group_id',         store=True
    )
    
    buyer_id = fields.Many2one(
        'res.partner', 
        string='Отримувач', 
        related='demand_group_id.partner_id'
    )
    
    def _action_done(self, cancel_backorder=False):
        """Розширення стандартного методу для створення бухгалтерських проводок
        при переведенні stock.move у статус Done"""
        # Викликаємо оригінальний метод
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        
        # Створюємо бухгалтерські проводки для переміщень, які відповідають умовам
        for move in moves:
            # Перевіряємо, чи локація призначення - це локація клієнта
            if move.location_dest_id.usage == 'customer':
                # Перевіряємо наявність lot_ids
                for move_line in move.move_line_ids:
                    if move_line.lot_id and move_line.lot_id.internal_owner_id:
                        lot = move_line.lot_id
                        # Перевіряємо умову різних власників
                        if move.location_id.internal_owner_id and lot.internal_owner_id != move.location_id.internal_owner_id:
                            # Шукаємо відповідний контракт
                            contract_sale = self.env['contract.contract'].search([
                                ('contragent_id', '=', move.location_id.internal_owner_id.id),
                                ('partner_id', '=', lot.internal_owner_id.id)
                            ], limit=1)
                            contract_purchase = self.env['contract.contract'].search([
                                ('partner_id', '=', move.location_id.internal_owner_id.id),
                                ('contragent_id', '=', lot.internal_owner_id.id)
                            ], limit=1)

                            if not contract_sale or not contract_purchase:
                                continue  # Пропускаємо, якщо контракт не знайдено
                            
                            # Отримуємо налаштування для міжкомпанійних взаєморозрахунків
                            company = self.env.company
                            intercompany_account = company.intercompany_account_id
                            intercompany_price_list = company.intercompany_price_list_id
                            
                            if not intercompany_account or not intercompany_price_list:
                                continue  # Пропускаємо, якщо не налаштовані рахунок або прайс-лист
                            
                            # Отримуємо ціну з прайс-листа
                            price_unit = intercompany_price_list._get_product_price(
                                product=lot.product_id,
                                quantity=move_line.quantity,
                                partner=move.location_id.internal_owner_id,
                                date=fields.Date.today(),
                                uom=move.product_uom
                            )
                            
                            # Розраховуємо суму
                            amount = price_unit * move_line.quantity
                            
                            # Створюємо бухгалтерську проводку
                            move_vals = {
                                'move_type': 'entry',
                                'stock_move_id': move.id,
                                'date': fields.Date.today(),
                                'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                                'ref': f'Міжкомпанійне переміщення: {move.name}, Партія: {lot.name}',
                                'line_ids': [
                                    # Запис 1 - кредит
                                    (0, 0, {
                                        'product_id': lot.product_id.id,
                                        'partner_id': move.location_id.internal_owner_id.id,
                                        'account_id': intercompany_account.id,
                                        'contract_id': contract_purchase.id,
                                        'quantity': move_line.quantity,
                                        'price_unit': price_unit,
                                        'credit': amount,
                                        'debit': 0.0,
                                        'name': f'Міжкомпанійне переміщення: {move.name}, Партія: {lot.name}',
                                    }),
                                    # Запис 2 - дебет
                                    (0, 0, {
                                        'product_id': lot.product_id.id,
                                        'partner_id': lot.internal_owner_id.id,
                                        'account_id': intercompany_account.id,
                                        'contract_id': contract_sale.id,
                                        'quantity': move_line.quantity,
                                        'price_unit': price_unit,
                                        'debit': amount,
                                        'credit': 0.0,
                                        'name': f'Міжкомпанійне переміщення: {move.name}, Партія: {lot.name}',
                                    })
                                ]
                            }
                            
                            # Створюємо проводку
                            account_move = self.env['account.move'].create(move_vals)
                            account_move.action_post()  # Підтверджуємо проводку
        
        return moves

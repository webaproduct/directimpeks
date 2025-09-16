from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockRequest(models.Model):
    _inherit = 'stock.request'

    demand_group_id = fields.Many2one('demand.group', string='Група попиту')
    for_purchase = fields.Boolean(string='Для закупівлі', default=True, 
                                 help='Позначте, якщо запит потрібно враховувати при формуванні закупівель')

    # Перевизначаємо поле states, щоб додати статус cancelled
    states = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approve', 'Approved'),
        ('receive', 'Received'),
        ('cancelled', 'Cancelled')],
        string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')


    def action_create_picking(self):
        """Розширення стандартного методу створення переміщення"""
        if self.env.user.has_group('stock.group_stock_manager'):
            for record in self:
                if not record.demand_group_id and record.for_purchase:
                    # Створюємо новий запис demand.group
                    vals = {
                        'name': f'{record.partner_id.name}/{record.name}',
                        'partner_id': record.partner_id.id,
                        'stock_request_id': record.id,
                    }
                    demand_group = self.env['demand.group'].create(vals)

                    # Зберігаємо посилання на створену групу
                    record.demand_group_id = demand_group.id
                picking_line = []
                picking_data = {
                    'partner_id': record.partner_id.id,
                    'picking_type_id': record.picking_type_id.id,
                    'origin': self.name,
                    'location_id': record.stock_location_id.id,
                    'location_dest_id': record.delivery_location_id.id,
                    'move_ids_without_package': picking_line,
                    #додаємо групу
                    'demand_group_id': record.demand_group_id.id,
                }
                for lines in self.stock_line_ids:
                    picking_line.append(((0, 0, {
                        'product_id': lines.product_id.id,
                        'name': lines.description,
                        'product_uom_qty': lines.product_qty,
                        'location_id': record.stock_location_id.id,
                        'location_dest_id': record.delivery_location_id.id,
                        'product_uom': lines.product_id.uom_id.id,
                        # додаємо групу
                        'demand_group_id': record.demand_group_id.id,
                    })))

                picking_id = self.env['stock.picking'].create(picking_data)

                # додаємо групу
                for move in picking_id.move_ids_without_package:
                    move.demand_group_id = record.demand_group_id.id

                record.write({
                    'states': 'approve',
                    'approved_by': self.env.user,
                })

    def copy(self, default=None):
        """При копіюванні замовлення копіюємо рядки, але не копіюємо значення demand_group_id та for_purchase"""
        default = dict(default or {})
        default['demand_group_id'] = False
        default['for_purchase'] = False
        
        # Створюємо копію запису
        new_request = super(StockRequest, self).copy(default)
        
        # Якщо рядки не скопіювалися автоматично, копіюємо їх вручну
        if not new_request.stock_line_ids and self.stock_line_ids:
            for line in self.stock_line_ids:
                line_vals = {
                    'stock_request_id': new_request.id,
                    'product_id': line.product_id.id,
                    'description': line.description,
                    'product_qty': line.product_qty,
                    'product_uom': line.product_uom.id,
                }
                self.env['stock.request.lines'].create(line_vals)
        
        return new_request
        
    def action_cancel(self):
        """Відміна запиту на склад та пов'язаних переміщень"""
        for request in self:
            # Перевіряємо, чи є пов'язані переміщення
            pickings = self.env['stock.picking'].search([('origin', '=', request.name)])
            
            # Перевіряємо, чи всі переміщення можна відмінити
            validated_pickings = pickings.filtered(lambda p: p.state == 'done')
            if validated_pickings:
                raise UserError(_(
                    "Неможливо відмінити запит, оскільки деякі пов'язані переміщення вже підтверджені. "
                    "Підтверджені переміщення: %s"
                ) % ", ".join(validated_pickings.mapped('name')))
            
            # Відміняємо всі переміщення, які ще не підтверджені
            for picking in pickings.filtered(lambda p: p.state != 'done'):
                picking.action_cancel()
            
            # Змінюємо статус запиту на cancelled
            request.write({'states': 'cancelled'})
            
    def action_draft(self):
        """Повернення запиту на склад до статусу draft"""
        for request in self:
            # Перевіряємо, чи є пов'язані переміщення
            pickings = self.env['stock.picking'].search([('origin', '=', request.name)])
            
            # Перевіряємо, чи всі переміщення відмінені
            active_pickings = pickings.filtered(lambda p: p.state != 'cancel')
            if active_pickings:
                raise UserError(_(
                    "Неможливо повернути запит до статусу чернетки, оскільки є активні пов'язані переміщення. "
                    "Спочатку відмініть всі пов'язані переміщення."
                ))
            
            # Змінюємо статус запиту на draft
            request.write({
                'states': 'draft',
                'approved_by': False,  # Скидаємо поле approved_by
            })
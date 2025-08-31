from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class DemandGroupWizard(models.TransientModel):
    _name = 'demand.group.wizard'
    _description = 'Майстер створення замовлень на закупівлю'

    date_from = fields.Date(string='Дата з', required=True, default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Дата по', required=True, default=lambda self: fields.Date.today())
    # consider_ordered = fields.Boolean(string='Враховувати вже замовлені потреби', default=True)
    
    line_ids = fields.One2many('demand.group.wizard.line', 'wizard_id', string='Замовлення')
    
    def action_generate_report(self):
        """Генерація звіту на основі обраних параметрів"""
        self.ensure_one()
        
        # Очищення попередніх записів
        self.line_ids.unlink()
        
        # Отримання підтверджених замовлень на продаж за період
        sale_orders = self.env['sale.order'].search([
            ('state', 'in', ['sale']),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
        ])
        
        # Отримання підтверджених запитів на склад за період з прапорцем "Для закупівлі"
        stock_requests = self.env['stock.request'].search([
            ('states', 'in', ['approve', 'receive']),
            ('requested_date', '>=', self.date_from),
            ('requested_date', '<=', self.date_to),
            ('for_purchase', '=', True),
        ])
        
        # Словник для збору даних по продуктах
        product_data = {}
        
        # Обробка замовлень на продаж
        for order in sale_orders:
            for line in order.order_line:
                if line.product_id.type == 'product':  # Тільки складські товари
                    key = (line.product_id.id, order.demand_group_id.id if order.demand_group_id else False)
                    if key not in product_data:
                        product_data[key] = {
                            'product_id': line.product_id.id,
                            'demand_group_id': order.demand_group_id.id if order.demand_group_id else False,
                            'sale_order_id': order.id,
                            'stock_request_id': False,
                            'quantity_demand': 0,
                            'quantity_purchase': 0,
                        }
                    product_data[key]['quantity_demand'] += line.product_uom_qty
        
        # Обробка запитів на склад
        for request in stock_requests:
            for line in request.stock_line_ids:
                if line.product_id.type == 'product':  # Тільки складські товари
                    key = (line.product_id.id, request.demand_group_id.id if request.demand_group_id else False)
                    if key not in product_data:
                        product_data[key] = {
                            'product_id': line.product_id.id,
                            'demand_group_id': request.demand_group_id.id if request.demand_group_id else False,
                            'sale_order_id': False,
                            'stock_request_id': request.id,
                            'quantity_demand': 0,
                            'quantity_purchase': 0,
                        }
                    product_data[key]['quantity_demand'] += line.product_qty
        
        # Якщо потрібно враховувати вже замовлені потреби
            # if self.consider_ordered:
        # Отримання замовлень на закупівлю за період
        purchase_orders = self.env['purchase.order'].search([
            ('state', 'in', ['purchase', 'done']),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
        ])

        for order in purchase_orders:
            for line in order.order_line:
                if line.product_id.type == 'product':  # Тільки складські товари
                    # Шукаємо відповідний ключ
                    for key in product_data:
                        if key[0] == line.product_id.id and key[1] == order.demand_group_id.id:
                            product_data[key]['quantity_purchase'] += line.product_qty
        
        # Створення записів для звіту
        lines_to_create = []
        for key, data in product_data.items():
            # Розрахунок кількості для замовлення
            quantity_to_order = data['quantity_demand'] - data['quantity_purchase']
            
            # Отримання основного постачальника для товару
            product = self.env['product.product'].browse(data['product_id'])
            supplier_id = False
            if product.seller_ids:
                supplier_id = product.seller_ids[0].partner_id.id
            
            # Створюємо запис тільки якщо є потреба
            if quantity_to_order > 0 or data['quantity_demand'] > 0:
                lines_to_create.append({
                    'wizard_id': self.id,
                    'product_id': data['product_id'],
                    'demand_group_id': data['demand_group_id'],
                    'sale_order_id': data['sale_order_id'],
                    'stock_request_id': data['stock_request_id'],
                    'quantity_demand': data['quantity_demand'],
                    'quantity_purchase': data['quantity_purchase'],
                    'quantity_to_order': quantity_to_order,
                    'supplier_id': supplier_id,
                })
        
        # Створення записів
        for line_data in lines_to_create:
            self.env['demand.group.wizard.line'].create(line_data)
        
        # Відкриття форми списку
        action = {
            'name': _('Аналіз потреб'),
            'type': 'ir.actions.act_window',
            'res_model': 'demand.group.wizard.line',
            'view_mode': 'tree,form',
            'domain': [('wizard_id', '=', self.id)],
            'context': {
                'search_default_group_by_supplier': 1,
                'search_default_group_by_demand_group': 1,
                'search_default_filter_to_order': 1
            },
        }
        return action


class DemandGroupWizardLine(models.TransientModel):
    _name = 'demand.group.wizard.line'
    _description = 'Лінія аналізу потреб'
    
    wizard_id = fields.Many2one('demand.group.wizard', string='Майстер', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Товар', required=True)
    demand_group_id = fields.Many2one('demand.group', string='Група попиту')
    sale_order_id = fields.Many2one('sale.order', string='Замовлення на продаж')
    stock_request_id = fields.Many2one('stock.request', string='Запит на склад')
    quantity_demand = fields.Float(string='Кількість потреби', digits='Product Unit of Measure')
    quantity_purchase = fields.Float(string='Кількість закупівлі', digits='Product Unit of Measure')
    quantity_to_order = fields.Float(string='Кількість до замовлення', digits='Product Unit of Measure')
    supplier_id = fields.Many2one('res.partner', string='Постачальник')
    
    def action_create_purchase_order(self):
        """Створення замовлення на закупівлю на основі обраних записів"""
        if not self:
            raise UserError(_('Не обрано жодного запису для створення замовлення'))
        
        # Групування за постачальником
        supplier_products = {}
        for line in self:
            if line.quantity_to_order <= 0:
                continue
                
            # Використовуємо вже визначеного постачальника або отримуємо основного
            supplier_id = line.supplier_id.id
            if not supplier_id:
                seller = line.product_id.seller_ids and line.product_id.seller_ids[0]
                if not seller:
                    raise UserError(_('Для товару %s не вказано постачальника') % line.product_id.display_name)
                supplier_id = seller.partner_id.id
            
            if supplier_id not in supplier_products:
                supplier_products[supplier_id] = []
            
            # Отримання ціни від постачальника
            seller = self.env['product.supplierinfo'].search([
                ('partner_id', '=', supplier_id),
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)
            ], limit=1)
            
            price_unit = seller.price if seller else 0.0
            
            supplier_products[supplier_id].append({
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'product_qty': line.quantity_to_order,
                'product_uom': line.product_id.uom_po_id.id,
                'price_unit': price_unit,
                'date_planned': fields.Datetime.now(),
                'demand_group_id': line.demand_group_id.id if line.demand_group_id else False,
            })
        
        # Створення замовлень на закупівлю
        purchase_order_ids = []
        for supplier_id, lines in supplier_products.items():
            # Визначення групи попиту для замовлення
            demand_group_id = False
            for line in lines:
                if line.get('demand_group_id'):
                    demand_group_id = line['demand_group_id']
                    break
            
            # Створення замовлення
            po_vals = {
                'partner_id': supplier_id,
                'date_order': fields.Datetime.now(),
                'demand_group_id': demand_group_id,
                'order_line': [(0, 0, line_vals) for line_vals in lines],
            }
            
            purchase_order = self.env['purchase.order'].create(po_vals)
            purchase_order_ids.append(purchase_order.id)
        
        # Відкриття створених замовлень
        action = {
            'name': _('Створені замовлення на закупівлю'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', purchase_order_ids)],
        }
        
        if len(purchase_order_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = purchase_order_ids[0]
        
        return action

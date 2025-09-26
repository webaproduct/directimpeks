from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class DemandGroupWizard(models.TransientModel):
    _name = 'demand.group.wizard'
    _description = 'Purchase Order Creation Wizard'

    date_from = fields.Date(string='Date From', required=True, default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Date To', required=True, default=lambda self: fields.Date.today())
    # consider_ordered = fields.Boolean(string='Consider Already Ordered Demands', default=True)
    
    line_ids = fields.One2many('demand.group.wizard.line', 'wizard_id', string='Orders')
    
    def action_generate_report(self):
        """Generate report based on selected parameters"""
        self.ensure_one()
        
        date_yesterday = fields.Date.today() - timedelta(days=1)
        # Clearing previous records
        self.env["demand.group.wizard.line"].sudo().search([("create_date", "<=", date_yesterday)]).unlink()
        # self.line_ids.unlink()
        
        # Getting confirmed sale orders for the period
        sale_orders = self.env['sale.order'].search([
            ('state', 'in', ['sale']),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
        ])
        
        # Getting confirmed stock requests for the period with "For Purchase" flag
        stock_requests = self.env['stock.request'].search([
            ('states', 'in', ['approve', 'receive']),
            ('requested_date', '>=', self.date_from),
            ('requested_date', '<=', self.date_to),
            ('for_purchase', '=', True),
        ])
        
        # Dictionary for collecting product data
        product_data = {}
        
        # Processing sale orders
        for order in sale_orders:
            for line in order.order_line:
                if line.product_id.type == 'product':  # Only stockable products
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
        
        # Processing stock requests
        for request in stock_requests:
            for line in request.stock_line_ids:
                if line.product_id.type == 'product':  # Only stockable products
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
        
        # If we need to consider already ordered demands
            # if self.consider_ordered:
        # Getting purchase orders for the period
        purchase_orders = self.env['purchase.order'].search([
            ('state', 'in', ['purchase', 'done']),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
        ])

        for order in purchase_orders:
            for line in order.order_line:
                if line.product_id.type == 'product':  # Only stockable products
                    # Looking for the corresponding key
                    for key in product_data:
                        if key[0] == line.product_id.id and key[1] == order.demand_group_id.id:
                            product_data[key]['quantity_purchase'] += line.product_qty
        
        # Creating records for the report
        lines_to_create = []
        for key, data in product_data.items():
            # Calculating quantity to order
            quantity_to_order = data['quantity_demand'] - data['quantity_purchase']
            
            # Getting the main supplier for the product
            product = self.env['product.product'].browse(data['product_id'])
            supplier_id = False
            if product.seller_ids:
                supplier_id = product.seller_ids[0].partner_id.id
            
            # Creating a record only if there is a demand
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
        
        # Creating records
        for line_data in lines_to_create:
            self.env['demand.group.wizard.line'].create(line_data)
        
        # Opening the list form
        action = {
            'name': _('Demand Analysis'),
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
    _description = 'Demand Analysis Line'
    
    date = fields.Date(readonly=True, default=datetime.today())
    wizard_id = fields.Many2one('demand.group.wizard', string='Wizard', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    stock_request_id = fields.Many2one('stock.request', string='Store Order')
    quantity_demand = fields.Float(string='Demand Quantity', digits='Product Unit of Measure')
    quantity_purchase = fields.Float(string='Purchase Quantity', digits='Product Unit of Measure')
    quantity_to_order = fields.Float(string='Quantity to Order', digits='Product Unit of Measure')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    
    def action_create_purchase_order(self):
        """Creating a purchase order based on selected records"""
        if not self:
            raise UserError(_('No records selected to create an order'))
        
        # Grouping by supplier
        supplier_products = {}
        for line in self:
            if line.quantity_to_order <= 0:
                continue
                
            # Using the already defined supplier or getting the main one
            supplier_id = line.supplier_id.id
            if not supplier_id:
                seller = line.product_id.seller_ids and line.product_id.seller_ids[0]
                if not seller:
                    raise UserError(_('No supplier specified for product %s') % line.product_id.display_name)
                supplier_id = seller.partner_id.id
            
            if supplier_id not in supplier_products:
                supplier_products[supplier_id] = []
            
            # Getting the price from the supplier
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
        
        # Creating purchase orders
        purchase_order_ids = []
        for supplier_id, lines in supplier_products.items():
            # Determining the demand group for the order
            demand_group_id = False
            for line in lines:
                if line.get('demand_group_id'):
                    demand_group_id = line['demand_group_id']
                    break
            
            # Creating an order
            po_vals = {
                'partner_id': supplier_id,
                'date_order': fields.Datetime.now(),
                'demand_group_id': demand_group_id,
                'order_line': [(0, 0, line_vals) for line_vals in lines],
            }
            
            purchase_order = self.env['purchase.order'].create(po_vals)
            purchase_order_ids.append(purchase_order.id)
        
        # Opening created orders
        action = {
            'name': _('Created Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', purchase_order_ids)],
        }
        
        if len(purchase_order_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = purchase_order_ids[0]
        
        return action

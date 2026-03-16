from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    internal_owner_id = fields.Many2one('res.partner', string='Product Owner')
    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
    related_purchase_count = fields.Integer(string='Related Purchases', compute='_compute_related_purchase_count')
    related_purchase_line_count = fields.Integer(string='Related Purchase Lines', compute='_compute_related_purchase_line_count')
    source_purchase_count = fields.Integer(string='Source Purchases', compute='_compute_source_purchase_count')
    fact_purchase = fields.Boolean(string='Фактична закупівля', default=False, copy=False)
    additional_purchase = fields.Boolean(string='Це дозамовлення?', default=False, copy=False)

    @api.depends('order_line.source_purchase_order_id')
    def _compute_related_purchase_count(self):
        for order in self:
            related_lines = self.env['purchase.order.line'].search([
                ('source_purchase_order_id', '=', order.id)
            ])
            order.related_purchase_count = len(related_lines.mapped('order_id'))

    @api.depends('order_line.source_purchase_order_id')
    def _compute_related_purchase_line_count(self):
        for order in self:
            related_lines = self.env['purchase.order.line'].search([
                ('source_purchase_order_id', '=', order.id)
            ])
            order.related_purchase_line_count = len(related_lines)

    @api.depends('order_line.source_purchase_order_id')
    def _compute_source_purchase_count(self):
        for order in self:
            source_orders = order.order_line.mapped('source_purchase_order_id')
            order.source_purchase_count = len(source_orders)

    def action_view_related_purchases(self):
        """Open related purchase orders created from this order"""
        self.ensure_one()
        related_lines = self.env['purchase.order.line'].search([
            ('source_purchase_order_id', '=', self.id)
        ])
        related_orders = related_lines.mapped('order_id')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', related_orders.ids)],
            'context': {'create': False},
        }

    def action_view_related_purchase_lines(self):
        """Open related purchase order lines created from this order"""
        self.ensure_one()
        related_lines = self.env['purchase.order.line'].search([
            ('source_purchase_order_id', '=', self.id)
        ])
        
        tree_view_id = self.env.ref('hk_demand_group.purchase_order_line_tree_related').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Purchase Order Lines',
            'res_model': 'purchase.order.line',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (False, 'form')],
            'domain': [('id', 'in', related_lines.ids)],
            'context': {'create': False},
        }

    def action_view_source_purchases(self):
        """Open source purchase orders from which this order was created"""
        self.ensure_one()
        source_orders = self.order_line.mapped('source_purchase_order_id')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Source Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', source_orders.ids)],
            'context': {'create': False},
        }

    def _prepare_picking(self):
        """
        Extension of the standard method to add fields demand_group_id and internal_owner_id
        when creating a picking
        """
        res = super(PurchaseOrder, self)._prepare_picking()
        # if self.demand_group_id:
        #     res['demand_group_id'] = self.demand_group_id.id
        if self.internal_owner_id:
            res['internal_owner_id'] = self.internal_owner_id.id
        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        # After confirming the order, ensure that all created pickings
        # have correct values for demand_group_id and internal_owner_id
        for order in self:
            for picking in order.picking_ids:
                # if order.demand_group_id and not picking.demand_group_id:
                #     picking.demand_group_id = order.demand_group_id.id
                if order.internal_owner_id and not picking.internal_owner_id:
                    picking.internal_owner_id = order.internal_owner_id.id
                # Update related stock moves
                # for move in picking.move_ids_without_package:
                #     if order.demand_group_id:
                #         move.demand_group_id = order.demand_group_id.id
            
            for line in order.order_line:
                if line.source_purchase_order_line_id:
                    source_line = line.source_purchase_order_line_id
                    new_qty = source_line.product_qty - line.product_qty
                    if new_qty < 0:
                        new_qty = 0
                                        
                    # Знаходимо відповідні stock.move для source_line
                    moves = self.env['stock.move'].search([
                        ('purchase_line_id', '=', source_line.id),
                        ('state', 'not in', ['done', 'cancel'])
                    ])
                    
                    for move in moves:
                        if move.product_uom_qty > line.product_qty:
                            new_move_qty = move.product_uom_qty - line.product_qty
                            move.product_uom_qty = new_move_qty
                    source_line.product_qty = new_qty
                
                # Оновлення sale.order.line для рядків з demand_group_id.sale_order_id
                if line.demand_group_id and line.demand_group_id.sale_order_id:
                    sale_order = line.demand_group_id.sale_order_id
                    # Знаходимо всі рядки sale.order з таким самим товаром
                    sale_lines = self.env['sale.order.line'].search([
                        ('order_id', '=', sale_order.id),
                        ('product_id', '=', line.product_id.id)
                    ])
                    
                    # Оновлюємо поля в знайдених рядках
                    for sale_line in sale_lines:
                        sale_line.write({
                            'delivery_date': line.date_planned,
                            'vendor_id': order.partner_id.id,
                            'purshase_ref': order.partner_ref if order.partner_ref else False,
                        })

        return res

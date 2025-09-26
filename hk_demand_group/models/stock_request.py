from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockRequest(models.Model):
    _inherit = 'stock.request'

    demand_group_id = fields.Many2one('demand.group', string='Demand Group')
    for_purchase = fields.Boolean(string='For Purchase', default=True, 
                                 help='Check if the request should be considered when forming purchases')

    # Redefining the states field to add cancelled status
    states = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approve', 'Approved'),
        ('receive', 'Received'),
        ('cancelled', 'Cancelled')],
        string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')


    def action_create_picking(self):
        """Extension of the standard method for creating movement"""
        if self.env.user.has_group('stock.group_stock_manager'):
            for record in self:
                if not record.demand_group_id and record.for_purchase:
                    # Creating a new demand.group record
                    vals = {
                        'name': f'{record.partner_id.name}/{record.name}',
                        'partner_id': record.partner_id.id,
                        'stock_request_id': record.id,
                    }
                    demand_group = self.env['demand.group'].create(vals)

                    # Saving reference to the created group
                    record.demand_group_id = demand_group.id
                picking_line = []
                picking_data = {
                    'partner_id': record.partner_id.id,
                    'picking_type_id': record.picking_type_id.id,
                    'origin': self.name,
                    'location_id': record.stock_location_id.id,
                    'location_dest_id': record.delivery_location_id.id,
                    'move_ids_without_package': picking_line,
                    #adding group
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
                        # adding group
                        'demand_group_id': record.demand_group_id.id,
                    })))

                picking_id = self.env['stock.picking'].create(picking_data)

                # adding group
                for move in picking_id.move_ids_without_package:
                    move.demand_group_id = record.demand_group_id.id

                record.write({
                    'states': 'approve',
                    'approved_by': self.env.user,
                })

    def copy(self, default=None):
        """When copying an order, copy the lines but don't copy demand_group_id and for_purchase values"""
        default = dict(default or {})
        default['demand_group_id'] = False
        default['for_purchase'] = False
        
        # Creating a copy of the record
        new_request = super(StockRequest, self).copy(default)
        
        # If lines were not copied automatically, copy them manually
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
        """Cancellation of stock request and related movements"""
        for request in self:
            # Checking if there are related movements
            pickings = self.env['stock.picking'].search([('origin', '=', request.name)])
            
            # Checking if all movements can be cancelled
            validated_pickings = pickings.filtered(lambda p: p.state == 'done')
            if validated_pickings:
                raise UserError(_(
                    "Cannot cancel the request because some related movements are already confirmed. "
                    "Confirmed movements: %s"
                ) % ", ".join(validated_pickings.mapped('name')))
            
            # Cancelling all movements that are not yet confirmed
            for picking in pickings.filtered(lambda p: p.state != 'done'):
                picking.action_cancel()
            
            # Changing the request status to cancelled
            request.write({'states': 'cancelled'})
            
    def action_draft(self):
        """Returning the stock request to draft status"""
        for request in self:
            # Checking if there are related movements
            pickings = self.env['stock.picking'].search([('origin', '=', request.name)])
            
            # Checking if all movements are cancelled
            active_pickings = pickings.filtered(lambda p: p.state != 'cancel')
            if active_pickings:
                raise UserError(_(
                    "Cannot return the request to draft status because there are active related movements. "
                    "First cancel all related movements."
                ))
            
            # Changing the request status to draft
            request.write({
                'states': 'draft',
                'approved_by': False,  # Resetting the approved_by field
            })
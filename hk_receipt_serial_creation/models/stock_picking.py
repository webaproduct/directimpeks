from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _generate_serial_number(self, product, picking_name):
        """
        Generate serial number based on template:
        Brand - Article - Color - Size - PickingNumber - Sequence(6 digits)
        If field is empty, use "#" symbol
        """
        # Get brand name or "#"
        brand = product.product_tmpl_id.brand_id.name if product.product_tmpl_id.brand_id else "#"
        
        # Get article (default_code) or "#"
        article = product.default_code if product.default_code else "#"
        
        # Get color or "#"
        color = product.color_manufacturer if product.color_manufacturer else "#"
        
        # Get size or "#"
        size = product.size_original_manufacturer if product.size_original_manufacturer else "#"
        
        # Get picking number (name)
        picking_number = self.origin if self.origin else "#"
        
        # Generate 6-digit sequence number
        sequence = self.env['ir.sequence'].next_by_code('serial.number.sequence')
        
        # Construct serial number: Brand-Article-Color-Size-PickingNumber-Sequence
        serial_number = f"{brand}-{article}-{color}-{size}-{picking_number}-{sequence}"
        
        return serial_number

    @api.model
    def _auto_fill_lots_before_validate(self):
        """Fills lot_name for lines where lot_id is missing."""
        for picking in self:
            for line in picking.move_line_ids_without_package:
                product = line.product_id
                if product.tracking == "serial" and not line.lot_id:
                    # Generate lot name using template
                    line.lot_name = self._generate_serial_number(product, picking.name)

    def button_validate(self):
        # Execute only for incoming operations
        if self.picking_type_id.code == "incoming":
            self._auto_fill_lots_before_validate()

        # Now execute the standard action
        return super().button_validate()

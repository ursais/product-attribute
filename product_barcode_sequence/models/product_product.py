# Copyright 2026 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    can_generate_barcode = fields.Boolean(
        compute="_compute_can_generate_barcode",
        help="Indicates if this product can have a barcode automatically generated"
        " based on its category configuration",
    )

    @api.depends(
        "barcode", "categ_id.auto_generate_barcode", "categ_id.barcode_sequence_id"
    )
    def _compute_can_generate_barcode(self):
        """Compute if barcode generation is possible for this product"""
        for product in self:
            product.can_generate_barcode = (
                product.categ_id.auto_generate_barcode
                and product.categ_id.barcode_sequence_id
            )

    def _calculate_gtin_check_digit(self, barcode_without_check):
        """
        Calculate GTIN check digit for EAN-13 barcode.
        :param barcode_without_check: 12-digit string without check digit
        :return: check digit (0-9)
        """
        if len(barcode_without_check) != 12 or not barcode_without_check.isdigit():
            raise UserError(
                _("Barcode must be 12 digits to calculate GTIN check digit")
            )
        # Sum of digits at odd positions (1st, 3rd, 5th, etc.)
        odd_sum = sum(int(barcode_without_check[i]) for i in range(0, 12, 2))
        # Sum of digits at even positions (2nd, 4th, 6th, etc.)
        even_sum = sum(int(barcode_without_check[i]) for i in range(1, 12, 2))
        # Calculate check digit
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        return check_digit

    def _generate_barcodes(self, force=False):
        """Generate barcodes for products in recordset"""
        products_to_generate = self.filtered(
            lambda x: (force or not x.barcode) and x.can_generate_barcode
        )
        for product in products_to_generate:
            # Generate next sequence number
            sequence_number = product.categ_id.barcode_sequence_id.next_by_id()
            # Calculate GTIN check digit
            check_digit = product._calculate_gtin_check_digit(str(sequence_number))
            barcode = str(sequence_number) + str(check_digit)
            # Update product with generated barcode
            product.barcode = barcode
        return products_to_generate

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        products._generate_barcodes()
        return products

    def action_generate_barcode(self, force=False):
        """
        Action to manually generate barcode for selected products.
        Can be called from server actions.
        """
        generated_products = self._generate_barcodes(force=force)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Barcode Generation"),
                "message": _("Successfully generated barcodes for %d products")
                % len(generated_products),
                "type": "success",
            },
        }

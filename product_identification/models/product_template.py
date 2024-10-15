from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    id_numbers_ids = fields.One2many(
        "product.identification", "product_id", string="Identification Numbers"
    )

from odoo import fields, models


class MarketLocation(models.Model):
    _name = "market.location"
    _description = "Farmers Market"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    city = fields.Char()
    state = fields.Char(default="WA")
    address = fields.Char()
    organizer_name = fields.Char()
    organizer_email = fields.Char()
    booth_fee_default = fields.Float(string="Default Booth Fee")
    notes = fields.Text()

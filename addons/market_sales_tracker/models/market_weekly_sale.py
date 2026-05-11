from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MarketWeeklySale(models.Model):
    _name = "market.weekly.sale"
    _description = "Weekly Market Sale Summary"
    _order = "week_ending desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    market_id = fields.Many2one("market.location", string="Market", required=True)
    week_ending = fields.Date(required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    gross_sales = fields.Monetary(required=True, default=0.0, currency_field="currency_id")
    processing_fees = fields.Monetary(default=0.0, currency_field="currency_id")
    booth_fee = fields.Monetary(default=0.0, currency_field="currency_id")
    other_costs = fields.Monetary(default=0.0, currency_field="currency_id")
    net_sales = fields.Monetary(
        compute="_compute_net_sales",
        store=True,
        currency_field="currency_id",
    )
    weather = fields.Selection(
        selection=[
            ("sunny", "Sunny"),
            ("cloudy", "Cloudy"),
            ("rainy", "Rainy"),
            ("windy", "Windy"),
            ("hot", "Hot"),
            ("cold", "Cold"),
            ("mixed", "Mixed"),
            ("other", "Other"),
        ]
    )
    estimated_foot_traffic = fields.Integer()
    bottles_sold = fields.Integer()
    best_selling_product = fields.Char()
    notes = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company.id,
    )

    _sql_constraints = [
        (
            "market_week_company_unique",
            "unique(market_id, week_ending, company_id)",
            "Only one weekly sale summary is allowed per market, week ending, and company.",
        ),
    ]

    @api.depends("market_id", "week_ending")
    def _compute_name(self):
        for record in self:
            if record.market_id and record.week_ending:
                record.name = (
                    f"{record.market_id.name} - Week Ending {record.week_ending}"
                )
            elif record.market_id:
                record.name = record.market_id.name
            else:
                record.name = "New Weekly Sale"

    @api.depends("gross_sales", "processing_fees", "booth_fee", "other_costs")
    def _compute_net_sales(self):
        for record in self:
            record.net_sales = (
                record.gross_sales
                - record.processing_fees
                - record.booth_fee
                - record.other_costs
            )

    @api.onchange("market_id")
    def _onchange_market_id(self):
        for record in self:
            if record.market_id:
                record.booth_fee = record.market_id.booth_fee_default or 0.0

    @api.constrains("gross_sales", "processing_fees", "booth_fee", "other_costs")
    def _check_non_negative_amounts(self):
        for record in self:
            if record.gross_sales < 0:
                raise ValidationError("Gross Sales cannot be negative.")
            if record.processing_fees < 0:
                raise ValidationError("Processing Fees cannot be negative.")
            if record.booth_fee < 0:
                raise ValidationError("Booth Fee cannot be negative.")
            if record.other_costs < 0:
                raise ValidationError("Other Costs cannot be negative.")

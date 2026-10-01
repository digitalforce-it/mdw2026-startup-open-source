from odoo import fields, models, tools


class ResCompany(models.Model):
    _inherit = 'res.company'

    mdw_cash_start = fields.Monetary('Saldo in banca oggi', currency_field='currency_id', default=35000)
    mdw_cash_books = fields.Monetary('Saldo secondo la contabilità', currency_field='currency_id',
                                     compute='_compute_mdw_cash_books')

    def _compute_mdw_cash_books(self):
        # bank accounts plus the "outstanding receipts/payments" accounts that payments land on
        for company in self:
            self.env.cr.execute("""
                SELECT COALESCE(SUM(l.balance), 0)
                  FROM account_move_line l
                  JOIN account_account a ON a.id = l.account_id
                 WHERE l.company_id = %s AND l.parent_state = 'posted'
                   AND (a.account_type = 'asset_cash'
                        OR a.id IN (SELECT outstanding_account_id FROM account_payment
                                     WHERE outstanding_account_id IS NOT NULL))
            """, [company.id])
            company.mdw_cash_books = self.env.cr.fetchone()[0]

    def action_mdw_open_forecast(self):
        return self.env['ir.actions.act_window']._for_xml_id('mdw_cash_flow.action_mdw_cash_flow')


class MdwCashFlow(models.Model):
    _name = 'mdw.cash.flow'
    _description = 'Previsione di cassa'
    _auto = False
    _order = 'date, id'

    date = fields.Date('Data prevista', readonly=True)
    source = fields.Selection([
        ('saldo', 'Saldo iniziale'),
        ('cliente', 'Da incassare'),
        ('fornitore', 'Da pagare'),
        ('ordine', 'Ordine confermato'),
        ('preventivo', 'Preventivo (ponderato)'),
    ], string='Tipo', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Contatto', readonly=True)
    name = fields.Char('Riferimento', readonly=True)
    due_date = fields.Date('Scadenza originale', readonly=True)
    late = fields.Boolean('In ritardo', readonly=True)
    amount = fields.Monetary('Importo', currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)

    def init(self):
        # One row per expected movement of money. Late items are moved to today.
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT c.id * 10 + 1 AS id, CURRENT_DATE AS date, 'saldo' AS source,
                       NULL::int AS partner_id, 'Saldo in banca oggi' AS name,
                       NULL::date AS due_date, FALSE AS late,
                       COALESCE(c.mdw_cash_start, 0) AS amount, c.currency_id, c.id AS company_id
                  FROM res_company c
                UNION ALL
                SELECT l.id * 10 + 2, GREATEST(l.date_maturity, CURRENT_DATE),
                       CASE WHEN a.account_type = 'asset_receivable' THEN 'cliente' ELSE 'fornitore' END,
                       l.partner_id, m.name, l.date_maturity, l.date_maturity < CURRENT_DATE,
                       l.amount_residual, l.company_currency_id, l.company_id
                  FROM account_move_line l
                  JOIN account_move m ON m.id = l.move_id
                  JOIN account_account a ON a.id = l.account_id
                 WHERE l.parent_state = 'posted' AND l.display_type = 'payment_term'
                   AND a.account_type IN ('asset_receivable', 'liability_payable')
                   AND l.amount_residual <> 0
                UNION ALL
                SELECT s.id * 10 + 3,
                       GREATEST(COALESCE(s.commitment_date, s.date_order)::date, CURRENT_DATE) + 30,
                       'ordine', s.partner_id, s.name, NULL, FALSE,
                       s.amount_total, c.currency_id, s.company_id
                  FROM sale_order s JOIN res_company c ON c.id = s.company_id
                 WHERE s.state = 'sale' AND s.invoice_status = 'to invoice'
                UNION ALL
                SELECT s.id * 10 + 4,
                       GREATEST(COALESCE(s.validity_date, s.date_order::date), CURRENT_DATE) + 30,
                       'preventivo', s.partner_id, s.name, NULL, FALSE,
                       s.amount_total * COALESCE(o.probability, 50) / 100.0, c.currency_id, s.company_id
                  FROM sale_order s
                  JOIN res_company c ON c.id = s.company_id
                  LEFT JOIN crm_lead o ON o.id = s.opportunity_id
                 WHERE s.state IN ('draft', 'sent')
            )
        """)

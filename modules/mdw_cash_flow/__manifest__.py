{
    'name': 'MDW 2026 - Previsione di cassa',
    'version': '19.0.1.0.0',
    'summary': 'Quanti soldi avrò in banca nei prossimi mesi?',
    'author': 'DigitalForce',
    'license': 'LGPL-3',
    'depends': ['account', 'sale_crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/cash_flow_views.xml',
    ],
    'installable': True,
}

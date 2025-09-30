{
    'name': "Detalle del Día TPV",

    'summary': """ Detalle del Día del Punto de Venta """,
    'description': """ Detalle del Día del Punto de Venta """,

    'category': 'Sales/Point of Sale',
    'author': 'Adderly Marte',
    'license': "OPL-1",
    'website': 'https://renace.tech',
    "price": 0,
    "currency": 'USD',

    'depends': ['point_of_sale'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/pos_config.xml',
        # Wizard
        'wizard/report_password_wizard_view.xml',
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_rnc_report/static/src/**/*"
        ]
    },

    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}

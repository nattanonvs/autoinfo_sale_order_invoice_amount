{
    "name": "AutoInfo Sale Order Invoice Amount",
    "version": "15.0.2.1.0",
    "author": "ForgeFlow, Odoo Community Association (OCA), The Auto-Info Co., Ltd.",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Sales",
    "license": "LGPL-3",
    "summary": "Extend Sale Order Invoice Amount with untaxed amounts and invoiced percentage",
    "depends": ["sale_order_invoice_amount", "sale_margin", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/close_agreement_wizard_views.xml",
        "views/sale_order_view.xml",
    ],
    "assets": {
        "web.assets_qweb": [
            "autoinfo_sale_order_invoice_amount/static/src/xml/**/*",
        ],
    },
    "installable": True,
}

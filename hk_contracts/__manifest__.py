{
    "name": "Contract's requisites base module (SIMBIOZ, Hotkey)",
    "summary": "Contract's requisites base module (SIMBIOZ, Hotkey) ",
    "version": "17.0.2.4.0",
    "license": "LGPL-3",
    "author": "Timkovych V, Zhmyhova T.N., Pavlo Zub",
    "depends": [
        "contract_sale_generation",
        "contract_purchase_generation",
        "purchase",
        "account",
    ],
    "data": [
        "views/contract.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/purchase_order_views.xml",
        "views/account_payment_views.xml",
        "views/account_account_views.xml",
        "views/menu.xml",
    ],
    "demo": [],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "installable": True,
}

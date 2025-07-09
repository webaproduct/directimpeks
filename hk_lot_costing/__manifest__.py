{
    "name": "Lot costing",
    "summary": """Use the cost of the lot in moves""",
    "category": "Warehouse",
    "author": "Simbioz Holding, Borovlev A. S., Hotkey, Pavlo Zub",
    "maintainer": "Hotkey",
    "website": "https://hotkey.ua",
    "version": "17.0.2.0.0",
    "license": "LGPL-3",
    "depends": [
        "stock_account",
        "stock_landed_costs",
    ],
    "data": [
        "views/stock_valuation_layer.xml",
        "views/stock_production_lot_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "post_load": "post_load_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}

{
    "name": "volodymyr_weba",
    "version": "17.0.1.0.0",
    "category": "Custom",
    "summary": "",
    "author": "Volodymyr Weba",
    "license": "LGPL-3",
    'depends': [
        'base',
        'crm',
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead_views.xml",
        "views/department_id_views.xml",
        "views/direction_id_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
# -*- coding: utf-8 -*-
#############################################################################
#
#    Beyondata Solution Pvt. Ltd.
#
#    Copyright (C) Beyondata Solution Pvt. Ltd.(<http://beyondatagroup.com/>)
#    Author: Mittal Nayar
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    "name": "Lot/Serial Number(s) Selector in Point of Sale (POS)",
    "summary": """
        Restrict user for creating the lot/serial number in Poin Of Sale.
        """,
    "description": """
        Restrict user for creating the lot/serial number in Poin Of Sale.
    """,
    "version": "17.0.0.1",
    "category": "Point of Sale",
    "author": "BeyonData Solutions Private Limited",
    'website': "https://www.beyondatagroup.com/",
    'live_test_url': 'https://www.beyondatagroup.com/contactus',
    "license": "LGPL-3",
    "price": "0",
    "currency": "EUR",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        "views/views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "bd_pos_lot_selection/static/src/js/**/*.js",
            "bd_pos_lot_selection/static/src/xml/**/*.xml",
        ],
    },
    "live_test_url": "https://www.beyondatagroup.com/contactus",
    "installable": True,
    "application": False,
    "auto_install": False,
}

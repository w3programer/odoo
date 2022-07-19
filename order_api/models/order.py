import requests
import json
import ssl
from xmlrpc import client as xmlrpclib

url = 'https://nssglobal-pos-3589592.dev.odoo.com'
db = 'nssglobal-pos-3589592'
username = 'admin'
password = 'admin'

server = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())
uid = server.login(db, username, password)
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())


pos_orders = models.execute_kw(db, uid, password,
            'pos.kitchen.order', 'search_read',
            [[['invoice_id', '=', False]]],
            {'fields': ['id','partner_id']})


for po in pos_orders:
    try:
        amount_total = 0
        customer = models.execute_kw(db, uid, password,
                'res.partner', 'search_read',
                [[['id', '=', po['partner_id'][0]]]],
                {'fields': ['mobile','email',"name"]})

        kot_lines = models.execute_kw(db, uid, password,
                'pos.kitchen.orderline', 'search_read',
                [[['order_id', '=', po['id']]]],
                {'fields': ['product_id']})

        for kot in kot_lines:
            sale_price = models.execute_kw(db, uid, password,
                'product.product', 'search_read',
                [[['id', '=', kot['product_id'][0]]]],
                {'fields': ['lst_price']})
            amount_total = sale_price[0]['lst_price']

        url = "https://apitest.myfatoorah.com/v2/SendPayment"

        payload = json.dumps({
        "CustomerName": customer[0]["name"],
        "NotificationOption": "lnk",
        "InvoiceValue": amount_total,
        "DisplayCurrencyIso": "kwd",
        "Language": "En",
        "CustomerMobile":customer[0]["mobile"] if customer[0]["mobile"] else '',
        "CustomerEmail":customer[0]["email"] if customer[0]["email"] else ''
        })
        headers = {
        'Authorization': 'Bearer 0AYGwuQS5I_r69l8Zl0YCJf81CGRB3epN6l_Up6sAwsU0jXD1v1FYvj8K-AJb95FszIs5pBXc6XhMF4v56ywEJ_ZUqqNus13uE39MLq4CgDkRhSWW0vBqOK5B5bJv74g7v5ltu0AW71yqJcJIl7K5CF5NZFEmKnUQ_zKYH6Y_LL9W6xTntmmdiOgAvI6uLFZrr1J0qRz9tNhraNr5NMSZBs3IHZTglXYgahHzqHmZenZ5LcWZL6cdUpFd4cNR4-WH_u4gVIYjc7MZDyfWDRlhJjjRki3nZZf-npeoaLEje8eZvraED9Qd0RMK4yG-tCmJQqF50Z6KHJ2-wZaEwO9-7V5-crEH8yKQzrPG2jOHkzmnCq_ad4D3iyt53NSNL9ePR1-xfl36ATbYI_r-GlmIUzDvFREduzEdq9zeB31M0ZgxOUBHmp-bQL1UWNRecsv4di2I48eKXhYaqs42nr0dSb-a-b0_S6ynCT00ECQuojEx4KjjMbG36ZaD73zntf-eAB5Juh78uSXcXc6c5lQOgiqCDlTm42o_jVOW4vbHiAHvp5zayetI7k3Z65A4HH3sptM-84Gj2qcfp8wqBt_eSPZpmqI5GjL-p-Zdb5_8Soq5LLUdYnqBFeLIU-NZJbGy9nI1bXw_h7tNQh2UcmKi0QKfmfDNVu6PTQKkP8ZcR_FPprDfnkuoSWruSVhywe8Fh-LpA',
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        fatoraLink=response.json()

        update_pos_order = models.execute_kw(db, uid, password, 'pos.kitchen.order', 'write', 
            [[po['id']],
            {'invoice_id': fatoraLink["Data"]["InvoiceId"],
            'invoice_link':fatoraLink["Data"]["InvoiceURL"],
            'is_link_sent':True
            }])
        print("added status: ",update_pos_order," ID: ",po['id'])

    except Exception as e:
        print(e)
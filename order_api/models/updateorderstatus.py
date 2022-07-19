import requests
import json
import ssl
from xmlrpc import client as xmlrpclib

url = 'https://nssglobal-pos-3589592.dev.odoo.com'
db = 'nssglobal-pos-3589592'
username = 'admin'
password = '123'

server = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())
uid = server.login(db, username, password)
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())


pos_orders = models.execute_kw(db, uid, password,
            'pos.kitchen.order', 'search_read',
            [[['payment_status', '=', 'pending']]],
            {'fields': ['id','invoice_id']})

for po in pos_orders:

    url = "https://apitest.myfatoorah.com/v2/GetPaymentStatus"

    payload = json.dumps({
    "Key": po['invoice_id'],
    "KeyType": "invoiceid"
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer 0AYGwuQS5I_r69l8Zl0YCJf81CGRB3epN6l_Up6sAwsU0jXD1v1FYvj8K-AJb95FszIs5pBXc6XhMF4v56ywEJ_ZUqqNus13uE39MLq4CgDkRhSWW0vBqOK5B5bJv74g7v5ltu0AW71yqJcJIl7K5CF5NZFEmKnUQ_zKYH6Y_LL9W6xTntmmdiOgAvI6uLFZrr1J0qRz9tNhraNr5NMSZBs3IHZTglXYgahHzqHmZenZ5LcWZL6cdUpFd4cNR4-WH_u4gVIYjc7MZDyfWDRlhJjjRki3nZZf-npeoaLEje8eZvraED9Qd0RMK4yG-tCmJQqF50Z6KHJ2-wZaEwO9-7V5-crEH8yKQzrPG2jOHkzmnCq_ad4D3iyt53NSNL9ePR1-xfl36ATbYI_r-GlmIUzDvFREduzEdq9zeB31M0ZgxOUBHmp-bQL1UWNRecsv4di2I48eKXhYaqs42nr0dSb-a-b0_S6ynCT00ECQuojEx4KjjMbG36ZaD73zntf-eAB5Juh78uSXcXc6c5lQOgiqCDlTm42o_jVOW4vbHiAHvp5zayetI7k3Z65A4HH3sptM-84Gj2qcfp8wqBt_eSPZpmqI5GjL-p-Zdb5_8Soq5LLUdYnqBFeLIU-NZJbGy9nI1bXw_h7tNQh2UcmKi0QKfmfDNVu6PTQKkP8ZcR_FPprDfnkuoSWruSVhywe8Fh-LpA',
    'Cookie': 'ApplicationGatewayAffinity=3ef0c0508ad415fb05a4ff3f87fb97da; ApplicationGatewayAffinityCORS=3ef0c0508ad415fb05a4ff3f87fb97da'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    myfatoorstatus=response.json()

    if myfatoorstatus['Data']['InvoiceStatus']=='Paid':
        update_pos_order = models.execute_kw(db, uid, password, 'pos.kitchen.order', 'write', 
            [[po['id']],
            {
                'payment_status': 'done'
            }])
        print("update Order Status: ",update_pos_order," ID: ",po['id'])
        
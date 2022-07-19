import requests
import json
import ssl
from xmlrpc import client as xmlrpclib

url = 'https://abarunited.odoo.com'
db = 'zeeshanarif8-nssglobal-production-3444035'
username = 'admin'
password = 'Admin2022!!##'

server = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())
uid = server.login(db, username, password)
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())


pos_orders = models.execute_kw(db, uid, password,
            'pos.order', 'search_read',
            [[['x_studio_payment_status', '=', 'Payment Pending'],['company_id','=',3]]],
            {'fields': ['id','x_studio_myfatoorah_invoice_id']})

for po in pos_orders:

    url = "https://api.myfatoorah.com/v2/GetPaymentStatus"

    payload = json.dumps({
    "Key": po['x_studio_myfatoorah_invoice_id'],
    "KeyType": "invoiceid"
    })
    headers = {
    'Authorization': 'Bearer LHXiQbW8xegHa0ke6RT7kiN_A0Q3DXXSzvtMZKAG1Yk8tTngS_P5zMmO866hvxccCStKFq-_FMoRkyzwjHmOEwcA-HMUEr3kG7Dp5osFYxQMB7xxeqZS3YNMqjTyTTAvKK1zjrqOEiDdjWGDpMxObQ_tIqWcoNgRAcr-G407jw6mJZl-vd-Ht3i6jlstUqE4epIZJFz0obV4fyczQwTAAu5q3a4hmRe2U8HCpB7sCEaS-orASNt3ZxwclT8pNvK6gGzdXQowOEo8xWr_Wsz9_nlXKPpKGO0PCSgALx11xdg54toBCGzLpxf7S8MR1Fg6uOVlH7HQF2t2XfxEsylG8Fn8v-6wNRWKuyusQF_CGl_HRx8GpvSeSRXyZcVWEjQ4eT2cTnDzZWyeQPglvuD1puakMYIk_ACBoSlXWpouazmKZeRwhQIRKrPAVZS9SLE7tkYyU9dfxpTaTN0Nm39Um3IRRWRHSGsWim4Ku2jgejkeMPUzJw0vrr-b6VyXDusveCaSEiV40wzZ31xBTE-U3UZ2A3SFfDCmYQUHgBEspBGPg2RLZNaB6AyPm3x6oOcdCLnkznCnQduoIKu288zoz989p36opVe_d2N_UkM6jBrIH8Im56Fk1ZyZr5VSCXkjtQjdHRQ2CvkOHvkyaqWTbMy-btdO-tAE6Rpafd-DyrElLloSCMW5Cm2dLMn7gVe-ZR77yQ',
    'Content-Type': 'application/json',
    'Cookie': 'ApplicationGatewayAffinity=3ef0c0508ad415fb05a4ff3f87fb97da; ApplicationGatewayAffinityCORS=3ef0c0508ad415fb05a4ff3f87fb97da'
    }
#ben@qforbs.com
    response = requests.request("POST", url, headers=headers, data=payload)
    myfatoorstatus=response.json()

    if myfatoorstatus['Data']['InvoiceStatus']=='Paid':
        update_pos_order = models.execute_kw(db, uid, password, 'pos.order', 'write', 
            [[po['id']],
            {
                'x_studio_payment_status': 'Payment Done'
            }])
        print("update Order Status: ",update_pos_order," ID: ",po['id'])
        
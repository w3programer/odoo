import requests
import json
import ssl
from xmlrpc import client as xmlrpclib
# from xmlrpc import client as xmlrpclib
import smtplib


url = 'https://abarunited.odoo.com'
db = 'zeeshanarif8-nssglobal-production-3444035'
username = 'admin'
password = 'Admin2022!!##'

server = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())
uid = server.login(db, username, password)
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url),verbose=False, use_datetime=True,context=ssl._create_unverified_context())


pos_orders = models.execute_kw(db, uid, password,
            'pos.order', 'search_read',
            [[['x_studio_my_fatoorah_invoice_link', '=', False],['company_id','=',3],['amount_paid','>',0]]],
            {'fields': ['id','partner_id','amount_paid']})


for po in pos_orders:
    try:
        amount_total = 0
        customer = models.execute_kw(db, uid, password,
                'res.partner', 'search_read',
                [[['id', '=', po['partner_id'][0]]]],
                {'fields': ['mobile','email',"name"]})

        kot_lines = models.execute_kw(db, uid, password,
                'pos.order.line', 'search_read',
                [[['order_id', '=', po['id']]]],
                {'fields': ['product_id']})

        # # for kot in kot_lines:
        # sale_price = models.execute_kw(db, uid, password,
        #     'product.product', 'search_read',
        #     [[['id', '=', po['product_id'][0]]]],
        #     {'fields': ['lst_price']})
        amount_total = po['amount_paid']

        url = "https://api.myfatoorah.com/v2/SendPayment"

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
        'Authorization': 'Bearer LHXiQbW8xegHa0ke6RT7kiN_A0Q3DXXSzvtMZKAG1Yk8tTngS_P5zMmO866hvxccCStKFq-_FMoRkyzwjHmOEwcA-HMUEr3kG7Dp5osFYxQMB7xxeqZS3YNMqjTyTTAvKK1zjrqOEiDdjWGDpMxObQ_tIqWcoNgRAcr-G407jw6mJZl-vd-Ht3i6jlstUqE4epIZJFz0obV4fyczQwTAAu5q3a4hmRe2U8HCpB7sCEaS-orASNt3ZxwclT8pNvK6gGzdXQowOEo8xWr_Wsz9_nlXKPpKGO0PCSgALx11xdg54toBCGzLpxf7S8MR1Fg6uOVlH7HQF2t2XfxEsylG8Fn8v-6wNRWKuyusQF_CGl_HRx8GpvSeSRXyZcVWEjQ4eT2cTnDzZWyeQPglvuD1puakMYIk_ACBoSlXWpouazmKZeRwhQIRKrPAVZS9SLE7tkYyU9dfxpTaTN0Nm39Um3IRRWRHSGsWim4Ku2jgejkeMPUzJw0vrr-b6VyXDusveCaSEiV40wzZ31xBTE-U3UZ2A3SFfDCmYQUHgBEspBGPg2RLZNaB6AyPm3x6oOcdCLnkznCnQduoIKu288zoz989p36opVe_d2N_UkM6jBrIH8Im56Fk1ZyZr5VSCXkjtQjdHRQ2CvkOHvkyaqWTbMy-btdO-tAE6Rpafd-DyrElLloSCMW5Cm2dLMn7gVe-ZR77yQ',
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        fatoraLink=response.json()

        update_pos_order = models.execute_kw(db, uid, password, 'pos.order', 'write', 
            [[po['id']],
            {'x_studio_myfatoorah_invoice_id': fatoraLink["Data"]["InvoiceId"],
            'x_studio_my_fatoorah_invoice_link':fatoraLink["Data"]["InvoiceURL"],
            'x_studio_link_sent':True
            }])
        print("added status: ",update_pos_order," ID: ",po['id'])
        gmail_user = 'sales@blancheneigespa.com'
        gmail_password = 'BNSpa2021##$$'
        sent_from = gmail_user
        to = ['ben@qforbs.com','jerrafii@abarunited.com']
        # to = ['zeeshan8arif@gmail.com', 'huxe.ahmed2@gmail.com','huzaifa.shaikh@mrgc.com.pk']
        server = smtplib.SMTP_SSL('mail.blancheneigespa.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        msg="Subject: يرجى استخدام رابط الفاتورة للدفع  \n  Invoice link for payment " + fatoraLink["Data"]["InvoiceURL"]        
        val = server.sendmail(sent_from, to ,msg.encode('utf-8'))
        server.close()
        # print(str(val))
        # print(str(e))
        # update_sale_order = models.execute_kw(db, uid, password, 'sale.order', 'write', [[so_id],
        # {'error_log_email': True}])

    except Exception as e:
        print(e)
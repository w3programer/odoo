# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api
import requests
from twilio.rest import Client
from odoo.exceptions import ValidationError, AccessError
class POSOrder(models.Model):
    _inherit = 'pos.order'

    payment_status = fields.Selection([('pending', 'Pending'), ('paid', 'Paid')],  string='Payment Status', default='pending')
    delivery_status = fields.Selection([('waiting', 'Waiting for Payment'), ('ready', 'Ready for delivery'), ('delivered', 'Delivered')], string='Delivery Status', default='waiting')
    myfatoorah_invoice_id = fields.Char( string='MyFatoorah Invoice ID')
    myfatoorah_link = fields.Char( string='MyFatoorah Invoice Link')
    myfatoorah_bol = fields.Boolean( string='Link Sent')
    formula = fields.Char( string='Formula')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(POSOrder, self).create(vals_list)
        res.create_fatoorah_link()
        return res

    def create_fatoorah_link(self):
        try:

            url = "https://apitest.myfatoorah.com/v2/SendPayment"

            payload = json.dumps({
            "CustomerName": self.partner_id.name,
            "NotificationOption": "lnk",
            "InvoiceValue": self.amount_total,
            "DisplayCurrencyIso": "kwd",
            "Language": "En",
            "CustomerMobile":self.partner_id.mobile,
            "CustomerEmail":self.partner_id.email
            })
            headers = {
            'Authorization': 'Bearer 0AYGwuQS5I_r69l8Zl0YCJf81CGRB3epN6l_Up6sAwsU0jXD1v1FYvj8K-AJb95FszIs5pBXc6XhMF4v56ywEJ_ZUqqNus13uE39MLq4CgDkRhSWW0vBqOK5B5bJv74g7v5ltu0AW71yqJcJIl7K5CF5NZFEmKnUQ_zKYH6Y_LL9W6xTntmmdiOgAvI6uLFZrr1J0qRz9tNhraNr5NMSZBs3IHZTglXYgahHzqHmZenZ5LcWZL6cdUpFd4cNR4-WH_u4gVIYjc7MZDyfWDRlhJjjRki3nZZf-npeoaLEje8eZvraED9Qd0RMK4yG-tCmJQqF50Z6KHJ2-wZaEwO9-7V5-crEH8yKQzrPG2jOHkzmnCq_ad4D3iyt53NSNL9ePR1-xfl36ATbYI_r-GlmIUzDvFREduzEdq9zeB31M0ZgxOUBHmp-bQL1UWNRecsv4di2I48eKXhYaqs42nr0dSb-a-b0_S6ynCT00ECQuojEx4KjjMbG36ZaD73zntf-eAB5Juh78uSXcXc6c5lQOgiqCDlTm42o_jVOW4vbHiAHvp5zayetI7k3Z65A4HH3sptM-84Gj2qcfp8wqBt_eSPZpmqI5GjL-p-Zdb5_8Soq5LLUdYnqBFeLIU-NZJbGy9nI1bXw_h7tNQh2UcmKi0QKfmfDNVu6PTQKkP8ZcR_FPprDfnkuoSWruSVhywe8Fh-LpA',
            'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            fatoraLink=response.json()
            self.note = fatoraLink
            if fatoraLink["IsSuccess"]!=False:
                self.myfatoorah_link=fatoraLink["Data"]["InvoiceURL"]
                self.myfatoorah_invoice_id=fatoraLink["Data"]["InvoiceId"]
                self.action_send_sms()
        except AccessError as e:
            raise e

    def update_fatoorah_status(self):
        try:
            url = "https://api.myfatoorah.com/v2/GetPaymentStatus"

            payload = json.dumps({
                "Key": self.myfatoorah_invoice_id,
                "KeyType": "invoiceid"
            })
            headers = {
                'Authorization': 'Bearer LHXiQbW8xegHa0ke6RT7kiN_A0Q3DXXSzvtMZKAG1Yk8tTngS_P5zMmO866hvxccCStKFq-_FMoRkyzwjHmOEwcA-HMUEr3kG7Dp5osFYxQMB7xxeqZS3YNMqjTyTTAvKK1zjrqOEiDdjWGDpMxObQ_tIqWcoNgRAcr-G407jw6mJZl-vd-Ht3i6jlstUqE4epIZJFz0obV4fyczQwTAAu5q3a4hmRe2U8HCpB7sCEaS-orASNt3ZxwclT8pNvK6gGzdXQowOEo8xWr_Wsz9_nlXKPpKGO0PCSgALx11xdg54toBCGzLpxf7S8MR1Fg6uOVlH7HQF2t2XfxEsylG8Fn8v-6wNRWKuyusQF_CGl_HRx8GpvSeSRXyZcVWEjQ4eT2cTnDzZWyeQPglvuD1puakMYIk_ACBoSlXWpouazmKZeRwhQIRKrPAVZS9SLE7tkYyU9dfxpTaTN0Nm39Um3IRRWRHSGsWim4Ku2jgejkeMPUzJw0vrr-b6VyXDusveCaSEiV40wzZ31xBTE-U3UZ2A3SFfDCmYQUHgBEspBGPg2RLZNaB6AyPm3x6oOcdCLnkznCnQduoIKu288zoz989p36opVe_d2N_UkM6jBrIH8Im56Fk1ZyZr5VSCXkjtQjdHRQ2CvkOHvkyaqWTbMy-btdO-tAE6Rpafd-DyrElLloSCMW5Cm2dLMn7gVe-ZR77yQ',
                'Content-Type': 'application/json',
                'Cookie': 'ApplicationGatewayAffinity=3ef0c0508ad415fb05a4ff3f87fb97da; ApplicationGatewayAffinityCORS=3ef0c0508ad415fb05a4ff3f87fb97da'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            myfatoorstatus = response.json()

            print(myfatoorstatus["IsSuccess"])

            if myfatoorstatus["IsSuccess"] != False:
                if myfatoorstatus['Data']['InvoiceStatus'] == 'Paid':
                    self.payment_status= 'paid'
        except AccessError as e:
            raise e

    def action_send_sms(self):
        try:
            if self.myfatoorah_link:
                if self.partner_id.mobile:
                    to=self.partner_id.mobile
                    mob_number =f"+92{to[1:]}"
                    print(mob_number)
                    twillo_data = self.env['twillio.config'].search([])
                    if twillo_data:
                        data = twillo_data[-1]
                        account_sid = data.account_sid
                        auth_token = data.auth_token
                        number = data.number_from
                        client = Client(account_sid, auth_token)
                        msg = "Invoice link for payment "  "\n"  " يرجى استخدام رابط الفاتورة للدفع" "\n" + str(self.myfatoorah_link)
                        message = client.messages.create(body=  msg , from_=number, to=mob_number )
                        if message.sid:
                            move_dict = {
                                'partner_id': self.partner_id.id,
                                'number': mob_number,
                                'body':   msg ,
                                'state': 'sent',
                            }
                            self.env['sms.sms'].create(move_dict)
                if self.partner_id.email:
                    msg = "Invoice link for payment "  "\n"  " يرجى استخدام رابط الفاتورة للدفع" "\n" + str(
                        self.myfatoorah_link)
                    email_values = {
                        'body_html': msg,
                        'subject': "Invoice link for payment يرجى استخدام رابط الفاتورة للدفع ",
                        'email_from': self.env.user.company_id.email,
                        'email_to': self.partner_id.email,
                    }
                    mail = self.env['mail.mail'].sudo().create(email_values).send()


        except AccessError as e:
            raise e


class twilio_sms_config(models.Model):
    _name = 'twillio.config'

    name = fields.Char('Name')
    account_sid = fields.Char('Account SID')
    auth_token = fields.Char('Auth Token')
    number_from = fields.Char('Number From')

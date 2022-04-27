# -*- coding: utf-8 -*-
from odoo import api, fields, models

class twilio_sms_config(models.Model):
    _name = 'twillio.config'
    
    name=fields.Char('Name')
    account_sid=fields.Char('Account SID')
    auth_token=fields.Char('Auth Token')
    number_from=fields.Char('Number From')

    
    

     
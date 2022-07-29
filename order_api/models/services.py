import requests
import json
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import json
from datetime import datetime



class ServiceNote(models.Model):
    _name ="service.note"
    
    name = fields.Char('Service' , required=True)
    name_ar = fields.Char('Service AR')
    service_line_ids = fields.One2many("service.line" ,'service_id')
    
    
class ServiceLine(models.Model):
    _name ="service.line"
    _rec_name ="product_id"
    service_id = fields.Many2one('service.note' ,string='Service')
    product_id = fields.Many2one("product.product",string='Sub Service' ,required=True)
    price = fields.Float(string="Price",related="product_id.lst_price")

class PlanningSlotService(models.Model):
    _inherit = 'planning.slot'
    
    partner_id = fields.Many2one('res.partner' ,string="Customer")
    service_id = fields.Many2one('service.note' ,string="Service")
    sub_service_id =fields.Many2one('service.line' ,string="Sub service")

    
    def action_send(self):
        res = super(PlanningSlotService ,self).action_send()
        if self.partner_id and self.sub_service_id:
            self.createSO(self.id)
        return res

    
    def createSO(self,id):
        try:
            line_val = []
            line_val.append((0, 0, {
                        'product_id': self.sub_service_id.product_id.id,
                        'product_uom_qty': 1.0,
                        'price_unit': self.sub_service_id.product_id.list_price,
                    }))
            vals = {
                'partner_id': self.partner_id.id,
                'company_id': self.env.company.id,
                'date_order': self.start_datetime,
                'order_line': line_val
            }
            record = self.env['sale.order'].create(vals)
            planning_obj= self.env['planning.slot'].search([("id",'=',id)])
            planning_obj.sale_order_id=record.id
            return record 
        except Exception as e:
            print(e.args)       

class ProductProduct(models.Model):
    _inherit = 'product.product'

    name_ar = fields.Char('Arabic Name')
    
    
    
       
    
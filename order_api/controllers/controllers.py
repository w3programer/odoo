# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class OrderApi(http.Controller):

    @http.route('/create_order_api', type='json', methods=['POST'], auth="public", website="True")
    def createOrderApi(self, **kw):
        try:
            if request.jsonrequest:
                string = json.dumps(request.jsonrequest)
                json_string = json.loads(string)
                if json_string:
                    dict=json_string.get("params")
                    if dict:
                        order_lines=dict.get("order_lines")
                        odoo_customer = request.env['res.partner'].sudo().search([('name', '=', dict.get('customer')),('email', '=', dict.get('email'))])
                        odooCountry = request.env['res.country'].sudo().search([('name', '=', dict.get('country'))])
                        if not odooCountry:
                            odooCountry = request.env['res.country'].sudo().create({'name': dict.get('country')})
                        odooState = request.env['res.country.state'].sudo().search([('name', '=', dict.get('state'))])
                        if not odooState:
                            odooState = request.env['res.country.state'].sudo().create({'name': dict.get('state'), 'country_id': odooCountry.id, 'code': 11})
                        if not odoo_customer:
                            odoo_customer = request.env['res.partner'].sudo().create({
                                'name': dict.get('customer'),
                                'street': dict.get('street'),
                                'zip': dict.get('zip'),
                                'country_id': odooCountry.id,
                                'state_id': odooState.id,
                                'city': dict.get('city'),
                                'email': dict.get('email'),
                                'phone': dict.get('phone'),
                                'mobile': dict.get('mobile'),
                                'website': dict.get('website'),
                                'vat': dict.get('vat')
                            })

                        line_vals = []
                        for line in order_lines:
                            product = request.env['product.product'].sudo().search([('name', '=', line.get('product_id'))])
                            if not product:
                                product = request.env['product.product'].sudo().create({
                                    'name': line.get('product_id'),
                                    'list_price': line.get('price_unit'),
                                    'type':'product'
                                })
                            line_vals.append((0, 0, {
                                'product_id': product.id,
                                'price_unit': line.get('price_unit'),
                                'product_uom_qty': line.get('quantity')
                            }))
                        vals={
                            'partner_id': odoo_customer.id,
                            'date_order': dict.get("date_order"),
                            'order_line': line_vals,
                            'state': 'draft',
                            'origin': dict.get("origin")
                        }
                        sale_order = request.env['sale.order'].sudo().create(vals)
                        args = {
                            "Success": "true",
                            "Message": "Order is Created",
                        }
                        data = json.dumps(args)
                        return data
        except Exception as e:
            print(e)
            # return json.dumps(e)
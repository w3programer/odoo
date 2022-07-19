# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import datetime
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

    @http.route('/delivery_staus_api', type='json', methods=['POST'], auth="public", website="True")
    def delivery_status_api(self, **kw):
        try:
            if request.jsonrequest:
                string = json.dumps(request.jsonrequest)
                json_string = json.loads(string)
                if json_string:
                    dict = json_string.get("params")

                    if dict.get('delivery_status')=='delivered':
                        odoo_order = request.env['pos.order'].sudo().search([("name","=",dict.get('order_no'))])
                        if odoo_order:
                            print(dict.get('delivery_status'))
                            odoo_order.delivery_status='delivered'
                            args = {
                                "Success": "true",
                                "Message": "Delivery Status updated to Delivered",
                            }
                            data = json.dumps(args)
                            return data
                    if dict.get('delivery_status') == 'ready':
                        odoo_order = request.env['pos.order'].sudo().search([("name", "=", dict.get('order_no'))])
                        if odoo_order:
                            odoo_order.delivery_status = 'ready'
                            print(dict.get('delivery_status'))
                            args = {
                                "Success": "true",
                                "Message": "Delivery Status updated to Ready",
                            }
                            data = json.dumps(args)
                            return data
                    else:
                        args = {
                            "Success": "false",
                            "Message": "Wrong Delivery Status",
                        }
                        data = json.dumps(args)
                        return data
        except Exception as e:
            return e

    @http.route('/return/dashboard/data', auth='public', website=True)
    def return_dashboard_data(self, **kw):

        invoice_untaxed=0
        invoice_total=0
        invoice_amount_residual=0
        invoice_tax=0
        invoice_percentage=0
        sale_untaxed = 0
        sale_total = 0
        sale_tax = 0
        sale_profit = 0
        expense_total = 0
        payroll_total = 0
        total_assets = 0
        total_liability = 0
        customer_satis = request.env['res.partner'].sudo().search_count([])
        employee_satis = request.env['hr.employee'].sudo().search_count([])
        total_asset = request.env['account.move.line'].sudo().search([("account_id.internal_group",'in',["asset"])])
        for assets in total_asset:
            total_assets=total_assets+assets.credit

        total_liabilitys = request.env['account.move.line'].sudo().search(
            [("account_id.internal_group", 'in', ["liability"])])
        for liability in total_liabilitys:
            total_liability = total_liability + liability.credit




        invoice_data = request.env['account.move'].sudo().search([])
        for invoice in invoice_data:
            invoice_untaxed=invoice_untaxed+invoice.amount_untaxed_signed
            invoice_total=invoice_total+invoice.amount_total_signed
            invoice_tax=invoice.amount_total_signed-invoice.amount_untaxed_signed
            invoice_amount_residual=invoice_amount_residual+invoice.amount_residual
            if invoice_tax:
                invoice_percentage=(invoice_total/invoice_tax)*100

        sale_data = request.env['sale.order'].sudo().search([])


        for sale in sale_data:
            sale_untaxed = sale_untaxed + sale.amount_untaxed
            sale_total = sale_total + sale.amount_total
            sale_tax = sale_untaxed - sale_total
            sale_profit = sale_profit + sale.margin

        expense_data = request.env['hr.expense'].sudo().search([])


        for expense in expense_data:
            expense_total = expense_total + expense.total_amount

        payrolls = request.env['hr.payslip'].sudo().search([])


        for payroll in payrolls:
            today=str(datetime.datetime.utcnow()).split("-")[1]
            lst=str(payroll.date_to).split("-")
            month=lst[1]
            if today==month:
                payroll_total = payroll_total + payroll.net_wage

        data={
            "invoice_untaxed":invoice_untaxed,
            "invoice_total":invoice_total,
            "invoice_amount_residual":invoice_amount_residual,
            "invoice_tax":invoice_tax,
            "ebit": invoice_tax/100,
            "invoice_percentage":invoice_percentage,
            "sale_untaxed":sale_untaxed,
            "sale_total":sale_total,
            "sale_tax":sale_tax,
            "sale_profit":sale_profit,
            "expense_total":expense_total,
            "berry_ratio":sale_profit/expense_total,
            "payroll_ratio":payroll_total/invoice_total,
            "eva":total_assets-total_liability,
            "customer_satis":customer_satis ,
            "employee_satis":employee_satis ,
        }

        json_data = json.dumps(data)
        return json_data

# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

import base64
import io
from datetime import datetime, date, time
from odoo.exceptions import UserError, ValidationError, Warning
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools.misc import xlwt


class MailTemplate(models.Model):
	_inherit = 'mail.template'

	def send_mail(self, res_id, force_send=False, raise_exception=False, email_values=None):
		res = super(MailTemplate, self).send_mail(res_id, force_send=False, raise_exception=False, email_values=None)
		
		if self._context.get('auther'):
			self.env['mail.mail'].sudo().browse(res).author_id = self._context.get('auther').id
			self.env['mail.mail'].sudo().browse(res).send() # [(6,0,[self._context.get('attachment').id])]
		return res

class PosSession(models.Model):
    _inherit = 'pos.session'

    def session_order_summary(self):
        orders = self.env['pos.order'].search([('session_id','=', self.id)], order="date_order")
        return orders
    
    def pos_daily_report(self):
        session_id = self.env['pos.session'].search([], order="stop_at desc", limit=1)
        # raise UserError(session_id)
        if session_id:
            template_id = self.env['mail.template'].browse(13)
            auther = session_id.user_id.partner_id
            val = template_id.sudo().with_context(auther=auther).send_mail(session_id.id, force_send=True)
            # raise UserError(val)



class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    report = fields.Selection([('daily', 'Daily'), ('monthly', 'Monthly'), ('date_range', 'Date Range')])
    sales_person = fields.Boolean(string="Sales Person", default=False)
    products = fields.Boolean(string="Products")
    pos_summary_file = fields.Binary('POS Summary Report')
    file_name = fields.Char('File Name')
    summary_report_printed = fields.Boolean('Summary Report Printed')

    @api.onchange('report')
    def onchange_report(self):
        if self.report == 'daily':
            self.start_date = datetime.combine(date.today(), time(00, 00, 00))
            self.end_date = datetime.combine(date.today(), time(23, 59, 59))

        if self.report == 'monthly':
            self.start_date = date.today() + relativedelta(day=1, hour=00, minute=00, second=00)
            self.end_date = date.today() + relativedelta(day=31, hour=23, minute=59, second=59)

        if self.report == 'date_range':
            self.start_date = datetime.combine(date.today(), time(00, 00, 00))

    @api.depends('start_date', 'end_date', 'report')
    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.report == 'daily':
            date1 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S')
            self.start_date = datetime.combine(date1, time(00, 00, 00))
            self.end_date = datetime.combine(date1, time(23, 59, 59))

    def find_payment_methods(self, date_from, date_to):
        pos = ()
        for config in self.pos_config_ids:
            pos += (config.id,)
        sql_query = """ select distinct pm.id, pm.name from pos_payment abs
                        left join pos_order po on abs.pos_order_id = po.id  
                        left join pos_session ps on po.session_id = ps.id 
                        left join pos_config pc on ps.config_id = pc.id  
                        left join pos_payment_method pm on abs.payment_method_id = pm.id 
                        where po.date_order >= %s and  po.date_order <= %s and pc.id in %s
                        group by pm.id, pm.name;"""
        params = (date_from, date_to, pos)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.dictfetchall()
        return results

    def find_sales_persons(self, date_from, date_to):
        pos = ()
        for config in self.pos_config_ids:
            pos += (config.id,)
        sql_query = """select distinct cashier from pos_order pos
                        left join res_users res on pos.user_id = res.id
                        left join res_partner rp on res.partner_id = rp.id
                        left join pos_session ps on pos.session_id = ps.id
                        left join pos_config pc on ps.config_id = pc.id
                        where pos.date_order >= %s and  pos.date_order <= %s and pc.id in %s
                        group by cashier
                        order by cashier;"""
        params = (date_from, date_to, pos)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.dictfetchall()
        return results

    def find_order_by_range_and_sales_man(self, date_from, date_to, sales_man):
        pos = ()
        for config in self.pos_config_ids:
            pos += (config.id,)
        sql_query = """ select pos.cashier, pm.payment_method_id, sum(pm.amount)
                        from pos_payment pm
                        left join pos_order pos on pm.pos_order_id = pos.id
                        left join pos_session ps on pos.session_id = ps.id
                        left join pos_config pc on ps.config_id = pc.id
                        where pos.date_order >= %s and  pos.date_order <= %s
                        and pos.cashier = %s and pc.id in %s
                        group by pos.id,pm.payment_method_id;"""
        params = (date_from, date_to, sales_man, pos)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.dictfetchall()
        return results

    def print_xls_report(self, context=None):
        workbook = xlwt.Workbook()
        money_format = xlwt.XFStyle()
        money_format.num_format_str = '#,##0.00'
        if self.report == "daily" and self.sales_person == True:
            pos = []
            for config in self.pos_config_ids:
                pos.append(config.id)
            domain = [('date_order', '>=', self.start_date),
                      ('date_order', '<=', self.end_date)]
            orders = self.env['pos.order'].search([])
            current_date1 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y")

            if len(orders) == 0:
                return False
            else:
                worksheet = workbook.add_sheet('pos order', cell_overwrite_ok=True)

                worksheet.col(0).width = 2000
                worksheet.col(1).width = 5000
                worksheet.col(2).width = 5000
                worksheet.col(3).width = 4000
                worksheet.col(4).width = 4000
                font_left = xlwt.easyxf('font: height 200')
                font_right = xlwt.easyxf('align: horiz right; font: height 200', num_format_str='#,##0.00')
                font_bold_center = xlwt.easyxf('align: horiz center;  font: height 200; font: bold True')
                heading = xlwt.easyxf('align: horiz center; font: height 400; font: bold True')

                net_total_without_tax = 0
                sales_person_dict = {}
                payment_dict = {}
                journal_dict = {}
                journal_index = {}
                payment_methods = self.find_payment_methods(self.start_date, self.end_date)
                i = 1
                for method in payment_methods:
                    journal_index[method['name']] = i
                    journal_dict[method['name']] = 0
                    i += 1
                for order in orders:
                    if order.cashier in payment_dict:
                        for pos_payment in order.payment_ids:
                            if pos_payment.payment_method_id.name in journal_dict:
                                journal_dict[pos_payment.payment_method_id.name] += pos_payment.amount
                    else:
                        for key in journal_dict:
                            journal_dict[key] = 0
                        for pos_payment in order.payment_ids:
                            if pos_payment.payment_method_id.name in journal_dict:
                                journal_dict[pos_payment.payment_method_id.name] += pos_payment.amount
                        payment_dict[order.cashier] = journal_dict.copy()

                    net_total_without_tax = (order.amount_total - order.amount_tax)
                    list_order = [net_total_without_tax, order.amount_tax, order.amount_total]

                    if order.cashier in sales_person_dict:
                        sales_person_dict[order.cashier][0] += (order.amount_total - order.amount_tax)
                        sales_person_dict[order.cashier][1] += order.amount_tax
                        sales_person_dict[order.cashier][2] += order.amount_total
                    else:
                        sales_person_dict[order.cashier] = list_order
                row = 5
                col = 1
                worksheet.write(row, col, 'Sales Person', font_bold_center)
                worksheet.write(row, col + 1, 'Untaxed Amount', font_bold_center)
                worksheet.write(row, col + 2, 'Tax', font_bold_center)
                worksheet.write(row, col + 3, 'Total Amount', font_bold_center)

                col = 4
                for key in journal_dict:
                    ind = journal_index[key]
                    worksheet.write(row, col + ind, key, font_bold_center)

                row = 6
                col = 0
                tot_untax = 0
                tot_tax = 0
                tot_amount = 0
                journal_tot = {}
                for key in sales_person_dict:
                    col = 0
                    worksheet.write(row, col + 1, key, font_left)
                    worksheet.write(row, col + 2, sales_person_dict[key][0], font_right)
                    worksheet.write(row, col + 3, sales_person_dict[key][1], font_right)
                    worksheet.write(row, col + 4, sales_person_dict[key][2], font_right)
                    for key1 in payment_dict[key]:
                        ind = journal_index[key1]
                        worksheet.col(row).width = 4000
                        worksheet.col(col + 5).width = 4000
                        worksheet.write(row, col + 4 + ind, payment_dict[key][key1], font_right)
                        if key1 in journal_tot:
                            journal_tot[key1] += payment_dict[key][key1]
                        else:
                            journal_tot[key1] = payment_dict[key][key1]

                    tot_untax += sales_person_dict[key][0]
                    tot_tax += sales_person_dict[key][1]
                    tot_amount += sales_person_dict[key][2]
                    row += 1
                col = 0
                worksheet.write(row + 1, col + 1, "Total", font_bold_center)
                worksheet.write(row + 1, col + 2, tot_untax, font_right)
                worksheet.write(row + 1, col + 3, tot_tax, font_right)
                worksheet.write(row + 1, col + 4, tot_amount, font_right)
                for key in journal_tot:
                    ind = journal_index[key]
                    worksheet.write(row + 1, col + 4 + ind, journal_tot[key], font_right)

                worksheet.write(1, len(journal_tot) + 3, 'Date', font_bold_center)
                worksheet.write(1, len(journal_tot) + 4, current_date1)
                worksheet.write_merge(2, 3, 1, len(journal_tot) + 4, "Daily Sales by Salesperson", heading)
                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.pos_summary_file = excel_file
                self.file_name = 'POS Summary Report.xls'
                self.summary_report_printed = True
                fp.close()
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=pos.details.wizard&'
                           'field=pos_summary_file&download=true&id=%s&filename=POS Summary Report.xls' % self.id,
                    'target': 'new',
                }


        if self.report == "date_range" and self.products == True or self.report == "daily" and self.products == True:
            date1 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y")
            date2 = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y")
            pos = []
            for config in self.pos_config_ids:
                pos.append(config.id)

            domain = [('session_id.config_id', 'in', pos), ('date_order', '>=', self.start_date),
                      ('date_order', '<=', self.end_date)]
            orders = self.env['pos.order'].search(domain)

            worksheet = workbook.add_sheet('Daily Item wise Sales Summary and DateRange Item wise Sales Summary',
                                           cell_overwrite_ok=True)
            worksheet.col(0).width = 2000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 7000
            worksheet.col(4).width = 4000
            worksheet.col(5).width = 3000
            worksheet.col(6).width = 3000

            font_left = xlwt.easyxf('font: height 200')
            font_right = xlwt.easyxf('align: horiz right; font: height 200', num_format_str='#,##0.00')
            font_bold_center = xlwt.easyxf('align: horiz center;  font: height 200; font: bold True')
            font_center = xlwt.easyxf('align: horiz center;  font: height 200;')
            heading = xlwt.easyxf('align: horiz center; font: height 400; font: bold True')

            if self.report == 'daily':
                worksheet.write_merge(3, 4, 1, 9, "Daily Item wise Sales Summary", heading)
                worksheet.write(2, 8, 'Date', font_bold_center)
                worksheet.write(2, 9, date1)
            else:
                worksheet.write(2, 8, 'From', font_bold_center)
                worksheet.write(2, 9, date1)
                worksheet.write(3, 8, 'To', font_bold_center)
                worksheet.write(3, 9, date2)
                worksheet.write_merge(4, 5, 1, 9, "DateRange Item wise Sales Summary", heading)

            worksheet.write(7, 1, 'SI No', font_bold_center)
            worksheet.write(7, 2, 'Product Ref', font_bold_center)
            worksheet.write(7, 3, 'Product', font_bold_center)
            worksheet.write(7, 4, 'Qty', font_bold_center)
            worksheet.write(7, 5, 'Unit Price', font_bold_center)
            worksheet.write(7, 6, 'Discount', font_bold_center)
            worksheet.write(7, 7, 'Subtotal', font_bold_center)
            worksheet.write(7, 8, 'Tax', font_bold_center)
            worksheet.write(7, 9, 'Total', font_bold_center)

            i = 1
            row = 8
            col = 0
            total = 0
            tax = 0
            for order in orders:
                for line in order.lines:
                    worksheet.write(row, col + 1, i, font_center)
                    worksheet.write(row, col + 2, line.product_id.default_code, font_center)
                    worksheet.write(row, col + 3, line.product_id.name, font_left)
                    worksheet.write(row, col + 4, line.qty, font_center)
                    worksheet.write(row, col + 5, line.price_unit, font_right)
                    worksheet.write(row, col + 6, str(line.discount) + '%', font_right)
                    worksheet.write(row, col + 7, line.price_subtotal, font_right)
                    worksheet.write(row, col + 8, line.tax_ids_after_fiscal_position.name, font_center)
                    worksheet.write(row, col + 9, line.price_subtotal_incl, font_right)
                    row += 1
                    i += 1
                total += order.amount_total
                tax += order.amount_tax
            worksheet.write(row + 1, col + 8, "Total Tax", font_bold_center)
            worksheet.write(row + 2, col + 8, "Net Total", font_bold_center)
            worksheet.write(row + 1, col + 9, tax, font_right)
            worksheet.write(row + 2, col + 9, total, font_right)

            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            self.pos_summary_file = excel_file
            self.file_name = 'POS Summary Report.xls'
            self.summary_report_printed = True
            fp.close()
            if len(orders) == 0:
                return False
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=pos.details.wizard&'
                           'field=pos_summary_file&download=true&id=%s&filename=POS Summary Report.xls' % self.id,
                    'target': 'new',
                }
            if len(orders) == 0:
                return False


        if self.report == "date_range" and self.sales_person == True:
            date1 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y")
            date2 = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y")
            valid = 0
            worksheet = workbook.add_sheet('Date Range Sales by SalesPerson', cell_overwrite_ok=True)
            worksheet.col(0).width = 3000
            worksheet.col(1).width = 15000
            font_left = xlwt.easyxf('font: height 200')
            font_right = xlwt.easyxf('align: horiz right; font: height 200', num_format_str='#,##0.00')
            font_bold_center = xlwt.easyxf('align: horiz center;  font: height 200; font: bold True')
            heading = xlwt.easyxf('align: horiz center; font: height 400; font: bold True')

            payment_methods = self.find_payment_methods(self.start_date, self.end_date)
            payment_methods_dict1 = {}
            payment_methods_dict2 = {}

            for method in payment_methods:
                payment_methods_dict1[method['id']] = 0
                payment_methods_dict2[method['id']] = method['name']

            sales_persons = self.find_sales_persons(self.start_date, self.end_date)
            sales_persons_dict1 = {}

            row = 5
            col = 1
            worksheet.write(row, col, 'Salesperson', font_bold_center)
            for person in sales_persons:
                sales_persons_dict1[person['cashier']] = payment_methods_dict1.copy()

            col1 = col2 = col + 1
            for key in payment_methods_dict2:
                worksheet.col(col + 1).width = 3000
                worksheet.write(row, col + 1, payment_methods_dict2[key], font_bold_center)
                col += 1
            worksheet.write(row, col + 1, "Total", font_bold_center)

            row += 1
            row1 = row
            for sales_person in sales_persons_dict1:
                for payment in payment_methods_dict1:
                    payment_methods_dict1[payment] = 0
                worksheet.write(row, 1, sales_person, font_left)
                row += 1
                orders = self.find_order_by_range_and_sales_man(self.start_date, self.end_date,
                                                                sales_person)
                for order in orders:
                    valid += 1
                    payment_methods_dict1[order['payment_method_id']] += order['sum']
                sales_persons_dict1[sales_person] = payment_methods_dict1.copy()
            total_dict = {}
            for sales_person in sales_persons_dict1:
                total = 0
                for method in sales_persons_dict1[sales_person]:
                    total += sales_persons_dict1[sales_person][method]
                total_dict[sales_person] = total

            for sales_person in sales_persons_dict1:
                col1 = col2
                for method in sales_persons_dict1[sales_person]:
                    worksheet.write(row1, col1, sales_persons_dict1[sales_person][method], font_right)
                    col1 += 1
                worksheet.write(row1, col1, total_dict[sales_person], font_right)
                row1 += 1

            worksheet.write(1, col, 'From', font_bold_center)
            worksheet.write(1, col + 1, date1)
            worksheet.write(2, col, 'To', font_bold_center)
            worksheet.write(2, col + 1, date2)
            worksheet.write_merge(3, 4, 1, col + 1, 'Date Range Sales by SalesPerson', heading)
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            self.pos_summary_file = excel_file
            self.file_name = 'POS Summary Report.xls'
            self.summary_report_printed = True
            fp.close()
            if valid == 0:
                return False
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=pos.details.wizard&'
                           'field=pos_summary_file&download=true&id=%s&filename=POS Summary Report.xls' % self.id,
                    'target': 'new',
                }


        if self.report == "monthly" and self.products == True:
            date1 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
            month1 = date1.strftime('%B')
            year1 = date1.strftime('%Y')
            date2 = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').date()
            month2 = date2.strftime('%B')
            year2 = date2.strftime('%Y')

            font_left = xlwt.easyxf('font: height 200')
            font_right = xlwt.easyxf('align: horiz right; font: height 200', num_format_str='#,##0.00')
            font_bold_center = xlwt.easyxf('align: horiz center;  font: height 200; font: bold True')
            font_center = xlwt.easyxf('align: horiz center;  font: height 200;')
            heading = xlwt.easyxf('align: horiz center; font: height 400; font: bold True')

            current_str_date_to = str(date.today())
            current_date1 = datetime.strptime(current_str_date_to, '%Y-%m-%d').date()
            current_year = current_date1.strftime('%Y')
            current_year = int(current_year)
            year_end = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').date()
            previous_yr = (datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()).strftime('%Y')

            year_start2 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
            current_month = int(year_start2.strftime('%-m'))
            current_year2 = int(previous_yr)

            col1 = 6
            row1 = 5
            status = 0
            while year_start2 < year_end:
                month_start = year_start2 + relativedelta(year=current_year2, month=current_month, day=1, hours=00,
                                                          minutes=00, seconds=00)
                month_end = year_start2 + relativedelta(year=current_year2, month=current_month, day=31, hours=23,
                                                        minutes=59, seconds=59)
                year = month_start.strftime('%Y')
                month = month_start.strftime('%b')

                worksheet = workbook.add_sheet(month + '-' + year, cell_overwrite_ok=True)
                worksheet.col(0).width = 2000
                worksheet.col(1).width = 2000
                worksheet.col(2).width = 7000
                worksheet.col(3).width = 10000
                worksheet.col(4).width = 5000
                worksheet.col(5).width = 5000

                worksheet.write(6, 1, 'SI No', font_bold_center)
                worksheet.write(6, 2, 'Product Ref', font_bold_center)
                worksheet.write(6, 3, 'Product', font_bold_center)
                worksheet.write(6, 4, 'Unit Price', font_bold_center)
                worksheet.write(6, 5, 'Disc (%)', font_bold_center)
                worksheet.write(6, 6, "Quantity", font_bold_center)

                if current_month == 13:
                    current_month = 1
                    current_year2 += 1
                pos = ()
                for config in self.pos_config_ids:
                    pos += (config.id,)

                sql_query = """ select pt.name,pos.product_id,pos.price_unit,pp.default_code,pos.discount,sum(pos.qty) from pos_order_line pos
                                        left join product_product pp
                                        on pos.product_id =  pp.id
                                        left join pos_order po
                                        on pos.order_id= po.id
                                        left join product_template pt on pp.product_tmpl_id = pt.id
                                        left join pos_session ps on po.session_id = ps.id
                                        left join pos_config pc on ps.config_id = pc.id
                                        where date_order >= %s and  date_order <= %s and pc.id in %s
                                        group by pos.product_id,pos.price_unit,pos.discount,pp.default_code, pt.name
                                        order by pos.product_id;"""
                params = (month_start, month_end, pos)
                self.env.cr.execute(sql_query, params)
                results = self.env.cr.dictfetchall()
                i = 1
                row = 7
                col = 0
                for line in results:
                    status += 1
                    worksheet.write(row, col + 1, i, font_center)
                    worksheet.write(row, col + 2, line['default_code'], font_left)
                    worksheet.write(row, col + 3, line['name'], font_left)
                    worksheet.write(row, col + 4, line['price_unit'], font_right)
                    worksheet.write(row, col + 5, line['discount'], font_right)
                    worksheet.write(row, col1, line['sum'], font_right)
                    row += 1
                    i += 1

                pos1 = []
                for config in self.pos_config_ids:
                    pos1.append(config.id)
                domain = [('session_id.config_id', 'in', pos1), ('date_order', '>=', str(month_start)),
                          ('date_order', '<=', str(month_end))]
                orders = self.env['pos.order'].search(domain)
                tax = 0
                total = 0
                for order in orders:
                    tax += order.amount_tax
                    total += order.amount_total
                worksheet.write(row + 1, col1 - 1, "Tax", font_bold_center)
                worksheet.write(row + 2, col1 - 1, "Total", font_bold_center)
                worksheet.write(row + 1, col1, tax, font_right)
                worksheet.write(row + 2, col1, total, font_right)

                year_start2 += relativedelta(year=current_year2, month=current_month, day=31, hours=00, minutes=00,
                                             seconds=00)
                current_month += 1

                worksheet.write(1, col1 - 1, "Month", font_bold_center)
                worksheet.write(1, col1, month + '-' + year)
                worksheet.write_merge(2, 3, 1, col1, "Monthly Item Wise Sales Summary", heading)
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            self.pos_summary_file = excel_file
            self.file_name = 'POS Summary Report.xls'
            self.summary_report_printed = True
            fp.close()
            if status == 0:
                return False
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=pos.details.wizard&'
                           'field=pos_summary_file&download=true&id=%s&filename=POS Summary Report.xls' % self.id,
                    'target': 'new',
                }


        if self.report == "monthly" and self.sales_person == True:
            date1 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
            date2 = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').date()
            month1 = date1.strftime('%B')
            year1 = date1.strftime('%Y')
            month2 = date2.strftime('%B')
            year2 = date2.strftime('%Y')

            valid = 0
            worksheet = workbook.add_sheet('Monthly Sales By SalesPerson', cell_overwrite_ok=True)
            worksheet.col(0).width = 2000
            worksheet.col(1).width = 7000
            font_left = xlwt.easyxf('font: height 200')
            font_right = xlwt.easyxf('align: horiz right; font: height 200', num_format_str='#,##0.00')
            font_bold_center = xlwt.easyxf('align: horiz center;  font: height 200; font: bold True')
            heading = xlwt.easyxf('align: horiz center; font: height 400; font: bold True')

            payment_methods = self.find_payment_methods(self.start_date, self.end_date)
            payment_methods_dict1 = {}
            payment_methods_dict2 = {}

            for method in payment_methods:
                payment_methods_dict1[method['id']] = 0
                payment_methods_dict2[method['id']] = method['name']

            sales_persons = self.find_sales_persons(self.start_date, self.end_date)
            sales_persons_dict1 = {}

            current_str_date_to = str(date.today())
            current_date1 = datetime.strptime(current_str_date_to, '%Y-%m-%d').date()
            current_year = current_date1.strftime('%Y')
            current_year = int(current_year)
            year_end = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').date()
            previous_yr = (datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()).strftime('%Y')

            year_start2 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
            current_month = int(year_start2.strftime('%-m'))
            current_year2 = int(previous_yr)

            row = 5
            col = 1
            worksheet.write_merge(row, 6, 1, col, 'Salesperson', font_bold_center)
            while year_start2 < year_end:
                row = 5
                for person in sales_persons:
                    sales_persons_dict1[person['cashier']] = payment_methods_dict1.copy()
                if current_month == 13:
                    current_month = 1
                    current_year2 += 1
                month_start = year_start2 + relativedelta(year=current_year2, month=current_month, day=1, hours=00,
                                                          minutes=00, seconds=00)
                month_end = year_start2 + relativedelta(year=current_year2, month=current_month, day=31, hours=23,
                                                        minutes=59, seconds=59)
                year = month_start.strftime('%Y')
                month = month_start.strftime('%b')

                col1 = col2 = col + 1
                worksheet.write_merge(row, row, col + 1, col + len(payment_methods) + 1, month + '-' + year,
                                      font_bold_center)
                for key in payment_methods_dict2:
                    worksheet.col(col + 1).width = 5000
                    worksheet.write(row + 1, col + 1, payment_methods_dict2[key], font_bold_center)
                    col += 1
                worksheet.col(col + 1).width = 5000
                worksheet.write(row + 1, col + 1, "Total", font_bold_center)
                col += 1

                row += 2
                row1 = row
                for sales_person in sales_persons_dict1:
                    for payment in payment_methods_dict1:
                        payment_methods_dict1[payment] = 0
                    worksheet.write(row, 1, sales_person, font_left)
                    row += 1
                    orders = self.find_order_by_range_and_sales_man(str(month_start), str(month_end),
                                                                    sales_person)
                    for order in orders:
                        valid += 1
                        payment_methods_dict1[order['payment_method_id']] += order['sum']
                    sales_persons_dict1[sales_person] = payment_methods_dict1.copy()
                year_start2 += relativedelta(year=current_year2, month=current_month, day=31, hours=00, minutes=00,
                                             seconds=00)
                current_month += 1
                total_dict = {}
                for sales_person in sales_persons_dict1:
                    total = 0
                    for method in sales_persons_dict1[sales_person]:
                        total += sales_persons_dict1[sales_person][method]
                    total_dict[sales_person] = total

                for sales_person in sales_persons_dict1:
                    col1 = col2
                    for method in sales_persons_dict1[sales_person]:
                        worksheet.write(row1, col1, sales_persons_dict1[sales_person][method], font_right)
                        col1 += 1
                    worksheet.write(row1, col1, total_dict[sales_person], font_right)
                    row1 += 1

            worksheet.write(1, col - 1, 'From', font_bold_center)
            worksheet.write(1, col, month1 + '-' + year1)
            worksheet.write(2, col - 1, 'To', font_bold_center)
            worksheet.write(2, col, month2 + '-' + year2)
            worksheet.write_merge(3, 4, 1, col, 'Date Range Sales by SalesPerson', heading)
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            self.pos_summary_file = excel_file
            self.file_name = 'POS Summary Report.xls'
            self.summary_report_printed = True
            fp.close()
            if valid == 0:
                return False
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=pos.details.wizard&'
                           'field=pos_summary_file&download=true&id=%s&filename=POS Summary Report.xls' % self.id,
                    'target': 'new',
                }


        if self.report == "date_range" or self.report == "daily" or self.report == "monthly":
            date1 = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
            date2 = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').date()
            day1 = date1.strftime('%d')
            month1 = date1.strftime('%b')
            year1 = date1.strftime('%Y')
            day2 = date2.strftime('%d')
            month2 = date2.strftime('%b')
            year2 = date2.strftime('%Y')

            pos = []
            for config in self.pos_config_ids:
                pos.append(config.id)

            domain = [('session_id.config_id', 'in', pos), ('date_order', '>=', self.start_date),
                      ('date_order', '<=', self.end_date)]
            orders = self.env['pos.order'].search(domain)
            if len(orders) == 0:
                return False
            else:
                worksheet = workbook.add_sheet('Order Summary', cell_overwrite_ok=True)
                font_left = xlwt.easyxf('font: height 200')
                font_right = xlwt.easyxf('align: horiz right; font: height 200', num_format_str='#,##0.00')
                font_bold_center = xlwt.easyxf('align: horiz center;  font: height 200; font: bold True')
                font_bold_right = xlwt.easyxf('align: horiz right;  font: height 200; font: bold True')
                font_center = xlwt.easyxf('align: horiz center;  font: height 200;')
                heading = xlwt.easyxf('align: horiz center; font: height 400; font: bold True')
                worksheet.col(0).width = 2000
                worksheet.col(1).width = 5000
                worksheet.col(2).width = 7000
                worksheet.col(3).width = 6000
                worksheet.col(4).width = 8000
                worksheet.col(5).width = 8000
                worksheet.col(6).width = 8000

                row = 1
                col = 4
                if self.report == 'daily':
                    worksheet.write(row, col + 1, 'Date', font_bold_center)
                    worksheet.write(row, col + 2, day1 + '-' + month1 + '-' + year1)
                else:
                    worksheet.write(row, col + 1, 'From', font_bold_center)
                    worksheet.write(row + 1, col + 1, 'To', font_bold_center)
                    worksheet.write(row, col + 2, day1 + '-' + month1 + '-' + year1)
                    worksheet.write(row + 1, col + 2, day2 + '-' + month2 + '-' + year2)

                worksheet.write_merge(3, 4, 1, col + 2, "Order Summary", heading)

                row = 6
                col = 1
                worksheet.write(row, col, 'Order Ref', font_bold_center)
                worksheet.write(row, col + 1, 'Date', font_bold_center)
                worksheet.write(row, col + 2, 'Salesman', font_bold_center)
                worksheet.write(row, col + 3, 'Untaxed Amount', font_bold_center)
                worksheet.write(row, col + 4, 'Tax Amount', font_bold_center)
                worksheet.write(row, col + 5, 'Total', font_bold_center)
                row = 7
                col = 0
                total = tax = wtax = 0
                for order in orders:
                    worksheet.write(row + 1, col + 1, order.name, font_center)
                    worksheet.write(row + 1, col + 2,
                                    datetime.strptime(str(order.date_order), '%Y-%m-%d %H:%M:%S').strftime("%d-%m-%Y"))
                    worksheet.write(row + 1, col + 3, order.user_id.name, font_left)
                    worksheet.write(row + 1, col + 4, order.amount_total - order.amount_tax, font_right)
                    worksheet.write(row + 1, col + 5, order.amount_tax, font_right)
                    worksheet.write(row + 1, col + 6, order.amount_total, font_right)
                    wtax += (order.amount_total - order.amount_tax)
                    tax += order.amount_tax
                    total += order.amount_total
                    row += 1

                worksheet.write(row + 2, col + 3, 'Net Total', font_bold_center)
                worksheet.write(row + 2, col + 4, wtax, font_bold_right)
                worksheet.write(row + 2, col + 5, tax, font_bold_right)
                worksheet.write(row + 2, col + 6, total, font_bold_right)
                fp = io.BytesIO()
                workbook.save(fp)
                excel_file = base64.encodestring(fp.getvalue())
                self.pos_summary_file = excel_file
                self.file_name = 'POS Summary Report.xls'
                self.summary_report_printed = True
                fp.close()
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=pos.details.wizard&'
                           'field=pos_summary_file&download=true&id=%s&filename=POS Summary Report.xls' % self.id,
                    'target': 'new',
                }

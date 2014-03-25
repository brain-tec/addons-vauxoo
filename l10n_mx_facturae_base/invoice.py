# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
############################################################################
#    Coded by: moylop260 (moylop260@vauxoo.com)
#    Launchpad Project Manager for Publication: Nhomar Hernandez - nhomar@vauxoo.com
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import pooler, tools
from openerp import netsvc
from openerp import release
import time
from xml.dom import minidom
import os
import base64
# import libxml2
# import libxslt
# import zipfile
# import StringIO
# import OpenSSL
import hashlib
import tempfile
import os
import codecs
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import string
import logging
_logger = logging.getLogger(__name__)
try:
    from qrcode import *
except:
    _logger.error('Execute "sudo pip install pil qrcode" to use l10n_mx_facturae_pac_finkok module.')
import jinja2
import xml
import cgi

def exec_command_pipe(name, *args):
    """
    @param name :
    """
    # Agregue esta funcion, ya que con la nueva funcion original, de tools no
    # funciona
    prog = tools.find_in_path(name)
    if not prog:
        raise Exception('Couldn\'t find %s' % name)
    if os.name == "nt":
        cmd = '"'+prog+'" '+' '.join(args)
    else:
        cmd = prog+' '+' '.join(args)
    return os.popen2(cmd, 'b')

# TODO: Eliminar esta funcionalidad, mejor agregar al path la aplicacion
# que deseamos


def find_in_subpath(name, subpath):
    """
    @param name :
    @param subpath :
    """
    if os.path.isdir(subpath):
        path = [dir for dir in map(lambda x: os.path.join(subpath, x),
                os.listdir(subpath)) if os.path.isdir(dir)]
        for dir in path:
            val = os.path.join(dir, name)
            if os.path.isfile(val) or os.path.islink(val):
                return val
    return None

# TODO: Agregar una libreria para esto


def conv_ascii(text):
    """
    @param text : text that need convert vowels accented & characters to ASCII
    Converts accented vowels, ñ and ç to their ASCII equivalent characters
    """
    old_chars = [
        'á', 'é', 'í', 'ó', 'ú', 'à', 'è', 'ì', 'ò', 'ù', 'ä', 'ë', 'ï', 'ö',
        'ü', 'â', 'ê', 'î', 'ô', 'û', 'Á', 'É', 'Í', 'Ó', 'Ú', 'À', 'È', 'Ì',
        'Ò', 'Ù', 'Ä', 'Ë', 'Ï', 'Ö', 'Ü', 'Â', 'Ê', 'Î', 'Ô', 'Û', 'ñ', 'Ñ',
        'ç', 'Ç', 'ª', 'º', '°', ' ', 'Ã', 'Ø'
    ]
    new_chars = [
        'a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o',
        'u', 'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U', 'A', 'E', 'I',
        'O', 'U', 'A', 'E', 'I', 'O', 'U', 'A', 'E', 'I', 'O', 'U', 'n', 'N',
        'c', 'C', 'a', 'o', 'o', ' ', 'A', '0'
    ]
    for old, new in zip(old_chars, new_chars):
        try:
            text = text.replace(unicode(old, 'UTF-8'), new)
        except:
            try:
                text = text.replace(old, new)
            except:
                raise osv.except_osv(_('Warning !'), _(
                    "Can't recode the string [%s] in the letter [%s]") % (text, old))
    return text

# Cambiar el error
msg2 = "Contact you administrator &/or to info@vauxoo.com"


class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def string_to_xml_format(self, cr, uid, ids, text):
        if text:
            return cgi.escape(text, True).encode('ascii', 'xmlcharrefreplace').replace('\n\n', ' ')

    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = False
        ids = isinstance(ids, (int, long)) and [ids] or ids
        ir_attach_facturae_mx_obj = self.pool.get('ir.attachment.facturae.mx')
        inv_type_facturae = {
            'out_invoice': True,
            'out_refund': True,
            'in_invoice': False,
            'in_refund': False}
        for inv in self.browse(cr, uid, ids, context=context):
            if inv_type_facturae.get(inv.type, False):
                ir_attach_facturae_mx_ids = ir_attach_facturae_mx_obj.search(
                    cr, uid, [('id_source', '=', inv.id), ('model_source', '=', self._name)], context=context)
                if ir_attach_facturae_mx_ids:
                    for attach in ir_attach_facturae_mx_obj.browse(cr, uid, ir_attach_facturae_mx_ids, context=context):
                        if attach.state <> 'cancel':
                            res = super(account_invoice, self).action_cancel(cr, uid, ids, context=context)
                            if res:
                                attach = ir_attach_facturae_mx_obj.signal_cancel(cr, uid, [attach.id], context=context)
                                if attach:
                                    self.write(cr, uid, ids, {'date_invoice_cancel': time.strftime('%Y-%m-%d %H:%M:%S')})
                        else:
                            res = super(account_invoice, self).action_cancel(cr, uid, ids, context=context)
                else:
                    res = super(account_invoice, self).action_cancel(cr, uid, ids, context=context)
        return res

    def create_ir_attachment_facturae(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        attach = ''
        ir_attach_obj = self.pool.get('ir.attachment.facturae.mx')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        attachment_obj = self.pool.get('ir.attachment')
        attach_ids = []
        inv_type_facturae = {
            'out_invoice': True,
            'out_refund': True,
            'in_invoice': False,
            'in_refund': False}
        file_globals = self._get_file_globals(cr, uid, ids, context=context)
        fname_cer_no_pem = file_globals['fname_cer']
        cerCSD = open(fname_cer_no_pem).read().encode('base64') #Mejor forma de hacerlo
        fname_key_no_pem = file_globals['fname_key']
        keyCSD = fname_key_no_pem and base64.encodestring(open(fname_key_no_pem, "r").read()) or ''
        for invoice in self.browse(cr, uid, ids, context=context):
            if inv_type_facturae.get(invoice.type, False):
                approval_id = invoice.invoice_sequence_id and invoice.invoice_sequence_id.approval_id or False
                if approval_id:
                    xml_fname, xml_data = self._get_facturae_invoice_xml_data(
                            cr, uid, ids, context=context)
                    fname = str(invoice.id) + '_XML_V3_2.xml' or ''
                    attachment_id = attachment_obj.create(cr, uid, {
                                        'name': fname,
                                        'datas': base64.encodestring(xml_data),
                                        'datas_fname': fname,
                                        'res_model': self._name,
                                        'res_id': invoice.id
                                }, context=context)
                    attach_ids = ir_attach_obj.create(cr, uid, {
                        'name': invoice.fname_invoice, 
                        'type': invoice.invoice_sequence_id.approval_id.type,
                        'journal_id': invoice.journal_id and invoice.journal_id.id or False,
                        'company_emitter_id': invoice.company_emitter_id.id,
                        'model_source': self._name or '',
                        'id_source': invoice.id,
                        'attachment_email': invoice.partner_id.email or '',
                        'certificate_password': file_globals.get('password', ''),
                        'certificate_file': cerCSD or '',
                        'certificate_key_file': keyCSD or '',
                        'user_pac': '',
                        'password_pac': '',
                        'url_webservice_pac': '',
                        #~'file_input_index': base64.encodestring(xml_data),
                        'document_source': invoice.number,
                        'file_input': attachment_id,
                        },
                      context=context)#Context, because use a variable type of our code but we dont need it.
                    ir_attach_obj.signal_confirm(cr, uid, [attach_ids], context=context)
                    if attach_ids:
                        result = mod_obj.get_object_reference(cr, uid, 'l10n_mx_ir_attachment_facturae',
                                                                        'action_ir_attachment_facturae_mx')
                        id = result and result[1] or False
                        result = act_obj.read(cr, uid, [id], context=context)[0]
                        #choose the view_mode accordingly
                        result['domain'] = "[('id','in',["+','.join(map(str, [attach_ids]))+"])]"
                        result['res_id'] = attach_ids or False
                        res = mod_obj.get_object_reference(cr, uid, 'l10n_mx_ir_attachment_facturae', 
                                                                        'view_ir_attachment_facturae_mx_form')
                        result['views'] = [(res and res[1] or False, 'form')]
                        return result
        return True


    def create_report(self, cr, uid, res_ids, report_name=False, file_name=False, context=None):
        """
        @param report_name : Name of report with the name of object more type
            of report
        @param file_name : Path where is save the report temporary more the
            name of report that is 'openerp___facturae__' more six random
            characters for no files duplicate
        """
        if context is None:
            context = {}
        if not report_name or not res_ids:
            return (False, Exception('Report name and Resources ids are required !!!'))
        # try:
        ret_file_name = file_name+'.pdf'
        service = netsvc.LocalService("report."+report_name)
        (result, format) = service.create(cr, uid, res_ids, report_name, context=context)
        fp = open(ret_file_name, 'wb+')
        fp.write(result)
        fp.close()
        # except Exception,e:
            # print 'Exception in create report:',e
            # return (False,str(e))
        return (True, ret_file_name)

    def create_report_pdf(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        id = ids[0]
        (fileno, fname) = tempfile.mkstemp(
            '.pdf', 'openerp_' + (False or '') + '__facturae__')
        os.close(fileno)
        file = self.create_report(cr, uid, [
                                  id], "account.invoice.facturae.pdf", fname)
        is_file = file[0]
        fname = file[1]
        if is_file and os.path.isfile(fname):
            f = open(fname, "r")
            data = f.read()
            f.close()
            data_attach = {
                'name': context.get('fname'),
                'datas': data and base64.encodestring(data) or None,
                'datas_fname': context.get('fname'),
                'description': 'Factura-E PDF',
                'res_model': self._name,
                'res_id': id,
            }
            self.pool.get('ir.attachment').create(
                cr, uid, data_attach, context=context)
        return True

    def action_make_cfd(self, cr, uid, ids, *args):
        self._attach_invoice(cr, uid, ids)
        return True

    def _get_fname_invoice(self, cr, uid, ids, field_names=None, arg=False, context=None):
        if context is None:
            context = {}
        res = {}
        sequence_obj = self.pool.get('ir.sequence')
        invoice_id__sequence_id = self._get_invoice_sequence(
            cr, uid, ids, context=context)
        for invoice in self.browse(cr, uid, ids, context=context):
            sequence_id = invoice_id__sequence_id[invoice.id]
            sequence = False
            if sequence_id:
                sequence = sequence_obj.browse(
                    cr, uid, [sequence_id], context)[0]
            fname = ""
            fname += (invoice.company_emitter_id.partner_id and (
                'vat_split' in invoice.company_emitter_id.partner_id._columns \
                and invoice.company_emitter_id.partner_id.vat_split or \
                invoice.company_emitter_id.partner_id.vat) or '')
            fname += '_'
            number_work = invoice.number or invoice.internal_number
            try:
                context.update({'number_work': int(number_work) or False})
                fname += sequence and sequence.approval_id and sequence.\
                approval_id.serie or '' 
                fname += '_'
            except:
                pass
            fname += number_work or ''
            res[invoice.id] = fname
        return res

    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'no_certificado': False,
            'certificado': False,
            'sello': False,
            'cadena_original': False,
            'date_invoice_cancel': False,
        })
        return super(account_invoice, self).action_cancel_draft(cr, uid, ids, args)

    def action_date_assign(self, cr, uid, ids, *args):
        context = {}
        currency_mxn_ids = self.pool.get('res.currency').search(
            cr, uid, [('name', '=', 'MXN')], limit=1, context=context)
        currency_mxn_id = currency_mxn_ids and currency_mxn_ids[0] or False
        if not currency_mxn_id:
            raise osv.except_osv(_('Error !'), _('No hay moneda MXN.'))
        for id in ids:
            invoice = self.browse(cr, uid, [id])[0]
            date_format = invoice.invoice_datetime or False
            context['date'] = date_format
            invoice = self.browse(cr, uid, [id], context)[0]
            rate = self.pool.get('res.currency').compute(
                cr, uid, invoice.currency_id.id, currency_mxn_id, 1,)
            self.write(cr, uid, [id], {'rate': rate})
        return super(account_invoice, self).action_date_assign(cr, uid, ids, args)

    def _get_cfd_xml_invoice(self, cr, uid, ids, field_name=None, arg=False, context=None):
        if context is None:
            context = {}
        res = {}
        attachment_obj = self.pool.get('ir.attachment')
        for invoice in self.browse(cr, uid, ids, context=context):
            attachment_xml_id = attachment_obj.search(cr, uid, [
                ('name', '=', invoice.fname_invoice+'.xml'),
                ('datas_fname', '=', invoice.fname_invoice+'.xml'),
                ('res_model', '=', 'account.invoice'),
                ('res_id', '=', invoice.id),
            ], limit=1)
            res[invoice.id] = attachment_xml_id and attachment_xml_id[
                0] or False
        return res

    _columns = {
        # Extract date_invoice from original, but add datetime
        #'date_invoice': fields.datetime('Date Invoiced', states={'open':[('readonly',True)],'close':[('readonly',True)]}, help="Keep empty to use the current date"),
        #'invoice_sequence_id': fields.function(_get_invoice_sequence, method=True, type='many2one', relation='ir.sequence', string='Invoice Sequence', store=True),
        #'certificate_id': fields.function(_get_invoice_certificate, method=True, type='many2one', relation='res.company.facturae.certificate', string='Invoice Certificate', store=True),
        'fname_invoice':  fields.function(_get_fname_invoice, method=True,
            type='char', size=26, string='File Name Invoice',
            help='Name used for the XML of electronic invoice'),
        #'amount_to_text':  fields.function(_get_amount_to_text, method=True, type='char', size=256, string='Amount to Text', store=True),
        'no_certificado': fields.char('No. Certificate', size=64,
            help='Number of serie of certificate used for the invoice'),
        'certificado': fields.text('Certificate', size=64,
            help='Certificate used in the invoice'),
        'sello': fields.text('Stamp', size=512, help='Digital Stamp'),
        'cadena_original': fields.text('String Original', size=512,
            help='Data stream with the information contained in the electronic \
            invoice'),
        'date_invoice_cancel': fields.datetime('Date Invoice Cancelled',
            readonly=True, help='If the invoice is cancelled, save the date \
            when was cancel'),
        'cfd_xml_id': fields.function(_get_cfd_xml_invoice, method=True,
            type='many2one', relation='ir.attachment', string='XML',
            help='Attachment that generated this invoice'),
        'rate': fields.float('Type of Change', readonly=True,
            help='Rate used in the date of invoice'),
        'cfdi_cbb': fields.binary('CFD-I CBB'),
        'cfdi_sello': fields.text('CFD-I Sello', help='Sign assigned by the SAT'),
        'cfdi_no_certificado': fields.char('CFD-I Certificado', size=32,
                                           help='Serial Number of the Certificate'),
        'cfdi_cadena_original': fields.text('CFD-I Cadena Original',
                                            help='Original String used in the electronic invoice'),
        'cfdi_fecha_timbrado': fields.datetime('CFD-I Fecha Timbrado',
                                               help='Date when is stamped the electronic invoice'),
        'cfdi_fecha_cancelacion': fields.datetime('CFD-I Fecha Cancelacion',
                                                  help='If the invoice is cancel, this field saved the date when is cancel'),
        'cfdi_folio_fiscal': fields.char('CFD-I Folio Fiscal', size=64,
                                         help='Folio used in the electronic invoice'),
        'pac_id': fields.many2one('params.pac', 'Pac', help='Pac used in singned of the invoice'),
    }

    _defaults = {
        #'date_invoice': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    """
    TODO: reset to draft considerated to delete these fields?
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'cfdi_cbb': False,
            'cfdi_sello':False,
            'cfdi_no_certificado':False,
            'cfdi_cadena_original':False,
            'cfdi_fecha_timbrado': False,
            'cfdi_folio_fiscal': False,
            'cfdi_fecha_cancelacion': False,
        })
        return super(account_invoice, self).action_cancel_draft(cr, uid, ids, args)
    """
    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'invoice_sequence_id': False,
            'no_certificado': False,
            'certificado': False,
            'sello': False,
            'cadena_original': False,
            'cfdi_sello': False,
            'cfdi_no_certificado': False,
            'cfdi_cadena_original': False,
            'cfdi_fecha_timbrado': False,
            'cfdi_folio_fiscal': False,
            'cfdi_fecha_cancelacion': False,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

    def binary2file(self, cr, uid, ids, binary_data, file_prefix="", file_suffix=""):
        """
        @param binary_data : Field binary with the information of certificate
                of the company
        @param file_prefix : Name to be used for create the file with the
                information of certificate
        @file_suffix : Sufix to be used for the file that create in this function
        """
        (fileno, fname) = tempfile.mkstemp(file_suffix, file_prefix)
        f = open(fname, 'wb')
        f.write(base64.decodestring(binary_data))
        f.close()
        os.close(fileno)
        return fname

    def _get_file_globals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        id = ids and ids[0] or False
        file_globals = {}
        if id:
            invoice = self.browse(cr, uid, id, context=context)
            # certificate_id = invoice.company_id.certificate_id
            context.update({'date_work': invoice.date_invoice_tz})
            certificate_id = self.pool.get('res.company')._get_current_certificate(
                cr, uid, [invoice.company_emitter_id.id],
                context=context)[invoice.company_emitter_id.id]
            certificate_id = certificate_id and self.pool.get(
                'res.company.facturae.certificate').browse(
                cr, uid, [certificate_id], context=context)[0] or False

            if certificate_id:
                if not certificate_id.certificate_file_pem:
                    # generate certificate_id.certificate_file_pem, a partir
                    # del certificate_id.certificate_file
                    pass
                fname_cer_pem = False
                try:
                    fname_cer_pem = self.binary2file(cr, uid, ids,
                        certificate_id.certificate_file_pem, 'openerp_' + (
                        certificate_id.serial_number or '') + '__certificate__',
                        '.cer.pem')
                except:
                    raise osv.except_osv(_('Error !'), _(
                        'Not captured a CERTIFICATE file in format PEM, in \
                        the company!'))
                file_globals['fname_cer'] = fname_cer_pem

                fname_key_pem = False
                try:
                    fname_key_pem = self.binary2file(cr, uid, ids,
                        certificate_id.certificate_key_file_pem, 'openerp_' + (
                        certificate_id.serial_number or '') + '__certificate__',
                        '.key.pem')
                except:
                    raise osv.except_osv(_('Error !'), _(
                        'Not captured a KEY file in format PEM, in the company!'))
                file_globals['fname_key'] = fname_key_pem

                fname_cer_no_pem = False
                try:
                    fname_cer_no_pem = self.binary2file(cr, uid, ids,
                        certificate_id.certificate_file, 'openerp_' + (
                        certificate_id.serial_number or '') + '__certificate__',
                        '.cer')
                except:
                    pass
                file_globals['fname_cer_no_pem'] = fname_cer_no_pem

                fname_key_no_pem = False
                try:
                    fname_key_no_pem = self.binary2file(cr, uid, ids,
                        certificate_id.certificate_key_file, 'openerp_' + (
                        certificate_id.serial_number or '') + '__certificate__',
                        '.key')
                except:
                    pass
                file_globals['fname_key_no_pem'] = fname_key_no_pem

                file_globals['password'] = certificate_id.certificate_password

                if certificate_id.fname_xslt:
                    if (certificate_id.fname_xslt[0] == os.sep or \
                        certificate_id.fname_xslt[1] == ':'):
                        file_globals['fname_xslt'] = certificate_id.fname_xslt
                    else:
                        file_globals['fname_xslt'] = os.path.join(
                            tools.config["root_path"], certificate_id.fname_xslt)
                else:
                    # Search char "," for addons_path, now is multi-path
                    all_paths = tools.config["addons_path"].split(",")
                    for my_path in all_paths:
                        if os.path.isdir(os.path.join(my_path,
                            'l10n_mx_facturae_base', 'SAT')):
                            # If dir is in path, save it on real_path
                            file_globals['fname_xslt'] = my_path and os.path.join(
                                my_path, 'l10n_mx_facturae_base', 'SAT',
                                'cadenaoriginal_2_0_l.xslt') or ''
                            break
                if not file_globals.get('fname_xslt', False):
                    raise osv.except_osv(_('Warning !'), _(
                        'Not defined fname_xslt. !'))

                if not os.path.isfile(file_globals.get('fname_xslt', ' ')):
                    raise osv.except_osv(_('Warning !'), _(
                        'No exist file [%s]. !') % (file_globals.get('fname_xslt', ' ')))

                file_globals['serial_number'] = certificate_id.serial_number
            else:
                raise osv.except_osv(_('Warning !'), _(
                    'Check date of invoice and the validity of certificate, & that the register of the certificate is active.\n%s!') % (msg2))
        
        invoice_datetime = self.browse(cr, uid, ids)[0].invoice_datetime
        ir_seq_app_obj = self.pool.get('ir.sequence.approval')
        invoice = self.browse(cr, uid, ids[0], context=context)
        sequence_app_id = ir_seq_app_obj.search(cr, uid, [(
            'sequence_id', '=', invoice.invoice_sequence_id.id)], context=context)
        if sequence_app_id:
            type_inv = ir_seq_app_obj.browse(
                cr, uid, sequence_app_id[0], context=context).type
        if invoice_datetime < '2012-07-01 00:00:00':
            return file_globals
        all_paths = tools.config["addons_path"].split(",")
        for my_path in all_paths:
            if os.path.isdir(os.path.join(my_path, 'l10n_mx_facturae_base', 'SAT')):
                # If dir is in path, save it on real_path
                file_globals['fname_xslt'] = my_path and os.path.join(
                    my_path, 'l10n_mx_facturae_base', 'SAT','cadenaoriginal_3_2',
                    'cadenaoriginal_3_2_l.xslt') or ''
        return file_globals

    def _get_facturae_invoice_txt_data(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        facturae_datas = self._get_facturae_invoice_dict_data(
            cr, uid, ids, context=context)
        facturae_data_txt_lists = []
        folio_data = self._get_folio(cr, uid, ids, context=context)
        facturae_type_dict = {'out_invoice': 'I', 'out_refund': 'E',
                            'in_invoice': False, 'in_refund': False}
        fechas = []
        for facturae_data in facturae_datas:
            invoice_comprobante_data = facturae_data['Comprobante']
            fechas.append(invoice_comprobante_data['fecha'])
            if facturae_data['state'] in ['open', 'paid']:
                facturae_state = 1
            elif facturae_data['state'] in ['cancel']:
                facturae_state = 0
            else:
                continue
            facturae_type = facturae_type_dict[facturae_data['type']]
            rate = facturae_data['rate']

            if not facturae_type:
                continue
            # if not invoice_comprobante_data['Receptor']['rfc']:
                # raise osv.except_osv('Warning !', 'No se tiene definido el
                # RFC de la factura [%s].\n%s
                # !'%(facturae_data['Comprobante']['folio'], msg2))

            invoice = self.browse(cr, uid, [facturae_data[
                                  'invoice_id']], context=context)[0]
            pedimento_numeros = ''
            pedimento_fechas = ''
            pedimento_aduanas = ''
            if 'tracking_id' in line._columns:
                pedimento_numeros = []
                pedimento_fechas = []
                pedimento_aduanas = []
                for line in invoice.invoice_line:
                    import_id = line.tracking_id and line.tracking_id.import_id or False
                    if import_id:
                        pedimento_numeros.append(
                            import_id.name or '')
                        pedimento_fechas.append(
                            import_id.date or '')
                        pedimento_aduanas.append(
                            import_id.customs or '')
                pedimento_numeros = ','.join(map(
                    lambda x: str(x) or '', pedimento_numeros))
                pedimento_fechas = ','.join(map(
                    lambda x: str(x) or '', pedimento_fechas))
                pedimento_aduanas = ','.join(map(
                    lambda x: str(x) or '', pedimento_aduanas))

            facturae_data_txt_list = [
                invoice_comprobante_data['Receptor']['rfc'] or '',
                invoice_comprobante_data.get('serie', False) or '',
                invoice_comprobante_data['folio'] or '',
                str(invoice_comprobante_data['anoAprobacion']) + str(
                    invoice_comprobante_data['noAprobacion']),
                time.strftime('%d/%m/%Y %H:%M:%S', time.strptime(facturae_data[
                              'date_invoice_tz'], '%Y-%m-%d %H:%M:%S')),  # invoice_comprobante_data['fecha'].replace('T', ' '),
                "%.2f" % (round(float(invoice_comprobante_data[
                'total'] or 0.0) * rate, 2)),
                "%.2f" % (round(float(invoice_comprobante_data['Impuestos'][
                'totalImpuestosTrasladados'] or 0.0) * rate, 2)),
                facturae_state,
                facturae_type,
                pedimento_numeros,
                pedimento_fechas,
                pedimento_aduanas,
            ]
            facturae_data_txt_lists.append(facturae_data_txt_list)

        fecha_promedio = time.strftime('%Y-%m-%d')
        if fechas:
            fecha_promedio = fechas[int(len(fechas)/2)-1]

        cad = ""
        for facturae_data_txt in facturae_data_txt_lists:
            cad += '|'
            cad += '|'.join(map(lambda x: str(x) or '', facturae_data_txt))
            cad += '|'
            cad += '\r\n'

        fname = "1" + invoice_comprobante_data['Emisor']['rfc'] + '-' + time.strftime(
            '%m%Y', time.strptime(fecha_promedio, '%Y-%m-%dT%H:%M:%S')) + '.txt'
        return cad, fname

    def _get_folio(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        folio_data = {}
        id = ids and ids[0] or False
        if id:
            invoice = self.browse(cr, uid, id, context=context)
            sequence_id = self._get_invoice_sequence(cr, uid, [id])[id]
            if sequence_id:
                # NO ES COMPATIBLE CON TINYERP approval_id =
                # sequence.approval_id.id
                number_work = invoice.number or invoice.internal_number
                if invoice.type in ['out_invoice', 'out_refund']:
                    try:
                        if number_work:
                            int(number_work)
                    except(ValueError):
                        raise osv.except_osv(_('Warning !'), _(
                            'The folio [%s] must be integer number, without letters')\
                                % (number_work))
                context.update({'number_work': number_work or False})
                approval_id = self.pool.get('ir.sequence')._get_current_approval(
                    cr, uid, [sequence_id], field_names=None, arg=False,
                    context=context)[sequence_id]
                approval = approval_id and self.pool.get(
                    'ir.sequence.approval').browse(cr, uid, [approval_id],
                    context=context)[0] or False
                if approval:
                    folio_data = {
                        'serie': approval.serie or '',
                        #'folio': '1',
                        'noAprobacion': approval.approval_number or '',
                        'anoAprobacion': approval.approval_year or '',
                        'desde': approval.number_start or '',
                        'hasta': approval.number_end or '',
                        #'noCertificado': "30001000000100000800",
                    }
                else:
                    raise osv.except_osv(_('Warning !'), _(
                        "The sequence don't have data of electronic invoice\nIn the sequence_id [%d].\n %s !")\
                            % (sequence_id, msg2))
            else:
                raise osv.except_osv(_('Warning !'), _(
                    'Not found a sequence of configuration. %s !') % (msg2))
        return folio_data

    def _dict_iteritems_sort(self, data_dict):  # cr=False, uid=False, ids=[], context=None):
        """
        @param data_dict : Dictionary with data from invoice
        """
        key_order = [
            'Emisor',
            'Receptor',
            'Conceptos',
            'Impuestos',
        ]
        keys = data_dict.keys()
        key_item_sort = []
        for ko in key_order:
            if ko in keys:
                key_item_sort.append([ko, data_dict[ko]])
                keys.pop(keys.index(ko))
        if keys == ['rfc', 'nombre', 'RegimenFiscal', 'DomicilioFiscal', 'ExpedidoEn'] or keys == ['rfc', 'nombre', 'RegimenFiscal', 'ExpedidoEn', 'DomicilioFiscal']:
            keys = ['rfc', 'nombre', 'DomicilioFiscal', 'ExpedidoEn', 'RegimenFiscal']
        if keys ==['rfc', 'nombre', 'cfdi:RegimenFiscal', 'cfdi:DomicilioFiscal', 'cfdi:ExpedidoEn'] or keys == ['rfc', 'nombre', 'cfdi:RegimenFiscal', 'cfdi:ExpedidoEn', 'cfdi:DomicilioFiscal']:
            keys = ['rfc', 'nombre', 'cfdi:DomicilioFiscal', 'cfdi:ExpedidoEn', 'cfdi:RegimenFiscal']
        for key_too in keys:
            key_item_sort.append([key_too, data_dict[key_too]])
        return key_item_sort

    #~def dict2xml(self, data_dict, node=False, doc=False):
        #~"""
        #~@param data_dict : Dictionary of attributes for add in the XML 
                    #~that will be generated
        #~@param node : Node from XML where will be added data from the dictionary
        #~@param doc : Document XML generated, where will be working
        #~"""
        #~parent = False
        #~if node:
            #~parent = True
#~
        #~for element, attribute in self._dict_iteritems_sort(data_dict):
            #~if not parent:
                #~doc = minidom.Document()
            #~if isinstance(attribute, dict):
                #~if not parent:
                    #~node = doc.createElement(element)
                    #~self.dict2xml(attribute, node, doc)
                #~else:
                    #~child = doc.createElement(element)
                    #~self.dict2xml(attribute, child, doc)
                    #~node.appendChild(child)
            #~elif isinstance(attribute, list):
                #~child = doc.createElement(element)
                #~for attr in attribute:
                    #~if isinstance(attr, dict):
                        #~self.dict2xml(attr, child, doc)
                #~node.appendChild(child)
            #~else:
                #~if isinstance(attribute, str) or isinstance(attribute, unicode):
                    #~attribute = conv_ascii(attribute)
                #~else:
                        #~attribute = str(attribute)
                #~node.setAttribute(element, attribute)
                #~# print "attribute",unicode( attribute, 'UTF-8')
        #~if not parent:
            #~doc.appendChild(node)
        #~return doc

    def _get_facturae_invoice_xml_data(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data_xml=False
        fname_xml=False
        ir_seq_app_obj = self.pool.get('ir.sequence.approval')
        invoices = self.browse(cr, uid, ids)
        importe = 0.0
        tasa = 0.0
        impuesto=''
        facturae_version = '3.2'
        totalImpuestosTrasladados = 0.0
        for invoice in invoices:
            if invoice.type == 'out_invoice':
                tipoComprobante = 'ingreso'
            elif invoice.type == 'out_refund':
                tipoComprobante = 'egreso'
            else:
                raise osv.except_osv(_('Warning !'), _(
                    'Only can issue electronic invoice to customers.!'))
            invoice_data_parent = {}
            invoice_data = invoice_data_parent = {}
            invoice_data['Impuestos'] = {}
            invoice_data['Impuestos'].update({
                #'totalImpuestosTrasladados': "%.2f"%( invoice.amount_tax or 0.0),
            })
            invoice_data['Impuestos'].update({
                #'totalImpuestosRetenidos': "%.2f"%( invoice.amount_tax or 0.0 )
            })
            invoice_data_impuestos = invoice_data['Impuestos']
            invoice_data_impuestos['Traslados'] = []
            invoice_data_impuestos['Retenciones'] = []
            tax_names = []
            totalImpuestosTrasladados = 0
            totalImpuestosRetenidos = 0
            for line_tax_id in invoice.tax_line:
                tax_name = line_tax_id.name2
                tax_names.append(tax_name)
                line_tax_id_amount = abs(line_tax_id.amount or 0.0)
                if line_tax_id.amount >= 0:
                    impuesto_list = invoice_data_impuestos['Traslados']
                    impuesto_str = 'Traslado'
                    totalImpuestosTrasladados += line_tax_id_amount
                else:
                    impuesto_list = invoice_data_impuestos['Retenciones']
                    impuesto_list = invoice_data_impuestos.setdefault(
                        'Retenciones', [])
                    impuesto_str = 'Retencion'
                    totalImpuestosRetenidos += line_tax_id_amount
                impuesto_dict = {impuesto_str:
                                {
                                 'impuesto': self.string_to_xml_format(cr, uid, ids, tax_name),
                                 'importe': "%.2f" % (line_tax_id_amount),
                                 }
                                 }
                if line_tax_id.amount >= 0:
                    impuesto_dict[impuesto_str].update({
                            'tasa': "%.2f" % (abs(line_tax_id.tax_percent))})
                impuesto_list.append(impuesto_dict)

            invoice_data['Impuestos'].update({
                'totalImpuestosTrasladados': "%.2f" % (totalImpuestosTrasladados),
            })
            if totalImpuestosRetenidos:
                invoice_data['Impuestos'].update({
                    'totalImpuestosRetenidos': "%.2f" % (totalImpuestosRetenidos)
                })

            tax_requireds = ['IVA', 'IEPS']
            for tax_required in tax_requireds:
                if tax_required in tax_names:
                    continue
                invoice_data_impuestos['Traslados'].append({'Traslado': {
                    'impuesto': self.string_to_xml_format(cr, uid, ids, tax_required),
                    'tasa': "%.2f" % (0.0),
                    'importe': "%.2f" % (0.0),
                }})
            context.update(self._get_file_globals(cr, uid, ids, context=context))
            htz = int(self._get_time_zone(cr, uid, ids, context=context))
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            date_now = now and datetime.strptime(invoice.invoice_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=htz) or False
            date_now = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(str(date_now), '%Y-%m-%d %H:%M:%S')) or False
            context.update({'fecha': date_now or ''})
            noCertificado = self._get_noCertificado(cr, uid, ids, context['fname_cer'])
            cert_str = self._get_certificate_str(context['fname_cer'])
            cert_str = cert_str.replace('\n\r', '').replace('\r\n', '').replace('\n', '').replace('\r', '').replace(' ', '')
            rfc_emisor = invoice.company_emitter_id.address_invoice_parent_company_id._columns.has_key('vat_split') and \
                        invoice.company_emitter_id.address_invoice_parent_company_id.vat_split or invoice.company_emitter_id.address_invoice_parent_company_id.vat
            rfc_receptor = invoice.partner_id.commercial_partner_id._columns.has_key('vat_split') and invoice.partner_id.commercial_partner_id.vat_split or invoice.partner_id.commercial_partner_id.vat
            sequence_app_id = ir_seq_app_obj.search(cr, uid, [(
                'sequence_id', '=', invoice.invoice_sequence_id.id)], context=context)
            if sequence_app_id:
                type_inv = ir_seq_app_obj.browse(cr, uid, sequence_app_id[0], context=context).type
            all_paths = tools.config["addons_path"].split(",")
            for my_path in all_paths:
                if os.path.isdir(os.path.join(my_path, 'l10n_mx_facturae_base', 'template')):
                    fname_jinja_tmpl = my_path and os.path.join(my_path, 'l10n_mx_facturae_base', 'template', 'cfdi' + '.xml') or ''
            dictargs = {
                'o': invoice,
                'time': time,
                'noCertificado': noCertificado,
                'certificado': cert_str,
                'rfc_emisor': rfc_emisor,
                'rfc_receptor': rfc_receptor,
                'tipoComprobante': tipoComprobante,
                'data_impuestos': invoice_data_impuestos
                }
            invoice_number = "sn"
            (fileno_xml, fname_xml) = tempfile.mkstemp('.xml', 'openerp_' + (invoice_number or '') + '__facturae__')
            with open(fname_jinja_tmpl, 'r') as f_jinja_tmpl:
                jinja_tmpl_str = f_jinja_tmpl.read().encode('utf-8')
                tmpl = jinja2.Template( jinja_tmpl_str )
                with open(fname_xml, 'w') as new_xml:
                    new_xml.write( tmpl.render(**dictargs) )
            with open(fname_xml,'rb') as b:
                jinja2_xml = b.read().encode('UTF-8')
            b.close()
            (fileno_sign, fname_sign) = tempfile.mkstemp('.txt', 'openerp_' + '__facturae_txt_md5__')
            os.close(fileno_sign)
            try:
                self.validate_scheme_facturae_xml(cr, uid, ids, [jinja2_xml], facturae_version)
            except Exception, e:
                raise orm.except_orm(_('Warning'), _('Parse Error XML: %s.') % (tools.ustr(e)))
            doc_xml = xml.dom.minidom.parseString(jinja2_xml)
            (fileno_xml, fname_xml) = tempfile.mkstemp('.xml', 'openerp_' + (invoice_number or '') + '__facturae__')
            fname_txt = fname_xml + '.txt'
            f = open(fname_xml, 'w')
            doc_xml_full = doc_xml.toxml().encode('ascii', 'xmlcharrefreplace')
            doc_xml = xml.dom.minidom.parseString(doc_xml_full)
            f = codecs.open(fname_xml,'w','utf-8')
            doc_xml.writexml(f, indent='    ', addindent='    ', newl='\r\n', encoding='UTF-8')
            f.close()
            os.close(fileno_xml)
            context.update({
                'fname_xml': fname_xml,
                'fname_txt': fname_txt,
                'fname_sign': fname_sign,
            })
            context.update(self._get_file_globals(cr, uid, ids, context=context))
            fname_txt, txt_str = self._xml2cad_orig(cr=False, uid=False, ids=False, context=context)
            if not txt_str:
                raise osv.except_osv(_('Error en Cadena original!'), _(
                    "Can't get the string original of the voucher.\nCkeck your configuration.\n%s" % (msg2)))
            context.update({'fecha': invoice.date_invoice_tz and time.strftime('%Y-%m-%dT%H:%M:%S', 
                    time.strptime(invoice.date_invoice_tz, '%Y-%m-%d %H:%M:%S')) or ''})
            sign_str = self._get_sello(cr=False, uid=False, ids=False, context=context)
            if not sign_str:
                raise osv.except_osv(_('Error in Stamp !'), _(
                    "Can't generate the stamp of the voucher.\nCkeck your configuration.\ns%s") % (msg2))
            nodeComprobante = doc_xml.getElementsByTagName("cfdi:Comprobante")[0]
            nodeComprobante.setAttribute("sello", sign_str)
            noCertificado = self._get_noCertificado(cr, uid, ids, context['fname_cer'])
            if not noCertificado:
                raise osv.except_osv(_('Error in No. Certificate !'), _(
                    "Can't get the Certificate Number of the voucher.\nCkeck your configuration.\n%s") % (msg2))
            nodeComprobante.setAttribute("noCertificado", noCertificado)
            cert_str = self._get_certificate_str(context['fname_cer'])
            if not cert_str:
                raise osv.except_osv(_('Error in Certificate!'), _(
                    "Can't generate the Certificate of the voucher.\nCkeck your configuration.\n%s") % (msg2))
            cert_str = cert_str.replace(' ', '').replace('\n', '')
            nodeComprobante.setAttribute("certificado", cert_str)
            data_dict = {'cfdi_cadena_original':txt_str,
                        'cfdi_no_certificado':noCertificado,
                        'sello':sign_str,
                        'certificado':cert_str,
            }
            self.write_cfd_data(cr, uid, ids, data_dict, context=context)
            data_xml = doc_xml.toxml('UTF-8')
            data_xml = codecs.BOM_UTF8 + data_xml
            fname_xml = str(invoice.id) + '_XML_V3_2.xml'
            data_xml = data_xml.replace('<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="UTF-8"?>\n')
        return fname_xml, data_xml

    def validate_scheme_facturae_xml(self, cr, uid, ids, datas_xmls=[], facturae_version = None, facturae_type="cfdv", scheme_type='xsd'):
    #TODO: bzr add to file fname_schema
        if not datas_xmls:
            datas_xmls = []
        certificate_lib = self.pool.get('facturae.certificate.library')
        for data_xml in datas_xmls:
            (fileno_data_xml, fname_data_xml) = tempfile.mkstemp('.xml', 'openerp_' + (False or '') + '__facturae__' )
            f = open(fname_data_xml, 'wb')
            data_xml = data_xml.replace("&amp;", "Y")#Replace temp for process with xmlstartle
            f.write( data_xml )
            f.close()
            os.close(fileno_data_xml)
            all_paths = tools.config["addons_path"].split(",")
            for my_path in all_paths:
                if os.path.isdir(os.path.join(my_path, 'l10n_mx_facturae_base', 'SAT')):
                    # If dir is in path, save it on real_path
                    fname_scheme = my_path and os.path.join(my_path, 'l10n_mx_facturae_base', 'SAT', facturae_type + facturae_version +  '.' + scheme_type) or ''
                    #fname_scheme = os.path.join(tools.config["addons_path"], u'l10n_mx_facturae_base', u'SAT', facturae_type + facturae_version +  '.' + scheme_type )
                    fname_out = certificate_lib.b64str_to_tempfile(cr, uid, ids, base64.encodestring(''), file_suffix='.txt', file_prefix='openerp__' + (False or '') + '__schema_validation_result__' )
                    result = certificate_lib.check_xml_scheme(cr, uid, ids, fname_data_xml, fname_scheme, fname_out)
                    if result: #Valida el xml mediante el archivo xsd
                        raise osv.except_osv('Error al validar la estructura del xml!', 'Validación de XML versión %s:\n%s'%(facturae_version, result))
        return True

    def write_cfd_data(self, cr, uid, ids, cfd_datas, context=None):
        """
        @param cfd_datas : Dictionary with data that is used in facturae CFD and CFDI
        """
        if context is None:
            context = {}
        if not cfd_datas:
            cfd_datas = {}
        comprobante = self._get_type_sequence(cr, uid, ids, context=context)
        id = ids[0]
        if True:
            data = {}
            cfd_data = cfd_datas
            noCertificado = cfd_data.get(
                comprobante, {}).get('noCertificado', '')
            certificado = cfd_data.get(
                comprobante, {}).get('certificado', '')
            sello = cfd_data.get(comprobante, {}).get('sello', '')
            cadena_original = cfd_data.get('cadena_original', '')
            data = {
                'no_certificado': noCertificado,
                'certificado': certificado,
                'sello': sello,
                'cadena_original': cadena_original,
            }
            self.write(cr, uid, [id], data, context=context)
        return True

    def _get_noCertificado(self, cr, uid, ids, fname_cer, pem=True):
        """
        @param fname_cer : Path more name of file created whit information 
                    of certificate with suffix .pem
        @param pem : Boolean that indicate if file is .pem
        """
        certificate_lib = self.pool.get('facturae.certificate.library')
        fname_serial = certificate_lib.b64str_to_tempfile(cr, uid, ids, base64.encodestring(
            ''), file_suffix='.txt', file_prefix='openerp__' + (False or '') + \
            '__serial__')
        result = certificate_lib._get_param_serial(cr, uid, ids,
            fname_cer, fname_out=fname_serial, type='PEM')
        return result

    def _get_sello(self, cr=False, uid=False, ids=False, context=None):
        if context is None:
            context = {}
        # TODO: Put encrypt date dynamic
        fecha = context['fecha']
        year = float(time.strftime('%Y', time.strptime(
            fecha, '%Y-%m-%dT%H:%M:%S')))
        if year >= 2011:
            encrypt = "sha1"
        if year <= 2010:
            encrypt = "md5"
        certificate_lib = self.pool.get('facturae.certificate.library')
        fname_sign = certificate_lib.b64str_to_tempfile(cr, uid, ids, base64.encodestring(
            ''), file_suffix='.txt', file_prefix='openerp__' + (False or '') + \
            '__sign__')
        result = certificate_lib._sign(cr, uid, ids, fname=context['fname_xml'],
            fname_xslt=context['fname_xslt'], fname_key=context['fname_key'],
            fname_out=fname_sign, encrypt=encrypt, type_key='PEM')
        return result

    def _xml2cad_orig(self, cr=False, uid=False, ids=False, context=None):
        if context is None:
            context = {}
        certificate_lib = self.pool.get('facturae.certificate.library')
        fname_tmp = certificate_lib.b64str_to_tempfile(cr, uid, ids, base64.encodestring(
            ''), file_suffix='.txt', file_prefix='openerp__' + (False or '') + \
            '__cadorig__')
        cad_orig = certificate_lib._transform_xml(cr, uid, ids, fname_xml=context['fname_xml'],
            fname_xslt=context['fname_xslt'], fname_out=fname_tmp)
        return fname_tmp, cad_orig

# TODO: agregar esta funcionalidad con openssl
    def _get_certificate_str(self, fname_cer_pem=""):
        """
        @param fname_cer_pem : Path and name the file .pem
        """
        fcer = open(fname_cer_pem, "r")
        lines = fcer.readlines()
        fcer.close()
        cer_str = ""
        loading = False
        for line in lines:
            if 'END CERTIFICATE' in line:
                loading = False
            if loading:
                cer_str += line
            if 'BEGIN CERTIFICATE' in line:
                loading = True
        return cer_str
# TODO: agregar esta funcionalidad con openssl

    def _get_md5_cad_orig(self, cadorig_str, fname_cadorig_digest):
        """
        @param cadorig_str :
        @fname cadorig_digest :
        """
        cadorig_digest = hashlib.md5(cadorig_str).hexdigest()
        open(fname_cadorig_digest, "w").write(cadorig_digest)
        return cadorig_digest, fname_cadorig_digest

    def _get_facturae_invoice_dict_data(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoices = self.browse(cr, uid, ids, context=context)
        invoice_tax_obj = self.pool.get("account.invoice.tax")
        invoice_datas = []
        invoice_data_parents = []
        for invoice in invoices:
            invoice_data_parent = {}
            if invoice.type == 'out_invoice':
                tipoComprobante = 'ingreso'
            elif invoice.type == 'out_refund':
                tipoComprobante = 'egreso'
            else:
                raise osv.except_osv(_('Warning !'), _(
                    'Only can issue electronic invoice to customers.!'))
            # Inicia seccion: Comprobante
            invoice_data_parent['cfdi:Comprobante'] = {}
            # default data
            invoice_data_parent['cfdi:Comprobante'].update({
                'xmlns:cfdi': "http://www.sat.gob.mx/cfd/3",
                'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
                'xsi:schemaLocation': "http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv32.xsd",
                'version': "3.2",
            })
            number_work = invoice.number or invoice.internal_number
            invoice_data_parent['cfdi:Comprobante'].update({
                'folio': number_work,
                'fecha': invoice.date_invoice_tz and
                # time.strftime('%d/%m/%y',
                # time.strptime(invoice.date_invoice, '%Y-%m-%d'))
                time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(
                invoice.date_invoice_tz, '%Y-%m-%d %H:%M:%S'))
                or '',
                'tipoDeComprobante': tipoComprobante,
                'formaDePago': u'Pago en una sola exhibición',
                'noCertificado': '@',
                'sello': '@',
                'certificado': '@',
                'subTotal': "%.2f" % (invoice.amount_untaxed or 0.0),
                'descuento': "0",  # Add field general
                'total': "%.2f" % (invoice.amount_total or 0.0),
            })
            folio_data = self._get_folio(
                cr, uid, [invoice.id], context=context)
            serie = folio_data.get('serie', False)
            if serie:
                invoice_data_parent['cfdi:Comprobante'].update({
                    'serie': serie,
                })
            # Termina seccion: Comprobante
            # Inicia seccion: Emisor
            partner_obj = self.pool.get('res.partner')
            address_invoice = invoice.address_issued_id or False
            address_invoice_parent = invoice.company_emitter_id and \
            invoice.company_emitter_id.address_invoice_parent_company_id or False

            if not address_invoice:
                raise osv.except_osv(_('Warning !'), _(
                    "Don't have defined the address issuing!"))

            if not address_invoice_parent:
                raise osv.except_osv(_('Warning !'), _(
                    "Don't have defined an address of invoicing from the company!"))

            if not address_invoice_parent.vat:
                raise osv.except_osv(_('Warning !'), _(
                    "Don't have defined RFC for the address of invoice to the company!"))

            invoice_data = invoice_data_parent['cfdi:Comprobante']
            invoice_data['cfdi:Emisor'] = {}
            invoice_data['cfdi:Emisor'].update({

                'rfc': (('vat_split' in address_invoice_parent._columns and \
                address_invoice_parent.vat_split or address_invoice_parent.vat) \
                or '').replace('-', ' ').replace(' ', ''),
                'nombre': address_invoice_parent.name or '',
                # Obtener domicilio dinamicamente
                # virtual_invoice.append( (invoice.company_id and
                # invoice.company_id.partner_id and
                # invoice.company_id.partner_id.vat or '').replac

                'cfdi:DomicilioFiscal': {
                    'calle': address_invoice_parent.street and \
                        address_invoice_parent.street.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or '',
                    'noExterior': address_invoice_parent.l10n_mx_street3 and \
                        address_invoice_parent.l10n_mx_street3.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').\
                        replace('\r', ' ') or 'N/A',  # "Numero Exterior"
                    'noInterior': address_invoice_parent.l10n_mx_street4 and \
                        address_invoice_parent.l10n_mx_street4.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').\
                        replace('\r', ' ') or 'N/A',  # "Numero Interior"
                    'colonia':  address_invoice_parent.street2 and \
                        address_invoice_parent.street2.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or False,
                    'localidad': address_invoice_parent.l10n_mx_city2 and \
                        address_invoice_parent.l10n_mx_city2.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').\
                        replace('\r', ' ') or False,
                    'municipio': address_invoice_parent.city and \
                        address_invoice_parent.city.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or '',
                    'estado': address_invoice_parent.state_id and \
                        address_invoice_parent.state_id.name and \
                        address_invoice_parent.state_id.name.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ') or '',
                    'pais': address_invoice_parent.country_id and \
                        address_invoice_parent.country_id.name and \
                        address_invoice_parent.country_id.name.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ')or '',
                    'codigoPostal': address_invoice_parent.zip and \
                        address_invoice_parent.zip.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ').replace(' ', '') or '',
                },
                'cfdi:ExpedidoEn': {
                    'calle': address_invoice.street and address_invoice.\
                        street.replace('\n\r', ' ').replace('\r\n', ' ').\
                        replace('\n', ' ').replace('\r', ' ') or '',
                    'noExterior': address_invoice.l10n_mx_street3 and \
                        address_invoice.l10n_mx_street3.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').\
                        replace('\r', ' ') or 'N/A',  # "Numero Exterior"
                    'noInterior': address_invoice.l10n_mx_street4 and \
                        address_invoice.l10n_mx_street4.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or 'N/A',  # "Numero Interior"
                    'colonia':  address_invoice.street2 and address_invoice.\
                        street2.replace('\n\r', ' ').replace('\r\n', ' ').\
                        replace('\n', ' ').replace('\r', ' ') or False,
                    'localidad': address_invoice.l10n_mx_city2 and \
                        address_invoice.l10n_mx_city2.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or False,
                    'municipio': address_invoice.city and address_invoice.\
                        city.replace('\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ') or '',
                    'estado': address_invoice.state_id and address_invoice.\
                        state_id.name and address_invoice.state_id.name.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').\
                        replace('\r', ' ') or '',
                    'pais': address_invoice.country_id and address_invoice.\
                        country_id.name and address_invoice.country_id.name.\
                        replace('\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ')or '',
                    'codigoPostal': address_invoice.zip and address_invoice.\
                        zip.replace('\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ').replace(' ', '') or '',
                },
            })
            if invoice_data['cfdi:Emisor']['cfdi:DomicilioFiscal'].get('colonia') == False:
                invoice_data['cfdi:Emisor']['cfdi:DomicilioFiscal'].pop('colonia')
            if invoice_data['cfdi:Emisor']['cfdi:ExpedidoEn'].get('colonia') == False:
                invoice_data['cfdi:Emisor']['cfdi:ExpedidoEn'].pop('colonia')
            if invoice_data['cfdi:Emisor']['cfdi:DomicilioFiscal'].get('localidad') == False:
                invoice_data['cfdi:Emisor']['cfdi:DomicilioFiscal'].pop('localidad')
            if invoice_data['cfdi:Emisor']['cfdi:ExpedidoEn'].get('localidad') == False:
                invoice_data['cfdi:Emisor']['cfdi:ExpedidoEn'].pop('localidad')
            # Termina seccion: Emisor
            # Inicia seccion: Receptor
            parent_id = invoice.partner_id.commercial_partner_id.id
            parent_obj = partner_obj.browse(cr, uid, parent_id, context=context)
            if not parent_obj.vat:
                raise osv.except_osv(_('Warning !'), _(
                    "Don't have defined RFC of the partner[%s].\n%s !") % (
                    parent_obj.name, msg2))
            if parent_obj._columns.has_key('vat_split') and\
                parent_obj.vat[0:2] <> 'MX':
                rfc = 'XAXX010101000'
            else:
                rfc = ((parent_obj._columns.has_key('vat_split')\
                    and parent_obj.vat_split or parent_obj.vat)\
                    or '').replace('-', ' ').replace(' ','')
            address_invoice = partner_obj.browse(cr, uid, \
                invoice.partner_id.id, context=context)
            invoice_data['cfdi:Receptor'] = {}
            invoice_data['cfdi:Receptor'].update({
                'rfc': rfc,
                'nombre': (parent_obj.name or ''),
                'cfdi:Domicilio': {
                    'calle': address_invoice.street and address_invoice.\
                        street.replace('\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ') or '',
                    'noExterior': address_invoice.l10n_mx_street3 and \
                        address_invoice.l10n_mx_street3.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or 'N/A',  # "Numero Exterior"
                    'noInterior': address_invoice.l10n_mx_street4 and \
                        address_invoice.l10n_mx_street4.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or 'N/A',  # "Numero Interior"
                    'colonia':  address_invoice.street2 and address_invoice.\
                        street2.replace('\n\r', ' ').replace('\r\n', ' ').\
                        replace('\n', ' ').replace('\r', ' ') or False,
                    'localidad': address_invoice.l10n_mx_city2 and \
                        address_invoice.l10n_mx_city2.replace('\n\r', ' ').\
                        replace('\r\n', ' ').replace('\n', ' ').replace(
                        '\r', ' ') or False,
                    'municipio': address_invoice.city and address_invoice.\
                        city.replace('\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ') or '',
                    'estado': address_invoice.state_id and address_invoice.\
                        state_id.name and address_invoice.state_id.name.replace(
                        '\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').\
                        replace('\r', ' ') or '',
                    'pais': address_invoice.country_id and address_invoice.\
                        country_id.name and address_invoice.country_id.name.\
                        replace('\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ')or '',
                    'codigoPostal': address_invoice.zip and address_invoice.\
                        zip.replace('\n\r', ' ').replace('\r\n', ' ').replace(
                        '\n', ' ').replace('\r', ' ') or '',
                },
            })
            if invoice_data['cfdi:Receptor']['cfdi:Domicilio'].get('colonia') == False:
                invoice_data['cfdi:Receptor']['cfdi:Domicilio'].pop('colonia')
            if invoice_data['cfdi:Receptor']['cfdi:Domicilio'].get('localidad') == False:
                invoice_data['cfdi:Receptor']['cfdi:Domicilio'].pop('localidad')
            # Termina seccion: Receptor
            # Inicia seccion: Conceptos
            invoice_data['cfdi:Conceptos'] = []
            for line in invoice.invoice_line:
                # price_type = invoice._columns.has_key('price_type') and invoice.price_type or 'tax_excluded'
                # if price_type == 'tax_included':
# price_unit = line.price_subtotal/line.quantity#Agrega compatibilidad con
# modulo TaxIncluded
                price_unit = line.quantity != 0 and line.price_subtotal / \
                    line.quantity or 0.0
                concepto = {
                    'cantidad': "%.2f" % (line.quantity or 0.0),
                    'descripcion': line.name or '',
                    'valorUnitario': "%.2f" % (price_unit or 0.0),
                    'importe': "%.2f" % (line.price_subtotal or 0.0),  # round(line.price_unit *(1-(line.discount/100)),2) or 0.00),#Calc: iva, disc, qty
                    # Falta agregar discount
                }
                unidad = line.uos_id and line.uos_id.name or ''
                if unidad:
                    concepto.update({'unidad': unidad})
                product_code = line.product_id and line.product_id.default_code or ''
                if product_code:
                    concepto.update({'noIdentificacion': product_code})
                invoice_data['cfdi:Conceptos'].append({'cfdi:Concepto': concepto})

                pedimento = None
                if 'tracking_id' in line._columns:
                    pedimento = line.tracking_id and line.tracking_id.import_id or False
                    if pedimento:
                        informacion_aduanera = {
                            'numero': pedimento.name or '',
                            'fecha': pedimento.date or '',
                            'aduana': pedimento.customs,
                        }
                        concepto.update({
                                        'InformacionAduanera': informacion_aduanera})
                # Termina seccion: Conceptos
            # Inicia seccion: impuestos
            invoice_data['cfdi:Impuestos'] = {}
            invoice_data['cfdi:Impuestos'].update({
                #'totalImpuestosTrasladados': "%.2f"%( invoice.amount_tax or 0.0),
            })
            invoice_data['cfdi:Impuestos'].update({
                #'totalImpuestosRetenidos': "%.2f"%( invoice.amount_tax or 0.0 )
            })

            invoice_data_impuestos = invoice_data['cfdi:Impuestos']
            invoice_data_impuestos['cfdi:Traslados'] = []
            # invoice_data_impuestos['Retenciones'] = []

            tax_names = []
            totalImpuestosTrasladados = 0
            totalImpuestosRetenidos = 0
            for line_tax_id in invoice.tax_line:
                tax_name = line_tax_id.name2
                tax_names.append(tax_name)
                line_tax_id_amount = abs(line_tax_id.amount or 0.0)
                if line_tax_id.amount >= 0:
                    impuesto_list = invoice_data_impuestos['cfdi:Traslados']
                    impuesto_str = 'cfdi:Traslado'
                    totalImpuestosTrasladados += line_tax_id_amount
                else:
                    # impuesto_list = invoice_data_impuestos['Retenciones']
                    impuesto_list = invoice_data_impuestos.setdefault(
                        'cfdi:Retenciones', [])
                    impuesto_str = 'cfdi:Retencion'
                    totalImpuestosRetenidos += line_tax_id_amount
                impuesto_dict = {impuesto_str:
                                {
                                 'impuesto': tax_name,
                                 'importe': "%.2f" % (line_tax_id_amount),
                                 }
                                 }
                if line_tax_id.amount >= 0:
                    impuesto_dict[impuesto_str].update({
                            'tasa': "%.2f" % (abs(line_tax_id.tax_percent))})
                impuesto_list.append(impuesto_dict)

            invoice_data['cfdi:Impuestos'].update({
                'totalImpuestosTrasladados': "%.2f" % (totalImpuestosTrasladados),
            })
            if totalImpuestosRetenidos:
                invoice_data['cfdi:Impuestos'].update({
                    'totalImpuestosRetenidos': "%.2f" % (totalImpuestosRetenidos)
                })

            tax_requireds = ['IVA', 'IEPS']
            for tax_required in tax_requireds:
                if tax_required in tax_names:
                    continue
                invoice_data_impuestos['cfdi:Traslados'].append({'cfdi:Traslado': {
                    'impuesto': tax_required,
                    'tasa': "%.2f" % (0.0),
                    'importe': "%.2f" % (0.0),
                }})
            # Termina seccion: impuestos
            invoice_data_parents.append(invoice_data_parent)
            invoice_data_parent['state'] = invoice.state
            invoice_data_parent['invoice_id'] = invoice.id
            invoice_data_parent['type'] = invoice.type
            invoice_data_parent['invoice_datetime'] = invoice.invoice_datetime
            invoice_data_parent['date_invoice_tz'] = invoice.date_invoice_tz
            invoice_data_parent['currency_id'] = invoice.currency_id.id

            date_ctx = {'date': invoice.date_invoice_tz and time.strftime(
                '%Y-%m-%d', time.strptime(invoice.date_invoice_tz,
                '%Y-%m-%d %H:%M:%S')) or False}
            currency = self.pool.get('res.currency').browse(
                cr, uid, [invoice.currency_id.id], context=date_ctx)[0]
            rate = currency.rate != 0 and 1.0/currency.rate or 0.0
            invoice_data_parent['rate'] = rate

        invoice_datetime = invoice_data_parents[0].get('invoice_datetime',
            {}) and datetime.strptime(invoice_data_parents[0].get(
            'invoice_datetime', {}), '%Y-%m-%d %H:%M:%S').strftime(
            '%Y-%m-%d') or False
        if not invoice_datetime:
            raise osv.except_osv(_('Date Invoice Empty'), _(
                "Can't generate a invoice without date, make sure that the state of invoice not is draft & the date of invoice not is empty"))
        if invoice_datetime < '2012-07-01':
            return invoice_data_parent
        else:
            invoice = self.browse(cr, uid, ids, context={
                                  'date': invoice_datetime})[0]
            city = invoice_data_parents and invoice_data_parents[0].get(
                'cfdi:Comprobante', {}).get('cfdi:Emisor', {}).get('cfdi:ExpedidoEn', {}).get(
                'municipio', {}) or False
            state = invoice_data_parents and invoice_data_parents[0].get(
                'cfdi:Comprobante', {}).get('cfdi:Emisor', {}).get('cfdi:ExpedidoEn', {}).get(
                'estado', {}) or False
            country = invoice_data_parents and invoice_data_parents[0].get(
                'cfdi:Comprobante', {}).get('cfdi:Emisor', {}).get('cfdi:ExpedidoEn', {}).get(
                'pais', {}) or False
            if city and state and country:
                address = city + ' ' + state + ', ' + country
            else:
                raise osv.except_osv(_('Address Incomplete!'), _(
                    'Ckeck that the address of company issuing of fiscal voucher is complete (City - State - Country)'))

            if not invoice.company_emitter_id.partner_id.regimen_fiscal_id.name:
                raise osv.except_osv(_('Missing Fiscal Regime!'), _(
                    'The Fiscal Regime of the company issuing of fiscal voucher is a data required'))

            invoice_data_parents[0]['cfdi:Comprobante'][
                'TipoCambio'] = invoice.rate or 1
            invoice_data_parents[0]['cfdi:Comprobante'][
                'Moneda'] = invoice.currency_id.name or ''
            invoice_data_parents[0]['cfdi:Comprobante'][
                'NumCtaPago'] = invoice.acc_payment.last_acc_number\
                    or 'No identificado'
            invoice_data_parents[0]['cfdi:Comprobante'][
                'metodoDePago'] = invoice.pay_method_id.name or 'No identificado'
            invoice_data_parents[0]['cfdi:Comprobante']['cfdi:Emisor']['cfdi:RegimenFiscal'] = {
                'Regimen': invoice.company_emitter_id.partner_id.\
                    regimen_fiscal_id.name or ''}
            invoice_data_parents[0]['cfdi:Comprobante']['LugarExpedicion'] = address
        return invoice_data_parents

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
        date_invoice=False, payment_term=False, partner_bank_id=False,
        company_id=False):
        """
        @param type : Type of invoice
        @param parter_id : Id of partner in the data base
        @param date_invoice : Date of invoice
        @param payment_term : Id of payment term to the invoice
        @param partner_bank_id : Id of bank account that is used in the invoice
        @param company_id : Id of the company from invoice
        """
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids,
            type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        partner_bank_obj = self.pool.get('res.partner.bank')
        acc_partner_bank = False
        if partner_id:
            acc_partner_bank_ids = partner_bank_obj.search(
                cr, uid, [('partner_id', '=', partner_id)], limit=1)
            if acc_partner_bank_ids:
                acc_partner_bank = acc_partner_bank_ids and partner_bank_obj.browse(
                    cr, uid, acc_partner_bank_ids)[0] or False
        res['value'][
            'acc_payment'] = acc_partner_bank and acc_partner_bank.id or False
        return res
        
    def cfdi_data_write(self, cr, uid, ids, cfdi_data, context=None):
        """
        @params cfdi_data : * TODO
        """
        if context is None:
            context = {}
        attachment_obj = self.pool.get('ir.attachment')
        cfdi_xml = cfdi_data.pop('cfdi_xml')
        if cfdi_xml:
            self.write(cr, uid, ids, cfdi_data)
            cfdi_data[
                'cfdi_xml'] = cfdi_xml  # Regresando valor, despues de hacer el write normal
        return True

    def _get_file(self, cr, uid, inv_ids, context=None):
        if context is None:
            context = {}
        id = inv_ids[0]
        invoice = self.browse(cr, uid, [id], context=context)[0]
        fname_invoice = invoice.fname_invoice and invoice.fname_invoice + \
            '.xml' or ''
        aids = self.pool.get('ir.attachment').search(cr, uid, [(
            'datas_fname', '=', invoice.fname_invoice+'.xml'), (
                'res_model', '=', 'account.invoice'), ('res_id', '=', id)])
        xml_data = ""
        if aids:
            brow_rec = self.pool.get('ir.attachment').browse(cr, uid, aids[0])
            if brow_rec.datas:
                xml_data = base64.decodestring(brow_rec.datas)
        else:
            fname, xml_data = self._get_facturae_invoice_xml_data(
                cr, uid, inv_ids, context=context)
            self.pool.get('ir.attachment').create(cr, uid, {
                'name': fname_invoice,
                'datas': base64.encodestring(xml_data),
                'datas_fname': fname_invoice,
                'res_model': 'account.invoice',
                'res_id': invoice.id,
            }, context=None)#Context, because use a variable type of our code but we dont need it.
        self.fdata = base64.encodestring(xml_data)
        msg = _("Press in the button  'Upload File'")
        return {'file': self.fdata, 'fname': fname_invoice,
                'name': fname_invoice, 'msg': msg}

    def _get_type_sequence(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ir_seq_app_obj = self.pool.get('ir.sequence.approval')
        invoice = self.browse(cr, uid, ids[0], context=context)
        sequence_app_id = ir_seq_app_obj.search(cr, uid, [(
            'sequence_id', '=', invoice.invoice_sequence_id.id)], context=context)
        type_inv = 'cfd22'
        if sequence_app_id:
            type_inv = ir_seq_app_obj.browse(
                cr, uid, sequence_app_id[0], context=context).type
        if 'cfdi' in type_inv:
            comprobante = 'cfdi:Comprobante'
        else:
            comprobante = 'Comprobante'
        return comprobante

    def _get_time_zone(self, cr, uid, invoice_id, context=None):
        if context is None:
            context = {}
        res_users_obj = self.pool.get('res.users')
        userstz = res_users_obj.browse(cr, uid, [uid])[0].partner_id.tz
        a = 0
        if userstz:
            hours = timezone(userstz)
            fmt = '%Y-%m-%d %H:%M:%S %Z%z'
            now = datetime.now()
            loc_dt = hours.localize(datetime(now.year, now.month, now.day,
                                             now.hour, now.minute, now.second))
            timezone_loc = (loc_dt.strftime(fmt))
            diff_timezone_original = timezone_loc[-5:-2]
            timezone_original = int(diff_timezone_original)
            s = str(datetime.now(pytz.timezone(userstz)))
            s = s[-6:-3]
            timezone_present = int(s)*-1
            a = timezone_original + ((
                timezone_present + timezone_original)*-1)
        return a
    
    def _get_file_cancel(self, cr, uid, inv_ids, context=None):
        if context is None:
            context = {}
        inv_ids = inv_ids[0]
        atta_obj = self.pool.get('ir.attachment')
        atta_id = atta_obj.search(cr, uid, [('res_id', '=', inv_ids), (
            'name', 'ilike', '%.xml')], context=context)
        res = {}
        if atta_id:
            atta_brw = atta_obj.browse(cr, uid, atta_id, context)[0]
            inv_xml = atta_brw.datas or False
        else:
            inv_xml = False
            raise osv.except_osv(('State of Cancellation!'), (
                "This invoice hasn't stamped, so that not possible cancel."))
        return {'file': inv_xml}
        
    def _create_qrcode(self, cr, uid, ids, invoice_id, folio_fiscal=False, context=None):
        if context is None:
            context = {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        invoice = self.browse(cr, uid, invoice_id)
        rfc_transmitter = invoice.company_id.partner_id.vat_split or ''
        rfc_receiver = invoice.partner_id.parent_id.vat_split or invoice.partner_id.parent_id.vat_split or ''
        amount_total = string.zfill("%0.6f"%invoice.amount_total,17)
        cfdi_folio_fiscal = folio_fiscal or ''
        qrstr = "?re="+rfc_transmitter+"&rr="+rfc_receiver+"&tt="+amount_total+"&id="+cfdi_folio_fiscal
        qr = QRCode(version=1, error_correction=ERROR_CORRECT_L)
        qr.add_data(qrstr)
        qr.make() # Generate the QRCode itself
        im = qr.make_image()
        fname=tempfile.NamedTemporaryFile(suffix='.png',delete=False)
        im.save(fname.name)
        return fname.name
        
    def _create_original_str(self, cr, uid, ids, invoice_id, context=None):
        if context is None:
            context = {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        invoice = self.browse(cr, uid, invoice_id)
        cfdi_folio_fiscal = invoice.cfdi_folio_fiscal or ''
        cfdi_fecha_timbrado = invoice.cfdi_fecha_timbrado or ''
        if cfdi_fecha_timbrado:
            cfdi_fecha_timbrado=time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(cfdi_fecha_timbrado, '%Y-%m-%d %H:%M:%S'))
        sello = invoice.sello or ''
        cfdi_no_certificado = invoice.cfdi_no_certificado or ''
        original_string = '||1.0|'+cfdi_folio_fiscal+'|'+str(cfdi_fecha_timbrado)+'|'+sello+'|'+cfdi_no_certificado+'||'
        return original_string

class ir_attachment_facturae_mx(osv.Model):

    _inherit = 'ir.attachment.facturae.mx'

    def signal_cancel(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = super(ir_attachment_facturae_mx, self).signal_cancel(cr, uid, ids)
        for att in self.browse(cr, uid, ids):
            if res and att.model_source == 'account.invoice' and att.id_source:
                if self.pool.get(att.model_source).browse(cr, uid, att.id_source).state != 'cancel':
                    res = self.pool.get(att.model_source).action_cancel(
                        cr, uid, [att.id_source], context=context)
        return res

#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/3/13 15:31
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : businessManager.py
# @Descr   : 
# @Software: PyCharm
import logging

logger = logging.getLogger('django')


class BuisnessOperator:
    def __init__(self, connection):
        self.connection = connection

    # # 获取查询用的年份列表
    # def get_year_list(self, request,function_title):
    #     api_path = request.path
    #     res = ""
    #     start = LoggerHelper.set_start_log_info(logger)
    #     try:
    #         sql = "select distinct insurance_year from tt_insurance_standing_book where 1=1  "
    #         # 增加用户关联保险险种过滤条件
    #         filter_sql = CommonHelper.get_sql_filter_insurance_by_user(request)
    #         sql += filter_sql
    #         sql += "and insurance_year is not null order by insurance_year asc"
    #         cursor = self.connection.cursor()
    #         cursor.execute(sql)
    #         records = cursor.fetchall()
    #         data_list = []
    #         for record in records:
    #             obj = {}
    #             obj['year'] = record[0]
    #             data_list.append(obj)
    #         res = {
    #             'success': True,
    #             'total': len(data_list),
    #             'info': data_list
    #         }
    #         LoggerHelper.set_end_log_info(SysLog,logger, start, api_path, request.auth.user, request,
    #                                       function_title)
    #     except Exception as exp:
    #         res = LoggerHelper.set_end_log_info_in_exception(SysLog,logger, start, api_path,
    #                                                          request.auth.user, request,
    #                                                          function_title, None, exp)
    #     finally:
    #         return res



    # # 预保单查询
    # def sql_search_pre_insurance_data(self, function_title,agent_name, pre_insurance_policy_number, sub_insurance_policy_number,
    #                                   insured_name,
    #                                   vessel_name, insurance_year, insurance_month, request):
    #     api_path = request.path
    #     res = ""
    #     start = LoggerHelper.set_start_log_info(logger)
    #     try:
    #         insurance_type, insurance_target_type, insurance_target_sub_name, insurance_target_sub_filed = CommonHelper.get_insurance_type_full(
    #             request)
    #         insurance_info_full = insurance_type + "-" + insurance_target_type + "-" + insurance_target_sub_name
    #         sql = "select id,insurance_year,insurance_month,pre_insurance_policy_number,sub_insurance_policy_number,insured_name,invoice_contract_nos,subject_matter,packing_quanlity,insured_amount,per_conveyance,from_port,to_port,sailing_date,insure_date,applicant_name,applicant_tel,insured_name,insured_date,insured_amount,insurance_day,vessel_age,vessel_name,vessel_registry,insured_conditions,insured_additional,currency_unit,currency_unit_position,is_audit,audit_name,agent_name,custom_name,warehouse_name, pre_insurance_from_date,pre_insurance_to_date,pre_insurance_days,apply_insurance_from_date,apply_insurance_to_date,apply_insurance_days,insurance_address,insurance_rate,quantity_unit,pre_insurance_quantity,apply_insurance_quantity,insurance_from_date,insurance_to_date,pre_insurance_date,apple_insurance_date,pre_insurance_amount,pre_preminum,apply_insurance_amount,apply_preminum,file_agent_name,remarks,match_id,insurance_apply_status_picc,insurance_apply_status_custom"
    #         sql += " from tt_insurance_pre where 1=1  "
    #         role_name = SysmanHelper.getRoleOfLoginUser(request)
    #         if role_name == "客户":
    #             sql += " and is_show_custom=true "
    #         if role_name == "PICC业务员":
    #             sql += " and is_show_picc=true "
    #         if agent_name is not None and agent_name.strip() != "":
    #             sql += " and agent_name like '%" + agent_name + "%'"
    #         if pre_insurance_policy_number is not None and str(pre_insurance_policy_number).strip() != "":
    #             sql += " and pre_insurance_policy_number like '%" + pre_insurance_policy_number + "%'"
    #         if sub_insurance_policy_number is not None and str(sub_insurance_policy_number).strip() != "":
    #             sql += " and sub_insurance_policy_number like '%" + sub_insurance_policy_number + "%'"
    #         if insured_name is not None and str(insured_name).strip() != "":
    #             sql += " and insured_name like '%" + insured_name + "%'"
    #         if vessel_name is not None and str(vessel_name).strip() != "":
    #             sql += " and vessel_name like '%" + vessel_name + "%'"
    #         if insurance_year is not None and str(insurance_year).strip() != "":
    #             sql += " and insurance_year =" + str(insurance_year)
    #         if insurance_month is not None and str(insurance_month).strip() != "":
    #             sql += " and insurance_month =" + str(insurance_month)
    #         sql += " and (agent_name=(select fullname from auth_user where id=" + str(request.auth.user_id) + ")"
    #         sql += " or audit_name=(select fullname from auth_user where id=" + str(request.auth.user_id) + ")"
    #         sql += " or custom_name=(select fullname from auth_user where id=" + str(request.auth.user_id) + "))"
    #         # 增加用户关联保险险种过滤条件
    #         filter_sql = CommonHelper.get_sql_filter_insurance_by_user(request)
    #         sql += filter_sql
    #         sql += " order by modify_time desc"
    #         cursor = self.connection.cursor()
    #         cursor.execute(sql)
    #         records = cursor.fetchall()
    #         data_list = []
    #         for record in records:
    #             obj = {}
    #             if insurance_info_full == "货运险-石油-原油" or insurance_info_full == "货运险-石油-成品油":
    #                 obj['id'] = record[0]
    #                 obj['insurance_year'] = record[1]
    #                 obj['insurance_month'] = record[2]
    #                 obj['pre_insurance_policy_number'] = str(record[3]) if record[3] is not None else None
    #                 obj['sub_insurance_policy_number'] = str(record[4]) if record[4] is not None else None
    #                 obj['insured_name'] = str(record[5]) if record[5] is not None else None
    #                 obj['invoice_contract_nos'] = str(record[6]) if record[6] is not None else None
    #                 obj['subject_matter'] = str(record[7]) if record[7] is not None else None
    #                 obj['packing_quanlity'] = str(record[8]) if record[8] is not None else None
    #                 # 对货币数据进行处理，数据库里是数值，返回到前端是带货币单位的会计格式
    #                 obj['insured_amount'] = CommonHelper.thousand_sep_currency_add_unit(record[9],
    #                                                                                     record[26],
    #                                                                                     record[27])
    #                 obj['per_conveyance'] = str(record[10]) if record[10] is not None else None
    #                 obj['from_port'] = str(record[11]) if record[11] is not None else None
    #                 obj['to_port'] = str(record[12]) if record[12] is not None else None
    #                 obj['sailing_date'] = str(record[13]) if record[13] is not None else None
    #                 obj['insure_date'] = str(record[14]) if record[14] is not None else None
    #                 obj['applicant_name'] = str(record[15]) if record[15] is not None else None
    #                 obj['applicant_tel'] = str(record[16]) if record[16] is not None else None
    #                 obj['insured_name'] = str(record[17]) if record[17] is not None else None
    #                 obj['insured_date'] = str(record[18]) if record[18] is not None else None
    #                 obj['insured_amount'] = CommonHelper.thousand_sep_currency_add_unit(record[9],
    #                                                                                     record[26],
    #                                                                                     record[27])
    #                 obj['insurance_day'] = str(record[20]) if record[20] is not None else None
    #                 obj['vessel_age'] = str(record[21]) if record[21] is not None else None
    #                 obj['vessel_name'] = str(record[22]) if record[22] is not None else None
    #                 obj['vessel_registry'] = str(record[23]) if record[23] is not None else None
    #                 obj['insured_conditions'] = str(record[24]) if record[24] is not None else None
    #                 obj['insured_additional'] = str(record[25]) if record[25] is not None else None
    #                 obj['currency_unit'] = str(record[26]) if record[26] is not None else None
    #                 obj['currency_unit_position'] = str(record[27]) if record[27] is not None else None
    #                 obj['is_audit'] = record[28] if record[28] is not None else None
    #                 obj['audit_name'] = str(record[29]) if record[29] is not None else None
    #                 obj['agent_name'] = str(record[30]) if record[30] is not None else None
    #                 obj['custom_name'] = str(record[31]) if record[31] is not None else None
    #                 obj['file_agent_name'] = str(record[52]) if record[52] is not None else None
    #                 obj['pre_insurance_amount'] = CommonHelper.thousand_sep_currency(str(record[48])) if record[
    #                                                                                                          48] is not None else None
    #                 obj['pre_preminum'] = CommonHelper.thousand_sep_currency(str(record[49])) if record[
    #                                                                                                  49] is not None else None
    #                 if role_name == "客户":
    #                     obj["insurance_apply_status_custom"] = str(record[56]) if record[56] is not None else None
    #                 if role_name == "PICC业务员":
    #                     obj["insurance_apply_status_picc"] = str(record[55]) if record[55] is not None else None
    #             if insurance_info_full == "财产险-仓储-短期":
    #                 obj['id'] = record[0]
    #                 obj['insurance_year'] = record[1]
    #                 obj['insurance_month'] = record[2]
    #                 obj['pre_insurance_policy_number'] = str(record[3]) if record[3] is not None else None
    #                 obj['insured_name'] = str(record[5]) if record[5] is not None else None
    #                 obj['invoice_contract_nos'] = str(record[6]) if record[6] is not None else None
    #                 obj['subject_matter'] = str(record[7]) if record[7] is not None else None
    #                 obj['applicant_name'] = str(record[15]) if record[15] is not None else None
    #                 obj['insured_name'] = str(record[17]) if record[17] is not None else None
    #                 obj['insured_conditions'] = str(record[24]) if record[24] is not None else None
    #                 # obj['insured_additional'] = str(record[25])
    #                 obj['currency_unit'] = str(record[26]) if record[26] is not None else None
    #                 obj['currency_unit_position'] = str(record[27]) if record[27] is not None else None
    #                 obj['is_audit'] = record[28]
    #                 obj['audit_name'] = str(record[29]) if record[29] is not None else None
    #                 obj['agent_name'] = str(record[30]) if record[30] is not None else None
    #                 obj['custom_name'] = str(record[31]) if record[31] is not None else None
    #
    #                 # 对货币和数量进行处理，数据库里是数值，返回到前端是百分位的会计格式
    #                 obj['warehouse_name'] = str(record[32]) if record[32] is not None else None
    #                 obj['pre_insurance_from_date'] = str(record[33]) if record[33] is not None else None
    #                 obj['pre_insurance_to_date'] = str(record[34]) if record[34] is not None else None
    #                 obj['pre_insurance_days'] = str(record[35]) if record[35] is not None else None
    #                 # obj['apply_insurance_from_date']= str(record[36])
    #                 # obj['apply_insurance_to_date'] = str(record[37])
    #                 # obj['apply_insurance_days'] = str(record[38])
    #                 obj['insurance_address'] = str(record[39]) if record[39] is not None else None
    #                 obj['insurance_rate'] = str(record[40]) if record[40] is not None else None
    #                 obj['quantity_unit'] = str(record[41]) if record[41] is not None else None
    #                 obj['pre_insurance_quantity'] = CommonHelper.thousand_sep_currency(str(record[42])) if record[
    #                                                                                                            42] is not None else None
    #                 # obj['apply_insurance_quantity'] = CommonHelper.thousand_sep_currency(str(record[43])) if record[
    #                 #                                                                                              43] is not None else None
    #                 # obj['insurance_from_date'] = str(record[44])
    #                 # obj['insurance_to_date'] = str(record[45])
    #                 obj['pre_insurance_date'] = str(record[46])
    #                 # obj['apple_insurance_date'] = str(record[47])
    #                 obj['pre_insurance_amount'] = CommonHelper.thousand_sep_currency(str(record[48])) if record[
    #                                                                                                          48] is not None else None
    #                 obj['pre_preminum'] = CommonHelper.thousand_sep_currency(str(record[49])) if record[
    #                                                                                                  49] is not None else None
    #                 # obj['apply_insurance_amount'] = CommonHelper.thousand_sep_currency(str(record[50])) if record[
    #                 #                                                                                            50] is not None else None
    #                 # obj['apply_preminum'] = CommonHelper.thousand_sep_currency(str(record[51])) if record[
    #                 #                                                                                    51] is not None else None
    #                 obj['file_agent_name'] = str(record[52]) if record[52] is not None else None
    #                 obj['remarks'] = str(record[53]) if record[53] is not None else None
    #                 obj['match_id'] = str(record[54]) if record[54] is not None else None
    #                 if role_name == "客户":
    #                     obj["insurance_apply_status_custom"] = str(record[56]) if record[56] is not None else None
    #                 if role_name == "PICC业务员":
    #                     obj["insurance_apply_status_picc"] = str(record[55]) if record[55] is not None else None
    #
    #             if insurance_info_full == "财产险-仓储-长期":
    #                 obj['id'] = record[0]
    #                 obj['insurance_year'] = record[1]
    #                 obj['insurance_month'] = record[2]
    #                 obj['pre_insurance_policy_number'] = str(record[3]) if record[3] is not None else None
    #                 obj['insured_name'] = str(record[5]) if record[5] is not None else None
    #                 # obj['invoice_contract_nos'] = str(record[6])
    #                 # obj['subject_matter'] = str(record[7])
    #                 obj['applicant_name'] = str(record[15]) if record[15] is not None else None
    #                 obj['insured_name'] = str(record[17]) if record[17] is not None else None
    #                 obj['insured_conditions'] = str(record[24]) if record[24] is not None else None
    #                 obj['insured_additional'] = str(record[25]) if record[25] is not None else None
    #                 obj['currency_unit'] = str(record[26]) if record[26] is not None else None
    #                 obj['currency_unit_position'] = str(record[27]) if record[27] is not None else None
    #                 obj['is_audit'] = record[28]
    #                 obj['audit_name'] = str(record[29]) if record[29] is not None else None
    #                 obj['agent_name'] = str(record[30]) if record[30] is not None else None
    #                 obj['custom_name'] = str(record[31]) if record[31] is not None else None
    #
    #                 # 对货币和数量进行处理，数据库里是数值，返回到前端是百分位的会计格式
    #                 # obj['warehouse_name'] = str(record[32])
    #                 # obj['pre_insurance_from_date'] = str(record[33])
    #                 # obj['pre_insurance_to_date'] = str(record[34])
    #                 # obj['pre_insurance_days'] = str(record[35])
    #                 # obj['apply_insurance_from_date']= str(record[36])
    #                 # obj['apply_insurance_to_date'] = str(record[37])
    #                 # obj['apply_insurance_days'] = str(record[38])
    #                 obj['insurance_address'] = str(record[39]) if record[39] is not None else None
    #                 obj['insurance_rate'] = str(record[40]) if record[40] is not None else None
    #                 obj['quantity_unit'] = str(record[41]) if record[41] is not None else None
    #                 obj['pre_insurance_quantity'] = CommonHelper.thousand_sep_currency(str(record[42])) if record[
    #                                                                                                            42] is not None else None
    #                 obj['apply_insurance_quantity'] = CommonHelper.thousand_sep_currency(str(record[43])) if record[
    #                                                                                                              43] is not None else None
    #                 obj['insure_date'] = str(record[14]) if record[14] is not None else None
    #                 obj['insured_date'] = str(record[18]) if record[18] is not None else None
    #                 obj['insurance_from_date'] = str(record[44]) if record[44] is not None else None
    #                 obj['insurance_to_date'] = str(record[45]) if record[45] is not None else None
    #                 # obj['pre_insurance_date'] = str(record[46]) if record[46] is not None else None
    #                 # obj['apple_insurance_date'] = str(record[47]) if record[47] is not None else None
    #                 obj['pre_insurance_amount'] = CommonHelper.thousand_sep_currency(str(record[48])) if record[
    #                                                                                                          48] is not None else None
    #                 obj['pre_preminum'] = CommonHelper.thousand_sep_currency(str(record[49])) if record[
    #                                                                                                  49] is not None else None
    #                 obj['apply_insurance_amount'] = CommonHelper.thousand_sep_currency(str(record[50])) if record[
    #                                                                                                            50] is not None else None
    #                 obj['apply_preminum'] = CommonHelper.thousand_sep_currency(str(record[51])) if record[
    #                                                                                                    51] is not None else None
    #                 obj['file_agent_name'] = str(record[52]) if record[52] is not None else None
    #                 obj['remarks'] = str(record[53])
    #                 # obj['match_id'] = str(record[54]) if record[54] is not None else None
    #                 if role_name == "客户":
    #                     obj["insurance_apply_status_custom"] = str(record[56]) if record[56] is not None else None
    #                 if role_name == "PICC业务员":
    #                     obj["insurance_apply_status_picc"] = str(record[55]) if record[55] is not None else None
    #
    #             data_list.append(obj)
    #             res = {
    #                 'success': True,
    #                 'total': len(data_list),
    #                 'info': data_list
    #             }
    #             LoggerHelper.set_end_log_info(SysLog,logger, start, api_path, request.auth.user, request,
    #                                           function_title)
    #     except Exception as exp:
    #         res = LoggerHelper.set_end_log_info_in_exception(SysLog,logger, start, api_path,
    #                                                          request.auth.user, request,
    #                                                          function_title, None, exp)
    #     finally:
    #         return res

    #
    # # 导出预保单(货运险-原油，附件2）
    # def export_pre_insurance_to_pdf_cargo_insurance_crude_oil(self, request,function_title):
    #     api_path = request.path
    #     ids = request.data["ids"]
    #     user_id = request.auth.user_id
    #     res = ""
    #     start = LoggerHelper.set_start_log_info(logger)
    #     try:
    #         # 先生成word，再转换为pdf
    #         if len(TtInsurancePre.objects.filter(id__in=ids)) > 0:
    #             pre_insurance_infos = TtInsurancePre.objects.filter(id__in=ids)
    #             template_word_path = str(settings.BASE_DIR) + "/my_app{}template/".format(settings.STATIC_URL)
    #             make_word_path = str(settings.BASE_DIR) + "/my_app{}doc/".format(settings.STATIC_URL)
    #             if not os.path.exists(make_word_path):
    #                 os.mkdir(make_word_path)
    #             output_work_path = str(settings.BASE_DIR) + "/my_app{}pdf/".format(settings.STATIC_URL)
    #             if not os.path.exists(output_work_path):
    #                 os.mkdir(output_work_path)
    #             # 多个导出生成压缩包,单个导出为单文件
    #             is_multi = False
    #             if len(pre_insurance_infos) > 1:
    #                 is_multi = True
    #                 zip_file_path = os.path.join(str(settings.BASE_DIR),
    #                                              "my_app{}zip/".format(settings.STATIC_URL) + "预保单压缩包_" + str(
    #                                                  uuid.uuid4()))
    #                 if not os.path.exists(zip_file_path):
    #                     os.makedirs(zip_file_path)
    #                 (zip_file_pre_path, temp_zip_filename) = os.path.split(zip_file_path)
    #             for pre_insurance_info in pre_insurance_infos:
    #                 # 定义报告生成名称
    #                 pre_insurance_policy_number = pre_insurance_info.pre_insurance_policy_number
    #                 word_file_name = "预保单{}_{}.docx".format(pre_insurance_policy_number,
    #                                                         str(uuid.uuid4()))
    #
    #                 word_file_path = os.path.join(make_word_path, word_file_name)
    #                 pdf_file_path = os.path.join(output_work_path, word_file_name.replace(".docx", ".pdf"))
    #                 # f = open(word_file_path, 'w', encoding='utf-8')
    #                 # 读取报告模板
    #                 word_template_file_name = "SUB_INSURANCE_TEMPPLATE.docx"
    #                 report_template_path = os.path.join(template_word_path, word_template_file_name)
    #                 data_doc = Document(report_template_path)
    #                 # 对报告里的文本信息进行动态替换
    #                 self.replace_txt_in_sub_insurance_word(data_doc, pre_insurance_info)
    #                 # 对报告里的表格内容进行动态替换
    #                 # self.replace_table_in_word(data_doc, pre_insurance_info)
    #                 # 对报告里的图片进行动态替换
    #                 self.replace_image_in_sub_insurance_word(data_doc, pre_insurance_info)
    #                 # 保存生成报告
    #                 data_doc.save(word_file_path)
    #                 # 将word导出为pdf
    #                 convert_doc_to_pdf(word_file_path, pdf_file_path)
    #                 (file_pre_path, temp_filename) = os.path.split(pdf_file_path)
    #                 # 多个导出将每个pdf复制到待压缩文件夹
    #                 if is_multi is True:
    #                     shutil.copy(pdf_file_path, zip_file_path)
    #                 result_file_url = "http://{}:{}{}pdf/{}".format(settings.ORC_SERVICE_IP,
    #                                                                 settings.ORC_SERVICE_PORT, settings.STATIC_URL,
    #                                                                 temp_filename)
    #             # 导出后在列表中进行隐藏，根据当前用户角色
    #             role_name = SysmanHelper.getRoleOfLoginUser(request)
    #             if role_name == "客户":
    #                 TtInsurancePre.objects.filter(id__in=ids).update(is_show_custom=False)
    #             if role_name == "PICC业务员":
    #                 TtInsurancePre.objects.filter(id__in=ids).update(is_show_picc=False)
    #             if is_multi is True:
    #                 # 压缩打包
    #                 shutil.make_archive(zip_file_path, "zip", root_dir=zip_file_path)
    #                 # 获取下载url
    #                 result_file_url = "http://{}:{}{}zip/{}".format(settings.ORC_SERVICE_IP,
    #                                                                 settings.ORC_SERVICE_PORT, settings.STATIC_URL,
    #                                                                 temp_zip_filename + ".zip")
    #             res = {
    #                 'success': True,
    #                 'info': result_file_url
    #             }
    #         else:
    #             error_info = "编号为{}的预保单在数据表里没有记录".format(id)
    #             res = LoggerHelper.set_end_log_info_in_exception(SysLog,logger, start, api_path,
    #                                                              request.auth.user, request,
    #                                                              function_title, error_info, None)
    #     except Exception as exp:
    #         res = LoggerHelper.set_end_log_info_in_exception(SysLog,logger, start, api_path,
    #                                                          request.auth.user, request,
    #                                                          function_title, None, exp)
    #     finally:
    #         return res

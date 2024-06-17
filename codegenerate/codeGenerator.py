#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/12/18 20:31
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : codeGenerator.py
# @Descr   : 代码生成器
# 生成django开发需要的代码
# 生成单文件调用传参
# @Software: PyCharm
import os

from vgis_code.codeGenerator import BuildCode, BuildDjango, BuildCommand
from vgis_database.pgTools import PgHelper
# # 加密包
# from vgis_database import PgHelper


# 构建命令行参数
def make_build_command():
    # 测试命令行
    args = {
        # py文件名称
        "py_file_name": "crawlerWebsiteData.py",
        # 全局变量定义,用分号隔离
        "var_name_list": "website_url;is_turn_page;turn_page_num;fields_name_str;fields_path_str;result_excel_path",
        # 全局变量注释，用分号隔离
        "var_anno_list": "进行网络抓取的网站URL;是否翻页;翻到多少页;提取字段名称字符串，用逗号连接;提取字段路径字符串，用&&连接;提取结果excel文件路径",
        # 全局变量赋值，用分号隔离
        "var_value_list": "https://bj.fang.lianjia.com/loupan;true;5;名称,面积,类型;div.resblock-list-container.clearfix>ul.resblock-list-wrapper>li.resblock-list.post_ulog_exposure_scroll.has-results>div.resblock-desc-wrapper>div.resblock-name>a.name&&div.resblock-list-container.clearfix>ul.resblock-list-wrapper>li.resblock-list.post_ulog_exposure_scroll.has-results>div.resblock-desc-wrapper>div.resblock-area>span&&div.resblock-list-container.clearfix>ul.resblock-list-wrapper>li.resblock-list.post_ulog_exposure_scroll.has-results>div.resblock-desc-wrapper>div.resblock-name>span.resblock-type;d:/qcndata/recong_tmp.xlsx",
        # 长类型定义,用分号隔离
        "var_long_option_list": "websiteUrl;isTurnPage;turnPageNum;fieldsNameStr;fieldsPathStr;resultExcelPath",
        # 短类型定义，用冒号隔离
        "var_short_opt_list": "w:t:s:n:p:d:"
    }
    code_builder = BuildCommand(args)
    code_builder.make_command_str()





# 生成django代码
def make_django_code():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    pre_directory = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    model_file = os.path.join(current_directory, "model.txt")
    host = "192.168.3.191"
    port = "5432"
    user = "postgres"
    passwd = "postgres123"
    database = "BXJCXTDB"
    connection = PgHelper.get_database_conection(host, port, user, passwd, database)
    token_key = "Authorization"
    postman_file = os.path.join(pre_directory, "postman", "通用项目.postman_collection.json")
    postman_file_encrpt = os.path.join(pre_directory, "postman", "通用项目（加密）.postman_collection.json")
    aes_key = "myaovgis0713wxgz"
    code_builder = BuildDjango(model_file, connection, token_key, postman_file, postman_file_encrpt, aes_key)
    code_builder.generate_serializer()
    print("-----------------------------------------")
    code_builder.generate_viewer()
    print("-----------------------------------------")
    code_builder.generate_classes()
    print("-----------------------------------------")
    code_builder.generate_urls()
    print("-----------------------------------------")
    code_builder.generate_postman()
    print("-----------------------------------------")
    code_builder.generate_postman_encrpyt()
    print("-----------------------------------------")
    code_builder.generate_cude_code_in_viewer("/zhbxfzcd_api/ttInsuranceStandingBook/", "台账总表",
                                              "TtInsuranceStandingBook", ["出单邮件编号"], ["email_number"])


# # 包装数量
# obj["{packing_quanlity}"] = pre_insurance_info.packing_quanlity
# # 投保金额
# obj["{insured_amount}"] = pre_insurance_info.insured_amount
# # 运输工具
# obj["{per_conveyance}"] = pre_insurance_info.per_conveyance


# request.data["subject_matter"] = relatedInsurancePreObj.subject_matter
# request.data["packing_quanlity"] = relatedInsurancePreObj.packing_quanlity
def make_code_snippt():
    code_builder = BuildCode()
    obj_name = "obj"
    class_name = "pre_insurance_info"
    attribute_name_list = ["packing_quanlity", "insured_amount", "per_conveyance"]
    # 中文可为空
    attribute_caption_list = ["包装数量", "投保金额", "运输工具"]
    code_builder.create_snippt(obj_name, class_name, attribute_name_list, attribute_caption_list)


#  obj = {}
#  obj['id'] = record[0]
#  obj['insurance_year'] = record[1]
#  obj = {}
#  obj['id'] = record[0] if record[0] is not None else None
#  obj['insurance_year'] =  if record[1] is not None else None
#  obj = {}
#  obj['id'] = record[0] if record[0] is not None else ""
#  obj['insurance_year'] =  if record[1] is not None else ""
#  obj = {}
#  obj['编号'] = record[0]
#  obj['保险年份'] = record[1]
#  obj = {}
#  obj['编号'] = record[0] if record[0] is not None else None
#  obj['保险年份'] =  if record[1] is not None else None
#  obj = {}
#  obj['编号'] = record[0] if record[0] is not None else ""
#  obj['保险年份'] =  if record[1] is not None else ""
def make_code_snippt2():
    code_builder = BuildCode()
    obj_name = "obj"
    attribute_cnames_str = "编号,台账编号,邮件编号"
    attribute_enames_str = "id,standing_book_number,email_number"
    code_builder.create_snippt2(obj_name, attribute_enames_str, attribute_cnames_str)


# sub_insurance_policy_number = request.data[ "sub_insurance_policy_number"] if "sub_insurance_policy_number" in request.data else None
# pre_insurance_policy_number = request.data["pre_insurance_policy_number"] if "pre_insurance_policy_number" in request.data else None
def make_code_snippt3():
    code_builder = BuildCode()
    obj_name = "request.data"
    attribute_names_str = "sub_insurance_policy_number,pre_insurance_policy_number"
    code_builder.create_snippt3(obj_name, attribute_names_str)

def make_code_snippt4():
    code_builder = BuildCode()
    excel_obj_name = "excel_data_obj"
    attribute_cnames_str = "序号,板块,分公司,投保人,投保人地址,起保日期,终保日期,被保险人职业分类,投保人数,意外伤害身故、残疾（万元/人）,意外伤害医疗（万元/人）,急性病身故（万元/人）,疾病身故（万元/人）,猝死（万元/人）,住院津贴（元/天）,住院津贴天数,门诊误工津贴（元/天）,死亡、伤残（%）,意外医疗（%）,急性病身故（%）,疾病身故（%）,猝死（%）,住院津贴（%）,门诊误工津贴（%）,每人保费,投保天数,总保费,保批单类型,投保单号,保单号,批单号,邮件日期,保费发票抬头（必须为被保险人）,保单发票邮寄联系人、地址及联系方式,邮寄单号,经纪人,到账金额,到账备注,备注,联共保标识"
    attribute_enames_str = "requirement_enterprise_number,enterprise_sector_name,enterprise_branch_name,applicant,applicant_address,insurance_start_date,insurance_end_date,insured_occupational_classification,policyholders_number,accidental_injury_death_disability_premium_standard,accidental_injury_medical_treatment_premium_standard,acute_illness_death_premium_standard,illness_death_premium_standard,sudden_death_premium_standard,hospitalization_allowance_premium_standard,hospitalization_allowance_days,outpatient_delay_allowance_premium_standard,accidental_injury_death_disability_premium_ratio,accidental_injury_medical_treatment_premium_ratio,acute_illness_death_premium_ratio,illness_death_premium_ratio,sudden_death_premium_ratio,hospitalization_allowance_premium_ratio,outpatient_delay_allowance_premium_ratio,per_person_premium,insurance_days,total_premium,policy_endorsement_type,sub_policy_number,policy_number,endorsement_number,email_received_time,premium_invoice_header,premium_invoice_delivery_information,premium_invoice_delivery_number,agent,received_moneyamount,recevied_money_memo,memo,joint_insurance_label"
    code_builder.create_snippt4(excel_obj_name, attribute_cnames_str, attribute_enames_str)


def get_full_field_str():
    code_builder = BuildCode()
    host = "192.168.3.191"
    port = "5432"
    user = "postgres"
    passwd = "postgres123"
    database = "ZHBXFZCD"
    connection = PgHelper.get_database_conection(host, port, user, passwd, database)
    code_builder.get_full_field_str(connection, "tt_group_accident_insurance_standing_book")

if __name__ == '__main__':
    # 构建命令行参数
    # make_build_command()
    # print("***************************************************************")
    # 生成django代码
    make_django_code()
    # print("***************************************************************")
    # 生成代码片段
    get_full_field_str()
    # print("***************************************************************")
    # make_code_snippt()
    # print("***************************************************************")
    # make_code_snippt2()
    # print("***************************************************************")
    # # make_code_snippt3()
    # print("***************************************************************")
    # # make_code_snippt4()
    # print("***************************************************************")
    pass

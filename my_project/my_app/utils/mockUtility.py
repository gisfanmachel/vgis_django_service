#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/6/7 10:45
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : mockUtility.py
# @Descr   : 模拟数据帮助类
# @Software: PyCharm
import datetime
import json
import random
import psycopg2
import pandas as pd

from my_project import settings



class MockHelper:
    def __init__(self):
        pass

#     @staticmethod
#     # 关联分析
#     def get_AssociationAnalysis_Result(zxd_quan_analysis_name, zxd_quan_create_time,
#                                        zxd_quan_analysis_desc, zxd_model_name, evaluation_algorithm_ids,
#                                        evaluation_algorithm_names, zxd_quan_analysis_time, zxd_result,
#                                        data_consistency_result, data_completeness_result,
#                                        algorithm_satisfaction_result):
#         str_test = '''
#
#                     {
#                       "results": {
#                           "task_info": {
#                               "task_name": "''' + str(zxd_quan_analysis_name) + '''",
#                               "task_create_time": "''' + str(zxd_quan_create_time) + '''",
#                               "task_analysis_time": "''' + str(zxd_quan_analysis_time) + '''",
#                               "task_desc": "''' + str(zxd_quan_analysis_desc) + '''",
#                               "zxd_model_name":  "''' + str(zxd_model_name) + '''",
#                               "evaluation_algorithm_ids": "''' + str(evaluation_algorithm_ids) + '''",
#                               "evaluation_algorithm_names": "''' + str(evaluation_algorithm_names) + '''",
#                               "zxd_result":  "''' + str(zxd_result) + '''",
#                               "data_consistency_result":  "''' + str(data_consistency_result) + '''",
#                               "data_completeness_result":  "''' + str(data_completeness_result) + '''",
#                               "algorithm_satisfaction_result":  "''' + str(algorithm_satisfaction_result) + '''"
#                           },
#
#                           "sample_analysis_result":
#                           {
#                             "sample_analysis_info": [
#                             {
#                                 "payload_name": "可见光",
#                                 "resolution_statics": [
#                                     {
#                                         "resolution_name": "2米",
#                                         "sample_count": 4
#                                     },
#                                     {
#                                         "resolution_name": "5米",
#                                         "sample_count": 8
#                                     },
#                                     {
#                                         "resolution_name": "10米",
#                                         "sample_count": 12
#                                     }
#                                 ]
#                             },
#                             {
#                                 "payload_name": "SAR",
#                                 "resolution_statics": [
#                                     {
#                                         "resolution_name": "2米",
#                                         "sample_count": 4
#                                     },
#                                     {
#                                         "resolution_name": "5米",
#                                         "sample_count": 8
#                                     },
#                                     {
#                                         "resolution_name": "10米",
#                                         "sample_count": 12
#                                     }
#                                 ]
#                             },
#                             {
#                                 "payload_name": "高光谱",
#                                 "resolution_statics": [
#                                     {
#                                         "resolution_name": "2米",
#                                         "sample_count": 4
#                                     },
#                                     {
#                                         "resolution_name": "5米",
#                                         "sample_count": 8
#                                     },
#                                     {
#                                         "resolution_name": "10米",
#                                         "sample_count": 12
#                                     }
#                                 ]
#                             }
#                         ],
#                          "sample_associtaion_task_list": [
#                                 {
#                                     "task_name": "定量分析任务1"
#                                 },
#                                 {
#                                     "task_name": "定量分析任务2"
#                                 },
#                                 {
#                                     "task_name": "定量分析任务3"
#                                 }
#                             ]
#
#
#                         },
#
#         "association_analysis_result": [
#             {
#                 "evaluation_algorithm_name": "目标识别算法2",
#                 "evaluation_algorithm_result": {
#
#                     "index_analysis_info": [
#                         {
#                             "index_name": "检测率",
#                             "index_statics": [
#                                 {
#                                     "analysis_time": "20220512",
#                                     "analysis_value": 0.95
#                                 },
#                                 {
#                                     "analysis_time": "20220513",
#                                     "analysis_value": 0.89
#                                 },
#                                 {
#                                     "analysis_time": "20220514",
#                                     "analysis_value": 0.92
#                                 },
#                                 {
#                                     "analysis_time": "20220515",
#                                     "analysis_value": 0.91
#                                 },
#                                 {
#                                     "analysis_time": "20220516",
#                                     "analysis_value": 0.88
#                                 },
#                                 {
#                                     "analysis_time": "20220517",
#                                     "analysis_value": 0.96
#                                 }
#                             ]
#                         },
#                         {
#                             "index_name": "识别率",
#                             "index_statics": [
#                                 {
#                                     "analysis_time": "20220512",
#                                     "analysis_value": 0.95
#                                 },
#                                 {
#                                     "analysis_time": "20220513",
#                                     "analysis_value": 0.89
#                                 },
#                                 {
#                                     "analysis_time": "20220514",
#                                     "analysis_value": 0.92
#                                 },
#                                 {
#                                     "analysis_time": "20220515",
#                                     "analysis_value": 0.91
#                                 },
#                                 {
#                                     "analysis_time": "20220516",
#                                     "analysis_value": 0.88
#                                 },
#                                 {
#                                     "analysis_time": "20220517",
#                                     "analysis_value": 0.96
#                                 }
#                             ]
#                         }
#                     ],
#                     "total_result": {
#                         "task_name": "置信度定量分析任务",
#                         "jiancelv_benci": 0.89,
#                         "jiancelv_lishi": 0.86,
#                         "jiancelv_yuzhi": 0.95,
#                         "jiancelv_result": "调优"
#                     },
#                     "association_task_result": {
#                         "zhibiao_associtaion_task_list": [
#                             {
#                                 "task_name": "定量分析任务4"
#                             },
#                             {
#                                 "task_name": "定量分析任务5"
#                             },
#                             {
#                                 "task_name": "定量分析任务5"
#                             }
#                         ]
#                     }
#                 }
#             },
#             {
#                 "evaluation_algorithm_name": "目标识别算法3",
#                 "evaluation_algorithm_result": {
#
#                     "index_analysis_info": [
#                         {
#                             "index_name": "检测率",
#                             "index_statics": [
#                                 {
#                                     "analysis_time": "20220512",
#                                     "analysis_value": 0.95
#                                 },
#                                 {
#                                     "analysis_time": "20220513",
#                                     "analysis_value": 0.89
#                                 },
#                                 {
#                                     "analysis_time": "20220514",
#                                     "analysis_value": 0.92
#                                 },
#                                 {
#                                     "analysis_time": "20220515",
#                                     "analysis_value": 0.91
#                                 },
#                                 {
#                                     "analysis_time": "20220516",
#                                     "analysis_value": 0.88
#                                 },
#                                 {
#                                     "analysis_time": "20220517",
#                                     "analysis_value": 0.96
#                                 }
#                             ]
#                         },
#                         {
#                             "index_name": "识别率",
#                             "index_statics": [
#                                 {
#                                     "analysis_time": "20220512",
#                                     "analysis_value": 0.95
#                                 },
#                                 {
#                                     "analysis_time": "20220513",
#                                     "analysis_value": 0.89
#                                 },
#                                 {
#                                     "analysis_time": "20220514",
#                                     "analysis_value": 0.92
#                                 },
#                                 {
#                                     "analysis_time": "20220515",
#                                     "analysis_value": 0.91
#                                 },
#                                 {
#                                     "analysis_time": "20220516",
#                                     "analysis_value": 0.88
#                                 },
#                                 {
#                                     "analysis_time": "20220517",
#                                     "analysis_value": 0.96
#                                 }
#                             ]
#                         }
#                     ],
#                     "total_result": {
#                         "task_name": "置信度定量分析任务",
#                         "jiancelv_benci": 0.89,
#                         "jiancelv_lishi": 0.86,
#                         "jiancelv_yuzhi": 0.95,
#                         "jiancelv_result": "调优"
#                     },
#                     "association_task_result": {
#
#                         "zhibiao_associtaion_task_list": [
#                             {
#                                 "task_name": "定量分析任务4"
#                             },
#                             {
#                                 "task_name": "定量分析任务5"
#                             },
#                             {
#                                 "task_name": "定量分析任务5"
#                             }
#                         ]
#                     }
#                 }
#             }
#         ]
#     }
# }
#                                                 '''
#         res = json.loads(str_test)
#         return res
#
#     # 定量分析结果的模拟结果数据，静态方法
#     @staticmethod
#     def get_QuanAnalysis_Result(analysis_time):
#         zxd_results = "0.96,0.95"
#         data_consistency_results = "0.89,0.92"
#         data_completeness_results = "0.93,0.92"
#         algorithm_satisfaction_results = "0.98,0.97"
#
#         sample_target_detail = {}
#         attribute_info_list = []
#         attribute_info = {}
#         attribute_info["attribute_name"] = "分辨率"
#         attribute_info["feature_list"] = "0.5米,0.8米"
#         attribute_info_list.append(attribute_info)
#         attribute_info = {}
#         attribute_info["attribute_name"] = "载荷"
#         attribute_info["feature_list"] = "可见光,SAR"
#         attribute_info_list.append(attribute_info)
#         sample_target_detail["attribute_info"] = attribute_info_list
#         target_info_list = []
#         target_info = {}
#         target_info["target_name"] = "战斗机"
#         target_info["pattern_name"] = "F12,F13"
#         target_info_list.append(target_info)
#         target_info = {}
#         target_info["target_name"] = "轰炸机"
#         target_info["pattern_name"] = "B2,B3"
#         target_info_list.append(target_info)
#         sample_target_detail["target_info"] = target_info_list
#
#         results_json = {}
#         body_json = {}
#         body_json["analysis_time"] = analysis_time
#         body_json["zxd_result"] = zxd_results
#         body_json["data_consistency_result"] = data_consistency_results
#         body_json["data_completeness_result"] = data_completeness_results
#         body_json["algorithm_satisfaction_result"] = algorithm_satisfaction_results
#         body_json["sample_analysis_info"] = sample_target_detail
#         results_json["results"] = body_json
#         res = results_json
#         return res, zxd_results, data_consistency_results, data_completeness_results, algorithm_satisfaction_results
#
#     # 置信区间计算的模拟结果数据，静态方法
#     @staticmethod
#     def get_RangeCompute_Result():
#         results_json = {}
#         body_array = []
#         body_json = {}
#         body_json["evaluation_index_cname"] = "检测率"
#         body_json["evaluation_index_ename"] = "clc_detection_rate"
#         body_json["left_range_result"] = 0.87
#         body_json["right_range_result"] = 0.88
#         body_json["significant_level"] = 0.05
#         body_json["curve_x_axis_values"] = "0.816,0.826,0.836,0.846,0.886,0.896,0.926,0.956"
#         body_json["curve_y_axis_values"] = "0.09,0.10,0.27,0.09,0.25,0.07,0.04,0.09"
#         body_array.append(body_json)
#         body_json = {}
#         body_json["evaluation_index_cname"] = "识别率"
#         body_json["evaluation_index_ename"] = "od_recognition_rate"
#         body_json["left_range_result"] = 0.75
#         body_json["right_range_result"] = 0.77
#         body_json["significant_level"] = 0.05
#         body_json["curve_x_axis_values"] = "0.425,0.683,0.725,0.785,0.825,0.826,0.885,0.925"
#         body_json["curve_y_axis_values"] = "0.06,0.09,0.01,0.22,0.29,0.10,0.11,0.11"
#         body_array.append(body_json)
#         results_json["results"] = body_array
#         res = results_json
#         analysis_results = "检测率:0.87-0.88;识别率:0.75-0.77"
#         all_zxd_result_str = '''
#         {"zxd_range": [{"evaluation_index_cname": "检测率", "evaluation_index_ename": "clc_detection_rate", "curve_x_axis_values": "0.836,0.826,0.846,0.886,0.956,0.926,0.816,0.896", "curve_y_axis_values": "0.27,0.10,0.09,0.25,0.09,0.04,0.09,0.07", "left_range_result": 0.87, "right_range_result": 0.88, "significant_level": 0.05}, {"evaluation_index_cname": "识别率", "evaluation_index_ename": "od_recognition_rate", "curve_x_axis_values": "0.785,0.826,0.683,0.885,0.925,0.825,0.425,0.725", "curve_y_axis_values": "0.22,0.10,0.09,0.11,0.11,0.29,0.06,0.01", "left_range_result": 0.75, "right_range_result": 0.77, "significant_level": 0.05}, {"evaluation_index_cname": "漏检率", "evaluation_index_ename": "clc_recall_missingrate", "curve_x_axis_values": "0.087,0.167,0.113,0.097,0.077,0.057,0.117,0.066", "curve_y_axis_values": "0.13,0.15,0.15,0.16,0.17,0.08,0.15,0.02", "left_range_result": 0.1, "right_range_result": 0.1, "significant_level": 0.05}, {"evaluation_index_cname": "虚警率", "evaluation_index_ename": "clc_false_alarm", "curve_x_axis_values": "0.097,0.077,0.087,0.167,0.057,0.117,0.066,0.053,0.113", "curve_y_axis_values": "0.15,0.13,0.10,0.11,0.08,0.13,0.03,0.12,0.13", "left_range_result": 0.09, "right_range_result": 0.09, "significant_level": 0.05}, {"evaluation_index_cname": "f1分数", "evaluation_index_ename": "clc_f_score", "curve_x_axis_values": "0.866,0.449,0.926,0.636,0.826,0.684", "curve_y_axis_values": "0.01,0.94,0.01,0.01,0.01,0.01", "left_range_result": 0.72, "right_range_result": 0.74, "significant_level": 0.05}, {"evaluation_index_cname": "ROC曲线-AUC值", "evaluation_index_ename": "od_roc_curve", "curve_x_axis_values": "0.683,0.825,0.73,0.684,0.925,0.926,0.785,0.885,0.826", "curve_y_axis_values": "0.12,0.26,0.12,0.03,0.08,0.01,0.13,0.11,0.12", "left_range_result": 0.8, "right_range_result": 0.81, "significant_level": 0.05}, {"evaluation_index_cname": "PR曲线-AUC值", "evaluation_index_ename": "od_pr_curve", "curve_x_axis_values": "0.866,0.87,0.926,0.636,0.826,0.684", "curve_y_axis_values": "0.01,0.94,0.01,0.01,0.01,0.01", "left_range_result": 0.79, "right_range_result": 0.81, "significant_level": 0.05}, {"evaluation_index_cname": "鲁棒性", "evaluation_index_ename": "od_robustness", "curve_x_axis_values": "0.79,0.997,0.89,0.684,0.876,0.69,0.984,0.816,0.846,0.9,0.926,0.826", "curve_y_axis_values": "0.04,0.17,0.16,0.21,0.08,0.07,0.03,0.03,0.03,0.08,0.08,0.01", "left_range_result": 0.85, "right_range_result": 0.86, "significant_level": 0.05}]}
#         '''
#         all_zxd_result = json.loads(all_zxd_result_str)
#         return res, analysis_results, all_zxd_result
#
#     # 模拟仿真计算的模拟结果数据，静态方法
#     @staticmethod
#     def get_Simuluation_Result(zxd_model_name, evaluation_algorithm_name, zxd_formula_weight1, zxd_formula_weight2,
#                                zxd_formula_weight3, target_name, analysis_time, evaluation_index_cnames,
#                                evaluation_index_enames):
#         zxd_results = 0.8
#         data_consistency_results = 0.9
#         data_completeness_results = 0.76
#         algorithm_satisfaction_results = 0.83
#
#         results_json = {}
#         all_body_json = {}
#         zxd_analysis_info_json = {}
#         zxd_analysis_info_json["zxd_model_name"] = str(zxd_model_name)
#         zxd_analysis_info_json["zxd_model_version"] = "V1.0"
#         zxd_analysis_info_json["algorithm_name"] = str(evaluation_algorithm_name)
#         zxd_analysis_info_json["algorithm_versione"] = "V1.0"
#         zxd_analysis_info_json["zxd_formula_weight1"] = str(zxd_formula_weight1)
#         zxd_analysis_info_json["zxd_formula_weight2"] = str(zxd_formula_weight2)
#         zxd_analysis_info_json["zxd_formula_weight3"] = str(zxd_formula_weight3)
#         zxd_analysis_info_json["simuluation_data_sets"] = ""
#         zxd_analysis_info_json["simuluation_data_attribute_features"] = ""
#         zxd_analysis_info_json["target_name"] = str(target_name)
#         zxd_analysis_info_json["analysis_result"] = zxd_results
#         zxd_analysis_info_json["data_consistency_result"] = data_consistency_results
#         zxd_analysis_info_json["data_completeness_result"] = data_completeness_results
#         zxd_analysis_info_json["algorithm_satisfaction_result"] = algorithm_satisfaction_results
#         zxd_analysis_info_json["analysis_time"] = analysis_time
#
#         sample_target_detail = {}
#         attribute_info_list = []
#         attribute_info = {}
#         attribute_info["attribute_name"] = "分辨率"
#         attribute_info["feature_list"] = "0.5米,0.8米"
#         attribute_info_list.append(attribute_info)
#         attribute_info = {}
#         attribute_info["attribute_name"] = "载荷"
#         attribute_info["feature_list"] = "可见光,SAR"
#         attribute_info_list.append(attribute_info)
#         sample_target_detail["attribute_info"] = attribute_info_list
#         target_info_list = []
#         target_info = {}
#         target_info["target_name"] = "战斗机"
#         target_info["pattern_name"] = "F12,F13"
#         target_info_list.append(target_info)
#         target_info = {}
#         target_info["target_name"] = "轰炸机"
#         target_info["pattern_name"] = "B2,B3"
#         target_info_list.append(target_info)
#         sample_target_detail["target_info"] = target_info_list
#         zxd_analysis_info_json["sample_analysis_info"] = sample_target_detail
#         all_body_json["zxd_analysis_info"] = zxd_analysis_info_json
#
#         range_analysis_info_json = {}
#         range_analysis_info_json["algorithm_name"] = str(evaluation_algorithm_name)
#         body_array = []
#         body_json = {}
#         body_json["evaluation_index_cname"] = str(evaluation_index_cnames.split(",")[0])
#         body_json["evaluation_index_ename"] = str(evaluation_index_enames.split(",")[0])
#         body_json["left_range_result"] = 0.86
#         body_json["right_range_result"] = 0.87
#         body_json["significant_level"] = 0.05
#         body_json[
#             "curve_x_axis_values"] = "0.684,0.69,0.784,0.79,0.816,0.826,0.836,0.846,0.866,0.874,0.876,0.886,0.896,0.916,0.926,0.936,0.956,0.984,0.996"
#         body_json[
#             "curve_y_axis_values"] = "0.02,0.01,0.01,0.01,0.06,0.05,0.38,0.06,0.01,0.01,0.01,0.18,0.04,0.02,0.06,0.01,0.05,0.01,0.01"
#         body_array.append(body_json)
#         body_json = {}
#         body_json["evaluation_index_cname"] = str(evaluation_index_cnames.split(",")[1])
#         body_json["evaluation_index_ename"] = str(evaluation_index_enames.split(",")[1])
#         body_json["left_range_result"] = 0.8
#         body_json["right_range_result"] = 0.82
#         body_json["significant_level"] = 0.05
#         body_json[
#             "curve_x_axis_values"] = "0.425,0.683,0.684,0.69,0.725,0.784,0.785,0.79,0.816,0.825,0.826,0.836,0.846,0.866,0.874,0.876,0.885,0.925,0.936,0.984,0.996"
#         body_json[
#             "curve_y_axis_values"] = "0.11,0.07,0.02,0.01,0.01,0.01,0.16,0.01,0.01,0.25,0.07,0.04,0.01,0.02,0.01,0.01,0.09,0.09,0.01,0.01,0.01"
#         body_array.append(body_json)
#         range_analysis_info_json["analysis_result"] = body_array
#         all_body_json["range_analysis_info"] = range_analysis_info_json
#
#         results_json["results"] = all_body_json
#         res = results_json
#         analysis_results = "{}:0.8-0.9;{}:0.75-0.8".format(str(evaluation_index_cnames.split(",")[0]),
#                                                            str(evaluation_index_cnames.split(",")[1]))
#
#         all_zxd_result_str = '''
#         {"data_consistency_result": 0.375, "data_completeness_result": 0.063, "algorithm_satisfaction_result": 0.388889, "zxd_result": 0.504267, "zxd_range": [{"evaluation_index_cname": "检测率", "evaluation_index_ename": "clc_detection_rate", "curve_x_axis_values": "0.836,0.866,0.936,0.79,0.984,0.996,0.816,0.846,0.684,0.926,0.876,0.826,0.874,0.886,0.896,0.916,0.956,0.69,0.784", "curve_y_axis_values": "0.38,0.01,0.01,0.01,0.01,0.01,0.06,0.06,0.02,0.06,0.01,0.05,0.01,0.18,0.04,0.02,0.05,0.01,0.01", "left_range_result": 0.86, "right_range_result": 0.87, "significant_level": 0.05}, {"evaluation_index_cname": "识别率", "evaluation_index_ename": "od_recognition_rate", "curve_x_axis_values": "0.836,0.425,0.866,0.936,0.79,0.984,0.825,0.996,0.785,0.846,0.684,0.925,0.876,0.826,0.874,0.885,0.683,0.725,0.69,0.816,0.784", "curve_y_axis_values": "0.04,0.11,0.02,0.01,0.01,0.01,0.25,0.01,0.16,0.01,0.02,0.09,0.01,0.07,0.01,0.09,0.07,0.01,0.01,0.01,0.01", "left_range_result": 0.8, "right_range_result": 0.82, "significant_level": 0.05}, {"evaluation_index_cname": "漏检率", "evaluation_index_ename": "clc_recall_missingrate", "curve_x_axis_values": "0.096,0.067,0.077,0.09,0.167,0.79,0.117,0.087,0.089,0.068,0.093,0.079,0.097,0.113,0.057,0.066", "curve_y_axis_values": "0.01,0.09,0.11,0.03,0.15,0.02,0.14,0.11,0.03,0.01,0.02,0.02,0.11,0.12,0.04,0.02", "left_range_result": 0.12, "right_range_result": 0.15, "significant_level": 0.05}, {"evaluation_index_cname": "虚警率", "evaluation_index_ename": "clc_false_alarm", "curve_x_axis_values": "0.084,0.053,0.09,0.167,0.113,0.068,0.078,0.117,0.097,873636.0,0.077,0.057,0.087,0.066,0.064", "curve_y_axis_values": "0.04,0.19,0.02,0.12,0.12,0.02,0.02,0.09,0.11,0.02,0.11,0.04,0.07,0.02,0.01", "left_range_result": 41263.72, "right_range_result": 75221.24, "significant_level": 0.05}, {"evaluation_index_cname": "f1分数", "evaluation_index_ename": "clc_f_score", "curve_x_axis_values": "0.836,0.449,0.866,0.936,0.79,0.984,0.996,0.846,0.684,0.926,0.876,0.874,0.636,0.69,0.816,0.826,0.784", "curve_y_axis_values": "0.04,0.82,0.02,0.01,0.01,0.01,0.01,0.01,0.02,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01", "left_range_result": 0.8, "right_range_result": 0.82, "significant_level": 0.05}, {"evaluation_index_cname": "ROC曲线-AUC值", "evaluation_index_ename": "od_roc_curve", "curve_x_axis_values": "0.836,0.73,0.866,0.936,0.79,0.984,0.684,0.996,0.825,0.846,0.926,0.876,0.785,0.874,0.683,0.885,0.826,0.925,0.636,0.69,0.816,0.784", "curve_y_axis_values": "0.04,0.12,0.02,0.01,0.01,0.01,0.05,0.01,0.25,0.01,0.01,0.01,0.16,0.01,0.07,0.05,0.06,0.08,0.01,0.01,0.01,0.01", "left_range_result": 0.82, "right_range_result": 0.83, "significant_level": 0.05}, {"evaluation_index_cname": "PR曲线-AUC值", "evaluation_index_ename": "od_pr_curve", "curve_x_axis_values": "0.836,0.87,0.866,0.936,0.79,0.984,0.996,0.846,0.684,0.926,0.876,0.874,0.636,0.69,0.816,0.826,0.784", "curve_y_axis_values": "0.04,0.82,0.02,0.01,0.01,0.01,0.01,0.01,0.02,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01", "left_range_result": 0.83, "right_range_result": 0.84, "significant_level": 0.05}, {"evaluation_index_cname": "鲁棒性", "evaluation_index_ename": "od_robustness", "curve_x_axis_values": "0.836,0.997,0.866,0.936,0.79,0.984,0.996,0.846,0.684,0.926,0.876,0.874,0.89,0.69,0.816,0.9,0.826,0.784", "curve_y_axis_values": "0.04,0.24,0.01,0.01,0.04,0.04,0.01,0.04,0.18,0.06,0.07,0.01,0.11,0.06,0.03,0.06,0.02,0.01", "left_range_result": 0.86, "right_range_result": 0.87, "significant_level": 0.05}]}
#         '''
#         all_zxd_result = json.loads(all_zxd_result_str)
#         return res, zxd_results, data_consistency_results, data_completeness_results, algorithm_satisfaction_results, analysis_results, all_zxd_result
#
#     # 典型任务分析的模拟结果数据，静态方法
#     @staticmethod
#     def get_TypicalAnalysis_Result():
#         str_test = '''
#
#         {
#             "results": {
#                 "task_info": {
#                     "task_name": "典型任务分析",
#                     "task_create_time": "2022-05-10 10:20:18",
#                     "task_analysis_time": "2022-05-12 10:20:18",
#                     "task_desc": "典型任务分析描述"
#                 },
#                 "sample_info": {
#                     "payload_info": [{
#                             "payload_type": "可见光",
#                             "payload_num": 12,
#                             "payload_percent": 0.21
#                         },
#                         {
#                             "payload_type": "SAR",
#                             "payload_num": 20,
#                             "payload_percent": 0.36
#                         },
#                         {
#                             "payload_type": "热红外",
#                             "payload_num": 15,
#                             "payload_percent": 0.37
#                         }
#                     ],
#                     "target_info": [{
#                             "target_name": "战斗机",
#                             "target_num": 40,
#                             "target_percent": 0.4
#                         },
#                         {
#                             "target_name": "运输机",
#                             "target_num": 40,
#                             "target_percent": 0.4
#                         },
#                         {
#                             "target_name": "轰炸机",
#                             "target_num": 30,
#                             "target_percent": 0.3
#                         }
#
#                     ]
#                 },
#                 "quant_analysis_info": [{
#                     "algorithm_name": "目标机识别算法1",
#                     "confidence_result": 0.8,
#                     "data_consistency_result": 0.9,
#                     "data_completeness_result": 0.76,
#                     "algorithm_satisfaction_result": 0.83
#                 }, {
#                     "algorithm_name": "目标识别算法2",
#                     "confidence_result": 0.87,
#                     "data_consistency_result": 0.9,
#                     "data_completeness_result": 0.8,
#                     "algorithm_satisfaction_result": 0.63
#                 }, {
#                     "algorithm_name": "目标识别算法3",
#                     "confidence_result": 0.85,
#                     "data_consistency_result": 0.8,
#                     "data_completeness_result": 0.76,
#                     "algorithm_satisfaction_result": 0.53
#                 }],
#                 "range_analysis_info": [{
#                         "algorithm_name": "目标识别算法1",
#                         "analysis_result": [{
#                                 "evaluation_index_cname": "检测率",
#                                 "evaluation_index_ename": "clc_detection_rate",
#                                 "left_range_result": 0.87,
#                                 "right_range_result": 0.88,
#                                 "significant_level": 0.05,
#                                 "curve_x_axis_values": "0.816,0.826,0.836,0.846,0.886,0.896,0.926,0.956",
#                                 "curve_y_axis_values": "0.09,0.10,0.27,0.09,0.25,0.07,0.04,0.09"
#                             },
#                             {
#                                 "evaluation_index_cname": "识别率",
#                                 "evaluation_index_ename": "od_recognition_rate",
#                                 "left_range_result": 0.75,
#                                 "right_range_result": 0.77,
#                                 "significant_level": 0.05,
#                                 "curve_x_axis_values": "0.425,0.683,0.725,0.785,0.825,0.826,0.885,0.925",
#                                 "curve_y_axis_values": "0.06,0.09,0.01,0.22,0.29,0.10,0.11,0.11"
#                             }
#                         ]
#                     },
#                     {
#                         "algorithm_name": "目标识别算法2",
#                         "analysis_result": [{
#                                 "evaluation_index_cname": "检测率",
#                                 "evaluation_index_ename": "clc_detection_rate",
#                                 "left_range_result": 0.87,
#                                 "right_range_result": 0.88,
#                                 "significant_level": 0.05,
#                                 "curve_x_axis_values": "0.836,0.826,0.846,0.886,0.956,0.926,0.816,0.896",
#                                 "curve_y_axis_values": "0.27,0.10,0.09,0.25,0.09,0.04,0.09,0.07"
#                             },
#                             {
#                                 "evaluation_index_cname": "识别率",
#                                 "evaluation_index_ename": "od_recognition_rate",
#                                 "left_range_result": 0.75,
#                                 "right_range_result": 0.77,
#                                 "significant_level": 0.05,
#                                 "curve_x_axis_values": "0.785,0.826,0.683,0.885,0.925,0.825,0.425,0.725",
#                                 "curve_y_axis_values": "0.22,0.10,0.09,0.11,0.11,0.29,0.06,0.01"
#                             }
#                         ]
#                     }, {
#                         "algorithm_name": "目标识别算法3",
#                         "analysis_result": [{
#                                 "evaluation_index_cname": "检测率",
#                                 "evaluation_index_ename": "clc_detection_rate",
#                                   "left_range_result": 0.87,
#                                 "right_range_result": 0.88,
#                                 "significant_level": 0.05,
#                                 "curve_x_axis_values": "0.836,0.826,0.846,0.886,0.956,0.926,0.816,0.896",
#                                 "curve_y_axis_values": "0.27,0.10,0.09,0.25,0.09,0.04,0.09,0.07"
#                             },
#                             {
#                                 "evaluation_index_cname": "识别率",
#                                 "evaluation_index_ename": "od_recognition_rate",
#                                 "left_range_result": 0.75,
#                                 "right_range_result": 0.77,
#                                 "significant_level": 0.05,
#                                 "curve_x_axis_values": "0.785,0.826,0.683,0.885,0.925,0.825,0.425,0.725",
#                                 "curve_y_axis_values": "0.22,0.10,0.09,0.11,0.11,0.29,0.06,0.01"
#                             }
#                         ]
#                     }
#
#                 ],
#                 "image_enhance_info": [{
#                     "image_enhance_type": "去薄云雾",
#                     "image_enhance_result": {
#                         "boyunwu_removal_rate_correct": 0.8,
#                         "boyunwu_removal_rate_error": 0.2,
#
#                         "image_info": [{
#                             "before_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_input?gridSet=EPSG:4326&format=image/png",
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }, {
#                             "before_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_input?gridSet=EPSG:4326&format=image/png",
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }]
#                     }
#                 }, {
#                     "image_enhance_type": "超分重建",
#                     "image_enhance_result": {
#                         "resolution_improve": 1.5,
#                         "structural_similarity": 0.98,
#                         "feature_similarity": 0.76,
#                         "image_info": [{
#                             "before_image_wms_url": [{
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }, {
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }],
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }, {
#                             "before_image_wms_url": [{
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }, {
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }],
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }]
#                     }
#                 }],
#                 "total_result": {
#                     "task_name": "典型任务分析",
#                     "chaofen_chongjian_num": 35,
#                     "qu_boyunwu_num": 23,
#                      "shibielv_result": [
#                                 {
#                                     "algorithm_name": "目标识别算法2",
#                                     "algorithm_change": "低"
#                                 },
#                                 {
#                                     "algorithm_name": "目标识别算法1",
#                                     "algorithm_change": "低"
#                                 }
#                             ],
#                     "tuxiang_zhiliang_reulst": "提升"
#                 }
#             }
#         }
#                                   '''
#         res = json.loads(str_test)
#         return res
#
#     # 图像增强任务的模拟结果数据，静态方法
#     @staticmethod
#     def get_ImageEnhance_Result():
#         str_test = '''
#
#         {
#             "results": {
#                 "task_info": {
#                     "task_name": "典型任务图像增强分析",
#                     "task_create_time": "2022-05-10 10:20:18",
#                     "task_analysis_time": "2022-05-12 10:20:18",
#                     "task_desc": "典型任务图像增强分析描述"
#                 },
#                 "image_enhance_info": [{
#                     "image_enhance_type": "去薄云雾",
#                     "image_enhance_result": {
#                         "boyunwu_removal_rate_correct": 0.8,
#                         "boyunwu_removal_rate_error": 0.2,
#
#                         "image_info": [{
#                             "before_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_input?gridSet=EPSG:4326&format=image/png",
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }, {
#                             "before_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_input?gridSet=EPSG:4326&format=image/png",
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:qyw_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }]
#                     }
#                 }, {
#                     "image_enhance_type": "超分重建",
#                     "image_enhance_result": {
#                         "resolution_improve": 1.5,
#                         "structural_similarity": 0.98,
#                         "feature_similarity": 0.76,
#                         "image_info": [{
#                             "before_image_wms_url": [{
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }, {
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }],
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }, {
#                             "before_image_wms_url": [{
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }, {
#                                 "url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_input?gridSet=EPSG:4326&format=image/png"
#                             }],
#                             "after_image_wms_url": "http://''' + settings.KEH_GEOSERVER + '''/geoserver/gwc/demo/KSHFXT:cf_kjg_output?gridSet=EPSG:4326&format=image/png"
#                         }]
#                     }
#                 }],
#                 "total_result": {
#                     "task_name": "典型任务分析",
#                     "chaofen_chongjian_num": 35,
#                     "qu_boyunwu_num": 23,
#                     "shibielv_result": "提升",
#                     "tuxiang_zhiliang_reulst": "提升"
#                 }
#             }
#         }
#
#                                   '''
#         res = json.loads(str_test)
#         return res
#
#     @staticmethod
#     # 生成评估数据表内容
#     def build_evaluation_table_data(task_id_list, target_name_list, target_id_list, db_conn_str, excel_path):
#         conn = psycopg2.connect(db_conn_str)
#         cursor = conn.cursor()
#         # 先清空数据表
#         # sql = "delete from tt_zxd_task_evaluation_result"
#         # cursor.execute(sql)
#         # 循环任务列表，获取每个任务的数据ID
#         # 循环任务列表，获取每个任务的算法code
#         # 循环每个任务每个算法，并用一个随机的数据id，读取excel数据，生成要插入评价的表的一条sql,excel里的count指标随机增加0-2
#         for task_id in task_id_list:
#             print("任务编号：" + str(task_id))
#             # 获取每个任务的数据ID
#             data_id_list = []
#             sql = "select data_id from tt_zxd_task_data_set "
#             sql += " where 1=1 "
#             sql += " and task_id =" + str(task_id)
#             sql += " and node_code in ("
#             sql += " select node_code from tt_zxd_task_node where task_id=" + str(task_id) + " and type=2"
#             sql += ")"
#             cursor.execute(sql)
#             records = cursor.fetchall()
#             for record in records:
#                 data_id = str(record[0])
#                 data_id_list.append(data_id)
#             # 获取每个任务的算法code
#             alg_node_list = []
#             alg_id_list = []
#             alg_type_list = []
#             alg_name_list = []
#             sql = "  select node_code, algorithm_id, algorithm_type, algorithm_name from tt_zxd_task_algorithm "
#             sql += " where 1=1 "
#             sql += " and algorithm_type in (1, 2,3,4)"
#             sql += " and data_set_node_code in ("
#             sql += " select node_code from tt_zxd_task_node where task_id=" + str(task_id) + " and type=2"
#             sql += ")"
#             cursor.execute(sql)
#             records = cursor.fetchall()
#             for record in records:
#                 alg_node_list.append(str(record[0]))
#                 alg_id_list.append(str(record[1]))
#                 alg_type_list.append(str(record[2]))
#                 alg_name_list.append(str(record[3]))
#             # 并用一个随机的数据id，读取excel数据，生成要插入评价的表的一条sql, excel里的count指标随机增加0 - 2
#             for index in range(len(alg_node_list)):
#                 alg_id = alg_id_list[index]
#                 alg_name = alg_name_list[index]
#                 alg_node = alg_node_list[index]
#                 alg_type = alg_type_list[index]
#                 print("算法ID:" + str(alg_id))
#                 data_id_random_index = random.randint(0, len(data_id_list) - 1)
#                 data_id = data_id_list[data_id_random_index]
#                 # 循环目标
#                 for tt in range(len(target_name_list)):
#                     target_name = target_name_list[tt]
#                     target_id = target_id_list[tt]
#                     print("目标名称:" + str(target_name))
#                     # 读取excel
#                     excel_data = pd.read_excel(excel_path, sheet_name="Sheet3")
#                     for row_index in range(len(excel_data)):
#                         # excel内容从第二行开始
#                         row_values = excel_data.values[row_index]
#                         now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                         countvalue = int(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "count"))
#                         addvalue = random.randint(0, 2)
#                         countvalue = countvalue + addvalue
#                         insert_sql = "INSERT INTO tt_zxd_task_evaluation_result_2(task_id, data_set_type, data_set_name, data_id, data_name, sample_thumb_url, sample_tif_url, sample_xml_url, algorithm_node_id, target_name, coords, precision, date, create_time, update_time, sample_name, start_time, end_time, od_compatible_detection_rate, clc_recognition_rate, od_compatible_missing_rate, od_compatible_false_alarm, od_compatible_f_score, od_roc_curve, od_pr_curve, dh_grad, dh_uge, dh_acc, dh_err, dh_resolution, dh_threshold, dh_trans_coef, sr_bitdepth, sr_pxresolution, sr_mse, class_sr_psnr, sr_ssim, sr_fsim, sr_corr, od_compatible_recall, od_compatible_precision, mbbh_detection_rate, mbbh_missing_rate, mbbh_false_alarm, sr_co, sr_pur, sr_grad, sr_uge,dz_recognition_rate,dz_missing_rate,dz_false_alarm,dz_detection_rate,ssbh_missing_rate,ssbh_false_alarm,ssbh_detection_rate,algorithm_id, algorithm_name, target_id, algorithm_type_id) VALUES ( {}, NULL, NULL, {}, NULL, NULL, NULL, NULL, {}, {}, NULL, NULL, NULL, {}, NULL, NULL, NULL, NULL, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{}, {},{},{},{},{},{},{},{},{},{})".format(
#                             task_id, data_id, "\'" + str(alg_node) + "\'", "\'" + str(target_name) + "\'",
#                                               "\'" + str(now_time) + "\'",
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "od_compatible_detection_rate")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                                "clc_recognition_rate")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "od_compatible_missing_rate")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "od_compatible_false_alarm")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "od_compatible_f_score")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "od_roc_curve")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "od_pr_curve")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "dh_grad")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dh_uge")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dh_acc")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dh_err")),
#                             int(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "dh_resolution")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dh_threshold")),
#                             int(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dh_trans_coef")),
#                             int(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "sr_bitdepth")),
#                             int(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "sr_pxresolution")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "sr_mse")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "class_sr_psnr")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "sr_ssim")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "sr_fsim")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "sr_corr")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "od_compatible_recall")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "od_compatible_precision")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index,
#                                                                              "mbbh_detection_rate")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "mbbh_missing_rate")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "mbbh_false_alarm")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "sr_co")),
#                             float(
#                                 ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "sr_pur")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "sr_grad")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "sr_uge")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dz_recognition_rate")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dz_missing_rate")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dz_false_alarm")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "dz_detection_rate")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "ssbh_missing_rate")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "ssbh_false_alarm")),
#                             float(ExcelHelper.get_field_value_by_name_in_excel(excel_data, row_index, "ssbh_detection_rate")),
#                                               "\'" + str(alg_id) + "\'",
#                                               "\'" + str(alg_name) + "\'", target_id, alg_type)
#                         for i in range(countvalue):
#                             print(insert_sql)
#                             cursor.execute(insert_sql)
#                             conn.commit()
#
#
# if __name__ == '__main__':
#     task_id_list = [232642081485623300, 233757351084167170, 256261950026158080]
#     # db_conn_str = "host=111.59.30.31 dbname=YSYZ_ZXD user=postgres password=vgis543^&*"
#     # db_conn_str = "host=10.18.10.110 dbname=YSYZ_ZXD user=postgres password=postgresql123"
#     db_conn_str = "host=192.168.3.191 dbname=YSYZ_ZXD user=postgres password=postgres123"
#     excel_path = "E:\\tt_zxd_task_evaluation_result-bak-10W.xls"
#     target_name_list = ["飞机类", "舰船类"]
#     target_id_list = [1, 2]
#     MockHelper.build_evaluation_table_data(task_id_list, target_name_list, target_id_list, db_conn_str, excel_path)

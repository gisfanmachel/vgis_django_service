/*
 * @Author: your name
 * @Date: 2021-05-10 19:21:24
 * @LastEditTime: 2022-03-21 10:30:58
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \qcn_front\public\config\index.js
 */
window.config = {
    "API_SERVER_URL": "http://192.168.3.191:8086/qcn", //API服务地址
    "GEO_SERVER": "http://192.168.3.191:8085/geoserver/qcn/wms?", //GeoServer服务地址头
    "ONlinePreview": "http://192.168.3.191:8014/onlinePreview?", //在线文档浏览kkviewer请求头
    "SCREEN_SERVER": "http://192.168.3.191:8889", //大屏展示服务地址
    "GOOFLOW": "http://192.168.3.191:8086/dist/gooflow", //工作流服务地址
    "SAT_CENTER_MAP": "http://satmap.sasclouds.com/OneMap2019/wms?", //卫星中心2019年2米影像WMS地址头,有水印
    "GPMODELDER": "http://192.168.3.191:8086/dist/gpmodeler", //工作流服务地址surmapiserver
    "ISERVER": "http://192.168.3.191:8090/iserver", //iserver服务地址
    "ISERVER_NAME": "root", // iserver 用户名
    "ISERVER_PASS": "Root12345", // iserver 密码
    "ISERVER_SOURCEDATASERVER": "/app/qcn/model/", // iserver数据源地址
    "ISERVER_SOURCEDATADBTYPE": "udbx", // iserver数据源类型
    "ISERVER_SOURCEDATAALIASE": "dataServer", // iserver数据源类型aliase混叠
    "ISERVER_SOURCEDATAPROVIDERTYPE": "sdx", // iserver数据源类型providertype指针类型
    "ISERVER_EXPORTPATH": "/www/upload/microservice/qcn/web/model/", // 导出地址路径 linux为上传的路径 www/upload/ 和后台的路径对应上
    "MONGOMAP_SERVER": "http://192.168.3.191:9090", //API服务地址头
    "USE_INTRANET_MAP": false, //是否使用内网地图服务
    "ISENCRYPT": false, //请求参数是否加密
    // "timeout": 10000, //超时时间
}
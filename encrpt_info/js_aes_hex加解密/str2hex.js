// 字符串转二进制再转十六进制
function stringToHex(text){
　　 var encoder = new TextEncoder();
    var arrayBuffer = encoder.encode(text);
    // 将字符串转二进制
    var binaryString = Array.from(new Uint8Array(arrayBuffer)).map(b => b.toString(2)).join(" ");
    // console.log(binaryString);
    binaryStringArray = binaryString.split(" ")
    hexString = ""
    for (var i = 0; i < binaryStringArray.length; i++) {
        var a = binaryStringArray[i]
        // 二进制转十进制
        var b = parseInt(a, 2)
        // 十进制转十六进制
        c = b.toString(16)
        // console.log(c)
        hexString += c
    }
    // console.log(hexString)
    return hexString
}


// 十六进制转二进制再转字符串
function hexToString(hexString){
    var decodeStr=""
    var pairsArray = splitStringIntoPairs(hexString);
    for (var i = 0; i < pairsArray.length; i++) {
        var hexValue = pairsArray[i]
        var binaryValue = hexToBinary(hexValue)
        var stringValue = binaryToString(binaryValue)
        decodeStr+=stringValue
    }
    // console.log(decodeStr)　　　
    return decodeStr
}

// 对字符串进行两个字符一组分割成数组
function splitStringIntoPairs(str) {
        // 使用正则表达式匹配每两个字符为一组
        var pairs = str.match(/.{1,2}/g);
        return pairs;
}

// 十六进制转二进制
function hexToBinary(hex) {
    // 移除可能存在的前缀（例如：0x）
    var hex = hex.replace(/^0x/, '');
    // 将十六进制转为整数
    var decimal = parseInt(hex, 16);
    // 将整数转为二进制字符串
    var binary = decimal.toString(2);
    return binary;
}

// 二进制转字符串
function binaryToString(binary) {
    // 将二进制字符串转为整数
    var decimal = parseInt(binary, 2);
    // 将整数转为字符
    var str = String.fromCharCode(decimal);
    return str;
}




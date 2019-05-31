function hrefBack() {
    history.go(-1);
}

// 获取csrf_token
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 获取路径上的键值对的
function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function showErrorMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){});
        },1000)
    });
}

$(document).ready(function(){

    // 判断用户是否登录
    $.get("/api/v1.0/session", function(data){
        if (data.errnum != "0"){
            location.href = "/login.html";
        }
    });

    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    $(".input-daterange").on("changeDate", function(){
        var startDate = $("#start-date").val();
        var endDate = $("#end-date").val();

        if (startDate && endDate && startDate > endDate) {
            showErrorMsg();
        } else {
            var sd = new Date(startDate);
            var ed = new Date(endDate);
            days = (ed - sd)/(1000*3600*24) + 1;
            var price = $(".house-text>p>span").html();
            var amount = days * parseFloat(price);
            $(".order-amount>span").html(amount.toFixed(2) + "(共"+ days +"晚)");
        }
    });

    // 路径上面的键值对
    var queryData = decodeQuery();
    // 从路径上获取房屋id
    var houseId = queryData["house_id"];

    // 获取房屋的信息
    $.get("/api/v1.0/house/" + houseId, function(data){
        if (data.errnum == "0"){
            $(".house-info>img").attr("src", data.data.house.img_urls[0]);
            $(".house-text>h3").html(data.data.house.title);
            // 记住jquery>只能到子元素,不能到子元素的子元素越级
            $(".house-text>p>span").html((data.data.house.price/100.0).toFixed(0));
        }
    });

    // 订单提交
    // on绑定事件
    $(".submit-btn").on("click", function(e){
        if($(".order-amount>span").html()){
            // disabled为true 使当前span标签失效
            $(this).prop("disabled", true);
            var startDate = $("#start-date").val();
            var endDate = $("#end-date").val();
            var data = {
                house_id: houseId,
                start_date: startDate,
                end_date: endDate,
            };

            data = JSON.stringify(data);

            $.ajax({
                url:"/api/v1.0/orders",
                type: "post",
                data: data,
                contentType: "application/json",
                dataType: "json",
                headers: {
                    "X-CSRFToken":getCookie("csrf_token")
                },
                success: function (data) {
                    if (data.errnum == "4101"){
                        // 用户未登录
                        location.href = "/login.html";
                    }else if(data.errnum == "4004"){
                        showErrorMsg("房间已被锁定, 请重新选择日期!");
                    }else if(data.errnum == "0"){
                        location.href = "/orders.html";
                    }
                }
            })
        }
    });
})




// function hrefBack() {
//     history.go(-1);
// }
//
// function getCookie(name) {
//     var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
//     return r ? r[1] : undefined;
// }
//
// function decodeQuery(){
//     var search = decodeURI(document.location.search);
//     return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
//         values = item.split('=');
//         result[values[0]] = values[1];
//         return result;
//     }, {});
// }
//
// function showErrorMsg() {
//     $('.popup_con').fadeIn('fast', function() {
//         setTimeout(function(){
//             $('.popup_con').fadeOut('fast',function(){});
//         },1000)
//     });
// }
//
// $(document).ready(function(){
//     // 判断用户是否登录
//     $.get("/api/v1.0/session", function(data) {
//         if ("0" != data.errnum) {
//             location.href = "/login.html";
//         }
//     }, "json");
//     $(".input-daterange").datepicker({
//         format: "yyyy-mm-dd",
//         startDate: "today",
//         language: "zh-CN",
//         autoclose: true
//     });
//     $(".input-daterange").on("changeDate", function(){
//         var startDate = $("#start-date").val();
//         var endDate = $("#end-date").val();
//
//         if (startDate && endDate && startDate > endDate) {
//             showErrorMsg("日期有误，请重新选择!");
//         } else {
//             var sd = new Date(startDate);
//             var ed = new Date(endDate);
//             days = (ed - sd)/(1000*3600*24) + 1;
//             var price = $(".house-text>p>span").html();
//             var amount = days * parseFloat(price);
//             $(".order-amount>span").html(amount.toFixed(2) + "(共"+ days +"晚)");
//         }
//     });
//
//     var queryData = decodeQuery();
//     var houseId = queryData["house_id"];
//
//     // 获取房屋的基本信息
//     $.get("/api/v1.0/house/" + houseId, function(data){
//         if ("0" == data.errnum) {
//             $(".house-info>img").attr("src", data.data.house.img_urls[0]);
//             $(".house-text>h3").html(data.data.house.title);
//             $(".house-text>p>span").html((data.data.house.price/100.0).toFixed(0));
//         }
//     });
//     // 订单提交
//     $(".submit-btn").on("click", function(e) {
//         if ($(".order-amount>span").html()) {
//             $(this).prop("disabled", true);
//             var startDate = $("#start-date").val();
//             var endDate = $("#end-date").val();
//             var data = {
//                 "house_id":houseId,
//                 "start_date":startDate,
//                 "end_date":endDate
//             };
//             $.ajax({
//                 url:"/api/v1.0/orders",
//                 type:"post",
//                 data: JSON.stringify(data),
//                 contentType: "application/json",
//                 dataType: "json",
//                 headers:{
//                     "X-CSRFToken":getCookie("csrf_token"),
//                 },
//                 success: function (data) {
//                     if ("4101" == data.errnum) {
//                         location.href = "/login.html";
//                     } else if ("4004" == data.errnum) {
//                         showErrorMsg("房间已被抢定，请重新选择日期！");
//                     } else if ("0" == data.errnum) {
//                         location.href = "/orders.html";
//                     }
//                 }
//             });
//         }
//     });
// })
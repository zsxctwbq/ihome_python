$(document).ready(function(){
    // 发布房源只有认证后的用户才可以, 所以先判断用户的实名认证状态
    $.get("/api/v1.0/user/auth", function(data){
        if (data.errnum == "4101"){
            // 用户未登录
            location.href = "/login.html";
        }else if(data.errnum == "0"){
            // 为认证的用户, 在页面中展示认证按钮
            if (!(data.data.real_name && data.data.id_card)){
                $(".auth-warn").show();
                return
            }

            $.get("/api/v1.0/user/houses", function(data){
                if (data.errnum == "0"){
                    $("#houses-list").html(template("houses-list-tmpl", {houses:data.data}))
                }else{
                    $("#houses-list").html(template("houses-list-tmpl", {houses:[]}))
                }
            })
        }
    })
})
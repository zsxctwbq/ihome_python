function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){
    $.get("/api/v1.0/user/auth", function(data){
        if (data.errnum == "4101"){
            // 用户未登录
            location.href = "/login.html";
        }else if(data.errnum == "0"){
            if (data.data.real_name && data.data.id_card){
                  $("#real-name").val(data.data.real_name);
                  $("#id-card").val(data.data.id_card);

                  // 把input框设置为不能更改
                  $("#real-name").prop("disabled", true);
                  $("#id-card").prop("disabled", true);

                  // 隐藏提交按钮
                  $("#form-auth>input[type=submit]").hide();
            }
        }else{
            alert(data.errmsg);
        }
    })

    $("#form-auth").submit(function(e){
        // 阻止表单的默认提交行为
        e.preventDefault();

        // 获取用户填写的真是姓名和身份证信息
        var realName = $("#real-name").val();
        var idCard = $("#id-card").val();

        if (realName == "" || idCard == ""){
            $(".error-msg").show();
            return;
        }

        var params = {
            "real_name": realName,
            "id_card": idCard
        };

        params = JSON.stringify(params);

        $.ajax({
            url:"api/v1.0/user/auth",
            type:"post",
            data:params,
            contentType:"application/json",
            dataType:"json",
            headers:{
                "X-CSRFToken":getCookie("csrf_token")
            },
            success:function(data){
                if (data.ernum == "0"){
                    // 保存成功
                    $(".error-msg").hide();
                    // 显示保存成功的提示信息
                    showSuccessMsg();

                    $("#real-name").prop("disabled", true);
                    $("#id-card").prop("disabled", true);

                    // 隐藏提交按钮
                    $("#form-auth>input[type=submit]").hide();
                }
            }

        })

    })

})


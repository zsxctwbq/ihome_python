function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){

    $.get("api/v1.0/areas", function(data){

        if (data.errnum == "0"){
            var areas = data.data;

            var html = template("area-templ", {areas:areas});

            $("#area-id").html(html);
        }else{
            alert(data.errmsg);
        }

    });

    $("#form-house-info").submit(function(e){
        // 阻止表单的默认提交行为
        e.preventDefault();
        // 获取所有提交的数据
        var data = {};
        $("#form-house-info").serializeArray().map(function(x){
            data[x.name]=x.value;
        });

        // 获取房屋设施的id
        var facility = [];
        $(":checked").each(function(index, x){
            facility[index]=$(x).val();
        });

        // 把获取的设施信息更新到data里
        data.facility = facility;

        $.ajax({
            url:"/api/v1.0/houses/info",
            type:"post",
            contentType:"application/json",
            data:JSON.stringify(data),
            dataType:"json",
            headers:{
                "X-CSRFToken":getCookie("csrf_token")
            },
            success:function(data){
                if (data.errnum == "4101"){
                    // 用户未登录
                    location.href = "/login.html";
                }else if(data.errnum == "0"){
                    // 成功
                    // 隐藏房屋信息表单
                    $("#form-house-info").hide();
                    // 显示房屋图片表单
                    $("#form-house-image").show();
                    // 把房屋id填下到house-id这个input标签里
                    $("#house-id").val(data.data.house_id);
                }else{
                    alert(data.errmsg);
                }
            }
        })

    });

    $("#form-house-image").submit(function(e){
        // 阻止表单的默认提交行为
        e.preventDefault();

        $(this).ajaxSubmit({
            url:"/api/v1.0/houses/image",
            type:"post",
            dataType: "json",
            headers:{
                "X-CSRFToken":getCookie("csrf_token")
            },
            success:function(data){
                if (data.errnum == "4101"){
                    // 用户未登录
                    location.href = "/login.html";
                }else if(data.errnum == "0"){
                    // 成功
                    $(".house-image-cons").append('<img src="' + data.data.image_url + '">');
                }else{
                    alert(data.errmsg);
                }
            }
        })
    })

});
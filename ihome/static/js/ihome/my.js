function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout() {
    $.ajax({
        url:"/api/v1.0/session",
        type:"delete",
        dataType:"json",
        headers:{
            "X-CSRFToken":getCookie("csrf_token")
        },
        success:function(data){
            if(data.errnum == "0"){
                location.href = "/";
            }
        }
    })
}

$(document).ready(function(){
    $.get("/api/v1.0/user", function(data){
        if (data.errnum == "4101"){
            // 用户未登录
            location.href = "/login.html";
        }else if(data.errnum == "0"){
            $("#user-name").text(data.data.name);
            $("#user-mobile").text(data.data.mobile);
            if (data.data.avatar){
                $("#user-avatar").attr("src", data.data.avatar);
            }
        }else{
            alert(data.errmsg);
        }

    })
})
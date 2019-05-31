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
   $.get("/api/v1.0/user", function(data){
       if (data.errnum == "4101"){
           // 用户未登录
           location.href = "/login.html"
       }else if (data.errnum == "0"){
           // 获取用户信息成功
           $("#user-name").val(data.data.name);
           if (data.data.avatar){
               // 头像数据不为空时
               $("#user-avatar").attr("src", data.data.avatar);
           }
       }else{
           alert(data.errmsg);
       }
   });

   $("#form-avatar").submit(function(e){
       // 阻止表单默认行为
       e.preventDefault();

       $(this).ajaxSubmit({
           url:"/api/v1.0/users/avatar",
           type:"post",
           dataType:"json",
           headers:{
               "X-CSRFToken":getCookie("csrf_token")
           },
           success:function(data){
               if (data.errnum == "0"){
                    $("#user-avatar").attr("src", data.data.avatar_user);
                    $("#user-avatar").show();
               }else{
                   alert(data.errmsg);
               }
           }
       })
   })

   $("#form-name").submit(function(e){
       // 阻止表单默认行为
       e.preventDefault();

       var name = $("#user-name").val();

       var params = {
           name:name
       };

       params = JSON.stringify(params)

       $.ajax({
           url:"/api/v1.0/users/name",
           type:"put",
           data:params,
           contentType:"application/json",
           dataType:"json",
           headers:{
               "X-CSRFToken":getCookie("csrf_token")
           },
           success:function(data){
               if (data.errnum == "0"){
                   $("#title-name span").text(data.data.name);
               }else{
                   $(".error-msg").show();
               }
           }
       })

   })

});
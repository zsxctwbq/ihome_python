function hrefBack() {
    history.go(-1);
}

// 解析提取url中的查询字符串参数
function decodeQuery(){
    // 获取路径上的参数
    var search = decodeURI(document.location.search);
    // 按照字符串的方式进行切分, 拿到那个值, 并且转换成js对象
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function(){
    // 获取详情页面要展示的房屋编号
    var queryData = decodeQuery();
    var houseId = queryData["id"];
    // 获取该房屋的详细信息
    $.get("/api/v1.0/house/" + houseId, function(data){

        if (data.errnum =="0" ) {
            $(".swiper-container").html(template("house-image-tmpl", {img_urls:data.data.house.img_urls, price:data.data.house.price}));
            $(".detail-con").html(template("house-detail-tmpl", {house:data.data.house}));
            // data.user_id为访问页面用户,data.data.user_id为房东
            if (data.data.user_id != data.data.house.user_id) {
                $(".book-house").attr("href", "/booking.html?house_id="+ data.data.house.house_id);
                $(".book-house").show();
            }

            var mySwiper = new Swiper ('.swiper-container', {
                loop: true,
                autoplay: 2000,
                autoplayDisableOnInteraction: false,
                pagination: '.swiper-pagination',
                paginationType: 'fraction'
            });
        }
    })

    //     // 获取详情页面要展示的房屋编号
    // var queryData = decodeQuery();
    // var houseId = queryData["id"];
    //
    // // 获取该房屋的详细信息
    // $.get("/api/v1.0/houses/" + houseId, function(resp){
    //     if ("0" == resp.errno) {
    //         $(".swiper-container").html(template("house-image-tmpl", {img_urls:resp.data.house.img_urls, price:resp.data.house.price}));
    //         $(".detail-con").html(template("house-detail-tmpl", {house:resp.data.house}));
    //
    //         // resp.user_id为访问页面用户,resp.data.user_id为房东
    //         if (resp.data.user_id != resp.data.house.user_id) {
    //             $(".book-house").attr("href", "/booking.html?hid="+resp.data.house.hid);
    //             $(".book-house").show();
    //         }
    //         var mySwiper = new Swiper ('.swiper-container', {
    //             loop: true,
    //             autoplay: 2000,
    //             autoplayDisableOnInteraction: false,
    //             pagination: '.swiper-pagination',
    //             paginationType: 'fraction'
    //         });
    //     }
    // })

})

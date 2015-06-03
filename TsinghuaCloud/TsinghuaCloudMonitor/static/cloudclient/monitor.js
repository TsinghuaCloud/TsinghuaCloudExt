{% csrf_token %}
{% load staticfiles %}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
// DONE DJANGO HACK

function get_site_prefix(){
    var href = $(location).attr("href");
    return href
}


function gethost(host_name){
    var prefix = get_site_prefix();
    
	$.ajax({
        type: "POST",
        url: prefix + "hostdetail/", 
        data: { 
        host_name: host_name, 
        },
  });	
}

$(function () {
var csrftoken = getCookie('csrftoken'); 
  $('.detail').click(function(event,ui){
     $(this).addClass('select');
     var host_name=$('.select').text();
     $(this).removeClass('select');
     gethost(host_name);
    
  });
      $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    // END DJANGO AJAX
   
});


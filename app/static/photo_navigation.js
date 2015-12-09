document.onkeydown = checkKey;

function checkKey(e) {

    e = e || window.event;

    if (e.keyCode == '37' && (!$("#photo_name").is(":focus"))){
		document.getElementById('left').click();
    }
    else if (e.keyCode == '39' && (!$("#photo_name").is(":focus"))) {
		document.getElementById('right').click();
    }
    else if (e.keyCode == '40') {
		document.getElementById('download').click();
	}
}

var a = document.createElement('a');

function get_name() {
    $.post('/ajax/get_photo_name', {
		photo_id: $("#photo_id").text()
    }).done(function(response) {
		if (response['text']) {
		$("#photo_name").val(response['text']);
		$("#photo_name").focus();
	}
    }).fail(function(response) {
		if (response['code'] == 404) {
			alert('not found!');
		}
		else if (response['code'] == 403) {
			alert('access denied!');
		}
    });
}

function set_name() {
    $.post('/ajax/set_photo_name', {
		photo_id: $("#photo_id").text(),
		name: $("#photo_name").val()
    }).done(function(response) {
		if (response['text']) {
		$("#label").text(response['text']);
		$(".button-tag").remove();
		for (tag in response['tags']) {
			"/gallery/{{gallery.id}}?tag={{tag.entity}}"
			$("#tags").after((jQuery('<a>').attr('href', "/gallery/"+$("#gallery_id").text()+"?tag="+response['tags'][tag]).text(response['tags'][tag])).addClass("button-tag"));
		}
	}
    }).fail(function() {
    });
}

function click() {
		if ($("#edit_form").data('hide')) {
			get_name();
			$("#edit_form").slideDown({
				complete: function() {
					$("#switch-bar").removeClass("triangle-down");
					$("#switch-bar").addClass("triangle-up");
				}
			});
		}
		else {
			$("#edit_form").slideUp({
				complete: function() {
					$("#switch-bar").removeClass("triangle-up");
					$("#switch-bar").addClass("triangle-down");
				}
			});
		}
		$("#edit_form").data('hide', ($("#edit_form").data('hide') == true ? false : true));
}

$(document).ready(function() {
	$("#edit_form").hide();
	$("#edit_form").data('hide', true);
	$("#switch-bar").click(click);
	$("#edit_form").submit(function(e) {
		set_name();
		e.preventDefault();
	});
});

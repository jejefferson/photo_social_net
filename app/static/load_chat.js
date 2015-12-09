function formfocus() {
		document.getElementById("form-message").focus();
		var elem = document.getElementById('textfield');
		elem.scrollTop = elem.scrollHeight;
}

function get_last_id() {
	var a = $("#textfield #message").last().text();
	b = a.split("|");
	id = parseInt(b[b.length-1]);
	return id;
}

function post_message(event) {
	event.preventDefault();
	message = $('#form-message').val();
	$.post('/ajax/chat_post_message', {
		msg_body: message
	}).done(function(resp) {
		if (resp['message']) {
			$(".textfield").append(resp['message']);
			$('#form-message').val("");
			formfocus();
		}
	}).fail(function() {
		alert("Error: пустое сообщение?");
		$('#form-message').val("");
		formfocus();
	});
}

function testajax() {
    $.post('/testajax', {
		msg_id: get_last_id()
    }).done(function(hello) {
		if (hello['text']) {
		$(".textfield").append(hello['text']);
		playSound();
		formfocus();
	}
    }).fail(function() {
        $(destId).text("{{ _('Error: Could not contact server.') }}");
        $(loadingId).hide();
        $(destId).show();
    });
}

setInterval(testajax, 3000);

function playSound() {
	document.getElementById("sound").innerHTML='<audio autoplay="autoplay"><source src="/static/notify.ogg" type="audio/mpeg" /><embed hidden="true" autostart="true" loop="false" src="/static/notify.ogg" /></audio>';
}

$(document).ready(function() {
	$("#submitbutton").click({}, post_message);
});

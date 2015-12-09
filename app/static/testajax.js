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

function testajax() {
    $.post('/testajax', {
		msg_id: get_last_id()
    }).done(function(hello) {
		if (hello['text']) {
		$(".textfield").append(hello['text']);
		formfocus();
	}
    }).fail(function() {
        $(destId).text("{{ _('Error: Could not contact server.') }}");
        $(loadingId).hide();
        $(destId).show();
    });
}

setInterval(testajax, 3000);

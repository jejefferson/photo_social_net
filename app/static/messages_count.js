function count_messages() {
    $.post('/unread_messages_count', {
    }).done(function(hello) {
		var text = $("#messages").text();
		if (hello['count']) {
			text = text.split('|')[0] + "|"+hello['count']+"|";
			$("#messages").text(text);
			playSound();
		} else {
			text = text.split('|')[0]
		}
    }).fail(function() {
    });
}

setInterval(count_messages, 60000);

function playSound() {
	document.getElementById("sound").innerHTML='<audio autoplay="autoplay"><source src="/static/notify.ogg" type="audio/mpeg" /><embed hidden="true" autostart="true" loop="false" src="/static/notify.ogg" /></audio>';
}

$(document).ready(function() {
	count_messages();
});

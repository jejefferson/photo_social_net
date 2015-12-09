function messages() {
    $.post('/get_recent_messages', {
    }).done(function(response) {
	if (response['message']) {
	$(".private_messages-box").prepend(response['message']);
	playSound();}
    }).fail(function() {
    });
}

function playSound() {
	document.getElementById("sound").innerHTML='<audio autoplay="autoplay"><source src="/static/notify.ogg" type="audio/mpeg" /><embed hidden="true" autostart="true" loop="false" src="/static/notify.ogg" /></audio>';
}

document.addEventListener('DOMContentLoaded', function() { setInterval(messages, 10000);});

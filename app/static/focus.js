//setInterval(function () {document.getElementById("online").click();}, 1000);
function formfocus() {
		document.getElementById("form-message").focus();
		var elem = document.getElementById('textfield');
		elem.scrollTop = elem.scrollHeight;
}
window.onload = formfocus;

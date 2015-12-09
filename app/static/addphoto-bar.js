function click() {
		if ($("#addphoto-bar").data('hide')) {
			$("#addphoto-bar").slideDown({
				complete: function() {
					$("#switch-bar").removeClass("triangle-down");
					$("#switch-bar").addClass("triangle-up");
				}
			});
			var addfile = document.getElementById('addfile');
			if (addfile) {
				setTimeout(function() {
				addfile.click();
			}, 500);
			}
		}
		else {
			$("#addphoto-bar").slideUp({
				complete: function() {
					$("#switch-bar").removeClass("triangle-up");
					$("#switch-bar").addClass("triangle-down");
				}
			});
		}
		$("#addphoto-bar").data('hide', ($("#addphoto-bar").data('hide') == true ? false : true));
}
	

$(document).ready(function() {
	$("#addphoto-bar").hide();
	$("#addphoto-bar").data('hide', true);
	
	$("#switch-bar").click(click);
		
	$(window).keypress(function(e) {
		if (e.keyCode == 13) {
			click();
		}
	});
});


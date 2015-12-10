window.reset = function (e) {
    e.wrap('<form>').closest('form').get(0).reset();
    e.unwrap();
}

function click() {
		var message_id = this.id.split('_')[1]
		if ($("#comments_"+message_id).data('hide')) {
			$("#comments_"+message_id).slideDown({
				complete: function() {
					$("#switch-bar_"+message_id).toggleClass("dark-eye");
				}
			});
		}
		else {
			$("#comments_"+message_id).slideUp({
				complete: function() {
					$("#switch-bar_"+message_id).toggleClass("dark-eye");
				}
			});
		}
		$("#comments_"+message_id).data('hide', ($("#comments_"+message_id).data('hide') == true ? false : true));
}

function clickcopy(event) {
	$('<div style="text-align: center; vertical-align:center; background: linear-gradient(rgba(255, 255, 0, 0.8), rgba(255, 255, 0, 0.8));' +
		'box-shadow: 0 0 20px rgba(64,5,42,6);"><input style="width: 90%" id="sel" type="text" />'+
		'<p>Press ctrl+c and close window by escape</p></div>').dialog().hide().fadeIn('quick');
	var result_url = '';
	result_url += event.data.host;
	if (event.data.location_pathname.split('/').length == 2) {
		result_url += ('/profile/' + $('#profile').text());
	}
	else {
		result_url += event.data.location_pathname;
	}
	result_url += ('#' + $(this).attr('id').split('_')[1]);
	$('[id^=sel]').val(result_url);
	$('[id^=sel]').select();
}

function reply(event) {
	event.preventDefault();
	var reply_id = $(this).attr('id').split('_')[1];
	var form = $("#comment_"+reply_id).parent();
	if (form.find('#form2-comment_message_body').length > 0) {
		form.find('.comment-form').show();
		form.find('#form2-comment_message_body').focus().val('#'+reply_id+' ');
	}
	else {
		form = $('#replyto_'+reply_id).parent().parent().parent().parent();
		form.find('.comment-form').show();
		form.find('#form2-comment_message_body').focus().val('#'+reply_id+' ');
		return;
	};
}

var files;
function prepareUpload(event)
{
  files = event.target.files;
}

var comment_files;
function prepareUploadComment(event) {
	comment_files = event.target.files;
}

function postMessage(event) {
	event.stopPropagation();
	event.preventDefault();
	var data = new FormData();
	var nick = event.data.location_pathname.split('/')[2];
	if (!nick) {
		nick = '';
	} else {
		nick = decodeURIComponent(nick);
	}
	if (files) {
		$.each(files, function(key, value) {
			data.append(value.name, value);
		});
	}
	var is_group = event.data.location_pathname.split('/')[1] == 'group'
	data.append('message', $('#form-message_body').val());
	data.append('nick', nick);
	data.append('is_group', is_group);
	if (files) {
		$('#progressbar_wrap').show();
	}
	var progressbar = $("#progressbar"),
			progressLabel = $(".progress-label");
	progressbar.progressbar({
          value: false,
          change: function () {
              progressLabel.text(progressbar.progressbar("value") + "%");
          },
          complete: function () {
              progressLabel.text("Загрузка завершена, идёт обработка...");
          }
	});
	$.ajax({
		xhr: function() {
        var xhr = new window.XMLHttpRequest();
        xhr.upload.addEventListener("progress", function(evt) {
            if (evt.lengthComputable) {
                var percentComplete = evt.loaded / evt.total;
                progressbar.progressbar( "value", percentComplete.toFixed(1)*100);
                console.log(percentComplete)*100;
            }
       }, false);

       xhr.addEventListener("progress", function(evt) {
           if (evt.lengthComputable) {
               var percentComplete = evt.loaded / evt.total;
               progressLabel.text("Успешно сохранено!");
               //console.log(percentComplete)*100;
           }
       }, false);

       return xhr;
    },
        url: '/ajax/post_message',
        type: 'POST',
        data: data,
        cache: false,
        dataType: 'json',
        processData: false, // Don't process the files
        contentType: false, // Set content type to false as jQuery will tell the server its a query string request
        success: function(data, textStatus, jqXHR)
        {
        	if(typeof data.error === 'undefined')
        	{
				$('.messages-box').prepend(data['response']);
				var comment_form = $('#add_comment_form');
				if (comment_form.length) {
					comment_form.clone().insertAfter($('[id^=comments_]').first());
				}
				else {
					$('[id^=comments_]').first().after($('#add_comment_prototype').html());
					$('#add_comment_form').hide();
				}
				var form = $('#add_comment_form').find('form');
				var replacement = form.attr('action').replace(/(add_comment\/)(\d+)/,
						'$1'+($(data['response']).find('[id^=comment_]').attr('id').split('_')[1]))
				form.attr('action', replacement);
				$("[id^=reply-button]").first().click({}, reply);
				$("#delete").click({}, deleteMessage);
				$("[id^=switch-bar]").first().click(click);
				$('#addition-button').toggle( function() {
					var form = $(this).parent().parent().parent();
					if (form.find('.addition').length > 0) {
					form.find('.addition').show();
					}
					else {
						form = form.parent();
						form.find('.addition').show();
					};
					},
					function() {
						var form = $(this).parent().parent().parent();
						if (form.find('.addition').length > 0) {
						form.find('.addition').hide();
						}
						else {
							form = form.parent();
							form.find('.addition').hide();
						};
						}
				);
				$("[id^=copy-button]").first().click({location_host: window.location.host,
					location_pathname: window.location.pathname,
					host: window.location.host}, clickcopy);
				$('#form2-comment_message_file').on('change', prepareUploadComment);
				$('#form2-comment_submit').click({location_pathname: window.location.pathname}, postComment);
				reset($('#form-message_body'));
				reset($('#form-message_file'));
				$('#progressbar_wrap').hide();
        	}
        	else
        	{
        		// Handle errors here
        		console.log('ERRORS: ' + data.error);
        	}
        },
        error: function(jqXHR, textStatus, errorThrown)
        {
        	// Handle errors here
        	console.log('ERRORS: ' + textStatus);
        	// STOP LOADING SPINNER
        }
    });
}


function deleteMessage(event) {
	event.stopPropagation();
	event.preventDefault();
	var id = $(this).parent().parent().parent().parent();
	if (!id.attr('id')) {
		id = id.parent();
		}
	id = id.attr('id').split('_')[1];
	$.post('/ajax/delmessage', {
		id: id
    }).done(function(response) {
		message_parent = ($('#comment_'+id).attr('class').match('parent_(\\d+)'));
		if ($('#comment_'+id).attr('class') == 'message') {
			var comments_box = $('#comments_'+id);
			var form = $('#add_comment_form');
			comments_box.remove();
			form.remove();
		}
		if (message_parent) {
			var count = $('#comment_'+message_parent[1]).find('#com_count');
			count.text(count.text()-1);
		}
		$('#comment_'+id).remove();
    }).fail(function() {
		alert('server error!');
    });
}

function postPrivateMessage(event) {
	event.stopPropagation();
	event.preventDefault();
	var data = new FormData();
	var msg_dest = event.data.location_pathname.match(/messages\/(.*)/)
	if (!msg_dest) {
		msg_dest = $('#message_dest').val();
	}
	else {
		msg_dest = msg_dest[1];
	}
	msg_dest = decodeURIComponent(msg_dest)
	if (files) {
		$.each(files, function(key, value) {
			data.append(value.name, value);
		});
	}
	data.append('message', $('#message_body').val());
	data.append('msg_dest', msg_dest);
	if (files) {
		$('#progressbar_wrap').show();
	}
	var progressbar = $("#progressbar"),
			progressLabel = $(".progress-label");
	progressbar.progressbar({
          value: false,
          change: function () {
              progressLabel.text(progressbar.progressbar("value") + "%");
          },
          complete: function () {
              progressLabel.text("Загрузка завершена, идёт обработка...");
          }
	});
	$.ajax({
		xhr: function() {
        var xhr = new window.XMLHttpRequest();
        xhr.upload.addEventListener("progress", function(evt) {
            if (evt.lengthComputable) {
                var percentComplete = evt.loaded / evt.total;
                progressbar.progressbar( "value", percentComplete.toFixed(1)*100);
                console.log(percentComplete)*100;
            }
       }, false);

       xhr.addEventListener("progress", function(evt) {
           if (evt.lengthComputable) {
               var percentComplete = evt.loaded / evt.total;
               progressLabel.text("Успешно сохранено!");
               //console.log(percentComplete)*100;
           }
       }, false);

       return xhr;
    },
        url: '/ajax/post_private_message',
        type: 'POST',
        data: data,
        cache: false,
        dataType: 'json',
        processData: false, // Don't process the files
        contentType: false, // Set content type to false as jQuery will tell the server its a query string request
        success: function(data, textStatus, jqXHR)
        {
        	if(typeof data.error === 'undefined')
        	{
				$(".private_messages-box").prepend(data['response']);
				$("#delete").click({}, deleteMessage);
				$('#addition-button').toggle( function() {
					var form = $(this).parent().parent().parent();
					if (form.find('.addition').length > 0) {
					form.find('.addition').show();
					}
					else {
						form = form.parent();
						form.find('.addition').show();
					};
					},
					function() {
						var form = $(this).parent().parent().parent();
						if (form.find('.addition').length > 0) {
						form.find('.addition').hide();
						}
						else {
							form = form.parent();
							form.find('.addition').hide();
						};
						}
				);
				$('#progressbar_wrap').hide();
				$("[id^=copy-button]").first().click({location_host: window.location.host,
					location_pathname: window.location.pathname,
					host: window.location.host}, clickcopy);
				reset($('#message_file'));
				reset($('#message_body'));
				var dest_input = $('#message_dest');
				if (dest_input.length) {
					reset($('#message_dest'));
				}
        	}
        	else
        	{
        		// Handle errors here
        		console.log('ERRORS: ' + data.error);
        	}
        },
        error: function(jqXHR, textStatus, errorThrown)
        {
        	// Handle errors here
        	console.log('ERRORS: ' + textStatus);
        	// STOP LOADING SPINNER
        }
    });
}

function postComment(event) {
	event.stopPropagation();
	event.preventDefault();
	var thisb = $(this);
	var parent_id = $(this).parent().parent().parent().find('.message').attr('id').split('_')[1];
	var nick = event.data.location_pathname.split('/')[2];
	var data = new FormData();
	if (!nick) {
		nick = '';
	}
	if (comment_files) {
		$.each(comment_files, function(key, value) {
			data.append(value.name, value);
		});
	}
	data.append('form2-comment_message_body', $(this).parent().find('#form2-comment_message_body').val());
	data.append('parent_id', parent_id);
	data.append('nick', nick);
	if (comment_files) {
		console.log('comment with files:', comment_files);
	}
	$.ajax({
		xhr: function() {
        var xhr = new window.XMLHttpRequest();
        xhr.upload.addEventListener("progress", function(evt) {
            if (evt.lengthComputable) {
                var percentComplete = evt.loaded / evt.total;
                //progressbar.progressbar( "value", percentComplete.toFixed(1)*100);
                console.log(percentComplete)*100;
            }
       }, false);

       xhr.addEventListener("progress", function(evt) {
           if (evt.lengthComputable) {
               var percentComplete = evt.loaded / evt.total;
               //progressLabel.text("Успешно сохранено!");
               console.log(percentComplete)*100;
           }
       }, false);

       return xhr;
    },
        url: '/ajax/post_comment',
        type: 'POST',
        data: data,
        cache: false,
        dataType: 'json',
        processData: false, // Don't process the files
        contentType: false, // Set content type to false as jQuery will tell the server its a query string request
        success: function(data, textStatus, jqXHR) {
        	if(typeof data.error === 'undefined') {
				var comments_div = thisb.parent().parent().parent().find('[id^=comments]');
				comments_div.show();
				var comment = comments_div.append(data['response']);
				comment = comment.find('[id^=comment_]').last();
				var button = comment.find("[id^=reply-button]");
				button.click({}, reply);
				comment.find("[id^=copy-button]").click({location_host: window.location.host,
					location_pathname: window.location.pathname,
					host: window.location.host}, clickcopy);
				comment.find("#delete").click({}, deleteMessage);
				var link = comment.find('[id^=replyto_]');
				var message_parent = comment.attr('class').match('parent_(\\d+)');
				if (message_parent) {
					var count = $('#comment_'+message_parent[1]).find('#com_count');
					count.text(parseInt(count.text())+1);
				}
				comment.find('[id^=addition-button]').toggle( function() {
					var form = $(this).parent().parent().parent();
					if (form.find('.addition').length > 0) {
						form.find('.addition').show();
					}
					else {
						form = form.parent();
						form.find('.addition').show();
					};
					},
					function() {
						var form = $(this).parent().parent().parent();
						if (form.find('.addition').length > 0) {
							form.find('.addition').hide();
						}
						else {
							form = form.parent();
							form.find('.addition').hide();
						};
					}
				);
				var hoverTimeout;
				link.hover(function(){
					clearTimeout(hoverTimeout);
					var reply_to_id = $(this).attr('href').substr(1);
					var message = $('#comment_' + reply_to_id);
					var already = link.find('[id^=comment_]').attr('id');
					if (!already) {
						$('#comment_' + reply_to_id).clone().appendTo($(this));
						var reply = link.find('[id^=comment_]');
						reply.hide();
						reply.fadeIn();
					};
					} ,function() {
						hoverTimeout = setTimeout(function() {
							link.find('[id^=comment_]').fadeOut().remove();
						}, 1000);
					}
				);
				reset(comments_div.parent().find('#form2-comment_message_body'));
				reset(comments_div.parent().find('#form2-comment_message_file'));
        	}
        	else {
        		// Handle errors here
        		console.log('ERRORS: ' + data.error);
        	}
        },
        error: function(jqXHR, textStatus, errorThrown) {
        	console.log('ERRORS: ' + textStatus);
        }
    });
}

$(document).ready(function() {
	$("[id^=comments]").hide();
	$("[id^=comments]").data('hide', true);
	$("[id^=switch-bar]").click(click);
	var anchor_id = window.location.hash.substring(1);
	if (anchor_id) {
		var parent_id = $("#comment_"+anchor_id).attr('class');
		if (parent_id && parent_id != 'message') {
			parent_id = parent_id.split(' ')[1].split('_')[1]
			$("#comments_"+parent_id).show();
			$("#comments_"+parent_id).data('hide', false);
			$("#switch-bar_"+parent_id).toggleClass("dark-eye");
		}
	}
	$("[id^=copy-button]").click({location_host: window.location.host,
		location_pathname: window.location.pathname,
		host: window.location.host}, clickcopy);
	
	$("[id^=reply-button]").click({}, reply);
	
	var hoverTimeout;
	
    $('[id^=replyto_]').hover(function(){
		clearTimeout(hoverTimeout);
		var message_id = ($(this).attr('href').substr(1));
		var message = $('#comment_' + message_id);
		var already = $(this).find('[id^=comment_]').attr('id');
		if (!already) {
			$('#comment_' + message_id).clone().appendTo($(this));
			var reply = $(this).find('[id^=comment_]');
			reply.hide();
			reply.fadeIn();
		};
		} ,function() {
			var $self = $(this);
			hoverTimeout = setTimeout(function() {
				$self.find('[id^=comment_]').fadeOut().remove();
			 }, 1000);
		}
	);
	
	$('[id^=addition-button]').toggle( function() {
		var form = $(this).parent().parent().parent();
		if (form.find('.addition').length > 0) {
			form.find('.addition').show();
		}
		else {
			form = form.parent();
			form.find('.addition').show();
		};
		
	},
	function() {
		var form = $(this).parent().parent().parent();
		if (form.find('.addition').length > 0) {
			form.find('.addition').hide();
		}
		else {
			form = form.parent();
			form.find('.addition').hide();
		};
	}
	);
	var showChar = 140;
    var ellipsestext = "...";
    var moretext = "показать";
    var lesstext = "спасибо, уберите";
    $('.more').each(function() {
        var content = $(this).html();
 
        if(content.length > showChar) {
 
            var c = content.substr(0, showChar);
            var h = content.substr(showChar, content.length - showChar);
 
            var html = c + '<span class="moreellipses">' + ellipsestext+ '&nbsp;</span><span class="morecontent"><span>' + h + '</span>&nbsp;&nbsp;<a href="" class="morelink">' + moretext + '('+h.length+')'+'</a></span>';
 
            $(this).html(html);
        }
 
    });
    $(".morelink").click(function(){
        if($(this).hasClass("less")) {
            $(this).removeClass("less");
            $(this).html(moretext);
            window.location = $(this).parent().parent().parent().find('#anchor').attr('href');
        } else {
            $(this).addClass("less");
            $(this).html(lesstext);
        }
        $(this).parent().prev().toggle();
        $(this).prev().toggle();
        return false;
    });
	$("[id=delete]").click({}, deleteMessage);
	$('input[type=file]').on('change', prepareUpload);
	$('#form-submit').click({location_pathname: window.location.pathname}, postMessage);
	$('[id=form2-comment_message_file]').on('change', prepareUploadComment);
	$('[id=form2-comment_submit]').click({location_pathname: window.location.pathname}, postComment);
	$('#submit').click({location_pathname: window.location.pathname}, postPrivateMessage);
});


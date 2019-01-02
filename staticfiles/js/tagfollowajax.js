// follow a tag
$('#followtag').on('submit', function(event){
    event.preventDefault();     
    var followform = $('#followtag');
    var unfollowform = $('#unfollowtag');
    var tag = $('.search_term',this).val();   
    console.log("Follow tag: " + tag);
    follow_tag(tag, followform, unfollowform);
});
function follow_tag(tag, followform, unfollowform) {
    console.log('Follow this tag ' + tag)
    $.ajax({
        url : "/follow_tag/", // the endpoint
        type : "POST", // http method
        data : { tag : tag }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            console.log(json['result']);
            followform.fadeToggle('fast', function(){
                unfollowform.fadeToggle();
            });
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};

// unfollow a tag
$('#unfollowtag').on('submit', function(event){
    event.preventDefault();        
    var tag = $('.search_term',this).val(); 
    var followform = $('#followtag');
    var unfollowform = $('#unfollowtag');  
    console.log("Unfollow tag: " + tag);
    unfollow_tag(tag, followform, unfollowform);
});
function unfollow_tag(tag, followform, unfollowform) {
    console.log('Unfollow this tag ' + tag)
    $.ajax({
        url : "/unfollow_tag/", // the endpoint
        type : "POST", // http method
        data : { tag : tag }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            console.log(json['result']);
            unfollowform.fadeToggle('fast', function(){
                followform.fadeToggle();
            });
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};
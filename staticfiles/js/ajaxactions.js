/*****************
FOLLOW USER
*****************/
$('.followuser').on('submit', function(event){
    event.preventDefault();        
    var userid = $('.follow_user_id',this).val();   
    var followuser = $('.followuser[data-id='+ userid +']');
    var unfollowuser = $('.unfollowuser[data-id='+ userid +']');    
    console.log("Start following user: " + userid);
    follow_user(followuser, unfollowuser, userid);
});

function follow_user(followuser, unfollowuser, userid) {
    console.log('Follow user ' + userid)
    $.ajax({
        url : "/b/follow/", // the endpoint
        type : "POST", // http method
        data : { userid : userid }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            followuser.fadeToggle('fast', function(){
                unfollowuser.fadeToggle();
            });
            var currentfollowing = $('.totFollowing').text();            
            currentfollowing = parseInt(currentfollowing);
            var newfollowing = currentfollowing+1;
            $('.totFollowing').text(newfollowing);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};


/*****************
UNFOLLOW USER
*****************/
$('.unfollowuser').on('submit', function(event){
    event.preventDefault();        
    var userid = $('.unfollow_user_id',this).val();   
    var followuser = $('.followuser[data-id='+ userid +']');
    var unfollowuser = $('.unfollowuser[data-id='+ userid +']');    
    console.log("Start unfollowing user: " + userid);
    unfollow_user(followuser, unfollowuser, userid);
});

function unfollow_user(followuser, unfollowuser, userid) {
    console.log('Unfollow user ' + userid)
    $.ajax({
        url : "/b/unfollow/", // the endpoint
        type : "POST", // http method
        data : { userid : userid }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            unfollowuser.fadeToggle('fast', function(){
                followuser.fadeToggle();
            });
            var currentfollowing = $('.totFollowing').text();            
            currentfollowing = parseInt(currentfollowing);
            var newfollowing = currentfollowing-1;
            $('.totFollowing').text(newfollowing);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log('broken');
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};


/*****************
SAVE ITEM
*****************/
$('.saveitem').on('submit', function(event){
    event.preventDefault();    
    var itemid = $('.save_item_id',this).val();   
    console.log('item id is: ' + itemid);
    save_item(itemid);
});

function save_item(itemid) {
    console.log("Now save the item...")
    $.ajax({
        url : "/b/save_item/", // the endpoint
        type : "POST", // http method
        data : { itemid : itemid }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            $(function(){
                new PNotify({
                    title: false,
                    type: "success",
                    text: 'The item was successfully added to your saved items.',
                    shadow: false,
                    delay: 5000,
                    buttons: {
                        sticker: false,
                    }
                }); 
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


/*****************
LIKE ITEM
*****************/
$('.likeitem').on('submit', function(event){
    event.preventDefault();    
    var itemid = $('.like_item_id',this).val();   
    var unlikeitem = $('.unlikeitem[data-id='+ itemid +']');
    var likeitem = $('.likeitem[data-id='+ itemid +']');    
    like_item(likeitem, unlikeitem, itemid);
});

function like_item(likeitem, unlikeitem, itemid) {
    $.ajax({
        url : "/b/like_item/", // the endpoint
        type : "POST", // http method
        data : { itemconx_id : itemid }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            likeitem.fadeToggle('fast', function(){
                unlikeitem.fadeToggle();
            });
            var currentlikes = $('.likeitembutton[data-id='+ itemid +'] span').text();            
            currentlikes = parseInt(currentlikes);
            var newlikes = currentlikes+1;
            console.log('item liked: ' + itemid);
            console.log('old likes: ' + currentlikes);
            console.log('new likes: ' + newlikes);
            $('.unlikeitembutton[data-id='+ itemid +'] span').text(newlikes);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};

/*****************
UNLIKE ITEM
*****************/
$('.unlikeitem').on('submit', function(event){
    event.preventDefault();
    var itemid = $('.unlike_item_id',this).val();   
    var unlikeitem = $('.unlikeitem[data-id='+ itemid +']');
    var likeitem = $('.likeitem[data-id='+ itemid +']');
    unlike_item(unlikeitem, likeitem, itemid);
});

function unlike_item(unlikeitem, likeitem, itemid) {
    $.ajax({
        url : "/b/unlike_item/", // the endpoint
        type : "POST", // http method
        data : { itemconx_id : itemid }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            unlikeitem.fadeToggle('fast', function(){
                likeitem.fadeToggle();
            });                
            var currentlikes = $('.unlikeitembutton[data-id='+ itemid +'] span').text();
            currentlikes = parseInt(currentlikes);
            var newlikes = currentlikes-1;
            console.log('item unliked: ' + itemid);
            console.log('old likes: ' + currentlikes);
            console.log('new likes: ' + newlikes);
            $('.likeitembutton[data-id='+ itemid +'] span').text(newlikes);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};

/*****************
LIKE BOARD
*****************/
$('#likeboard').on('submit', function(event){
    event.preventDefault();
    console.log("form submitted!")  // sanity check
    like_board();
});

function like_board() {
    $.ajax({
        url : "/b/like_board/", // the endpoint
        type : "POST", // http method
        data : { board_id : $('#like_board_id').val() }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            console.log("success"); // another sanity check
            $('#likeboard').fadeToggle('fast', function(){
                $('#unlikeboard').fadeToggle();
            });
            var currentlikes = $('#likeboardbutton span').text();
            currentlikes = parseInt(currentlikes);
            console.log(currentlikes);
            var newlikes = currentlikes+1;
            console.log(newlikes);
            $('#unlikeboardbutton span').text(newlikes);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};


/*****************
UNLIKE BOARD
*****************/
$('#unlikeboard').on('submit', function(event){
    event.preventDefault();
    console.log("form submitted!")  // sanity check
    unlike_board();
});

function unlike_board() {
    $.ajax({
        url : "/b/unlike_board/", // the endpoint
        type : "POST", // http method
        data : { board_id : $('#unlike_board_id').val() }, // data sent with the post request

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            console.log("success"); // another sanity check
            $('#unlikeboard').fadeToggle('fast', function(){
                $('#likeboard').fadeToggle();
            });                
            var currentlikes = $('#unlikeboardbutton span').text();
            currentlikes = parseInt(currentlikes);
            console.log(currentlikes);
            var newlikes = currentlikes-1;
            console.log(newlikes);
            $('#likeboardbutton span').text(newlikes);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};
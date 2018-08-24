// like item ajax request
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

// unlike item ajax request
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

// like board ajax request
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


// unlike board ajax request
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
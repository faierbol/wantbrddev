$(window).on("load", function() {
    console.log('page loaded');

    let board = $('#homeBoardItems')
    board.append(
        '<div class="featBox whatIsWantbrdBox">' +
            '<div class="whatIsInner">' +
                '<strong>What is Wantbrd?</strong>' +
                'Wantbrd is a place for you to share the things you want and recommend with your friends, family and followers.' +
                '<a class="btn" href="#loginModal" rel="modal:open">Create your wantbrd now</a>'+
            '</div>' +
        '</div>'
    );

    $.ajax({
        url : "/b/get_home_items/", // the endpoint
        dataType: 'json',
        data : {}, // data sent with the post request

        // handle a successful response
        success : function(data) {
            console.log(data);
            $('.loadingcont').remove();                
            
            data.map(function(item){

                if (item.type == 'trending_item') {

                    board.append(
                        '<div class="featBox trendingItem">'+
                            '<div class="trendingTop clearfix">'+
                                '<strong>TRENDING ITEM</strong>'+
                            '</div>'+
                            '<div class="trendingItemItem">' +
                                '<a href="' + item.item_url + '"><img src="' + item.item_image + '" alt="' + item.item_name + '"></a>'+
                            '</div>' +
                            '<div class="trendingItemName">'+
                                '<a href="' + item.item_url + '">' + item.item_name + '</a>'+
                                '<div class="trendingItemMeta">' +
                                    'Found on <a href="' + item.board_url + '">' + item.board_name + '</a>'+
                                    'by <a href="' + item.user_url + '">' + item.user + '</a>'+
                                '</div>'+
                            '</div>'+
                            '<div class="trendingFooter">'+
                                '<span><a href="' + item.item_url + '"><i class="far fa-comments"></i></a> 0'+                                    
                                '</span>' +                                
                                '<span><i class="fas fa-eye"></i>' + item.item_views + '</span>'+
                            '</div>'+
                        '</div>'
                    )

                } else if(item.type == 'trending_board')  {

                    totalItemsSuffix = item.total_items == 1 ? "item" : "items";
                    totalItems = "<span>" + item.total_items + " " + totalItemsSuffix + "</span>";

                    viewsSuffix = item.views == 1 ? "view" : "views";
                    views = "<span>" + item.views + " " + viewsSuffix + "</span>";      

                    userpic = "<div class='circle' style='background-image:url(" + item.user_pic + ");'></div>";

                    boardpic = "<a class='trendingBoardHero' style='background-image:url(" + item.hero + ");' href='" + 
                    item.board_url + "'><div class='trendingBoardMeta'><strong>" + item.board_name + "</div></strong></a>";
                    
                    var itemHtml = '';
                    var x = 1;
                    for (var key in item.items) {
                        itemHtml += '<a data-id="this" style="background-image:url(' + item.items[key].image + ');" href="' + item.items[key].link + '"></a>'                            
                    }

                    board.append(

                        '<div class="featBox trendingBoard">' +
                            '<div class="trendingTop clearfix">' +
                                '<strong>Trending Board</strong>' +
                            '</div>' +

                            boardpic +

                            "<div class='trendingItems clearfix'>" +
                                itemHtml +
                            "</div>" +

                            '<a class="trendingUserUser" href="' + item.user_url + '">' +
                                '<div class="trendingUserUserWrap clearfix">' +
                                    '<div class="trendingUserPic">' +
                                        userpic +
                                    '</div>' +
                                    '<div class="trendingUserNames">' +
                                        '<strong>@' + item.username + '</strong>' +
                                        '<span>' + item.full_name + '</span>' +
                                    '</div>' +
                                '</div>' +
                            '</a>' +
                            '<div class="trendingFooter">' +
                            views +
                            totalItems +
                            '</div>' +
                        '</div>' 

                    );

                } else if(item.type == 'trending_user') {

                    totalItemsSuffix = item.total_items == 1 ? "item" : "items";
                    total_items = "<span>" + item.total_items + " " + totalItemsSuffix + "</span>";

                    boardsSuffix = item.total_boards == 1 ? "board" : "boards";
                    total_boards = "<span>" + item.total_boards + " " + boardsSuffix + "</span>";

                    var itemHtml = '';
                    var x = 1;
                    for (var key in item.items) {
                        itemHtml += '<a style="background-image:url(' + item.items[key].image + ');" href="' + item.items[key].link + '"></a>'                            
                    }

                    board.append(

                        '<div class="featBox trendingUser">' +
                            '<div class="trendingTop clearfix">' +
                                '<strong>Trending User</strong>' +
                            '</div>' +
                            '<a class="trendingUserUser" href="' + item.user_url + '">' +
                                '<div class="trendingUserUserWrap clearfix">' +
                                    '<div class="trendingUserPic">' +                                            
                                        '<div class="circle" style="background-image:url(' + item.user_pic + ');"></div>' +
                                    '</div>' +
                                    '<div class="trendingUserNames">' +
                                        '<strong>@' + item.username + '</strong>' +
                                        '<span>' + item.name + '</span>' +
                                    '</div>' +
                                '</div>' +
                            '</a>' +
                            
                            '<a class="trendingUserHero" href="' + item.user_url + '" style="background-image:url(' + item.hero + ')"></a>' +

                            '<div class="trendingItems clearfix">' +
                                itemHtml +
                            '</div>' +

                            '<div class="trendingFooter">' +
                                total_items +
                                total_boards +
                            '</div>' +

                        '</div>'

                    )

                } else if(item.type == 'community') {

                    board.append(
                        `
                        <div class="featBox communityCta">
                            <div class="comTop">
                                Featured Community
                            </div>
                            <div class="communityCtaImage" style="background-image:url('${item.image}')">
                            </div>
                            <div class="communityCtaCont">
                                <h2>#${item.name}</h2>
                                <div class="communityCtaProducts">
                                    ${item.products}
                                </div>
                                <a href="/community/${item.slug}">Explore now</a>
                            </div>
                        </div>
                        `
                    )

                } 
            })             

            // then do masonry
            var masonry = new Macy({
                container: '#homeBoardItems',
                trueOrder: false,
                waitForImages: false,
                useOwnImageLoader: false,
                debug: true,
                mobileFirst: true,
                columns: 1,
                margin: 24,
                breakAt: {
                    860: 3,
                    520: 2,
                    320: 1
                }
            });   
        }
    });

})
function EditSubsXBlockAdminView(runtime, element) {
    var videoId;
    var $adminView;

    function _requestHelper(serverHandler, sendData, callback){
        $.post(runtime.handlerUrl(element, serverHandler), JSON.stringify(sendData))
            .done(function(data){
                if(data.result === "success"){
                    callback(data.data);
                }
                else if(data.result === "error") {
                    showError(data.message);
                }
            });
    }

    $(function($){
        $adminView = $(".editsubs-adminview", element);
        videoId = $adminView.data("videoid");

        $('.editsubs-tabs').each(function(){
            var $active, $content, $links = $(this).find('a');
            $active = $($links.filter('[href="'+location.hash+'"]')[0] || $links[0]);
            $active.addClass('active');
            $content = $($active[0].hash);
            $links.not($active).each(function () {
                $(this.hash).hide();
            });
            $(this).on('click', 'a', function(e){
                $active.removeClass('active');
                $content.hide();
                $active = $(this);
                $content = $(this.hash);
                $active.addClass('active');
                $content.show();
                $content.find('table').dataTable();
                e.preventDefault();
            });
        });

        $(".editsubs-show-table", element).on("click", function(){
            $(this).removeClass("editsubs-show-table")
                .addClass("editsubs-hide-table")
                .text("Hide adminpanel");
            $adminView.show();
        });

        $(".editsubs-hide-table", element).on("click", function(){
            $(this).removeClass("editsubs-hide-table")
                .addClass("editsubs-show-table")
                .text("Show adminpanel");
            $adminView.hide();
        });
    });





}
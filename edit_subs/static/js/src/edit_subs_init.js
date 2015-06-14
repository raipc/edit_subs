function EditSubsXBlockInit(runtime, element) {
    var initUrl = runtime.handlerUrl(element, 'initialize');

    var selectElement = $("#edit_subs_videos");

    function findVideos(){
        return $(".video").map(function () {
            var thisVideoElement = $(this);
            var thisVideoMetaObject = {};
            var longStreamId = thisVideoElement.data("streams");
            /*
             5 is "1.00:".length
             12 is the length of YouTube video ID
             Size is fixed for compatibility with old courses where different videos for different speeds were hosted
             */
            thisVideoMetaObject.videoId = longStreamId.substr(longStreamId.indexOf("1.00:") + 5, 12);
            thisVideoMetaObject.videoName = thisVideoElement.parent().find("h2").text();
            thisVideoMetaObject.defaultSubtitleId = thisVideoElement.data("sub");
            thisVideoMetaObject.defaultSubtitleLangs = Object.keys(thisVideoElement.data("transcript-languages"));
            selectElement.append(
                $("<option></option>").val(thisVideoMetaObject.videoId).html(thisVideoMetaObject.videoName)
            );
            return thisVideoMetaObject;
        }).get();
    }

    $(element).find('.save-button').bind('click', function() {
        var options = findVideos();
        if (options.length === 0) {
            alert("You must choose a video");
            return;
        }
        //find object describing selected video. Using Underscore.js
        var data = _.find(options, function(elem){
            return elem.videoId === selectElement.find(":selected").val();
        });

        $('.xblock-editor-error-message', element).html();
        $('.xblock-editor-error-message', element).css('display', 'none');
        $.post(initUrl, JSON.stringify(data)).done(function(response) {
            if (response.result === 'success') {
                window.location.reload(false);
            } else {
                $('.xblock-editor-error-message', element).html('Error: '+response.message);
                $('.xblock-editor-error-message', element).css('display', 'block');
            }
        });
    });

    $(element).find('.cancel-button').bind('click', function() {
        runtime.notify('cancel', {});
    });


}
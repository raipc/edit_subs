/* Javascript for EditSubsXBlock. */
function EditSubsXBlock(runtime, element) {
    var banned = true;
    var subtitlesBtn;
    var activateBtn;
    var videoElement;
    var longId = videoElement.attr('id');
    var videoId = longId.slice(longId.length - 32);

    var internalSubsId = videoElement.data('sub');
    var courseId = longId.slice(10, longId.indexOf("-video"));
    var repos;
    var isEditingActive = false;
    var changedSubtitleString;
    var editableSubtitleObject;

    var getSubtitlesUrl = runtime.handlerUrl(element, 'get_subtitles');
    var getSubtitlesForRateUrl = runtime.handlerUrl(element, 'get_subtitles_to_rate');
    var getReposUrl = runtime.handlerUrl(element, 'get_repos');
    var activateUrl = runtime.handlerUrl(element, 'activate');
    var upvoteUrl = runtime.handlerUrl(element, 'upvote');
    var downvoteUrl = runtime.handlerUrl(element, 'downvote');




    $(function ($) {

        videoId = $("editsubs-container",element).data("videoId");
        var videoElement = $(".video").filter(function() { return $(this).data("metadata").sub == videoId; })
        if (videoElement){
            $(".editsubs-activate", element).appendTo($(".wrapper-downloads", videoElement));
            activateBtn = $(".hide-subtitles", videoElement);

        }





        $(".editsubs-cancel").click(function(){
            editableSubtitleObject.text(changedSubtitleString);
            isEditingActive = false;
        })

        $(".editsubs-string").on('input', function(){
            if(isEditingActive) return;
            editableSubtitleObject = $(this);
            changedSubtitleString = editableSubtitleObject.text();
            isEditingActive = true;
        })


    });

    function activate(){
        getReposRequest(videoId);
        var defSubtitleBtn = $(".hide-subtitles", videoElement).css("display","none");
        if (subtitlesBtn) {
            subtitlesBtn.css("display", "block");
        }
        else {
            subtitlesBtn = $('<a href="#" class="editsubs-hide-subtitles">').appendTo(defSubtitleBtn.parent());
        }

    }

    function hideCaptureButtton(){

    }

    function getReposRequest(){
        $.ajax({
            type: "POST",
            url: getReposUrl,
            data: JSON.stringify(),
            success: function(data){
                repos = data;
            }
        });
    }
    function getSubtitlesRequest(repo_id){
        $.ajax({
            type: "POST",
            url: getSubtitlesUrl,
            data: JSON.stringify({"repo_id": repo_id}),
            success: function(data){
                //handle!!
            }
        });
    }

    function submitSubtitlesRequest(index, start, text){
        $.ajax({
            type: "POST",
            url: getSubtitlesUrl,
            data: JSON.stringify({"index": index, "start": start, "text": text}),
            success: function(data){
                alert("OK")
            },
            error: function(){
                alert("error");
            }
        });
        }

    function createRepoRequest(repoName, repoDesc, repoLang){

    }

    function upvote(subtitleId){
        $.ajax({
            type: "POST",
            url: upvoteUrl,
            data: JSON.stringify({"id": id}),
            success: function(data){
                alert("data")
            },
            error: function(){
                alert("error");
            }
        });
    }
    }

    function downvote(subtitleId){

    }

    $('.editsubs-repo').click(function(){
        getSubtitlesRequest($(this).data("repo-id"));
    });
    $('.editsubs-submit').click(function () {
        var el = editableSubtitleObject;
        submitSubtitlesRequest(el.data("index"), el.data("start"), el.text());
    });


    function subtitleUpdateHandler(data){

    }

    function repositoriesUpdateHandler(data) {

    }

}

// var t = $("#video_i4x-ITMO-001-video-4b1af04d7751437e967e3a27bdada1d7").find(".video-player");
// $('<div class="inner-red" style="background-color:red;width:150px;height:50px;position:absolute;bottom:50px;"></div>').appendTo(t);

/* VideoCapture(state) */
var VideoCapture = RequireJS.require("video/09_video_caption.js");

var el = $(".editsubs-container");
var videoElem = el.parent().find("video");
var videoContainer = $(".video").has(videoElem)
el.css({
        "width": videoElem.css("width"),
        "right": !videoContainer.hasClass("closed") + 0 &&
                 $("#transcript-captions").css("width")
    });
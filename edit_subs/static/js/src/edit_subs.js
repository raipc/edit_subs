/* Javascript for EditSubsXBlock. */
function EditSubsXBlock(runtime, element) {
    //var banned = true;
    var videoId;
    var $videoElement;
    var $container;

    var $activateBtn;
    var $subtitlesBtn;
    var $defSubtitleBtn;
    var $subtitleString;

    var $reposDom;
    var changedSubtitleString; //Value before editing
    var isEditingActive = false;
    var observer;

    var repos;
    var currentRepo;
    var subtitleData; //Esjson object

    function Repos(data){
        this.repo_id = data.repo_id;
        this.repo_name = data.repo_name;
        this.description = data.description;
    }

    function Esjson(data){
        this.start = data.start;
        this.end = data.end;
        this.text = data.text;
        this.rating = data.rating;
        this.updated_at = data.updated_at;
        this.subtitle_id = data.subtitle_id;
    }

    Esjson.prototype.search = function(time){
        var index, max, min;
        min = 0;
        max = this.start.length - 1;
        while (min < max) {
            index = Math.ceil((max + min) / 2);
            if (time < this.start[index])
                max = index - 1;
            if (time >= this.start[index])
                min = index;
        }
        return min;
    };

    Esjson.prototype.showSubtitle = function(time){
        var index = this.search(time);
        if (this.end[index] <= time)
            return false;
        return {
            "index": index,
            "text": this.text[index]
        }
    };

    function updateSubtitle(event, time){
        var subtitle = subtitleData.showSubtitle(time);
        if (subtitle === false) {
            $subtitleString.text("");
            $subtitleString.data("index", "");
            return;
        }
        $subtitleString.text(subtitleData.text);
        $subtitleString.data("index", subtitleData.index);
    }

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

    function loadSubtitles(data){
        subtitleData = new Esjson(data);
    }

    function showMessage(messageClass, message){
        var $messageField = $('<div/>').attr("class","es-message-container").append(
            $('<span/>').attr("class", "es-message " + messageClass).html(message)
        );
        $messageField.appendTo($videoElement);
        setTimeout(function(){$messageField.remove();}, 3000);
    }

    function showError(message){
        showMessage("es-error-message", message);
    }
    function showResult(message){
        showMessage("es-result-message", message);
    }

    function rate(subtitleIndex, serverHandler){
        _requestHelper(
            serverHandler,
            {
                "subtitle_id": subtitleData.subtitle_id[subtitleIndex]
            },
            showResult
        )
    }

    function subtitleUpdateHandler(data){
        if(data.repo_id !== currentRepo)
            return;
        if(isEditingActive && data.start === $subtitleString.data("index")){
            $container.needEvents("deferredUpdate", function(){
                subtitleUpdateHandler(data);
            });
        }
        var index = subtitleData.start.indexOf(data.start);
        if (index < 0) return;
        if (subtitleData.rating[index] > data.rating) return;
        else if (subtitleData.rating[index] === data.rating
            && new Date(subtitleData.updated_at[index]) > new Date(data.updated_at) )
            return;
        subtitleData.text[index] = data.text;
        subtitleData.subtitle_id[index] = data.subtitle_id;
        subtitleData.rating[index] = data.rating;
        subtitleData.updated_at = data.updated_at;
    }

    function repositoriesUpdateHandler(data) {
        if (!(data.repo_id in repos.repo_id)){
            repos.repo_id.push(data.repo_id);
            repos.repo_name.push(data.repo_name);
            repos.description.push(data.description);
        }
        //TODO: Append to DOM
    }

    $.fn.needEvents = function(events){
        var deferred, $element, elemIndex, eventIndex;
        events = events.split( /\s+/g );
        var deferreds = [];
        for(elemIndex = 0; elemIndex < this.length; elemIndex++){
            $element = $( this[ elemIndex ] );
            for (eventIndex = 0; eventIndex < events.length; eventIndex++){
                deferreds.push(( deferred = $.Deferred() ));
                $element.one( events[ eventIndex ], deferred.resolve);
            }
        }
        return $.when.apply(null, deferreds);
    };

    $(function ($) {
        $container = $(".editsubs-container", element);
        videoId = $container.data("videoid");
        $videoElement = $(".video").filter(function() {
            return $(this).data("metadata").sub === videoId;
        });
        if ($videoElement){
            $activateBtn = $("<li/>")
                .attr("class", "editsubs-activate video-download-button")
                .append($("<a/>").attr("class", "es-activate")
                        .text("Activate edit_subs module"));
            $activateBtn.appendTo($(".wrapper-downloads", $videoElement));

            $subtitleString = $(".editsubs-subtitle", $videoElement);
            $videoElement.find(".video-player").append($container);
        }
        else
            alert("Video not found");


        /*
            Handle events only after activating module
         */
        $activateBtn.on("click",".es-deactivated", function(){
            _requestHelper("activate", {}, function(data){
                repos = new Repos(data.repos);
                loadSubtitles(data.subs);
            });

            $(".video").on("caption:update", updateSubtitle);

            $defSubtitleBtn = $(".hide-subtitles", $videoElement)
                .css("display","none");
            if ($subtitlesBtn) {
                $subtitlesBtn.css("display", "block");
            }
            else {
                $subtitlesBtn = $('<a href="#" class="editsubs-hide-subtitles">')
                    .appendTo($defSubtitleBtn.parent());
            }

            $(".editsubs-operation-cancel", $videoElement).click(function(){
                $subtitleString.text(changedSubtitleString);
                isEditingActive = false;
            });

            $(".editsubs-operation-save", $videoElement).click(function(){
                _requestHelper(
                    "add_subtitle",
                    JSON.stringify({
                        "text": $subtitleString.text(),
                        "start": subtitleData.start[$subtitleString.data("index")],
                        "end": subtitleData.end[$subtitleString.data("index")]
                    }),
                    showResult
                );
                isEditingActive = false;
            });

            $(".editsubs-string", $videoElement).on('input', function(){
                if(isEditingActive) return;
                $subtitleString = $(this);
                changedSubtitleString = $subtitleString.text();
                $videoElement.find(".pause").click();
                isEditingActive = true;
            });

            $(".es-rate-positive:not(.es-rated)", $videoElement)
                .on("click", function(){
                    rate($subtitleString.data("index"), "rate_positive");
                });

            $(".es-rate-negative:not(.es-rated)", $videoElement).on("click",
                function(){
                    rate($subtitleString.data("index"), "rate_negative");
                });

            $(".editsubs-repo", $videoElement).on("click", function(){
                _requestHelper(
                    "switch_to_repository",
                    {"repo_id": $(this).data("repo_id")},
                    loadSubtitles
                )
            });


            /*
                 Show modal window to create repository. Add handlers to submit-buttons
             */
            $(".editsubs-repo-create", $videoElement).on("click", function(){
                var $createRepoForm = $("#editsubs-repo-create-modal");
                $createRepoForm.leanModal();
                $(".es-repo-create-submit", $createRepoForm).on("click", function(){
                    _requestHelper(
                        "create_repository",
                        {
                            "name": $createRepoForm.find("#es-repo-name").text(),
                            "description": $createRepoForm.find("#es-repo-desc").text(),
                            "lang_tag": $createRepoForm.find("#es-lang-tag").val(),
                            "is_private": $createRepoForm.find("#es-repo-private").is(":checked")
                        },
                        showResult
                    );
                    $(this).off("click");
                });
            });

            /*
                Show modal window to rate subtitles
             */
            $(".editsubs-repo-rate", $videoElement).on("click", function(){
                var $rateForm = $("#editsubs-rate-modal");
                $rateForm.leanModal();
                _requestHelper(
                    "get_subtitles",
                    {"repo_id": currentRepo},
                    function(data){
                        //TODO: make table
                    }
                );
            });

            $container.on("subtitleUpdate", function(e, data){
                subtitleUpdateHandler(data);
            });

            $container.on("repoUpdate", function(e, data){
                repositoriesUpdateHandler(data);
            });

            observer = new MutationObserver(function() {
                $container.trigger("deferredUpdate");
            });

            observer.observe($container[0], {
                "childList": false,
                "attributes": false,
                "characterData": true
            });
            $(this).text("Dectivate edit_subs module");
            $(this).removeClass("es-deactivated").addClass("es-activated");

        });

        /*
            Remove all handlers while deactivating module
         */
        $activateBtn.on("click",".es-activated", function(){
            $(".video").off("caption:update", updateSubtitle);
            $subtitlesBtn.css("display", "none");
            $defSubtitleBtn.css("display","block");

            $(".editsubs-operation-cancel", $videoElement).off("click");
            $(".editsubs-operation-save", $videoElement).off("click");
            $(".editsubs-string", $videoElement).off('input');
            $(".es-rate-positive:not(.es-rated)", $videoElement).off("click");
            $(".es-rate-negative:not(.es-rated)", $videoElement).off("click");
            $(".editsubs-repo", $videoElement).off("click");
            $(".editsubs-repo-create", $videoElement).off("click");
            observer.deactivate();
            $(this).text("Activate edit_subs module");
            $(this).removeClass("es-activated").addClass("es-deactivated");

        });
    });
}

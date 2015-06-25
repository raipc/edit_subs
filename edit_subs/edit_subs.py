"""
This XBlock lets the students easily edit subtitles to videos. 
Students can do it in isolated repositories.
Best subtitles are chosen by their vote rating.

Course staff may block students and not allow them to add changes to
subtitles, create repositories and rate subtitles.
Course staff may easily convert subtitles from XBlock to contentstore.
"""

import pkg_resources
import datetime
from xblock.core import XBlock
from xblock.fields import Scope, Boolean, String, List
from xblock.fragment import Fragment
from xmodule.video_module.transcripts_utils import Transcript
from edx_notifications.data import NotificationMessage
import xmodule.video_module.video_module
import xmodule.video_module.transcripts_utils
import models


def not_banned(error_function=lambda: {
    "result": "error",
    "message": "You cannot perform this action as you have been banned"
    }):
    def wrapper(func):
        def wrapped(self, *args, **kwargs):
            if self.is_not_banned:
                return func(self, *args, **kwargs)
            else:
                return error_function()
        return wrapped
    return wrapper

def staff(error_function=lambda: {"result": "error",
                                  "message": "Permission denied"}):
    def wrapper(func):
        def wrapped(self, *args, **kwargs):
            if self.user_is_staff:
                return func(self, *args, **kwargs)
            else:
                return error_function()
        return wrapped
    return wrapper

def resource_string(path):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")

class EditSubsXBlockMixin(object):
    """
    A mixin which provides useful decorators and several properties taken from 
    badly documented xmodule_runtime service. Needs to be updated in the future.
    """
    @property
    def course_id(self):
        """Retrieve the course ID.
        Returns:
            CourseKey
        """
        if hasattr(self, "xmodule_runtime"):
            return unicode(self.xmodule_runtime.course_id)
        else:
            return u"edX/Test_101/April_1"

    @property
    def is_course_staff(self):
        """
         Check if user is course staff.

         Returns:
            bool
        """
        if hasattr(self, 'xmodule_runtime'):
            return getattr(self.xmodule_runtime, 'user_is_staff', False)
        else:
            return False

    @property
    def is_not_banned(self):
        """
        Return True if user is course staff or not banned, False otherwise
        """
        if self.is_course_staff:
            return True
        return models.user_is_not_banned(self.username(), self.course_id)

    def user_id(self):
        if hasattr(self, "xmodule_runtime"):
            anonymous_id = self.xmodule_runtime.anonymous_student_id
            return self.xmodule_runtime.get_real_user(anonymous_id).id        

    def username(self):
        """
        :return: string  current user's nickname
        """
        if hasattr(self, "xmodule_runtime"):
            anonymous_id = self.xmodule_runtime.anonymous_student_id
            return self.xmodule_runtime.get_real_user(anonymous_id).username
        else:
            return u"Anonymous"

    def show_moderator_interface_in_lms(self):
        """
        Return True if current user is staff and not in LMS, False otherwise.
        """
        in_lms = self.scope_ids.user_id is not None
        return self.is_course_staff and in_lms

        
@XBlock.needs('user')
@XBlock.needs('notifications')
class EditSubsXBlock(EditSubsXBlockMixin, XBlock):
    """
    The block providing means to edit subtitles in standard edX player.
    """
    olx_mode = Boolean(
        default=False, scope=Scope.settings,
        help="An indicator that the block is created from OLX editor"
    )
    allow_sharing = Boolean(
        default=False, scope=Scope.settings,
        help="Can students see and edit repos from other courses?"
    )
    initialized = Boolean(
        default=False, scope=Scope.settings,
        help="An indicator that the block is ready for work"
    )
    video_id = String(
        default="", scope=Scope.settings,
        help="ID of the video which subtitles the block handles"
    )
    video_name = String(
        default="", scope=Scope.settings,
        help="Name of the video we work with"
    )
    default_subtitles_id = String(
        default="", scope=Scope.settings,
        help="""ID of subtitles for the given video in contentstore"""
    )
    default_subtitles_langs = List(
        default=[], scope=Scope.settings,
        help="""A list containing 2-symbol language identifiers
             for existing subtitles"""
    ),
    init_repo_id = String(
        default="", scope=Scope.settings,
        help="ID of repository where default subtitles are saved to"
    )
    current_repo_id = String(
        default=init_repo_id, scope=Scope.user_state,
        help="ID of the repo to load subtitles from"
    )
    current_repo_name = String(
        default="", scope=Scope.user_state,
        help="Name of the repo to load subtitles from"
    )

    def student_view(self, context=None):
        """
        The primary view of the EditSubsXBlock, shown to students
        when viewing courses.
        """
        if not self.initialized:
            return Fragment()
        html = self.resource_string("static/html/edit_subs.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/edit_subs.css"))
        frag.add_javascript(self.resource_string("static/js/src/edit_subs.js"))
        frag.initialize_js('EditSubsXBlock')
        if self.show_moderator_interface_in_lms():
            frag.add_content("static/html/edit_subs_moderate.html")
            frag.add_css_url("https://cdn.datatables.net/1.10.7/css/jquery.dataTables.css")
            frag.add_javascript_url("https://cdn.datatables.net/1.10.7/js/jquery.dataTables.min.js")
            frag.add_javascript(self.resource_string("static/js/src/edit_subs_moderate.js"))
            frag.initialize_js("EditSubsXBlockAdminView")
        return frag

    def studio_view(self):
        """
        The view of the EditSubsXBlock, shown to course authors in studio
        """
        html = self.resource_string("static/html/edit_subs_initialize.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/edit_subs.css"))
        frag.add_javascript(self.resource_string("static/js/src/edit_subs_init.js"))
        frag.initialize_js('EditSubsXBlockInit')
        return frag

    @XBlock.json_handler
    @staff
    def initialize(self, data):
        paramlist = [data["video_name"],
                     data["video_id"],
                     data["videoblock_opaque_key"],
                     data["default_subtitles_id"],
                     data["default_subtitles_langs"]
                     ]

        if "" in paramlist:
            return {"result": "error", "message": "All the fields must be filled"}
        else:
            [self.video_name,
             self.video_id,
             self.default_subtitles_id,
             self.default_subtitles_langs] = paramlist

            init_repo = models.init_repo()
            if not init_repo:
                return {"result": "error", "message": "Error connecting to database"}

            self.init_repo_id = init_repo
            self.current_repo_id = init_repo
            self.current_repo_name = self.default_subtitles_langs[0]
            self.initialized = True
            return {"result": "success"}

    @XBlock.json_handler
    def activate(self):
        repos = models.get_repos_list_for_video(self.video_id, self.course_id)
        subs = models.get_sjson_subtitles(self.current_repo_id)
        models.subscribe(self.current_repo_id, self.location, self.user_id())
        return {
            "result": "success",
            "data": {
                "repos": repos,
                "subs": subs,
                "current_repo": self.current_repo_id
            }
        }

    def push_update(self):
        notifications_service = self.runtime.service(self, 'notifications')
        msg_type = notifications_service.get_notification_type('open-edx.xblock.edit_subs.subtitle_update')
        initiator = self.username
        msg = NotificationMessage(
            msg_type=msg_type,
            namespace=unicode(self.current_repo_id),
            expires_at=datetime.datetime.now()+datetime.timedelta(seconds=10),
            payload={
                '_schema_version': 1,
                'action_username': initiator,
                'activity_name': 'subtitles_update'
            }
        )
        user_ids = models.get_subscribers(self.current_repo_id)
        notifications_service.bulk_publish_notification_to_users(
            user_ids, msg, exclude_user_ids=[initiator])

    def notify_repo_create(self):
        notifications_service = self.runtime.service(self, 'notifications')
        msg_type = notifications_service.get_notification_type('open-edx.xblock.edit_subs.repo_create')
        initiator = self.user_id
        msg = NotificationMessage(
            msg_type=msg_type,
            namespace=unicode(self.location),
            expires_at=datetime.datetime.now()+datetime.timedelta(seconds=10),
            payload={
                '_schema_version': 1,
                'action_username': initiator,
                'activity_name': 'subtitles_update'
            }
        )
        user_ids = models.get_subscribers(self.current_repo_id)
        notifications_service.bulk_publish_notification_to_users(
            user_ids, msg, exclude_user_ids=[initiator])

    def convert_contentstore_subs_to_xblock(self):
        sjson_subs = Transcript.asset(
            self.location,
            self.default_subtitles_id,
            self.default_subtitles_langs[0]
            )
        return sjson_subs

    def save_subtitles_to_contentstore(self, repo_id, lang):
        """
        Save sjson subtitles from module to sjson file in contentstore
        """
        sjson_subs = models.get_sjson_subtitles(repo_id)
        result = xmodule.video_module.save_subs_to_store(
            sjson_subs,
            self.default_subtitles_id,
            self,
            lang
        )
        if result:
            return {"result": "success"}
        return {"result": "error"}

    @XBlock.json_handler
    def get_subtitles(self, data):
        return models.get_sjson_subtitles(data["repo_id"])

    @not_banned
    def add_subtitle(self, data):
        query = models.add_subtitle(
            text=data["text"],
            start=data["start"],
            end=data["end"],
            repo_id=self.current_repo,
            course_id=self.course_id,
            username=self.username()
        )
        if query:
            return {"result": "success"}
        return {"result": "error"}

    @XBlock.json_handler
    def create_repository(self, data):
        query = models.create_repos(
            name=data["name"],
            description=data["description"],
            course_id=self.course_id,
            username=self.username(),
            lang_tag=data["lang_tag"]
        )
        if query:
            return {"result": "success"}
        return {"result": "error"}

    @XBlock.json_handler
    def switch_to_repository(self, data):
        self.current_repo_id = data["repo_id"]
        query = models.get_sjson_subtitles(self.current_repo)
        if query:
            return {"result": "success", "data": query}
        return {"result": "error"}

    @XBlock.json_handler
    @not_banned
    def rate_positive(self, data):
        query = models.vote(
            data["subtitle_id"],
            self.username,
            value='plus'
        )
        if query:
            return {"result": "success"}
        return {"result": "error"}

    @XBlock.json_handler
    @not_banned
    def rate_negative(self, data):
        query = models.vote(
            data["subtitle_id"],
            self.username,
            value='minus'
        )
        if query:
            return {"result": "success"}
        return {"result": "error"}

    @XBlock.json_handler
    @staff
    def ban_user(self, data):
        query = models.ban_user(
            username=data["username"],
            course_id=self.course_id,
            moderator=self.username()
        )
        if query:
            return {"result": "success", "data": query}
        return {"result": "error"}

    def __del__(self):
        models.unsubscribe(self.user_id(), self.location, self.current_repo_id)

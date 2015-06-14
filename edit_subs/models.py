import mongoengine
import datetime
from collections import OrderedDict
# mongoengine.connect('edit_subs')
mongoengine.connect('test')

class NotificationSubscribers(mongoengine.Document):
    repo_id = mongoengine.ObjectIdField(required=True)
    user_id = mongoengine.StringField(required=True)
    location = mongoengine.StringField(required=True)
    meta = {
        'indexes': [
            ('repo_id', 'user_id'),
            ('location', 'user_id')
        ]
    }

class ActionEvent(mongoengine.EmbeddedDocument):
    by = mongoengine.StringField(required=True)
    at = mongoengine.DateTimeField(default=datetime.datetime.now)
    meta = {'allow_inheritance': True}

class Repos(mongoengine.Document):
    name = mongoengine.StringField(required=True)
    description = mongoengine.StringField(required=True)
    course_id = mongoengine.ListField(mongoengine.StringField(required=True), default=[])
    video_id = mongoengine.StringField(required=True)
    language_tag = mongoengine.StringField()
    created = mongoengine.EmbeddedDocumentField(ActionEvent)
    owner = mongoengine.StringField()
    meta = {
        'indexes': [
            'course_id',
            'video_id'
        ]
    }

class BanFacts(mongoengine.Document):
    username = mongoengine.StringField(required=True)
    course_id = mongoengine.StringField(required=True, unique_with='username')
    banned = mongoengine.EmbeddedDocumentField(ActionEvent)
    meta = {
        'indexes': [
            ('username', 'course_id')
        ]
    }

class Votes(ActionEvent):
    value = mongoengine.StringField(required=True, choices=('plus', 'minus'))


class Rating(mongoengine.EmbeddedDocument):
    total = mongoengine.IntField(default=1)
    totalPlus = mongoengine.IntField(default=1)
    totalMinus = mongoengine.IntField(default=0)
    updated_at = mongoengine.DateTimeField()
    votes = mongoengine.ListField(mongoengine.EmbeddedDocumentField(Votes), default=[])


class Subtitles(mongoengine.Document):
    text = mongoengine.StringField(required=True)
    start = mongoengine.IntField(required=True)
    duration = mongoengine.IntField(required=True)
    repo_id = mongoengine.ObjectIdField(required=True)
    course_id = mongoengine.StringField(required=True)
    created = mongoengine.EmbeddedDocumentField(ActionEvent)
    rating = mongoengine.EmbeddedDocumentField(Rating)
    deleted = mongoengine.BooleanField(default=False)
    meta = {
        'indexes': [
            ('text', 'deleted'),
            ('repo_id', 'deleted'),
            ('course_id', 'deleted'),
            ('start', 'deleted'),
            ('repo_id', '-rating.total', '-rating.rating.updated_at', 'deleted')
        ]
    }

def subscribe(repo_id, location,  username):
    return NotificationSubscribers.objects.insert(repo_id=repo_id, username=username)

def change_repo_subscribe(username, location, old_repo, new_repo):
    return NotificationSubscribers.objects(
        username=username,
        location=location,
        repo=old_repo).update_one(repo=new_repo)

def unsubscribe(user_id, repo_id):
    user_subscribe = NotificationSubscribers.objects(repo_id=repo_id, user_id=user_id).first()
    return user_subscribe.delete()

def get_subscribers(repo_id):
    return NotificationSubscribers.objects(repo_id=repo_id).only('user_id')

def create_repos(name, description, course_id, username, lang_tag=None):
    """
    Create public and private repos

    :param name: str
    :param description: str
    :param course_id: str
    :param username: str
    :param lang_tag: str
    :return: object
    """
    repo = Repos(
        name=name,
        description=description,
        course_id=course_id,
        language_tag=lang_tag,
        created=ActionEvent(by=username)
    )

    owned_repo = Repos(
        name=name + "_private",
        description=description + "\nThis is a private repo",
        course_id=course_id,
        language_tag=lang_tag,
        created=ActionEvent(by=username),
        owner=username
    )
    return Repos.objects.insert([repo, owned_repo])


def clone_repo(current_repo, new_repo):
    pass
    # current_repo_subtitles = get_best_subtitles(current_repo)

    #return Subtitles.objects(id__in=objectids).update(push__repo_id=new_repo)


def get_repos_list_for_video(video_id, course_id):
    return Repos.objects(video_id=video_id, course_id=course_id)


def get_repos_list_for_course(course_id):
    return Repos.objects(course_id=course_id)

def ban_user(username, course_id, moderator):
    return BanFacts.objects.insert(
        username=username,
        course_id=course_id,
        banned=ActionEvent(by=moderator)
    )

def user_is_not_banned(username, course_id):
    courses = BanFacts.objects(username=username,
                               course_id=course_id).first()
    return courses is None


def get_best_subtitles(repo_id):
    """

    :return : dict
    """
    cursor = Subtitles._get_collection().aggregate([
        {"$match": {"repo_id": repo_id, "deleted": False}},
        {"$project": {"_id": 1, "text": 1, "start": 1, "duration": 1,
                      "rating.total": 1, "created.at": 1}},
        {"$sort": OrderedDict([("rating.total", -1), ("rating.votes.time", -1)])},
        {"$group": {
            "_id": "$start",
            "start": {"$first": "$start"},
            "duration": {"$first": "$duration"},
            "text": {"$first": "$text"},
            "rating": {"$first": "$rating.total"},
            "id": {"$first": "$$ROOT._id"}
        }
         },
        {"$sort": {"_id": 1}}
    ])
    return cursor['result']

def get_sjson_subtitles(repo_id):
    """
    Get subtitles for given repo from database converted to SJSON

    :param repo_id: ObjectId
    :return: object containing SJSON subtitles
    :rtype : dict
    """
    cursor = Subtitles._get_collection().aggregate([
        {"$match": {"repo_id": repo_id, "deleted": False}},
        {"$project": {"_id": 1, "text": 1, "start": 1, "duration": 1,
         "repo_id": 1, "rating.total": 1, "created.at": 1}},
        {"$sort": OrderedDict([("rating.total", -1), ("created.at", -1)])},
        {"$group": {
            "_id": "$start",
            "start": {"$first": "$start"},
            "duration": {"$first": "$duration"},
            "text": {"$first": "$text"},
            "rating": {"$first": "$rating.total"},
            "id": {"$first": "$$ROOT._id"}
            }
        },
        {"$sort": {"_id": 1}},
        {"$group": {
            "_id": None,
            "start": {"$push": "$start"},
            "duration": {"$push": "$duration"},
            "text": {"$push": "$text"},
            "rating": {"$push": "$rating"},
            "id": {"$push": "$id"}
        }}
    ])
    return cursor['result']


def add_subtitle(text, start, duration, repo_id, video_id, course_id, username):
    """
    Insert user's subtitle to given repo

    :param text: str
    :param start: int
    :param duration: int
    :param repo_id: ObjectId
    :param username: str
    :return: object
    """
    subtitle = Subtitles.objects(repo_id=repo_id, text=text).first()
    if subtitle:
        vote(subtitle.id, username, 'plus')
    else:
        query = Subtitles.objects(
            repo_id=repo_id,
            start=start,
            initial=True
        ).update(
            upsert=True,
            multi=False,
            text=text,
            start=start,
            duration=duration,
            repo_id=repo_id,
            course_id=course_id,
            created=ActionEvent(by=username),
            rating=Rating(votes=[Votes(username=username, value='plus')]),
            unset__initial=1
        )
        return query

def _user_rated_subtitle(subtitle_id, username):
    """
    Have the user rated that subtitle? If yes, return value. If no, return None

    Need to reimplement
    Returns:
        str or None
    """
    cursor = Subtitles._get_collection().aggregate([
        {"$match": {"_id": subtitle_id, "rating.votes.username": username}},
        {"$project": {"rating.votes.username": 1, "rating.votes.value": 1}},
        {"$unwind": "$rating.votes"},
        {"$match": {"rating.votes.username": username}}
    ])
    if cursor["result"]:
        return cursor["result"][0]["rating"]["votes"]["value"]
    return None


def _change_current_vote(subtitle_id, username, value):
    """
    Changes current vote
    :param subtitle_id: ObjectId
    :param username: str
    :param value: str. May be 'minus' or 'plus'
    :return: object
    """
    if value is 'minus':
        return Subtitles.objects(
            id=subtitle_id,
            rating__votes__match={"username":username, "value":value}
        ).modify(
            inc__rating__totalPlus=1,
            inc__rating__total=2,
            dec__rating__totalMinus=1,
            set__rating__votes__S__value='plus',
            set__rating__votes__S__time=datetime.datetime.now
        )
    if value is 'plus':
        return Subtitles.objects(
            id=subtitle_id,
            rating__votes__match={"username": username, "value": value}
        ).modify(
            inc__rating__totalMinus=1,
            dec__rating__total=2,
            dec__rating__totalPlus=1,
            set__rating__votes__S__value='minus',
            set__rating__votes__S__time=datetime.datetime.now
        )

def vote(subtitle_id, username, value):
    """
    Vote for given subtitle

    :param subtitle_id: ObjectId
    :param username: str
    :param value: str. May be 'minus' or 'plus'
    :return: object, result of the operation
    """
    possible_votes = ('plus', 'minus')
    current_vote = _user_rated_subtitle(subtitle_id, username)
    if current_vote is value:
        return {"error": "You have already voted"}
    if current_vote in possible_votes:
        return _change_current_vote(subtitle_id, username, current_vote)
    if value is 'minus':
        return Subtitles.objects(id=id).update(
            rating__updated_at=datetime.datetime.now(),
            inc__rating__totalMinus=1,
            dec__rating__total=1,
            push__rating__votes=Votes(username=username, value='minus')
        )
    if value is 'plus':
        return Subtitles.objects(id=subtitle_id).update(
            inc__rating__totalPlus=1,
            inc__rating__total=1,
            push__rating__votes=Votes(username=username, value='plus')
        )

def remove_subtitle(subtitle_id):
    """
    Remove subtitle with given subtitle_id
    :param subtitle_id: ObjectId
    :return: object
    """
    return Subtitles.objects(id=subtitle_id).update_one(deleted=True)



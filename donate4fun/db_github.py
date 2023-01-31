from sqlalchemy.orm.exc import NoResultFound  # noqa

from .models import GithubUser, GithubUserOwned
from .db_models import GithubUserDb, GithubUserLink
from .db_social import SocialDbWrapper


class GithubDbLib(SocialDbWrapper):
    db_model = GithubUserDb
    link_db_model = GithubUserLink
    model = GithubUser
    owned_model = GithubUserOwned
    donation_column = 'github_user_id'
    name = 'github'
    donation_field = 'github_user'
    db_model_name_column = 'name'
    db_model_thumbnail_url_column = 'avatar_url'

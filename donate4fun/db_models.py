from sqlalchemy import Column, TIMESTAMP, String, BigInteger, ForeignKey, func, text, Boolean
from sqlalchemy.dialects.postgresql import UUID as Uuid, JSONB
from sqlalchemy.orm import declarative_base, relationship, foreign
from sqlalchemy.schema import CheckConstraint, Index

Base = declarative_base()


class DonateeDb(Base):
    __abstract__ = True
    balance = Column(BigInteger, nullable=False, server_default=text('0'))
    total_donated = Column(BigInteger, nullable=False, server_default=text('0'))
    last_fetched_at = Column(TIMESTAMP)


class YoutubeChannelDb(DonateeDb):
    __tablename__ = 'youtube_channel'
    __table_args__ = dict(info=dict(
        external_key='channel_id',
    ))

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())

    channel_id = Column(String, unique=True, nullable=False)
    title = Column(String)
    thumbnail_url = Column(String)
    banner_url = Column(String)
    handle = Column(String)
    lightning_address = Column(String)

    links = relationship('YoutubeChannelLink', viewonly=True)


class YoutubeVideoDb(Base):
    __tablename__ = 'youtube_video'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    video_id = Column(String, unique=True, nullable=False)
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), nullable=False)
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')
    title = Column(String)
    thumbnail_url = Column(String)
    default_audio_language = Column(String)

    total_donated = Column(BigInteger, nullable=False, server_default=text('0'))


class TwitterTweetDb(Base):
    __tablename__ = 'twitter_tweet'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    tweet_id = Column(BigInteger, unique=True, nullable=False)


class TwitterAuthorDb(DonateeDb):
    __tablename__ = 'twitter_author'
    __table_args__ = dict(info=dict(
        external_key='user_id',
    ))

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())

    user_id = Column(BigInteger, unique=True, nullable=False)
    handle = Column(String, nullable=False)
    name = Column(String)
    profile_image_url = Column(String)
    lightning_address = Column(String)

    links = relationship('TwitterAuthorLink', viewonly=True)


class GithubUserDb(DonateeDb):
    __tablename__ = 'github_user'
    __table_args__ = dict(info=dict(
        external_key='user_id',
    ))

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())

    user_id = Column(BigInteger, unique=True, nullable=False)
    login = Column(String, nullable=False)
    avatar_url = Column(String)
    name = Column(String)


class DonatorDb(Base):
    __tablename__ = 'donator'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String)
    avatar_url = Column(String)
    lnauth_pubkey = Column(String, unique=True)
    balance = Column(BigInteger, nullable=False, server_default=text('0'))
    lightning_address = Column(String, unique=True)

    linked_youtube_channels = relationship(
        YoutubeChannelDb,
        lazy='noload',
        foreign_keys=lambda: YoutubeChannelLink.donator_id,
        secondary=lambda: YoutubeChannelLink.__table__,
        primaryjoin=lambda: DonatorDb.id == YoutubeChannelLink.donator_id,
        secondaryjoin=lambda: YoutubeChannelDb.id == foreign(YoutubeChannelLink.youtube_channel_id),
    )
    linked_twitter_authors = relationship(
        TwitterAuthorDb,
        lazy='noload',
        foreign_keys=lambda: TwitterAuthorLink.donator_id,
        secondary=lambda: TwitterAuthorLink.__table__,
        primaryjoin=lambda: DonatorDb.id == TwitterAuthorLink.donator_id,
        secondaryjoin=lambda: TwitterAuthorDb.id == foreign(TwitterAuthorLink.twitter_author_id),
    )
    linked_github_users = relationship(
        GithubUserDb,
        lazy='noload',
        foreign_keys=lambda: GithubUserLink.donator_id,
        secondary=lambda: GithubUserLink.__table__,
        primaryjoin=lambda: DonatorDb.id == GithubUserLink.donator_id,
        secondaryjoin=lambda: GithubUserDb.id == foreign(GithubUserLink.github_user_id),
    )


def num_nonnulls(*columns):
    return 'num_nonnulls(' + ','.join(columns) + ')'


class DonationDb(Base):
    __tablename__ = 'donation'
    __table_args__ = (
        CheckConstraint(
            num_nonnulls('receiver_id', 'youtube_channel_id', 'twitter_account_id') + '=1',
            name='has_a_single_target',
        ),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # This field is set only if local LND has been used for the donation
    # For donations from an external wallet to an external lightning address this field is None
    # Encoding is base64
    r_hash = Column(String, unique=True)
    # For transient donations (look at models.py for description)
    transient_r_hash = Column(String, unique=True)
    amount = Column(BigInteger, nullable=False)
    fee_msat = Column(BigInteger)
    donator_id = Column(Uuid(as_uuid=True))
    donator = relationship(
        DonatorDb, lazy='joined', foreign_keys=[donator_id], primaryjoin=lambda: DonationDb.donator_id == DonatorDb.id,
    )
    paid_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)
    claimed_at = Column(TIMESTAMP)

    # FIXME: split this table to multiple tables one for each social provider
    receiver_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id))
    receiver = relationship(DonatorDb, lazy='joined', foreign_keys=[receiver_id])

    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id))
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')

    youtube_video_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeVideoDb.id))
    youtube_video = relationship(YoutubeVideoDb, lazy='joined')

    twitter_account_id = Column(Uuid(as_uuid=True), ForeignKey(TwitterAuthorDb.id))
    twitter_account = relationship(TwitterAuthorDb, lazy='joined', foreign_keys=[twitter_account_id])

    twitter_tweet_id = Column(Uuid(as_uuid=True), ForeignKey(TwitterTweetDb.id))
    twitter_tweet = relationship(TwitterTweetDb, lazy='joined', foreign_keys=[twitter_tweet_id])

    twitter_invoice_tweet_id = Column(BigInteger)

    github_user_id = Column(Uuid(as_uuid=True), ForeignKey(GithubUserDb.id))
    github_user = relationship(GithubUserDb, lazy='joined')

    lightning_address = Column(String)

    donator_twitter_account_id = Column(Uuid(as_uuid=True), ForeignKey(TwitterAuthorDb.id))
    donator_twitter_account = relationship(TwitterAuthorDb, lazy='joined', foreign_keys=[donator_twitter_account_id])


class BaseLink(Base):
    __abstract__ = True
    donator_id = Column(Uuid(as_uuid=True), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    via_oauth = Column(Boolean, server_default='f')


class YoutubeChannelLink(BaseLink):
    __tablename__ = 'youtube_channel_link'
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), primary_key=True)
    __table_args__ = (
        Index('youtube_only_one_oauth_link', youtube_channel_id, unique=True, postgresql_where='via_oauth'),
    )


class TwitterAuthorLink(BaseLink):
    __tablename__ = 'twitter_author_link'
    twitter_author_id = Column(Uuid(as_uuid=True), ForeignKey(TwitterAuthorDb.id), primary_key=True)
    __table_args__ = (
        Index('twitter_only_one_oauth_link', twitter_author_id, unique=True, postgresql_where='via_oauth'),
    )


class GithubUserLink(BaseLink):
    __tablename__ = 'github_user_link'
    github_user_id = Column(Uuid(as_uuid=True), ForeignKey(GithubUserDb.id), primary_key=True)
    __table_args__ = (
        Index('github_only_one_oauth_link', github_user_id, unique=True, postgresql_where='via_oauth'),
    )


class WithdrawalDb(Base):
    """
    Withdrawal from donator balance (or from youtube/twitter unitl migration to TransferDb) to his lightning wallet
    """
    __tablename__ = 'withdrawal'
    __table_args__ = (
        CheckConstraint(
            num_nonnulls('youtube_channel_id', 'twitter_author_id') + '<=1',
            name='has_a_single_target',
        ),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    amount = Column(BigInteger)
    fee_msat = Column(BigInteger)
    created_at = Column(TIMESTAMP, nullable=False)
    paid_at = Column(TIMESTAMP)
    donator_id = Column(Uuid(as_uuid=True), nullable=False)
    donator = relationship(
        DonatorDb, lazy='joined', foreign_keys=[donator_id], primaryjoin=lambda: WithdrawalDb.donator_id == DonatorDb.id,
    )

    # These are deprecated fields and should not be used anymore
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id))
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')

    twitter_author_id = Column(Uuid(as_uuid=True), ForeignKey(TwitterAuthorDb.id))
    twitter_author = relationship(TwitterAuthorDb, lazy='joined')


class TransferDb(Base):
    """
    Transfer from donation target (youtube, twitter, etc.) to a donator balance
    """
    __tablename__ = 'transfer'
    __table_args__ = (
        CheckConstraint(
            num_nonnulls('youtube_channel_id', 'twitter_author_id', 'github_user_id') + '=1',
            name='has_a_single_target',
        ),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    amount = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    donator_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id), nullable=False)

    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id))
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')

    twitter_author_id = Column(Uuid(as_uuid=True), ForeignKey(TwitterAuthorDb.id))
    twitter_author = relationship(TwitterAuthorDb, lazy='joined')

    github_user_id = Column(Uuid(as_uuid=True), ForeignKey(GithubUserDb.id))
    github_user = relationship(GithubUserDb, lazy='joined')


class EmailNotificationDb(Base):
    __tablename__ = 'email_notification'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    email = Column(String, unique=True)
    created_at = Column(TIMESTAMP, nullable=False)


class OAuthTokenDb(Base):
    __tablename__ = 'oauth_token'

    name = Column(String, primary_key=True)
    token = Column(JSONB, nullable=False)


Base.registry.configure()  # Create backrefs

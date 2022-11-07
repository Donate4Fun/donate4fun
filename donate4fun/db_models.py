from sqlalchemy import Column, TIMESTAMP, String, BigInteger, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID as Uuid
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class YoutubeChannelDb(Base):
    __tablename__ = 'youtube_channel'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    channel_id = Column(String, unique=True, nullable=False)
    title = Column(String)
    thumbnail_url = Column(String)
    balance = Column(BigInteger, nullable=False, server_default=text('0'))
    total_donated = Column(BigInteger, nullable=False, server_default=text('0'))
    last_fetched_at = Column(TIMESTAMP)


class YoutubeVideoDb(Base):
    __tablename__ = 'youtube_video'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    video_id = Column(String, unique=True, nullable=False)
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), nullable=False)
    title = Column(String)
    thumbnail_url = Column(String)
    total_donated = Column(BigInteger, nullable=False, server_default=text('0'))
    default_audio_language = Column(String)

    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')


class DonatorDb(Base):
    __tablename__ = 'donator'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String)
    avatar_url = Column(String)
    lnauth_pubkey = Column(String, unique=True)
    balance = Column(BigInteger, nullable=False, server_default=text('0'))

    linked_youtube_channels = relationship(
        YoutubeChannelDb,
        lazy='noload',
        secondary=lambda: Base.metadata.tables['youtube_channel_link'],
    )


class DonationDb(Base):
    __tablename__ = 'donation'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    r_hash = Column(String, unique=True)
    amount = Column(BigInteger, nullable=False)
    donator_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id), nullable=False)
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id))
    youtube_video_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeVideoDb.id))
    receiver_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    paid_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)

    donator = relationship(DonatorDb, lazy='joined', foreign_keys=[donator_id])
    receiver = relationship(DonatorDb, lazy='joined', foreign_keys=[receiver_id])
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')
    youtube_video = relationship(YoutubeVideoDb, lazy='joined')


class YoutubeChannelLink(Base):
    __tablename__ = 'youtube_channel_link'

    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), primary_key=True)
    donator_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class WithdrawalDb(Base):
    __tablename__ = 'withdrawal'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    donator_id = Column(Uuid(as_uuid=True), ForeignKey(DonatorDb.id), nullable=False)
    youtube_channel_id = Column(Uuid(as_uuid=True), ForeignKey(YoutubeChannelDb.id), nullable=False)
    amount = Column(BigInteger)

    created_at = Column(TIMESTAMP, nullable=False)
    paid_at = Column(TIMESTAMP)

    donator = relationship(DonatorDb, lazy='joined')
    youtube_channel = relationship(YoutubeChannelDb, lazy='joined')


class EmailNotificationDb(Base):
    __tablename__ = 'email_notification'

    id = Column(Uuid(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    email = Column(String, unique=True)
    created_at = Column(TIMESTAMP, nullable=False)


Base.registry.configure()  # Create backrefs

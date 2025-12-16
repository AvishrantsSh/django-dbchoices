from enum import Enum


class Status(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Genre(Enum):
    COMEDY = "comedy"
    DRAMA = "drama"
    HORROR = "horror"
    ACTION = "action"

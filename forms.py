from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    SelectMultipleField,
    IntegerField,
    BooleanField,
    DateTimeField,
)

from wtforms.validators import (
    DataRequired,
    URL,
    Length,
    InputRequired,
    ValidationError,
)

STATES = [
    ("Alabama", "AL"),
    ("Alaska", "AK"),
    ("Arizona", "AZ"),
    ("Arkansas", "AR"),
    ("California", "CA"),
    ("Colorado", "CO"),
    ("Connecticut", "CT"),
    ("Delaware", "DE"),
    ("Washington", "DC"),
    ("Florida", "FL"),
    ("Georgia", "GA"),
    ("Hawaii", "HI"),
    ("Idaho", "ID"),
    ("Illinois", "IL"),
    ("Indiana", "IN"),
    ("Iowa", "IA"),
    ("Kansas", "KS"),
    ("Kentucky", "KY"),
    ("Louisiana", "LA"),
    ("Maine", "ME"),
    ("Montana", "MT"),
    ("Nebraska", "NE"),
    ("Nevada", "NV"),
    ("New Hampshire", "NH"),
    ("New Jersey", "NJ"),
    ("New Mexico", "NM"),
    ("New York", "NY"),
    ("North Carolina", "NC"),
    ("North Dakota", "ND"),
    ("Ohio", "OH"),
    ("Oklahoma", "OK"),
    ("Oregon", "OR"),
    ("Maryland", "MD"),
    ("Massachusetts", "MA"),
    ("Michigan", "MI"),
    ("Minnesota", "MN"),
    ("Mississippi", "MS"),
    ("Missouri", "MO"),
    ("Pennsylvania ", "PA"),
    ("Rhode Island", "RI"),
    ("South Carolina", "SC"),
    ("South Dakota", "SD"),
    ("Tennessee", "TN"),
    ("Texas", "TX"),
    ("Utah", "UT"),
    ("Vermont", "VT"),
    ("Virginia", "VA"),
    ("Washington", "WA"),
    ("West Virginia", "WV"),
    ("Wisconsin", "WI"),
    ("Wyoming", "WY"),
]

GENRES = [
    ("Alternative", "Alternative"),
    ("Blues", "Blues"),
    ("Classical", "Classical"),
    ("Country", "Country"),
    ("Electronic", "Electronic"),
    ("Folk", "Folk"),
    ("Funk", "Funk"),
    ("Hip-Hop", "Hip-Hop"),
    ("Heavy Metal", "Heavy Metal"),
    ("Instrumental", "Instrumental"),
    ("Jazz", "Jazz"),
    ("Musical Theatre", "Musical Theatre"),
    ("Pop", "Pop"),
    ("Punk", "Punk"),
    ("R&B", "R&B"),
    ("Reggae", "Reggae"),
    ("Rock n Roll", "Rock n Roll"),
    ("Soul", "Soul"),
    ("Other", "Other"),
]


def validate_phone(form, field):
    if not field.data.isdecimal():
        raise ValidationError("Invalid phone number")


class VenueForm(FlaskForm):
    name = StringField(
        "name",
        validators=[InputRequired(), Length(min=1, max=120)],
    )
    city = StringField("city", validators=[DataRequired(), Length(min=1, max=120)])
    state = SelectField("state", validators=[DataRequired()], choices=STATES)
    address = StringField(
        "address", validators=[DataRequired(), Length(min=1, max=120)]
    )
    phone = StringField(
        "phone",
        validators=[DataRequired(), validate_phone],
    )
    image_link = StringField("image_link", validators=[URL()])
    genres = SelectMultipleField(
        # TODO Done implement enum restriction
        "genres",
        validators=[DataRequired()],
        choices=GENRES,
    )
    facebook_link = StringField("facebook_link", validators=[URL()])
    website = StringField("website", validators=[URL()])
    seeking_talent = BooleanField("seeking_talent")
    seeking_description = StringField("seeking_description")


class ArtistForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField("state", validators=[DataRequired()], choices=STATES)
    phone = StringField("phone", validators=[DataRequired(), validate_phone])
    image_link = StringField("image_link", validators=[URL()])
    genres = SelectMultipleField(
        "genres",
        validators=[DataRequired()],
        choices=GENRES,
    )
    facebook_link = StringField(
        "facebook_link",
        validators=[URL()],
    )
    website = StringField("website", validators=[URL()])
    seeking_venue = BooleanField("seeking_venue")
    seeking_description = StringField("seeking_description")


class ShowForm(FlaskForm):
    artist_id = IntegerField("artist_id", validators=[DataRequired()])
    venue_id = IntegerField("venue_id", validators=[DataRequired()])
    start_time = DateTimeField(
        "start_time",
        validators=[DataRequired(message="Please enter a valid date and time")],
        default=datetime.today(),
    )


# TODO Done IMPLEMENT NEW ARTIST FORM AND NEW SHOW FORM

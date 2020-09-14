# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import sys
from datetime import datetime
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    abort,
)
from flask_moment import Moment
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import logging
from logging import Formatter, FileHandler
from forms import VenueForm, ShowForm, ArtistForm
from flask_migrate import Migrate
from itertools import chain
from models import Venue, Artist, Show, db

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)

# TODO Done: connect to a local postgresql database
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters and Helper Functions
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


# Function to get unique values
def unique(list):
    unique_list = []
    for x in list:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list


def getShowData(showlist):
    data = []
    for show in showlist:
        showdata = {}
        showdata["id"] = show.id
        showdata["venue_id"] = show.venue_id
        showdata["artist_id"] = show.artist_id
        showdata["venue_name"] = Venue.query.get(show.venue.id).name
        showdata["artist_name"] = Artist.query.get(show.artist_id).name
        showdata["artist_image_link"] = Artist.query.get(show.artist_id).image_link
        showdata["start_time"] = (show.start_time).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        data.append(showdata)
    return data


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  VENUES
#  ----------------------------------------------------------------

#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # TODO Done: insert form data as a new Venue record in the db, instead
    # TODO Done: modify data to be the data object returned from db insertion
    form = VenueForm(request.form)

    if not form.validate_on_submit():
        return render_template("forms/new_venue.html", form=form)

    error = False
    try:
        venue = Venue()
        form.populate_obj(venue)
        db.session.add(venue)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured. Venue " + form.name.data + " could not be listed.")
    else:
        flash("Venue " + form.name.data + " was successfully listed!")

    # on successful db insert, flash success
    # TODO Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


#  Read Venue
#  ----------------------------------------------------------------
@app.route("/venues")
def venues():
    # TODO Done: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    venues = Venue.query.order_by("city", "state").all()

    citiesAndStates = []
    for venue in venues:
        citiesAndStates.append([venue.city, venue.state])
    citiesAndStates = unique(citiesAndStates)

    areas = []

    for cityAndState in citiesAndStates:
        area = {}
        area["city"] = cityAndState[0]
        area["state"] = cityAndState[1]
        filteredVenues = Venue.query.filter_by(
            city=cityAndState[0], state=cityAndState[1]
        ).all()
        venues = []
        for ven in filteredVenues:
            venu = {}
            venu["id"] = ven.id
            venu["name"] = ven.name
            venu["num_upcoming_shows"] = Show.query.filter(
                Show.start_time >= datetime.now(), Show.venue_id == ven.id
            ).count()
            venues.append(venu)
        area["venues"] = venues
        areas.append(area)

    return render_template("pages/venues.html", areas=areas)


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue_info = Venue.query.options(
        joinedload("shows").options(joinedload("artist"))
    ).get(venue_id)

    data = venue_info.__dict__
    past_shows = [r.__dict__ for r in venue_info.shows if r.start_time < datetime.now()]
    upcoming_shows = [
        r.__dict__ for r in venue_info.shows if r.start_time >= datetime.now()
    ]

    for show in past_shows:
        show["start_time"] = show["start_time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        show["artist_image_link"] = show["artist"].__dict__["image_link"]
        show["artist_name"] = show["artist"].__dict__["name"]

    for show in upcoming_shows:
        show["start_time"] = show["start_time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        show["artist_image_link"] = show["artist"].__dict__["image_link"]
        show["artist_name"] = show["artist"].__dict__["name"]

    data["past_shows"] = past_shows
    data["upcoming_shows"] = upcoming_shows
    data["past_shows_count"] = len(past_shows)
    data["upcoming_shows_count"] = len(upcoming_shows)

    return render_template("pages/show_venue.html", venue=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO Done: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    searchTerm = request.form.to_dict()["search_term"]
    searchResult = Venue.query.filter(Venue.name.ilike("%" + searchTerm + "%")).all()
    response = {}
    response["count"] = len(searchResult)

    data = []
    for venue in searchResult:
        body = {}
        body["id"] = venue.id
        body["name"] = venue.name
        body["num_upcoming_shows"] = Show.query.filter(
            Show.venue_id == venue.id, Show.start_time >= datetime.now()
        ).count()
        data.append(body)

    response["data"] = data

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


#  Update Venue
#  ----------------------------------------------------------------


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    # TODO Done: populate form with values from venue with ID <venue_id>
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # TODO Done: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)

    if not form.validate_on_submit():
        return render_template("forms/edit_venue.html", form=form, venue=venue)

    error = False
    try:
        form.populate_obj(venue)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured.  Venue " + form.name.data + " could not be edited.")
    else:
        flash("Venue " + form.name.data + " was successfully edited!")
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Delete Venue
#  ----------------------------------------------------------------


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # TODO Done: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured.  Venue could not be deleted!")
    else:
        flash("Venue was successfully deleted!")

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for("index"), code=200)


#  ARTISTS
#  ----------------------------------------------------------------

#  Create Artist
#  ----------------------------------------------------------------
@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO Done: insert form data as a new Venue record in the db, instead
    # TODO Done: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)

    if not form.validate_on_submit():
        return render_template("forms/new_artist.html", form=form)

    error = False
    try:
        artist = Artist()
        form.populate_obj(artist)
        db.session.add(artist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured. Artist " + form.name.data + " could not be listed!")
    else:
        flash("Artist " + form.name.data + " was successfully listed!")

    # TODO Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template("pages/home.html")


#  Read Artist
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # TODO Done: replace with real data returned from querying the database

    artists = Artist.query.order_by("id").all()
    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist_info = Artist.query.options(
        joinedload("shows").options(joinedload("venue"))
    ).get(artist_id)

    data = artist_info.__dict__
    past_shows = [
        r.__dict__ for r in artist_info.shows if r.start_time < datetime.now()
    ]
    upcoming_shows = [
        r.__dict__ for r in artist_info.shows if r.start_time >= datetime.now()
    ]

    for show in past_shows:
        show["start_time"] = show["start_time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        show["venue_image_link"] = show["venue"].__dict__["image_link"]
        show["venue_name"] = show["venue"].__dict__["name"]

    for show in upcoming_shows:
        show["start_time"] = show["start_time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        show["venue_image_link"] = show["venue"].__dict__["image_link"]
        show["venue_name"] = show["venue"].__dict__["name"]

    data["past_shows"] = past_shows
    data["upcoming_shows"] = upcoming_shows
    data["past_shows_count"] = len(past_shows)
    data["upcoming_shows_count"] = len(upcoming_shows)

    return render_template("pages/show_artist.html", artist=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO Done: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    searchTerm = request.form.to_dict()["search_term"]
    searchResult = Artist.query.filter(Artist.name.ilike("%" + searchTerm + "%")).all()
    response = {}
    response["count"] = len(searchResult)

    data = []
    for artist in searchResult:
        body = {}
        body["id"] = artist.id
        body["name"] = artist.name
        body["num_upcoming_shows"] = Show.query.filter(
            Show.artist_id == artist.id, Show.start_time >= datetime.now()
        ).count()
        data.append(body)

    response["data"] = data

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


#  Update Artist
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    # TODO Done: populate form with fields from artist with ID <artist_id>
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # TODO Done: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)

    if not form.validate_on_submit():
        return render_template("forms/edit_artist.html", form=form, artist=artist)
    error = False

    try:
        form.populate_obj(artist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured.  Artist " + form.name.data + " could not be edited!")
    else:
        flash("Artist " + form.name.data + " was successfuly edited!")

    return redirect(url_for("show_artist", artist_id=artist_id))


#  Delete Artist
#  ----------------------------------------------------------------


@app.route("/artists/<artist_id>", methods=["DELETE"])
def delete_artist(artist_id):
    # TODO Done: Complete this endpoint
    error = False
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured.  Artist could not be deleted")
    else:
        flash("Artist was successfully deleted!")

    return redirect(url_for("index"), code=200)


#  SHOWS
#  ----------------------------------------------------------------

#  Create Show
#  ----------------------------------------------------------------


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO Done: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)

    validEntry = form.validate_on_submit()

    artistExists = Artist.query.filter_by(id=form.artist_id.data).scalar()
    venueExists = Venue.query.filter_by(id=form.venue_id.data).scalar()
    if artistExists is None:
        form.artist_id.errors.append("This artist does not exist")
        validEntry = False
    if venueExists is None:
        form.venue_id.errors.append("This venue does not exist")
        validEntry = False

    if not validEntry:
        return render_template("forms/new_show.html", form=form)

    error = False
    try:
        show = Show()
        form.populate_obj(show)
        db.session.add(show)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured. Show could not be listed!")
    else:
        flash("Show was successfully listed!")

    # TODO Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


#  Read Show
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO Done: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    past_shows = Show.query.filter(Show.start_time < datetime.now()).all()
    upcoming_shows = Show.query.filter(Show.start_time >= datetime.now()).all()

    pastshowdata = getShowData(past_shows)
    upcomingshowdata = getShowData(upcoming_shows)

    return render_template(
        "pages/shows.html", upcoming_shows=upcomingshowdata, past_shows=pastshowdata
    )


@app.route("/shows/search", methods=["POST"])
def search_shows():
    searchTerm = request.form.to_dict()["search_term"]
    venueSearch = (
        Venue.query.with_entities(Venue.id)
        .filter(Venue.name.ilike("%" + searchTerm + "%"))
        .all()
    )
    artistSearch = (
        Artist.query.with_entities(Artist.id)
        .filter(Artist.name.ilike("%" + searchTerm + "%"))
        .all()
    )

    showSearch = Show.query.filter(
        or_(
            Show.artist_id.in_(list(chain(*artistSearch))),
            Show.venue_id.in_(list(chain(*venueSearch))),
        )
    ).all()

    return render_template(
        "pages/search_shows.html",
        showcount=len(showSearch),
        shows=getShowData(showSearch),
        search_term=request.form.get("search_term", ""),
    )


#  Update Show
#  ----------------------------------------------------------------


@app.route("/shows/<int:show_id>/edit", methods=["GET"])
def edit_show(show_id):
    show = Show.query.get(show_id)
    form = ShowForm(obj=show)
    return render_template("forms/edit_show.html", form=form, show=show)


@app.route("/shows/<int:show_id>/edit", methods=["POST"])
def edit_show_submission(show_id):
    form = ShowForm(request.form)
    show = Show.query.get(show_id)

    validEntry = form.validate_on_submit()

    artistExists = Artist.query.filter_by(id=form.artist_id.data).scalar()
    venueExists = Venue.query.filter_by(id=form.venue_id.data).scalar()
    if artistExists is None:
        form.artist_id.errors.append("This artist does not exist")
        validEntry = False
    if venueExists is None:
        form.venue_id.errors.append("This venue does not exist")
        validEntry = False

    if not validEntry:
        return render_template("forms/edit_show.html", form=form, show=show)

    error = False
    try:
        form.populate_obj(show)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured.  Show id" + show.id + " could not be edited!")
    else:
        flash("Show was successfully edited!")

    return redirect(url_for("shows"))


#  Delete Show
#  ----------------------------------------------------------------


@app.route("/shows/<show_id>", methods=["DELETE"])
def delete_show(show_id):
    error = False
    try:
        show = Show.query.get(show_id)
        db.session.delete(show)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash("An error occured.  Show could not be deleted!")
    else:
        flash("Show was successfully deleted!")

    return redirect(url_for("index"), code=200)


#  Error Handlers
#  ----------------------------------------------------------------


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""

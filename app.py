#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

from enums import GenreEnum, StateEnum
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
#----------------------------------------------------------------------------#
#  INSTRUCTIONS
#----------------------------------------------------------------------------#
#----------------------------------------------------------------------------#
# > su postgres
# > createdb fyyur
# > psql fyyur
#
# =# \password
# =# abc
# =# abc
# =# \q
#
# > exit()
# > flask db upgrade && python3 app.py
#----------------------------------------------------------------------------#
#----------------------------------------------------------------------------#


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)
# TODO: connect to a local postgresql database
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    
    venues = Venue.query;
    areas = venues.distinct(Venue.city).all()
    
    data = []
    upcoming_show_count = 0
    
    for area in areas:
        venues_per_city = venues.filter_by(city=area.city)
        upcoming_show_count += venues_per_city.join(Show).count()
        
        data.append({
            "city": area.city,
            "state": area.state,
            "venues": venues_per_city.all()
        })
    
    return render_template('pages/venues.html', areas=data, num_upcoming_shows=upcoming_show_count)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    
    venues = Venue.query.filter(Venue.name.ilike(f"%{request.form.get('search_term', '')}%"));
    response = {
        "count": venues.count(),
        "data": []
    }
    
    for venue in venues:
        response['data'].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(venue.shows)
        })        

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    
    data = Venue.query.get(venue_id)
    data = data.__dict__
    data['genres'] = data['genres'].split(",")
    shows = Show.query.filter_by(venue_id=venue_id).join(Artist).all()
    
    data["past_shows"] = []
    data["upcoming_shows"] = []
    
    for show in shows:
        if show.start_time < datetime.utcnow():
            show_type =  "past_shows" 
        else:
            show_type = "upcoming_shows"
            
        data[show_type].append({
            "artist_id": show.artists.id,
            "artist_name": show.artists.name,
            "artist_image_link": show.artists.image_link,
            "start_time": show.start_time
        })
        
    data["past_shows_count"] = len(data["past_shows"])        
    data["upcoming_shows_count"] = len(data["upcoming_shows"])
    
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    form = VenueForm()
    if form.validate():
        try:
            venue = Venue()
            form.populate_obj(venue)
            venue.genres = ",".join(form.genres.data)
            db.session.add(venue)
            db.session.commit()
            
            # on successful db insert, flash success
            
            flash('Venue ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')
        
        except:
            db.session.rollback()
            
        finally:
            db.session.close()
            
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing
    print(form.errors)
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed', 'error')
    return render_template('forms/new_venue.html', form=form, errors=form.errors)
              

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue deleted successfully!')
        
    except:
        db.session.rollback()
        
    finally:
        db.session.close()
        

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect("/")


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    
    artists = Artist.query.filter(Artist.name.ilike(f"%{request.form.get('search_term', '')}%"))
    response={
        "count": artists.count(),
        "data": [{
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": Show.query.filter_by(artist_id=artist.id).filter(show.start_time < datetime.utcnow()).count()
        } for artist in artists.all()]
    }
    
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    
    data = Artist.query.get(artist_id).__dict__
    data['genres'] = data['genres'].split(",")
    shows = Show.query.filter_by(artist_id=artist_id).join(Venue).all()
    
    data["past_shows"] = []
    data["upcoming_shows"] = []

    for show in shows:
        if show.start_time < datetime.utcnow():
            show_type =  "past_shows" 
        else:
            show_type = "upcoming_shows"

        data[show_type].append({
            "venue_id": show.venues.id,
            "venue_name": show.venues.name,
            "venue_image_link": show.venues.image_link,
            "start_time": show.start_time
        })
            
    data["past_shows_count"] = len(data["past_shows"])        
    data["upcoming_shows_count"] = len(data["upcoming_shows"])

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    form.genres.data = artist.genres.split(",")

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()
    if form.validate():
        try:
            artist = Artist.query.get(artist_id)
            form.populate_obj(artist)
            artist.genres = ",".join(form.genres.data)
            db.session.commit()
            
            flash("Artist edited successfully")
            return redirect(url_for('show_artist', artist_id=artist_id))

        except:
            db.session.rollback()
            
        finally:
            db.session.close()
            
    flash('An error occurred. Artist ' + form.name.data + ' could not be edited', 'error')
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # TODO: populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    form.genres.data = venue.genres.split(",")
    
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    
    form = VenueForm()
    if form.validate():
        try:
            venue = Venue.query.get(venue_id)
            form.populate_obj(venue)
            venue.genres = ",".join(form.genres.data)
            db.session.commit()
            
            flash("Venue edited successfully")
            return redirect(url_for('show_venue', venue_id=venue_id))
            
        except:
            db.session.rollback()
            
        finally:
            db.session.close()
    
    flash('An error occurred. Venue ' + form.name.data + ' could not be edited', 'error')
    return render_template("forms/edit_artist.html", form=form, venue=venue)

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    
    form = ArtistForm()
    if form.validate():
        try:
            artist = Artist()
            form.populate_obj(artist)
            artist.genres = ",".join(form.genres.data)
            db.session.add(artist)
            db.session.commit()

            # on successful db insert, flash success
            flash('Artist ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')

        except:
            db.session.rollback()
        finally:
            db.session.close()
            
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    return render_template('forms/new_artist.html', form=form)
    

#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = [{
        "venue_id": show.venues.id,        
        "venue_name": show.venues.name,
        "artist_id": show.artists.id,
        "artist_name": show.artists.name,        
        "artist_image_link": show.artists.image_link,
        "start_time": show.start_time
    } for show in Show.query.all()]

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm()
    if form.validate():
        try:
            show = Show()
            form.populate_obj(show)

            db.session.add(show)
            db.session.commit()

            # on successful db insert, flash success
            flash('Show was successfully listed!')
            return render_template('pages/home.html')

        except:
            db.session.rollback()

        finally:
            db.session.close()

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed.')
    return render_template('forms/new_show.html', form=form)



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''


#----------------------------------------------------------------------------#
# Some references.
#----------------------------------------------------------------------------#
# For a good grasp of raelationships
# https://fmhelp.filemaker.com/help/18/fmp/en/index.html#page/FMP_Help/many-to-many-relationships.html
# https://www.pythoncentral.io/sqlalchemy-association-tables/
#
# Python Class and Datatypes
# https://www.geeksforgeeks.org/class-method-vs-static-method-python/
# https://stackoverflow.com/questions/44078845/using-wtforms-with-enum
#
# CSRF Issues
# https://nickjanetakis.com/blog/fix-missing-csrf-token-issues-with-flask
#
#
#
#
#
#
#
#
#
#


# Importing liabries
import datetime as dt
import numpy as np
import sqlalchemy
import pandas as pd
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import session_user
from sqlalchemy.sql.selectable import subquery


### Database Setup ###
# Create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table - Measurament and Station
Measurement = Base.classes.measurement
Station = Base.classes.station

# Setting up Flask Setup
app = Flask(__name__)

#################################
# Setting Up Flask Routes
#################################


@app.route("/")
def welcome():
    '''
    This is the initial page that will give the routes the user can go to
    '''
    return (
        f"<h1> Climate Analysis Hawaii </h1><br/>"
        f"<br/>"
        f"<h2>Available Routes Listed Below: </h2><br/>"
        f"Precipitation: /api/v1.0/precipitation<br/>"
        f"List of Stations:/api/v1.0/stations<br/>"
        f"Temperature observations of the most-active station for the previous year of data: /api/v1.0/tobs<br/>"
        f"Enter a date between 2010-01-01 and 2017-08-23: /api/v1.0/yyyy-mm-dd<br/>"
        f"Start date and end date between 2010-01-01 and 2017-08-23: /api/v1.0/yyyy-mm-dd/yyyy-mm-dd"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    '''
    Returns json with the date as the key and the value as the precipitation
    Only returns the jsonified precipitation data for the last year in the database 
    '''
    session = Session(engine)

    # Get the last date in the database
    last_date = session.query(func.max(Measurement.date)).\
        scalar()
    dt_last_date = dt.datetime.strptime(last_date, "%Y-%m-%d").date()
    dt_start_date = dt_last_date - dt.timedelta(days=365)
    start_date = dt_start_date.strftime("%Y-%m-%d")

    # Query the date and precipitation values for the last year
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date.between(start_date, last_date)).\
        all()
    session.close()

    # Converting the results into a list of dictionaries
    precipitation = []
    for date, prcp in results:
        precipitation_dict = {}
        precipitation_dict['date'] = date
        precipitation_dict['prcp'] = prcp
        precipitation.append(precipitation_dict)
    return jsonify(precipitation)


@app.route("/api/v1.0/stations")
def stations():
    '''
    Returns jsonified data of all of the stations in the database
    '''
    session = Session(engine)
    results = session.query(Station.name).all()
    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(results))

    # Create a list of dictionaries, each containing a single station
    stations_list = [{"Station": station} for station in all_stations]

    # Return the JSON response with each station on a separate line
    return jsonify(stations_list)


@app.route("/api/v1.0/tobs")
def tobs():
    '''
    Returns jsonified data for the most active station (USC00519281), Only returns the jsonified data for the last year of data

    '''
    session = Session(engine)

    # Query the station with the most observations
    m_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).\
        subquery()

    # Get the last date in the database
    last_date = session.query(func.max(Measurement.date)).\
        scalar()
    dt_last_date = dt.datetime.strptime(last_date, "%Y-%m-%d").date()
    dt_start_date = dt_last_date - dt.timedelta(days=365)
    start_date = dt_start_date.strftime("%Y-%m-%d")

    # Query the date and temperature values for the last year for the top station
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date.between(start_date, last_date)).\
        filter(Measurement.station.in_(m_active_station)).\
        all()
    session.close()

    # Convert the results into a list of dictionaries
    most_active_station = []
    for date, tobs in results:
        tobs_dict = {}
        tobs_dict['date'] = date
        tobs_dict['tobs'] = tobs
        most_active_station.append(tobs_dict)
    return jsonify(most_active_station)


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def rangestart(start, end=None):
    '''
    A start route that: Accepts the start date as a parameter from the URL and Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset 

    A start/end route that:
    Accepts the start and end dates as parameters from the URL
    Returns the min, max, and average temperatures calculated from the given start date to the given end date
    '''

    session = Session(engine)
    if end == None:
        last_date = session.query(func.max(Measurement.date)).\
            scalar()
    else:
        last_date = str(end)
    start_date = str(start)

    # Query the minimum, average, and maximum temperature within the specified date range
    results = session.query(func.min(Measurement.tobs).label('TMIN'),
                            func.avg(Measurement.tobs).label('TAVG'),
                            func.max(Measurement.tobs).label('TMAX')).\
        filter(Measurement.date.between(start_date, last_date)).\
        first()
    session.close()
    data_results = list(np.ravel(results))

    # Convert the results into a list
    return jsonify(data_results)


if __name__ == "__main__":
    app.run(debug=False)

# Import the dependencies.

from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import datetime as dt

# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify 

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model

Base = automap_base()

# reflect the tables

Base.prepare(engine, reflect = True)

# Save references to each table

measurement_tb = Base.classes.measurement
station_tb = Base.classes.station

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

# Main Route 
@app.route("/")
def Homepage():
    """All of the Routes"""
    return(
        f"Available Routes: <br/>"
        f"/api/v1.0/precipitation <br/>"
        f"/api/v1.0/stations <br/>"
        f"/api/v1.0/tobs <br/>"
        f"/api/v1.0/<start> <br/>"
        f"/api/v1.0/<start>/<end> <br/>"
    )

#################################################
# Flask Routes
#################################################



# Precipitation Route
# Convert the query results from your precipitation analysis 
# (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    most_recent_date = session.query(measurement_tb.date).order_by(measurement_tb.date.desc()).first()  
    (last_date, ) = most_recent_date
    last_date = dt.datetime.strftime(last_date, "%Y-%m%d")
    last_date = last_date.date()
    only_last_months = dt.date(2017,8,23) - dt.timedelta(day=365)

    year_precip = session.query(measurement_tb.date, measurement_tb.prcp).\
    filter(measurement_tb.date >= only_last_months).all()

    session.close()

    dates_prcp = []
    for dtprcp in year_precip:
        if dtprcp != None:
            dtprcp_dict = {}    
            dtprcp_dict["date"] = dtprcp
            dates_prcp.append(dtprcp_dict)

    return jsonify(dates_prcp)



#Station Route 
# Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():

     # Create our session (link) from Python to the DB
    session = Session(engine)
    
    stations = session.query(station_tb.station, station_tb.name, station_tb.latitude, station_tb.longitude, station_tb.elevation).all()

    session.close()

    all_stations = []
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name 
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    return jsonify(all_stations)



# Tobs Route
# Query the dates and temperature observations of the most-active station for the previous year of data.
# Return a JSON list of temperature observations for the previous year.
@app.route("/api/v1.0/tobs")
def tobs():

 # Create our session (link) from Python to the DB
    session = Session(engine)

    most_recent_date = session.query(measurement_tb.date).order_by(measurement_tb.date.desc()).first()
    (most_recent, ) = most_recent_date
    most_recent = dt.datetime.strptime(most_recent, "%Y-%m-%d")
    most_recent = most_recent.date()
    only_last_months = dt.date(2017,8,23) - dt.timedelta(days=365)

    # Most Active Station

    most_active_station = session.query(measurement_tb.station).\
        group_by(measurement_tb.station).\
        order_by(func.count().desc()).first()

    (active_stations, ) = most_active_station

    last_year_data = session.query(measurement_tb.date, measurement_tb.tobs).\
        filter(measurement_tb.station == active_stations).filter(measurement_tb.date >= only_last_months).all()
    
    session.close()

    temps = []
    for date, temp in last_year_data:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            temps.append(temp_dict)

    return jsonify(temps)



# Start Route and Start End Route 
# Combined together for start and start/end
# Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.
# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
# For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.

@app.route("/api/v1.0/<start>", defaults = {"end" : None})
@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):

    # Create our session (link) from Python to the DB
    session = Session(engine)

    if end != None:
        temp_data = session.query(func.min(measurement_tb.tobs), func.max(measurement_tb.tobs), func.avg(measurement_tb.tobs)).\
        filter(measurement_tb.date <= end).all()

    else:
        temp_data = session.query(func.min(measurement_tb.tobs), func.max(measurement_tb.tobs), func.avg(measurement_tb.tobs)).\
        filter(measurement_tb.date >= start).all()

    session.close()

    temp_list = []
    no_temp_found = False
    for min_temp, max_temp, avg_temp in temp_data:
        if min_temp == None or max_temp == None or avg_temp == None:
            no_temp_found = True
        temp_list.append(min_temp)
        temp_list.append(max_temp)
        temp_list.append(avg_temp)

    if no_temp_found == True:
        return f"No Temperature Found"
    else:
        return jsonify(temp_list)



if __name__== '__main__':
    app.run(debug = True)
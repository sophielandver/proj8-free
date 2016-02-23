import flask
from flask import render_template
from flask import request
from flask import url_for
import uuid

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we still need time
from dateutil import tz  # For interpreting local times


# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services 
from apiclient import discovery

from agenda import *

###
# Globals
###
import CONFIG
app = flask.Flask(__name__)

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = CONFIG.GOOGLE_LICENSE_KEY  ## You'll need this
APPLICATION_NAME = 'MeetMe class project'

#############################
#
#  Pages (routed from URLs)
#
#############################

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Entering index")
  if 'begin_date' not in flask.session:
    init_session_values()
  return render_template('index.html')

@app.route("/choose")
def choose():
    ## We'll need authorization to list calendars 
    ## I wanted to put what follows into a function, but had
    ## to pull it back here because the redirect has to be a
    ## 'return' 
    app.logger.debug("Checking credentials for Google calendar access")
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      return flask.redirect(flask.url_for('oauth2callback'))

    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    flask.session['calendars'] = list_calendars(gcal_service)
    return render_template('index.html')

####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
#  Protocol for use ON EACH REQUEST: 
#     First, check for valid credentials
#     If we don't have valid credentials
#         Get credentials (jump to the oauth2 protocol)
#         (redirects back to /choose, this time with credentials)
#     If we do have valid credentials
#         Get the service object
#
#  The final result of successful authorization is a 'service'
#  object.  We use a 'service' object to actually retrieve data
#  from the Google services. Service objects are NOT serializable ---
#  we can't stash one in a cookie.  Instead, on each request we
#  get a fresh serivce object from our credentials, which are
#  serializable. 
#
#  Note that after authorization we always redirect to /choose;
#  If this is unsatisfactory, we'll need a session variable to use
#  as a 'continuation' or 'return address' to use instead. 
#
####

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value. 
    """
    if 'credentials' not in flask.session:
      return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
        credentials.access_token_expired):
      return None
    return credentials


def get_gcal_service(credentials):
  """
  We need a Google calendar 'service' object to obtain
  list of calendars, busy times, etc.  This requires
  authorization. If authorization is already in effect,
  we'll just return with the authorization. Otherwise,
  control flow will be interrupted by authorization, and we'll
  end up redirected back to /choose *without a service object*.
  Then the second call will succeed without additional authorization.
  """
  app.logger.debug("Entering get_gcal_service")
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http_auth)
  app.logger.debug("Returning service")
  return service

@app.route('/oauth2callback')
def oauth2callback():
  """
  The 'flow' has this one place to call back to.  We'll enter here
  more than once as steps in the flow are completed, and need to keep
  track of how far we've gotten. The first time we'll do the first
  step, the second time we'll skip the first step and do the second,
  and so on.
  """
  app.logger.debug("Entering oauth2callback")
  flow =  client.flow_from_clientsecrets(
      CLIENT_SECRET_FILE,
      scope= SCOPES,
      redirect_uri=flask.url_for('oauth2callback', _external=True))
  ## Note we are *not* redirecting above.  We are noting *where*
  ## we will redirect to, which is this function. 
  
  ## The *second* time we enter here, it's a callback 
  ## with 'code' set in the URL parameter.  If we don't
  ## see that, it must be the first time through, so we
  ## need to do step 1. 
  app.logger.debug("Got flow")
  if 'code' not in flask.request.args:
    app.logger.debug("Code not in flask.request.args")
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
    ## This will redirect back here, but the second time through
    ## we'll have the 'code' parameter set
  else:
    ## It's the second time through ... we can tell because
    ## we got the 'code' argument in the URL.
    app.logger.debug("Code was in flask.request.args")
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    ## Now I can build the service and execute the query,
    ## but for the moment I'll just log it and go back to
    ## the main screen
    app.logger.debug("Got credentials")
    return flask.redirect(flask.url_for('choose'))

#####
#
#  Option setting:  Buttons or forms that add some
#     information into session state.  Don't do the
#     computation here; use of the information might
#     depend on what other information we have.
#   Setting an option sends us back to the main display
#      page, where we may put the new information to use. 
#
#####

@app.route('/setrange', methods=['POST'])
def setrange():
    """
    User chose a date range with the bootstrap daterange
    widget and a time range with a time picker widget. This
    function stores the begin date, end date, start time, and 
    end time in the session object. It also stores the original
    date range and time range in the session object as a simple
    string so that it can be displayed to the user every time 
    the page reloads. 
    """
    app.logger.debug("Entering setrange")  
    flask.flash("Setrange gave us '{}'".format(
      request.form.get('daterange')))
    daterange = request.form.get('daterange')
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')
    
    app.logger.debug(starttime)
    app.logger.debug(endtime)
    
    flask.session['daterange'] = daterange
    flask.session['text_beg_time'] = starttime
    flask.session['text_end_time'] = endtime
    daterange_parts = daterange.split()
    flask.session['begin_date'] = interpret_date(daterange_parts[0])
    flask.session['end_date'] = interpret_date(daterange_parts[2])
    flask.session['begin_time'] = interpret_time(starttime)
    flask.session['end_time'] = interpret_time(endtime)
    
    app.logger.debug("Setrange parsed {} - {}  dates as {} - {}".format(
      daterange_parts[0], daterange_parts[1], 
      flask.session['begin_date'], flask.session['end_date']))
    app.logger.debug("Set time range from {} - {} TO {} - {}".format(starttime, endtime, flask.session['begin_time'], flask.session['end_time']))
    return flask.redirect(flask.url_for("choose"))


@app.route('/calcBusyFreeTimes')
def calcBusyFreeTimes():
    """
    Once the user has selected the google calendars he wants to use and clicks the 
    'Calculate Busy Times' button this function gets invoked. This function stores in 
    the session object a list of calendar ids, the calendar ids of the calendars the user
    selected. Then, this function calls find_busy() which goes through the list of 
    calendar ids and finds the times in the time span in which the user cannot meet.  
    """
    temp_selected_cal = request.args.get('selected', 0, type=str)
    selected_cal = temp_selected_cal.split() #list of strings
    flask.session['selected_cal'] = selected_cal
    app.logger.debug(flask.session['selected_cal'])
    find_busy() #a dict of dicts 
    find_free() 
    return "nothing"

@app.route('/displayBusyFreeTimes')
def displayBusyFreeTimes():
    """
    This function gets called once the busy times have been calculated and we are 
    ready to display them to the user. This function displays the busy times to the user.
    """
    """
    createDisplayBusyTimes()
    createDisplayFreeTimes(flask.session['free_apts'])
    """
    createDisplayFreeBusyTimes()
    return render_template('index.html')
    

def createDisplayFreeBusyTimes():
    free_busy = []
    for event in flask.session['busy_list']:
        del event[0] #delete the event ID
        free_busy.append(event)
    for free in flask.session['free_apts']:
        free.insert(0, "Available")
        free_busy.append(free)
    free_busy.sort(key=lambda r: r[1]) #sort by begin date
    
    display_free_busy = []
    for apt in free_busy:
        apt_str = ""
        apt_str = apt_str + apt[0] + ": "
        apt_str = apt_str + convertDisplayDateTime(apt[1]) + " - "
        apt_str = apt_str + convertDisplayDateTime(apt[2]) 
        display_free_busy.append(apt_str)
    flask.session['display_free_busy'] = display_free_busy
        
    
#NOT USING THIS
def createDisplayFreeTimes(free_apts): #given particular list of list free [["gym", arrow iso start date time, arrow iso end date time],...]
    display_free = [] 
    for apt in free_apts:
        free_str = ""
        free_str = free_str + convertDisplayDateTime(apt[0]) + " - "
        free_str = free_str + convertDisplayDateTime(apt[1]) 
        display_free.append(free_str)
    app.logger.debug(display_free)
    flask.session['display_total_free'] = display_free
    
#NOT USING THIS
def createDisplayBusyTimes(): #given particular dictionary total_busy
    display_total_busy = [] #list of strings
    for cal in flask.session['total_busy']:
        cal_dict = flask.session['total_busy'][cal]
        app.logger.debug(cal_dict)
        for conflict_event in cal_dict:
            busy_str = ""
            info_list = cal_dict[conflict_event]
            app.logger.debug(info_list)
            busy_str = busy_str + (info_list[0]) + ": "
            busy_str = busy_str + convertDisplayDateTime(info_list[1]) + " -  "
            busy_str = busy_str + convertDisplayDateTime(info_list[2])
            display_total_busy.append(busy_str)
    app.logger.debug(display_total_busy)
    flask.session['display_total_busy'] = display_total_busy
            

####
#
#   Initialize session variables 
#
####

def init_session_values():
    """
    Start with some reasonable defaults for date and time ranges.
    Note this must be run in app context ... can't call from main. 
    """
    # Default date span = tomorrow to 1 week from now
    now = arrow.now('local')
    tomorrow = now.replace(days=+1)
    nextweek = now.replace(days=+7)
    flask.session["begin_date"] = tomorrow.floor('day').isoformat()
    flask.session["end_date"] = nextweek.ceil('day').isoformat()
    flask.session["daterange"] = "{} - {}".format(
        tomorrow.format("MM/DD/YYYY"),
        nextweek.format("MM/DD/YYYY"))
    # Default time span each day, 8 to 5
    flask.session["begin_time"] = interpret_time("9am")
    flask.session["end_time"] = interpret_time("5pm")

def interpret_time( text ):
    """
    Read time in a human-compatible format and
    interpret as ISO format with local timezone.
    May throw exception if time can't be interpreted. In that
    case it will also flash a message explaining accepted formats.
    """
    app.logger.debug("Decoding time '{}'".format(text))
    time_formats = ["ha", "h:mma",  "h:mm a", "h:mm A", "H:mm"]
    try: 
        as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
        app.logger.debug("Succeeded interpreting time")
    except:
        app.logger.debug("Failed to interpret time")
        flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
              .format(text))
        raise
    return as_arrow.isoformat()

def interpret_date( text ):
    """
    Convert text of date to ISO format used internally,
    with the local time zone.
    """
    try:
      as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
          tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()

def next_day(isotext):
    """
    ISO date + 1 day (used in query to Google calendar)
    """
    as_arrow = arrow.get(isotext)
    return as_arrow.replace(days=+1).isoformat()

####
#
#  Functions (NOT pages) that return some information
#
####

def find_free():
    busy_agenda = Agenda.from_list(flask.session['busy_list'])
        
    span_begin_date = arrow.get(flask.session['begin_date'])
    span_end_date = arrow.get(flask.session['end_date'])
    span_begin_time = arrow.get(flask.session['begin_time'])
    span_end_time = arrow.get(flask.session['end_time'])
    free_agenda = busy_agenda.complementTimeSpan(span_begin_date, span_end_date, span_begin_time, span_end_time)
    
    flask.session['free_apts'] = free_agenda.to_list()




"""
def find_free():
    busy_agenda = Agenda()
    for event in flask.session['busy_list']:
        apt = Appt.from_list(event)
        busy_agenda.append(apt)
        
    free_times = []
    flask_beg_date = arrow.get(flask.session['begin_date'])
    date = flask_beg_date.date()
    end_date = arrow.get(flask.session['end_date']).date()
    while(date <= end_date):
        app.logger.debug("here is date from while loop")
        app.logger.debug(date)
        fb_year = date.year
        fb_month = date.month
        fb_day = date.day
        fb_begin = arrow.get(flask.session['begin_time']).replace(year=fb_year, month=fb_month, day=fb_day)
        fb_end = arrow.get(flask.session['end_time']).replace(year=fb_year, month=fb_month, day=fb_day)
        app.logger.debug("here is free block begin of apt")
        app.logger.debug(fb_begin)
        freeblock = Appt(fb_begin, fb_end, "freeblock")
        free_agenda = busy_agenda.complement(freeblock)
        for apt in free_agenda:
            apt_list = apt.to_list()
            free_times.append(apt_list)
        
        flask_beg_date = flask_beg_date.replace(days=+1)
        date = flask_beg_date.date()
    
    app.logger.debug("here is all free times")
    app.logger.debug(free_times)
    flask.session['free_apts'] = free_times

"""
    

def find_busy():
    """
    This function goes through the list of selected calendar ids, which is stored in the 
    session object, and collects all the appointments that lie within or partially overlap
    the desired meeting time range and are not transparent. It stores all the busy times
    it collects in the session object.  
    """
    total_busy = {} #dictionary of dicts  
    busy_list = [] #list of lists
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    service = get_gcal_service(credentials)
    for id in flask.session['selected_cal']:
        events = service.events().list(calendarId=id, pageToken=None).execute()
        event_dict = {}
        for event in events['items']:
            if ('transparency' in event) and event['transparency']=='transparent':
                continue 
            start_datetime = arrow.get(event['start']['dateTime'])
            end_datetime = arrow.get(event['end']['dateTime'])
            if overlap(start_datetime, end_datetime):   
                event_dict[event['id']] = [event['summary'], start_datetime.isoformat(), end_datetime.isoformat()]
                event_list = [event['id'], event['summary'], start_datetime.isoformat(), end_datetime.isoformat()]
                app.logger.debug("here is event_list of busy_list")
                app.logger.debug(event_list)
                busy_list.append(event_list)
        total_busy[id] = event_dict
    
    app.logger.debug("HERE is busy list")
    app.logger.debug(busy_list)
    app.logger.debug(total_busy)
    flask.session['total_busy'] = total_busy
    flask.session['busy_list'] = busy_list
    app.logger.debug(flask.session['total_busy'])


def overlap(event_sdt, event_edt):
    """
    This function returns true if and only if the inputed event overlaps the 
    desired meeting time range. 
    """
#sdt = start date time 
#edt = end date time 
    event_sd = event_sdt.date()
    event_ed = event_edt.date()
    event_st = event_sdt.time()
    event_et = event_edt.time()
    desired_sd= arrow.get(flask.session['begin_date']).date()
    desired_ed = arrow.get(flask.session['end_date']).date()
    desired_st = arrow.get(flask.session['begin_time']).time()
    desired_et = arrow.get(flask.session['end_time']).time()
    if not (desired_sd <= event_sd <= desired_ed) or not (desired_sd <= event_ed <= desired_ed):
        return False 
    elif (event_et <= desired_st):
        return False 
    elif (event_st >= desired_et):
        return False
    else:
        return True


def convertDisplayDateTime(date_time):
    """
    This function takes in an isoformat() string, makes it into an arrow object, converts it to the 
    local time of the server, and then returns it as a formatted string for displaying in the
    form MM/DD/YYYY h:mm A. We use this function every time before we want to display a time 
    to the user.
    """
    arrow_date_time = arrow.get(date_time)
    local_arrow = arrow_date_time.to('local')
    formatted_str = local_arrow.format('MM/DD/YYYY h:mm A')
    return formatted_str


def list_calendars(service):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict, so that
    it can be stored in the session object and converted to
    json for cookies. The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")  
    calendar_list = service.calendarList().list().execute()["items"]
    result = [ ]
    for cal in calendar_list:
        kind = cal["kind"]
        id = cal["id"]
        app.logger.debug("HERE IS CALENDAR ID: {}". format(id))
        if "description" in cal: 
            desc = cal["description"]
        else:
            desc = "(no description)"
        summary = cal["summary"]
        # Optional binary attributes with False as default
        selected = ("selected" in cal) and cal["selected"]
        primary = ("primary" in cal) and cal["primary"]
        

        result.append(
          { "kind": kind,
            "id": id,
            "summary": summary,
            "selected": selected,
            "primary": primary
            })
    return sorted(result, key=cal_sort_key)


def cal_sort_key( cal ):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
       selected_key = " "
    else:
       selected_key = "X"
    if cal["primary"]:
       primary_key = " "
    else:
       primary_key = "X"
    return (primary_key, selected_key, cal["summary"])


#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"

@app.template_filter( 'fmttime' )
def format_arrow_time( time ):
    try:
        normal = arrow.get( time )
        return normal.format("HH:mm")
    except:
        return "(bad time)"
    
#############


if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running in a CGI script)

  app.secret_key = str(uuid.uuid4())  
  app.debug=CONFIG.DEBUG
  app.logger.setLevel(logging.DEBUG)
  # We run on localhost only if debugging,
  # otherwise accessible to world
  if CONFIG.DEBUG:
    # Reachable only from the same computer
    app.run(port=CONFIG.PORT)
  else:
    # Reachable from anywhere 
    app.run(port=CONFIG.PORT,host="0.0.0.0")
    

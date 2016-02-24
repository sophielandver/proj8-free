Author: Sophie Landver

Path to project8 on ix: slandver@ix-trusty: ~/public_html/cis399/htbin/proj8-free

# proj8-free
A flask app that asks the user for a desired meeting date range and time range and asks the
user to select the google calendars he/she would like the program to use. Then the "busy" (defined below)
and "free" (defined below) times are computed and displayed to the user in sorted order by 
begin date/time. In addition, the app permits the user to make a different selection of calendars 
after viewing the busy and free times.

busy times: all the appointments from the user's selected google calendars that lie within or 
partially overlap the desired time range and are appointments that block time 
(in iCalendar terms, non-transparent), i.e. the times in the date/time range in which the 
user cannot meet. 
free times: the times in the date/time range in which the user can meet. 

The functions used for the free time calculation can be found in agenda.py
A thorough test suite for the free time calculations can be found in test_agenda.py 








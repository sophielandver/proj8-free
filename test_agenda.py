"""
Nose tests for agenda.py
"""

from agenda import *
import arrow
import io

def test_complement():
    """
    fb_begin = arrow.get("10:00 AM 02/22/2016","h:mm A MM/DD/YYYY")
    fb_end = arrow.get("4:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    freeblock = Appt(fb_begin, fb_end, "Freeblock")
    
    apt1_begin = arrow.get("8:00 AM 02/22/2016","h:mm A MM/DD/YYYY")
    apt1_end = arrow.get("9:00 AM 02/22/2016","h:mm A MM/DD/YYYY")
    apt1 = Appt(apt1_begin, apt1_end, "busy")
    
    apt2_begin = arrow.get("10:00 AM 02/22/2016","h:mm A MM/DD/YYYY")
    apt2_end = arrow.get("12:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    apt2 = Appt(apt2_begin, apt2_end, "busy")
    
    apt3_begin = arrow.get("1:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    apt3_end = arrow.get("2:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    apt3 = Appt(apt3_begin, apt3_end, "busy")
    
    apt4_begin = arrow.get("3:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    apt4_end = arrow.get("5:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    apt4 = Appt(apt4_begin, apt4_end, "busy")
    
    apt5_begin = arrow.get("6:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    apt5_end = arrow.get("7:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    apt5 = Appt(apt5_begin, apt5_end, "busy")
    
    busy_agenda = Agenda()
    busy_agenda.append(apt1)
    busy_agenda.append(apt2)
    busy_agenda.append(apt3)
    busy_agenda.append(apt4)
    busy_agenda.append(apt5)
    
    ex1_begin = arrow.get("12:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    ex1_end = arrow.get("1:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    ex1 = Appt(ex1_begin, ex1_end, "Available")
    
    ex2_begin = arrow.get("2:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    ex2_end = arrow.get("3:00 PM 02/22/2016","h:mm A MM/DD/YYYY")
    ex2 = Appt(ex2_begin, ex2_end, "Available")
    
    ex_agenda = Agenda()
    ex_agenda.append(ex1)
    ex_agenda.append(ex2)
    
    assert busy_agenda.complement(freeblock) == ex_agenda
    """
    
    #TEST1
    freeblock = Appt.from_string("02/22/2016 10:00 AM-02/22/2016 4:00 PM|Freeblock")
    busy_agtxt = """
    02/22/2016 8:00 AM-02/22/2016 9:00 AM|busy
    02/22/2016 10:00 AM-02/22/2016 12:00 PM|busy
    02/22/2016 1:00 PM-02/22/2016 2:00 PM|busy
    02/22/2016 3:00 PM-02/22/2016 5:00 PM|busy
    02/22/2016 6:00 PM-02/22/2016 7:00 PM|busy
    """
    busy_agenda = Agenda.from_file(io.StringIO(busy_agtxt))
    expected_txt = """
    02/22/2016 12:00 PM-02/22/2016 1:00 PM|Available
    02/22/2016 2:00 PM-02/22/2016 3:00 PM|Available
    """
    expected_agenda = Agenda.from_file(io.StringIO(expected_txt))
    assert busy_agenda.complement(freeblock) == expected_agenda
    
    
    
def test_complement_again():
    busy_agtxt = """
    02/22/2016 8:00 AM-02/22/2016 9:00 AM|busy
    02/22/2016 10:00 AM-02/22/2016 12:00 PM|busy
    02/22/2016 1:00 PM-02/22/2016 2:00 PM|busy
    02/22/2016 3:00 PM-02/22/2016 5:00 PM|busy
    02/22/2016 6:00 PM-02/22/2016 7:00 PM|busy
    """
    busy_agenda = Agenda.from_file(io.StringIO(busy_agtxt))
    
    begin_date = arrow.get("12:00 PM 02/22/2016","h:mm A MM/DD/YYYY") #from 22nd
    end_date = arrow.get("12:00 PM 02/23/2016","h:mm A MM/DD/YYYY") #to 23rd
    begin_time = arrow.get("10:00 AM 02/22/2016","h:mm A MM/DD/YYYY") #begin time is 10 AM
    end_time = arrow.get("4:00 PM 02/22/2016","h:mm A MM/DD/YYYY") #end time is 4 PM
    
    expected2_txt = """
    02/22/2016 12:00 PM-02/22/2016 1:00 PM|Available
    02/22/2016 2:00 PM-02/22/2016 3:00 PM|Available
    02/23/2016 10:00 AM-02/23/2016 4:00 PM|Available
    """
    expected2_agenda = Agenda.from_file(io.StringIO(expected2_txt))
    assert busy_agenda.complementTimeSpan(begin_date, end_date, begin_time, end_time) == expected2_agenda
    
    



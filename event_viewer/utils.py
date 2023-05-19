import datetime
import re
import time
from event_viewer.models import EventLogReaderModel
import win32con
import win32evtlog
import pandas as pd
import win32evtlogutil
import winerror


class EventLogReader:
    def __init__(self, log_name):

        self.log_name = log_name
        self.handle = None
        self.evt_dict = {win32con.EVENTLOG_AUDIT_FAILURE: 'EVENTLOG_AUDIT_FAILURE',
                         win32evtlog.EVENTLOG_AUDIT_SUCCESS: 'EVENTLOG_AUDIT_SUCCESS',
                         win32evtlog.EVENTLOG_INFORMATION_TYPE: 'EVENTLOG_INFORMATION_TYPE',
                         win32evtlog.EVENTLOG_WARNING_TYPE: 'EVENTLOG_WARNING_TYPE',
                         win32evtlog.EVENTLOG_ERROR_TYPE: 'EVENTLOG_ERROR_TYPE'}
        self.flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    def enter(self):
        self.handle = win32evtlog.OpenEventLog(None, self.log_name)
        return self

    def exit(self):
        if self.handle:
            win32evtlog.CloseEventLog(self.handle)
            self.handle = None

    def to_csvfile(self, filename, data):
        df = pd.DataFrame([data])
        df.to_csv(f'{filename}.csv', index=False, mode='a', header=False)

    def read_events(self):
        self.enter()

        try:
            # Get the next event from the event log
            flags = self.flags

            events = win32evtlog.ReadEventLog(self.handle, flags, 0)

            begin_sec = time.time()
            begin_time = time.strftime('%H:%M:%S ', time.localtime(begin_sec))
            total = win32evtlog.GetNumberOfEventLogRecords(self.handle)

            for event in events:

                try:
                    the_time = event.TimeGenerated.Format()
                    seconds = self.time2sec(the_time)

                    etv_id = str(winerror.HRESULT_CODE(event.EventID))
                    computer = str(event.ComputerName)
                    cat = str(event.EventCategory)
                    msg = str(win32evtlogutil.SafeFormatMessage(event, self.log_name))
                    src = str(event.SourceName)
                    record = str(event.RecordNumber)
                    event_type = self.evt_dict.get(event.EventType, 'Unknown')
                    user_name = event.StringInserts[1]
                    frst_msg = re.match(r'^.*?[\.\?!]', msg).group(0)

                    data = {'Event_ID': etv_id, 'Time': the_time, 'user_name': user_name, 'Computer': computer,
                            'Category': cat, 'src': src, 'record': record, 'event_type': event_type,
                            'Text_Info': frst_msg}
                    event_model = EventLogReaderModel.objects.create(the_time=the_time, etv_id=etv_id,
                                                                     computer_name=computer,
                                                                     user_name=user_name, category=cat, source=src,
                                                                     record=record,
                                                                     event_type=event_type, message=frst_msg)
                    event_model.save()
                    self.to_csvfile('read_events', data)

                except Exception as e:
                    print(f'Error processing event: {e}')
        except Exception as e:
            print(f'Error reading event log: {e}')

    def time2sec(self, evt_date):

        if re.match('\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}', evt_date):
            date_format = '%m/%d/%Y %H:%M:%S'
        else:
            date_format = '%a %b %d %H:%M:%S %Y'

        dt = datetime.datetime.strptime(evt_date, date_format)
        sec = time.mktime(dt.timetuple())
        return sec


# If you need python filtering. i've used django query.
class EventFilter(EventLogReader):

    def __filter_events(self, event_type=None, event_id=None, computer_name=None, seconds_time=None, user_name=None):
        """"
        Private method to filter events based on the input parameters
        """
        events = win32evtlog.ReadEventLog(self.handle, self.flags, 0)
        begin_sec = time.time()
        begin_time = time.strftime('%H:%M:%S', time.localtime(begin_sec))
        total = win32evtlog.GetNumberOfEventLogRecords(self.handle)

        for event in events:
            if event_type is not None and event.EventType != event_type:
                continue

            if event_id is not None and event.EventID != event_id:
                continue

            if computer_name is not None and event.ComputerName != computer_name:
                continue

            if user_name is not None and event.StringInserts[1] != user_name:
                continue

            try:
                the_time = event.TimeGenerated.Format()
                seconds = self.time2sec(the_time)

                if seconds_time is not None and seconds < begin_sec - seconds_time:
                    break

                etv_id = str(winerror.HRESULT_CODE(event.EventID))
                computer = str(event.ComputerName)
                cat = str(event.EventCategory)
                msg = str(win32evtlogutil.SafeFormatMessage(event, self.log_name))
                src = str(event.SourceName)
                record = str(event.RecordNumber)
                event_type = self.evt_dict.get(event.EventType, 'Unknown')
                user_name = event.StringInserts[1]

                frst_msg = re.match(r'^.*?[\.\\?!]', msg).group(0)

                data = {'Event_ID': etv_id,
                        'Time': the_time,
                        'user_name': user_name,
                        'Computer': computer,
                        'Category': cat,
                        'src': src,
                        'record': record,
                        'event_type': event_type,
                        'Text-Info': frst_msg
                        }
                self.to_csvfile('filtering_events', data)

            except Exception as e:
                print(f"Error reading event log: {str(e)}")

    def filter_logging_success(self):
        self.__filter_events(event_type=win32evtlog.EVENTLOG_AUDIT_SUCCESS, event_id=4624)

    def filter_logging_failure(self):
        self.__filter_events(event_type=win32evtlog.EVENTLOG_AUDIT_FAILURE, event_id=4625)

    def filter_success_and_failure(self):
        self.__filter_events(event_type=[win32evtlog.EVENTLOG_AUDIT_SUCCESS, win32evtlog.EVENTLOG_AUDIT_FAILURE],
                             event_id=[4624, 4625])

    def filter_events_by_computer(self, computer_name='', seconds_time=None):
        self.__filter_events(computer_name=computer_name, seconds_time=seconds_time)

    def filter_events_by_user_name(self, username=''):
        self.__filter_events(user_name=username)

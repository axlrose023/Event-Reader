import calendar
import csv
import datetime
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse
from event_viewer.models import EventLogReaderModel
from django.shortcuts import render
from .utils import EventLogReader


def get_page_range(current_page, num_pages):
    page_range = []

    # Add the first page
    if current_page > 1:
        page_range.append(1)

    # add the pages before the current page
    for page in range(current_page - 3, current_page):
        if page > 1:
            page_range.append(page)

    # add the current page
    page_range.append(current_page)

    # add the three last pages
    for page in range(current_page + 1, current_page + 4):
        if page <= num_pages:
            page_range.append(page)

    return page_range


def paginate_queryset(queryset, request, per_page=20):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    num_pages = paginator.num_pages
    current_page = page_obj.number
    page_range = get_page_range(current_page, per_page)

    return page_obj, page_range, num_pages


@login_required()
def eventlog_reader(request):
    EventLogReader('Security').read_events()

    events = EventLogReaderModel.objects.all().order_by('-created_date')

    total = EventLogReaderModel.objects.all().count()

    page_obj, page_range, num_pages = paginate_queryset(events, request)

    context = {'page_obj': page_obj,
               'num_pages': num_pages,
               'page_range': page_range,
               'total': total}

    return render(request, 'simple_events.html', context)


@login_required()
def home(request):
    return render(request, 'index.html')


@login_required()
def filter_events_success(request):
    success_events = EventLogReaderModel.objects.filter(etv_id=4624).order_by('-created_date')
    page_obj, page_range, num_pages = paginate_queryset(success_events, request)
    total = success_events.count()

    context = {'page_obj': page_obj,
               'num_pages': num_pages,
               'total': total,
               'page_range': page_range}

    return render(request, 'success_events.html', context)


@login_required()
def filter_events_failure(request):
    failure_events = EventLogReaderModel.objects.filter(etv_id=4625).order_by('-created_date')
    page_obj, page_range, num_pages = paginate_queryset(failure_events, request)
    total = failure_events.count()

    context = {'page_obj': page_obj,
               'num_pages': num_pages,
               'total': total,
               'page_range': page_range}

    return render(request, 'failure_events.html', context)


@login_required()
def download_csv(queryset):
    queryset = EventLogReaderModel.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="event_log.csv"'
    writer = csv.writer(response)
    writer.writerow(['Event ID', 'Time', 'Computer', 'Event Category', 'Username', 'Source', 'Record',
                     'Event Type', 'Message'])
    for event in queryset:
        writer.writerow([event.etv_id, event.the_time, event.computer_name, event.category, event.user_name,
                         event.source, event.record, event.event_type, event.message])
    return response


# errors
def page_not_found(request, exception):
    return render(request, 'errors/error_404.html', {'path': request.path}, status=404)


def bad_request(request, exception=None):
    return render(request, 'errors/400_error.html', status=400)


def permission_denied(request, exception=None):
    return render(request, 'errors/403csrf.html', status=403)


def server_error(request, exception=None):
    return render(request, 'errors/501_error.html', status=501)


@login_required()
def filtering_events(request):
    computer = request.GET.get('computer')
    username = request.GET.get('username')
    event_id = request.GET.get('event_id')

    # timing
    timing = request.GET.get('timing')
    now = timezone.now()

    # Define filters based on GET parameters
    filters = {}
    if computer:
        filters['computer_name'] = computer
    if username:
        filters['user_name'] = username
    if event_id:
        filters['etv_id'] = event_id

    try:
        time_ranges = {
            'month': (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                      now.replace(day=calendar.monthrange(now.year, now.month)[1], hour=23, minute=59, second=59,
                                  microsecond=999999)),
            'week': (now - timedelta(days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second,
                                     microseconds=now.microsecond),
                     now.replace(hour=23, minute=59, second=59, microsecond=999999)),
            'one_day': (now.replace(hour=0, minute=0, second=0, microsecond=0),
                        now.replace(hour=23, minute=59, second=59, microsecond=999999)),
            '8_hours': (now - timedelta(hours=8, minutes=now.minute, seconds=now.second, microseconds=now.microsecond),
                        now.replace(second=59, microsecond=999999)),
            'all_period': (datetime.datetime.min, datetime.datetime.max)
        }
        start_date, end_date = time_ranges[timing]

    except (KeyError, TypeError):
        context = {'error_message': 'Виникла проблема з часом. Просто виберіть час отримання подій'}

        return render(request, 'errors/error.html', context)

    # Validate Filters
    if not any([computer, username, event_id]):
        context = {'error_message': "Будь ласка, вкажіть ім'я комп'ютера, користувача або ID події"}
        return render(request, 'errors/error.html', context)

    params_map = {
        computer: 'computer_name',
        username: 'user_name',
        event_id: 'etv_id'
    }

    for param, field in params_map.items():
        if param:
            try:
                if not EventLogReaderModel.objects.filter(**{field: param}).exists():
                    error_message = f'Неправильно вказано: {param}.'
                    context = {'error_message': error_message}
                    return render(request, 'errors/error.html', context)

            except ValueError as e:
                error_message = f'Виникла помилка: {str(e)}'
                context = {'error_message': error_message}
                return render(request, 'errors/error.html', context)

    events = EventLogReaderModel.objects.filter(**filters, created_date__range=(start_date, end_date)).order_by(
        '-the_time')

    total = events.count()

    context = {'page_obj': events,
               'total': total
               }

    return render(request, 'filter_computer.html', context)

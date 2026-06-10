from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Layout, Station, Crossover
import csv
import json


# ─────────────────────────────────────────────
#  LOGIN / LOGOUT
# ─────────────────────────────────────────────

def login_view(request):
    """
    Show login page.
    On POST: authenticate and redirect to input form.
    """
    if request.user.is_authenticated:
        return redirect('input')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('input')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'dashboard/login.html')


def logout_view(request):
    """Log the user out and send them back to login."""
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────
#  INPUT FORM
# ─────────────────────────────────────────────

@login_required(login_url='login')
def input_view(request):
    """
    Show the input form where the user enters:
      - Number of stations
      - Number of crossovers
      - Which stations each crossover connects

    On POST: validate, save to DB, redirect to layout.
    """
    if request.method == 'POST':
        try:
            num_stations  = int(request.POST.get('num_stations', 0))
            num_crossovers = int(request.POST.get('num_crossovers', 0))

            # Basic validation
            if num_stations < 2:
                messages.error(request, 'You need at least 2 stations.')
                return redirect('input')

            if num_crossovers < 0:
                messages.error(request, 'Number of crossovers cannot be negative.')
                return redirect('input')

            # ── Parse crossover pairs from the form ──────────────────────
            # The form sends fields named: from_station_1, to_station_1,
            #                              from_station_2, to_station_2 …
            crossover_pairs = []
            errors = []

            for i in range(1, num_crossovers + 1):
                from_s = request.POST.get(f'from_station_{i}')
                to_s   = request.POST.get(f'to_station_{i}')

                if from_s is None or to_s is None:
                    errors.append(f'Crossover {i}: missing station values.')
                    continue

                from_s = int(from_s)
                to_s   = int(to_s)

                if from_s == to_s:
                    errors.append(f'Crossover {i}: from and to station cannot be the same.')
                elif from_s < 1 or from_s > num_stations:
                    errors.append(f'Crossover {i}: "from" station {from_s} is out of range.')
                elif to_s < 1 or to_s > num_stations:
                    errors.append(f'Crossover {i}: "to" station {to_s} is out of range.')
                else:
                    crossover_pairs.append((from_s, to_s))

            if errors:
                for err in errors:
                    messages.error(request, err)
                return redirect('input')

            # ── Save to database ─────────────────────────────────────────
            layout = Layout.objects.create(
                user=request.user,
                num_stations=num_stations,
                num_crossovers=num_crossovers,
            )

            for idx in range(1, num_stations + 1):
                Station.objects.create(layout=layout, number=idx)

            for from_s, to_s in crossover_pairs:
                Crossover.objects.create(
                    layout=layout,
                    from_station=from_s,
                    to_station=to_s,
                )

            # Store layout id in session so layout_view can retrieve it
            request.session['layout_id'] = layout.id
            return redirect('layout')

        except (ValueError, TypeError):
            messages.error(request, 'Please enter valid numbers.')
            return redirect('input')

    return render(request, 'dashboard/input.html')


# ─────────────────────────────────────────────
#  LAYOUT VIEW  (the SVG track drawing)
# ─────────────────────────────────────────────

@login_required(login_url='login')
def layout_view(request):
    """
    Retrieve the saved layout from DB.
    Calculate (x, y) pixel positions for each station and crossover.
    Pass everything to layout.html which draws the SVG.
    """
    layout_id = request.session.get('layout_id')

    if not layout_id:
        messages.error(request, 'No layout found. Please fill the form first.')
        return redirect('input')

    try:
        layout = Layout.objects.get(id=layout_id, user=request.user)
    except Layout.DoesNotExist:
        messages.error(request, 'Layout not found.')
        return redirect('input')

    num_stations = layout.num_stations

    # ── Calculate SVG geometry ────────────────────────────────────────────
    # Canvas settings
    SVG_WIDTH        = 1200
    SVG_HEIGHT       = 300
    MARGIN_LEFT      = 80
    MARGIN_RIGHT     = 80
    STATION_SPACING  = (SVG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) // max(num_stations - 1, 1)

    UP_LINE_Y   = 100   # y-coordinate of UP track
    DOWN_LINE_Y = 200   # y-coordinate of DOWN track
    STATION_W   = 60
    STATION_H   = 30

    # Build station data list
    stations = []
    for i in range(1, num_stations + 1):
        x = MARGIN_LEFT + (i - 1) * STATION_SPACING
        stations.append({
            'number': i,
            'label': f'ST-{i:02d}',
            'x': x,
            'up_y': UP_LINE_Y,
            'down_y': DOWN_LINE_Y,
            'box_x': x - STATION_W // 2,
            'box_up_y': UP_LINE_Y - STATION_H // 2,
            'box_down_y': DOWN_LINE_Y - STATION_H // 2,
            'width': STATION_W,
            'height': STATION_H,
        })

    # Build crossover data list
    crossovers_db = Crossover.objects.filter(layout=layout)
    crossovers = []
    for co in crossovers_db:
        # midpoint between the two stations
        x1 = MARGIN_LEFT + (co.from_station - 1) * STATION_SPACING
        x2 = MARGIN_LEFT + (co.to_station   - 1) * STATION_SPACING
        mid_x = (x1 + x2) // 2
        crossovers.append({
            'from_station': co.from_station,
            'to_station':   co.to_station,
            'x1': x1,
            'x2': x2,
            'mid_x': mid_x,
            'up_y':   UP_LINE_Y,
            'down_y': DOWN_LINE_Y,
        })

    # Track line endpoints
    track_x1 = MARGIN_LEFT
    track_x2 = SVG_WIDTH - MARGIN_RIGHT

    context = {
        'layout':     layout,
        'stations':   stations,
        'crossovers': crossovers,
        'svg_width':  SVG_WIDTH,
        'svg_height': SVG_HEIGHT,
        'up_y':       UP_LINE_Y,
        'down_y':     DOWN_LINE_Y,
        'track_x1':   track_x1,
        'track_x2':   track_x2,
    }

    return render(request, 'dashboard/layout.html', context)


# ─────────────────────────────────────────────
#  CSV EXPORT
# ─────────────────────────────────────────────

@login_required(login_url='login')
def export_csv(request):
    """
    Export the current layout as a downloadable CSV file.
    Columns: Type, Station Number / Crossover From, To
    """
    layout_id = request.session.get('layout_id')

    if not layout_id:
        messages.error(request, 'No layout to export.')
        return redirect('input')

    try:
        layout = Layout.objects.get(id=layout_id, user=request.user)
    except Layout.DoesNotExist:
        return redirect('input')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dmrc_layout_{layout.id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Type', 'Number / From Station', 'To Station'])

    # Stations
    for s in Station.objects.filter(layout=layout).order_by('number'):
        writer.writerow(['Station', s.number, ''])

    # Crossovers
    for co in Crossover.objects.filter(layout=layout):
        writer.writerow(['Crossover', co.from_station, co.to_station])

    return response

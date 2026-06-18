
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Layout, Station, Crossover, Depot
import csv
import json


def login_view(request):
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
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def input_view(request):
    if request.method == 'POST':
        try:
            num_stations   = int(request.POST.get('num_stations', 0))
            num_crossovers = int(request.POST.get('num_crossovers', 0))
            num_depots     = int(request.POST.get('num_depots', 0))

            if num_stations < 2:
                messages.error(request, 'You need at least 2 stations.')
                return redirect('input')

            crossover_data = []
            errors = []
            for i in range(1, num_crossovers + 1):
                from_s   = request.POST.get(f'from_station_{i}')
                to_s     = request.POST.get(f'to_station_{i}')
                position = request.POST.get(f'co_position_{i}', 'after')
                if not from_s or not to_s:
                    errors.append(f'Crossover {i}: missing values.')
                    continue
                from_s, to_s = int(from_s), int(to_s)
                if from_s == to_s:
                    errors.append(f'Crossover {i}: from and to cannot be same.')
                elif from_s < 1 or from_s > num_stations:
                    errors.append(f'Crossover {i}: station {from_s} out of range.')
                elif to_s < 1 or to_s > num_stations:
                    errors.append(f'Crossover {i}: station {to_s} out of range.')
                else:
                    crossover_data.append((from_s, to_s, position))

            depot_data = []
            for i in range(1, num_depots + 1):
                near_s   = request.POST.get(f'depot_station_{i}')
                track    = request.POST.get(f'depot_track_{i}', 'up')
                position = request.POST.get(f'depot_position_{i}', 'after')
                if not near_s:
                    errors.append(f'Depot {i}: missing station.')
                    continue
                near_s = int(near_s)
                if near_s < 1 or near_s > num_stations:
                    errors.append(f'Depot {i}: station {near_s} out of range.')
                else:
                    depot_data.append((near_s, track, position))

            if errors:
                for e in errors:
                    messages.error(request, e)
                return redirect('input')

            layout = Layout.objects.create(
                user=request.user,
                num_stations=num_stations,
                num_crossovers=num_crossovers,
            )
            for idx in range(1, num_stations + 1):
                Station.objects.create(layout=layout, number=idx)
            for from_s, to_s, position in crossover_data:
                Crossover.objects.create(
                    layout=layout,
                    from_station=from_s,
                    to_station=to_s,
                    position=position,
                )
            for near_s, track, position in depot_data:
                Depot.objects.create(
                    layout=layout,
                    near_station=near_s,
                    track=track,
                    position=position,
                )

            request.session['layout_id'] = layout.id
            return redirect('layout')

        except (ValueError, TypeError):
            messages.error(request, 'Please enter valid numbers.')
            return redirect('input')

    return render(request, 'dashboard/input.html')


@login_required(login_url='login')
def layout_view(request):
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
    SVG_WIDTH    = 1200
    SVG_HEIGHT   = 400
    MARGIN_LEFT  = 100
    MARGIN_RIGHT = 100
    SPACING      = (SVG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) // max(num_stations - 1, 1)
    UP_Y         = 120
    DOWN_Y       = 260
    ST_W         = 60
    ST_H         = 24

    # ── stations ───────────────────────────────────────────────
    stations = []
    for i in range(1, num_stations + 1):
        x = MARGIN_LEFT + (i - 1) * SPACING
        stations.append({
            'number':     i,
            'label':      f'ST-{i:02d}',
            'x':          x,
            'box_x':      x - ST_W // 2,
            'box_up_y':   UP_Y   - ST_H // 2,
            'box_down_y': DOWN_Y - ST_H // 2,
            'width':      ST_W,
            'height':     ST_H,
            'up_y':       UP_Y,
            'down_y':     DOWN_Y,
        })

    # ── crossovers ─────────────────────────────────────────────
    # Crossover sits a FIXED distance away from the station —
    # it does not stretch toward the next station.
    crossovers = []
    XOV_WIDTH    = 50   # fixed width of the X itself
    XOV_DISTANCE = 60   # fixed distance from station edge to crossover

    for co in Crossover.objects.filter(layout=layout):
        from_x = MARGIN_LEFT + (co.from_station - 1) * SPACING

        if co.position == 'after':
            x_left  = from_x + ST_W // 2 + XOV_DISTANCE
            x_right = x_left + XOV_WIDTH
        else:
            x_right = from_x - ST_W // 2 - XOV_DISTANCE
            x_left  = x_right - XOV_WIDTH

        mid_x = (x_left + x_right) // 2
        mid_y = (UP_Y + DOWN_Y) // 2

        crossovers.append({
            'from_station': co.from_station,
            'to_station':   co.to_station,
            'position':     co.position,
            'd1_x1': x_left,  'd1_y1': UP_Y,
            'd1_x2': x_right, 'd1_y2': DOWN_Y,
            'd2_x1': x_left,  'd2_y1': DOWN_Y,
            'd2_x2': x_right, 'd2_y2': UP_Y,
            'up_left': x_left, 'up_right': x_right,
            'dn_left': x_left, 'dn_right': x_right,
            'mid_x': mid_x, 'mid_y': mid_y,
            'x_left': x_left, 'x_right': x_right,
        })

    # ── depots ─────────────────────────────────────────────────
    depots = []
    DEPOT_LEN = 55
    DEPOT_H   = 45
    CO_OFFSET = 20

    for dp in Depot.objects.filter(layout=layout):
        base_x   = MARGIN_LEFT + (dp.near_station - 1) * SPACING
        branch_x = base_x + CO_OFFSET if dp.position == 'after' else base_x - CO_OFFSET
        track_y  = UP_Y if dp.track == 'up' else DOWN_Y
        direction = -1 if dp.track == 'up' else 1
        end_x = branch_x + DEPOT_LEN
        end_y = track_y + direction * DEPOT_H

        depots.append({
            'near_station': dp.near_station,
            'track':        dp.track,
            'position':     dp.position,
            'x1':           branch_x,
            'y1':           track_y,
            'x2':           end_x,
            'y2':           end_y,
            'label_x':      end_x + 4,
            'label_y':      end_y,
        })

    context = {
        'layout':     layout,
        'stations':   stations,
        'crossovers': crossovers,
        'depots':     depots,
        'svg_width':  SVG_WIDTH,
        'svg_height': SVG_HEIGHT,
        'up_y':       UP_Y,
        'down_y':     DOWN_Y,
        'track_x1':   MARGIN_LEFT,
        'track_x2':   SVG_WIDTH - MARGIN_RIGHT,
    }

    context['stations_json'] = json.dumps(stations)
    context['crossovers_json'] = json.dumps(crossovers)
    context['last_crossover_x'] = crossovers[-1]['mid_x'] if crossovers else None

    return render(request, 'dashboard/layout.html', context)


@login_required(login_url='login')
def export_csv(request):
    layout_id = request.session.get('layout_id')
    if not layout_id:
        return redirect('input')
    try:
        layout = Layout.objects.get(id=layout_id, user=request.user)
    except Layout.DoesNotExist:
        return redirect('input')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dmrc_layout_{layout.id}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Type', 'Detail 1', 'Detail 2', 'Position'])
    for s in Station.objects.filter(layout=layout).order_by('number'):
        writer.writerow(['Station', s.number, '', ''])
    for co in Crossover.objects.filter(layout=layout):
        writer.writerow(['Crossover', co.from_station, co.to_station, co.position])
    for dp in Depot.objects.filter(layout=layout):
        writer.writerow(['Depot', dp.near_station, dp.track, dp.position])
    return response

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Layout, Station, Crossover, Depot
import csv
import json
# =====================================================================
# Backend Object-Oriented Design (OOP) for Metro Simulation Elements
# =====================================================================
class TrackCircuit:
    """
    Represents an isolated track segment (Block) that can detect 
    train occupancy. Occupancy drops to 0 when occupied, and picks up to 1 when clear.
    """
    def __init__(self, tc_id, line, start_x, end_x, idx=1):
        self.tc_id = tc_id          # Unique identifier, e.g. "AX19"
        self.line = line            # "up", "down", or "crossover"
        self.start_x = start_x      # Left boundary coordinate
        self.end_x = end_x          # Right boundary coordinate
        self.is_occupied = False    # State: False (Pick-up / Clear), True (Drop / Occupied)
        
        # Extended fields for ATS Mimic & Commands
        self.name = f"STN{idx}-STN{idx+1} UP" if line == 'up' else (f"STN{idx}-STN{idx+1} DOWN" if line == 'down' else f"XOV{idx} BLOCK")
        self.section = f"Station {idx} - Station {idx+1}" if line != 'crossover' else f"Crossover {idx}"
        self.type = "INTERSTATION" if line != 'crossover' else "CROSSOVER"
        self.chainageStart = 48000 + int(start_x * 10)
        self.chainageEnd = 48000 + int(end_x * 10)
        self.startAxId = f"AXC{30 + idx*2 - 1}"
        self.endAxId = f"AXC{30 + idx*2}"
        self.lineDirection = "UP" if line == 'up' else ("DOWN" if line == 'down' else "CROSSOVER")
        self.status = "CLEAR"
        self.length = int(abs(end_x - start_x) * 10)
        self.routeLocked = False
        self.reservation = "NONE"
        self.axleCounterReset = "NORMAL"
        self.failureStatus = False
        self.maintenanceBlock = False
        self.blocked = False
        self.noEntry = False
        self.tsr = False
        self.lowAdhesion = False
        self.reducedBrakeRate = False
        self.neutralZone = False
        self.raDisabled = False
        self.directionArrow = "UP" if line == 'up' else ("DOWN" if line == 'down' else "NONE")
        self.cbiMapping = f"CBI-{tc_id}"
        self.atpBlockRef = f"ATP-{tc_id}"
        import datetime
        self.lastStatusChange = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        self.x1 = int(start_x)
        self.y1 = 120 if line == 'up' else (260 if line == 'down' else 190)
        self.x2 = int(end_x)
        self.y2 = 120 if line == 'up' else (260 if line == 'down' else 190)

    def to_dict(self):
        return {
            'tc_id': self.tc_id,
            'line': self.line,
            'start_x': self.start_x,
            'end_x': self.end_x,
            'is_occupied': self.is_occupied,
            'name': self.name,
            'section': self.section,
            'type': self.type,
            'chainageStart': self.chainageStart,
            'chainageEnd': self.chainageEnd,
            'startAxId': self.startAxId,
            'endAxId': self.endAxId,
            'lineDirection': self.lineDirection,
            'status': self.status,
            'length': self.length,
            'routeLocked': self.routeLocked,
            'reservation': self.reservation,
            'axleCounterReset': self.axleCounterReset,
            'failureStatus': self.failureStatus,
            'maintenanceBlock': self.maintenanceBlock,
            'blocked': self.blocked,
            'noEntry': self.noEntry,
            'tsr': self.tsr,
            'lowAdhesion': self.lowAdhesion,
            'reducedBrakeRate': self.reducedBrakeRate,
            'neutralZone': self.neutralZone,
            'raDisabled': self.raDisabled,
            'directionArrow': self.directionArrow,
            'cbiMapping': self.cbiMapping,
            'atpBlockRef': self.atpBlockRef,
            'lastStatusChange': self.lastStatusChange,
            'x1': self.x1,
            'y1': self.y1,
            'x2': self.x2,
            'y2': self.y2
        }
class PointSwitch:
    """
    Represents physical crossover track switch points. Points guide trains between lines
    and can be set to Normal (straight) or Reverse (diverging).
    """
    def __init__(self, point_id, tc_id, from_station, to_station, position_type, x_left, x_right, y_up, y_down):
        self.point_id = point_id          # Unique identifier, e.g. "P-01"
        self.tc_id = tc_id                # Track Circuit segment the switch sits on
        self.from_station = from_station  # Reference station number
        self.to_station = to_station      # Secondary station number
        self.position_type = position_type# "before" or "after" the station
        self.x_left = x_left              # Left geometric coordinate
        self.x_right = x_right            # Right geometric coordinate
        self.y_up = y_up                  # Y coordinate on UP line
        self.y_down = y_down              # Y coordinate on DOWN line
        self.current_state = 'NORMAL'     # State: 'NORMAL' (Normal / Straight) or 'REVERSE' (Reverse / Diverging)
        self.is_locked = False            # True when a train occupies self.tc_id (cannot switch)
    def to_dict(self):
        return {
            'point_id': self.point_id,
            'tc_id': self.tc_id,
            'from_station': self.from_station,
            'to_station': self.to_station,
            'position_type': self.position_type,
            'x_left': self.x_left,
            'x_right': self.x_right,
            'y_up': self.y_up,
            'y_down': self.y_down,
            'current_state': self.current_state,
            'is_locked': self.is_locked
        }
class SignalPost:
    """
    Represents a physical wayside 3-Aspect Signal (Green, Violet, Red)
    used to protect blocks and crossovers.
    """
    def __init__(self, signal_id, line, x, y, protects_tc_id, signal_type):
        self.signal_id = signal_id        # Unique identifier, e.g. "S-UP-02"
        self.line = line                  # "up" or "down"
        self.x = x                        # Layout X coordinate
        self.y = y                        # Layout Y coordinate
        self.protects_tc_id = protects_tc_id # The track circuit this signal regulates entry to
        self.signal_type = signal_type    # Type: "station" or "crossover"
        self.aspect = 'GREEN'             # Current aspect: 'GREEN', 'VIOLET', 'RED'
    def to_dict(self):
        return {
            'signal_id': self.signal_id,
            'line': self.line,
            'x': self.x,
            'y': self.y,
            'protects_tc_id': self.protects_tc_id,
            'signal_type': self.signal_type,
            'aspect': self.aspect
        }
class MetroNetwork:
    """
    Master container class that reads the database models, builds the track layout,
    instantiates all OOP classes, links signals to blocks, and validates layout interlocking.
    """
    def __init__(self, layout, spacing, up_y, down_y, margin_left, margin_right, svg_width, st_w, st_h):
        self.layout = layout
        self.spacing = spacing
        self.up_y = up_y
        self.down_y = down_y
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.svg_width = svg_width
        self.st_w = st_w
        self.st_h = st_h
        self.stations = []
        self.track_circuits = []
        self.points = []
        self.signals = []
        self._build_network()

    def _build_network(self):
        try:
            data = json.loads(self.layout.layout_data)
        except Exception:
            data = {}

        stations_up = data.get('stations_up', ['UP-ST-1', 'UP-ST-2', 'UP-ST-3'])
        stations_down = data.get('stations_down', ['DN-ST-1', 'DN-ST-2', 'DN-ST-3'])
        tc_lengths_up = data.get('tc_lengths_up', [250, 250, 250, 250])
        tc_lengths_down = data.get('tc_lengths_down', [250, 250, 250, 250])
        crossovers_input = data.get('crossovers', [
            {'type': 'down_to_up', 'position': 15},
            {'type': 'up_to_down', 'position': 85}
        ])
        signals_input = data.get('signals', [
            {'line': 'up', 'position': 30},
            {'line': 'up', 'position': 70},
            {'line': 'down', 'position': 30},
            {'line': 'down', 'position': 70}
        ])

        # 1. Instantiate Track Circuits (Sequential on UP and DOWN lines using scaled lengths)
        total_width = self.svg_width - self.margin_left - self.margin_right # 1000px

        # UP Line TCs
        sum_len_up = sum(tc_lengths_up) if tc_lengths_up else 1.0
        scale_up = total_width / sum_len_up
        curr_x = self.margin_left
        for idx, length in enumerate(tc_lengths_up, 1):
            scaled_len = length * scale_up
            tc_id = f"AX{2*idx + 15}"
            self.track_circuits.append(TrackCircuit(tc_id, 'up', curr_x, curr_x + scaled_len, idx))
            curr_x += scaled_len

        # DOWN Line TCs
        sum_len_down = sum(tc_lengths_down) if tc_lengths_down else 1.0
        scale_down = total_width / sum_len_down
        curr_x = self.margin_left
        for idx, length in enumerate(tc_lengths_down, 1):
            scaled_len = length * scale_down
            tc_id = f"AX{2*idx + 16}"
            self.track_circuits.append(TrackCircuit(tc_id, 'down', curr_x, curr_x + scaled_len, idx))
            curr_x += scaled_len

        # 2. Instantiate Stations
        # UP stations
        num_up = len(stations_up)
        for idx, name in enumerate(stations_up, 1):
            x = self.margin_left + idx * (total_width / (num_up + 1))
            self.stations.append({
                'number': idx,
                'label': name,
                'line': 'up',
                'x': x,
                'box_x': x - self.st_w // 2,
                'box_up_y': self.up_y - self.st_h // 2,
                'box_down_y': self.down_y - self.st_h // 2,
                'width': self.st_w,
                'height': self.st_h,
                'up_y': self.up_y,
                'down_y': self.down_y,
            })

        # DOWN stations
        num_down = len(stations_down)
        for idx, name in enumerate(stations_down, 1):
            x = self.margin_left + idx * (total_width / (num_down + 1))
            self.stations.append({
                'number': num_up + idx,
                'label': name,
                'line': 'down',
                'x': x,
                'box_x': x - self.st_w // 2,
                'box_up_y': self.up_y - self.st_h // 2,
                'box_down_y': self.down_y - self.st_h // 2,
                'width': self.st_w,
                'height': self.st_h,
                'up_y': self.up_y,
                'down_y': self.down_y,
            })

        # 3. Instantiate Crossover Points
        XOV_WIDTH = 50
        for idx, co in enumerate(crossovers_input, 1):
            pct = co['position']
            co_type = co['type']
            x_center = self.margin_left + (pct / 100.0) * total_width
            x_left = x_center - XOV_WIDTH // 2
            x_right = x_center + XOV_WIDTH // 2
            
            tc_id = f'AX-XOV-{idx}'
            
            # Instantiate PointSwitches for each label drawn on screen
            if idx % 2 == 1:
                labels = [f"P{2*idx - 1}", f"P{2*idx}"]
            else:
                labels = [f"P{2*idx - 1}", f"P{2*idx}", f"P{2*idx + 1}", f"P{2*idx + 2}"]
                
            for label in labels:
                pt = PointSwitch(
                    point_id=label,
                    tc_id=tc_id,
                    from_station=1,
                    to_station=2,
                    position_type='after',
                    x_left=x_left,
                    x_right=x_right,
                    y_up=self.up_y,
                    y_down=self.down_y
                )
                pt.crossover_type = co_type
                self.points.append(pt)
            
            self.track_circuits.append(TrackCircuit(tc_id, 'crossover', x_left, x_right, idx))

        # 4. Instantiate Wayside Signal Posts
        for idx, sig in enumerate(signals_input, 1):
            line = sig['line']
            pct = sig['position']
            x = self.margin_left + (pct / 100.0) * total_width
            y = self.up_y if line == 'up' else self.down_y
            protects_tc_id = self._get_tc_at(x, line)
            
            self.signals.append(SignalPost(
                signal_id=f'S-{line.upper()}-{idx}',
                line=line,
                x=x,
                y=y,
                protects_tc_id=protects_tc_id,
                signal_type='station'
            ))

    def _get_tc_at(self, x, line):
        for tc in self.track_circuits:
            if tc.line == line and tc.start_x <= x <= tc.end_x:
                return tc.tc_id
        return 'TC-UNKNOWN'

    def get_serialized_data(self):
        points_serialized = []
        for p in self.points:
            d = p.to_dict()
            d['crossover_type'] = getattr(p, 'crossover_type', 'up_to_down')
            points_serialized.append(d)
        return {
            'stations': self.stations,
            'track_circuits': [tc.to_dict() for tc in self.track_circuits],
            'points': points_serialized,
            'signals': [s.to_dict() for s in self.signals]
        }
# =====================================================================
# Django Controller Views
# =====================================================================
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
            # 1. Parse station counts and names
            num_stations = int(request.POST.get('num_stations', 0))
            
            stations = []
            for i in range(1, num_stations + 1):
                name = request.POST.get(f'st_name_{i}', f'ST-{i}').strip()
                stations.append(name)
                
            stations_up = list(stations)
            stations_down = list(stations)

            # 2. Parse track circuit counts and lengths
            num_tc_up = int(request.POST.get('num_tc_up', 0))
            tc_lengths_up = []
            for i in range(1, num_tc_up + 1):
                length = float(request.POST.get(f'tc_up_len_{i}', 250))
                tc_lengths_up.append(length)

            num_tc_down = int(request.POST.get('num_tc_down', 0))
            tc_lengths_down = []
            for i in range(1, num_tc_down + 1):
                length = float(request.POST.get(f'tc_down_len_{i}', 250))
                tc_lengths_down.append(length)

            # 3. Parse crossovers
            num_crossovers = int(request.POST.get('num_crossovers', 0))
            crossovers_data = []
            for i in range(1, num_crossovers + 1):
                pos = float(request.POST.get(f'co_pos_{i}', 50))
                co_type = request.POST.get(f'co_type_{i}', 'up_to_down')
                crossovers_data.append({'position': pos, 'type': co_type})

            # Sort crossovers by position
            crossovers_data.sort(key=lambda c: c['position'])

            # 4. Parse signals
            num_signals = int(request.POST.get('num_signals', 0))
            signals_data = []
            for i in range(1, num_signals + 1):
                line = request.POST.get(f'sig_line_{i}', 'up')
                pos = float(request.POST.get(f'sig_pos_{i}', 50))
                signals_data.append({'line': line, 'position': pos})

            # Form data dict
            layout_data_dict = {
                'stations_up': stations_up,
                'stations_down': stations_down,
                'tc_lengths_up': tc_lengths_up,
                'tc_lengths_down': tc_lengths_down,
                'crossovers': crossovers_data,
                'signals': signals_data
            }
            
            # Save Layout model
            layout = Layout.objects.create(
                user=request.user,
                num_stations=len(stations_up),
                num_crossovers=len(crossovers_data),
                layout_data=json.dumps(layout_data_dict)
            )

            request.session['layout_id'] = layout.id
            if 'sim_state' in request.session:
                del request.session['sim_state']
            if 'last_tick_time' in request.session:
                del request.session['last_tick_time']
                
            return redirect('layout')
        except (ValueError, TypeError) as e:
            messages.error(request, f'Please enter valid numbers. Error: {e}')
            return redirect('input')
            
    # GET Request: Load existing layout data or sensible defaults
    layout_id = request.session.get('layout_id')
    layout_data_json = '{}'
    if layout_id:
        try:
            layout = Layout.objects.get(id=layout_id, user=request.user)
            layout_data_json = layout.layout_data
        except Layout.DoesNotExist:
            pass
            
    if layout_data_json == '{}':
        # Default layout structure
        default_layout = {
            'stations_up': ['Dwarka Sec 21', 'Dwarka Sec 8', 'Dwarka Sec 9'],
            'stations_down': ['Noida Electronic City', 'Noida Sec 62', 'Noida Sec 59'],
            'tc_lengths_up': [250, 250, 250, 250],
            'tc_lengths_down': [250, 250, 250, 250],
            'crossovers': [
                {'position': 15, 'type': 'down_to_up'},
                {'position': 85, 'type': 'up_to_down'}
            ],
            'signals': [
                {'line': 'up', 'position': 30},
                {'line': 'up', 'position': 70},
                {'line': 'down', 'position': 30},
                {'line': 'down', 'position': 70}
            ]
        }
        layout_data_json = json.dumps(default_layout)
        
    return render(request, 'dashboard/input.html', {'layout_data_json': layout_data_json})

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
    
    SVG_WIDTH    = 1200
    SVG_HEIGHT   = 400
    MARGIN_LEFT  = 100
    MARGIN_RIGHT = 100
    SPACING      = 200 # unused but kept for compatibility
    UP_Y         = 120
    DOWN_Y       = 260
    ST_W         = 60
    ST_H         = 24
    
    # Instantiate the OOP MetroNetwork class to build the layout components
    network = MetroNetwork(
        layout=layout,
        spacing=SPACING,
        up_y=UP_Y,
        down_y=DOWN_Y,
        margin_left=MARGIN_LEFT,
        margin_right=MARGIN_RIGHT,
        svg_width=SVG_WIDTH,
        st_w=ST_W,
        st_h=ST_H
    )
    network_data = network.get_serialized_data()
    
    # Prepare depots (fallback logic since depots are automatic/unused by form)
    depots = []
    DEPOT_LEN = 55
    DEPOT_H   = 45
    CO_OFFSET = 20
    # Place a depot near the first station if stations exist
    if network_data['stations']:
        first_st = network_data['stations'][0]
        base_x = first_st['x']
        branch_x = base_x + CO_OFFSET
        end_x = branch_x + DEPOT_LEN
        end_y = UP_Y - DEPOT_H
        depots.append({
            'near_station': 1,
            'track':        'up',
            'position':     'after',
            'x1':           branch_x,
            'y1':           UP_Y,
            'x2':           end_x,
            'y2':           end_y,
            'label_x':      end_x + 4,
            'label_y':      end_y,
        })
    
    # Prepare Context dictionary
    context = {
        'layout':     layout,
        'stations':   network_data['stations'],
        'depots':     depots,
        'svg_width':  SVG_WIDTH,
        'svg_height': SVG_HEIGHT,
        'up_y':       UP_Y,
        'down_y':     DOWN_Y,
        'track_x1':   MARGIN_LEFT,
        'track_x2':   SVG_WIDTH - MARGIN_RIGHT,
    }
    context['stations_json'] = json.dumps(network_data['stations'])
    
    # Format crossovers to match frontend key expectations
    frontend_crossovers = []
    try:
        layout_data = json.loads(layout.layout_data)
    except Exception:
        layout_data = {}
    crossovers_input = layout_data.get('crossovers', [])
    
    total_width = SVG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    XOV_WIDTH = 50
    for idx, co in enumerate(crossovers_input, 1):
        pct = co['position']
        co_type = co['type']
        x_center = MARGIN_LEFT + (pct / 100.0) * total_width
        x_left = x_center - XOV_WIDTH // 2
        x_right = x_center + XOV_WIDTH // 2
        mid_x = (x_left + x_right) // 2
        mid_y = (UP_Y + DOWN_Y) // 2
        frontend_crossovers.append({
            'index':        idx,
            'from_station': 1,
            'to_station':   2,
            'position':     'after',
            'type':         co_type,
            'x_left':       x_left,
            'x_right':      x_right,
            'width':        XOV_WIDTH,
            'mid_x':        mid_x,
            'mid_y':        mid_y,
        })
    context['crossovers'] = frontend_crossovers
    context['crossovers_json'] = json.dumps(frontend_crossovers)
    context['last_crossover_x'] = frontend_crossovers[-1]['mid_x'] if frontend_crossovers else None
    
    # Enrich signals with line index for template ID matching
    signals_list = []
    for idx, sig in enumerate(network_data['signals'], 1):
        sig_copy = dict(sig)
        sig_copy['num'] = idx
        signals_list.append(sig_copy)
    context['signals'] = signals_list
    
    # Pass the full network model details to the template as a JSON string
    context['network_json'] = json.dumps(network_data)
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
        
    try:
        data = json.loads(layout.layout_data)
    except Exception:
        data = {}

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dmrc_layout_{layout.id}.csv"'
    writer = csv.writer(response)
    
    writer.writerow(['Category', 'Name / Length', 'Line / Type', 'Position (%)'])
    
    # Stations UP
    for s_name in data.get('stations_up', []):
        writer.writerow(['Station', s_name, 'UP', ''])
        
    # Stations DOWN
    for s_name in data.get('stations_down', []):
        writer.writerow(['Station', s_name, 'DOWN', ''])
        
    # Track Circuits UP
    for idx, L in enumerate(data.get('tc_lengths_up', []), 1):
        writer.writerow(['Track Circuit', f'TC-UP-{idx}', f'Length: {L}m', ''])

    # Track Circuits DOWN
    for idx, L in enumerate(data.get('tc_lengths_down', []), 1):
        writer.writerow(['Track Circuit', f'TC-DN-{idx}', f'Length: {L}m', ''])
        
    # Crossovers
    for idx, co in enumerate(data.get('crossovers', []), 1):
        writer.writerow(['Crossover', f'XOV-{idx}', co['type'].upper(), f"{co['position']}%"])
        
    # Signals
    for idx, sig in enumerate(data.get('signals', []), 1):
        writer.writerow(['Signal', f"S-{sig['line'].upper()}-{idx}", sig['line'].upper(), f"{sig['position']}%"])
        
    return response
# =====================================================================
# Real-Time Python Simulation Engine & Kinematics Loop
# =====================================================================
import math
import time
def build_journey_path(margin_left, margin_right, spacing, num_stations, up_y, down_y, crossovers, svg_width):
    """
    Builds the closed-loop path segments that the train follows.
    """
    path = []
    sorted_co = sorted(crossovers, key=lambda c: c['x_left'])
    first_co = sorted_co[0] if sorted_co else None
    last_co = sorted_co[-1] if sorted_co else None
    track_x1 = margin_left
    track_x2 = svg_width - margin_right
    if first_co and last_co and first_co['x_left'] != last_co['x_left']:
        path.append({'x1': first_co['x_right'], 'y1': up_y, 'x2': last_co['x_left'], 'y2': up_y, 'track': 'up'})
        path.append({'x1': last_co['x_left'], 'y1': up_y, 'x2': last_co['x_right'], 'y2': down_y, 'track': 'crossover', 'index': last_co['index']})
        path.append({'x1': last_co['x_right'], 'y1': down_y, 'x2': first_co['x_left'], 'y2': down_y, 'track': 'down'})
        path.append({'x1': first_co['x_left'], 'y1': down_y, 'x2': first_co['x_right'], 'y2': up_y, 'track': 'crossover', 'index': first_co['index']})
    elif last_co:
        path.append({'x1': track_x1, 'y1': up_y, 'x2': last_co['x_left'], 'y2': up_y, 'track': 'up'})
        path.append({'x1': last_co['x_left'], 'y1': up_y, 'x2': last_co['x_right'], 'y2': down_y, 'track': 'crossover', 'index': last_co['index']})
        path.append({'x1': last_co['x_right'], 'y1': down_y, 'x2': track_x1, 'y2': down_y, 'track': 'down'})
        path.append({'x1': track_x1, 'y1': down_y, 'x2': track_x1, 'y2': up_y, 'track': 'crossover', 'index': None})
    else:
        path.append({'x1': track_x1, 'y1': up_y, 'x2': track_x2, 'y2': up_y, 'track': 'up'})
        path.append({'x1': track_x2, 'y1': up_y, 'x2': track_x2, 'y2': down_y, 'track': 'crossover', 'index': None})
        path.append({'x1': track_x2, 'y1': down_y, 'x2': track_x1, 'y2': down_y, 'track': 'down'})
        path.append({'x1': track_x1, 'y1': down_y, 'x2': track_x1, 'y2': up_y, 'track': 'crossover', 'index': None})
    for seg in path:
        seg['length'] = math.hypot(seg['x2'] - seg['x1'], seg['y2'] - seg['y1'])
    return path
class Train:
    """
    Models physical train movement parameters and kinematics math.
    """
    def __init__(self, train_id, journey):
        self.train_id = train_id
        self.journey = journey
        self.seg_index = 0
        self.seg_progress = 0.0
        self.speed = 0.0
        self.acc = 0.0
        self.state = 'ACCELERATING'
        self.dwell_timer = 0.0
        self.x = journey[0]['x1']
        self.y = journey[0]['y1']
        self.last_stopped_station = None
        self.last_stopped_line = None
        
        # New telemetry parameters (m, d, s, t mappings)
        self.current_tc = 'TC-UNKNOWN'
        self.chainage = 0.0
        self.direction = 'UP'
        self.mode = 'ATO'
    def get_speed_kmh(self):
        return self.speed * 3.6
    def calculate_acceleration(self):
        speed_kmh = self.get_speed_kmh()
        if speed_kmh < 30:
            return 1.3
        elif speed_kmh < 45:
            return 1.2
        else:
            return 1.0
    def to_dict(self):
        return {
            'train_id': self.train_id,
            'seg_index': self.seg_index,
            'seg_progress': self.seg_progress,
            'speed': self.speed,
            'acc': self.acc,
            'state': self.state,
            'dwell_timer': self.dwell_timer,
            'x': self.x,
            'y': self.y,
            'last_stopped_station': self.last_stopped_station,
            'last_stopped_line': self.last_stopped_line,
            
            # Signaling parameters (m, d, s, t)
            'current_tc': self.current_tc,
            'current_track_circuit': self.current_tc,
            'chainage': self.chainage,
            'mode': self.mode,
            'm': self.mode,
            'direction': self.direction,
            'd': self.direction,
            's': self.get_speed_kmh(),
            't': self.current_tc
        }
    @classmethod
    def from_dict(cls, data, journey):
        t = cls(data['train_id'], journey)
        t.seg_index = data['seg_index']
        t.seg_progress = data['seg_progress']
        t.speed = data['speed']
        t.acc = data['acc']
        t.state = data['state']
        t.dwell_timer = data['dwell_timer']
        t.x = data['x']
        t.y = data['y']
        t.last_stopped_station = data['last_stopped_station']
        t.last_stopped_line = data['last_stopped_line']
        
        # Load new fields with fallback
        t.current_tc = data.get('current_tc', 'TC-UNKNOWN')
        t.chainage = data.get('chainage', 0.0)
        t.direction = data.get('direction', 'UP')
        t.mode = data.get('mode', 'ATO')
        return t
class TrainSimEngine:
    """
    Python Simulation Engine running occupancy, speed, and safety interlocking checks.
    """
    def __init__(self, network_data, journey):
        self.stations = network_data['stations']
        self.track_circuits = [TrackCircuit(tc['tc_id'], tc['line'], tc['start_x'], tc['end_x']) for tc in network_data['track_circuits']]
        self.points = [PointSwitch(p['point_id'], p['tc_id'], p['from_station'], p['to_station'], p['position_type'], p['x_left'], p['x_right'], p['y_up'], p['y_down']) for p in network_data['points']]
        self.signals = [SignalPost(s['signal_id'], s['line'], s['x'], s['y'], s['protects_tc_id'], s['signal_type']) for s in network_data['signals']]
        self.journey = journey
        self.train = Train('TR-0011', journey)
        self.event_logs = []
    def log_event(self, message, type='INFO'):
        import datetime
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.event_logs.append({
            'timestamp': timestamp,
            'message': message,
            'type': type
        })
        self.event_logs = self.event_logs[-50:]
    def to_dict(self):
        return {
            'train': self.train.to_dict(),
            'track_circuits': [tc.to_dict() for tc in self.track_circuits],
            'points': [p.to_dict() for p in self.points],
            'signals': [s.to_dict() for s in self.signals],
            'event_logs': self.event_logs
        }
    @classmethod
    def from_dict(cls, data, network_data, journey):
        engine = cls(network_data, journey)
        engine.train = Train.from_dict(data['train'], journey)
        
        tc_dict = {tc_data['tc_id']: tc_data for tc_data in data.get('track_circuits', [])}
        for tc in engine.track_circuits:
            tc_data = tc_dict.get(tc.tc_id)
            if tc_data:
                tc.is_occupied = tc_data.get('is_occupied', False)
                tc.routeLocked = tc_data.get('routeLocked', False)
                tc.reservation = tc_data.get('reservation', 'NONE')
                tc.axleCounterReset = tc_data.get('axleCounterReset', 'NORMAL')
                tc.failureStatus = tc_data.get('failureStatus', False)
                tc.maintenanceBlock = tc_data.get('maintenanceBlock', False)
                tc.blocked = tc_data.get('blocked', False)
                tc.noEntry = tc_data.get('noEntry', False)
                tc.tsr = tc_data.get('tsr', False)
                tc.lowAdhesion = tc_data.get('lowAdhesion', False)
                tc.reducedBrakeRate = tc_data.get('reducedBrakeRate', False)
                tc.neutralZone = tc_data.get('neutralZone', False)
                tc.raDisabled = tc_data.get('raDisabled', False)
                tc.status = tc_data.get('status', 'CLEAR')
                tc.name = tc_data.get('name', tc.name)
                tc.section = tc_data.get('section', tc.section)
                tc.type = tc_data.get('type', tc.type)
                tc.chainageStart = tc_data.get('chainageStart', tc.chainageStart)
                tc.chainageEnd = tc_data.get('chainageEnd', tc.chainageEnd)
                tc.startAxId = tc_data.get('startAxId', tc.startAxId)
                tc.endAxId = tc_data.get('endAxId', tc.endAxId)
                tc.lineDirection = tc_data.get('lineDirection', tc.lineDirection)
                tc.length = tc_data.get('length', tc.length)
                tc.directionArrow = tc_data.get('directionArrow', tc.directionArrow)
                tc.cbiMapping = tc_data.get('cbiMapping', tc.cbiMapping)
                tc.atpBlockRef = tc_data.get('atpBlockRef', tc.atpBlockRef)
                tc.lastStatusChange = tc_data.get('lastStatusChange', tc.lastStatusChange)
                tc.x1 = tc_data.get('x1', tc.x1)
                tc.y1 = tc_data.get('y1', tc.y1)
                tc.x2 = tc_data.get('x2', tc.x2)
                tc.y2 = tc_data.get('y2', tc.y2)
                
        p_dict = {p_data['point_id']: p_data for p_data in data.get('points', [])}
        for p in engine.points:
            p_data = p_dict.get(p.point_id)
            if p_data:
                p.current_state = p_data.get('current_state', 'NORMAL')
                p.is_locked = p_data.get('is_locked', False)
                
        sig_dict = {s_data['signal_id']: s_data for s_data in data.get('signals', [])}
        for s in engine.signals:
            s_data = sig_dict.get(s.signal_id)
            if s_data:
                s.aspect = s_data.get('aspect', 'GREEN')
                
        engine.event_logs = data.get('event_logs', [])
        return engine
    def tick(self, dt):
        t = self.train
        prev_state = t.state
        prev_seg_index = t.seg_index
        prev_tc = t.current_tc
        current_seg = self.journey[t.seg_index]
        speed_limit = (25.0 / 3.6) if current_seg['track'] == 'crossover' else (60.0 / 3.6)
        if t.state == 'DWELLING':
            t.speed = 0.0
            t.acc = 0.0
            t.dwell_timer -= dt
            if t.dwell_timer <= 0.0:
                t.state = 'ACCELERATING'
                self.log_event(f"Train {t.train_id} completed dwelling and is departing")
            return
        # 1. Locate next station target stop on the current segment
        stop_target_dist = None
        target_station_obj = None
        if current_seg['track'] == 'up':
            valid_stations = [s for s in self.stations if s['line'] == 'up' and current_seg['x1'] < s['x'] <= current_seg['x2']]
            valid_stations.sort(key=lambda s: s['x'])
            for s in valid_stations:
                d_station = s['x'] - current_seg['x1']
                if d_station > t.seg_progress - 2.0 and (t.last_stopped_station != s['number'] or t.last_stopped_line != 'up'):
                    stop_target_dist = d_station
                    target_station_obj = s
                    break
        elif current_seg['track'] == 'down':
            valid_stations = [s for s in self.stations if s['line'] == 'down' and current_seg['x2'] <= s['x'] < current_seg['x1']]
            valid_stations.sort(key=lambda s: s['x'], reverse=True)
            for s in valid_stations:
                d_station = current_seg['x1'] - s['x']
                if d_station > t.seg_progress - 2.0 and (t.last_stopped_station != s['number'] or t.last_stopped_line != 'down'):
                    stop_target_dist = d_station
                    target_station_obj = s
                    break
        # 2. Deceleration zones
        if stop_target_dist is not None:
            dist_to_station = stop_target_dist - t.seg_progress
            brake_dist = (t.speed * t.speed) / (2.0 * 1.2)
            if dist_to_station <= brake_dist + 2.0:
                t.state = 'BRAKING'
                t.acc = - (t.speed * t.speed) / (2.0 * max(1.0, dist_to_station))
                if t.acc > -0.2 and t.speed > 1.5:
                    t.acc = -1.2
            
            if dist_to_station < 2.0 and t.speed < 1.5:
                t.speed = 0.0
                t.seg_progress = stop_target_dist
                t.state = 'DWELLING'
                t.dwell_timer = 3.0
                t.last_stopped_station = target_station_obj['number']
                t.last_stopped_line = current_seg['track']
                
                self.log_event(f"Train {t.train_id} arrived at {target_station_obj['label']} (" + ("PF-01" if current_seg['track'] == 'up' else "PF-02") + ") and is dwelling")
                self.evaluate_interlocking(target_station_obj['x'], current_seg['track'])
                return
        else:
            # Slow down for crossover speed caution
            next_seg = self.journey[(t.seg_index + 1) % len(self.journey)]
            if next_seg and next_seg['track'] == 'crossover' and t.speed > (25.0 / 3.6):
                dist_to_crossover = current_seg['length'] - t.seg_progress
                slow_dist = (t.speed * t.speed - (25.0/3.6)**2) / (2.0 * 1.2)
                if dist_to_crossover <= slow_dist + 2.0:
                    t.state = 'BRAKING'
                    t.acc = - (t.speed * t.speed - (25.0/3.6)**2) / (2.0 * max(1.0, dist_to_crossover))
                    if t.acc > -0.2 and t.speed > (25.0 / 3.6) + 1.0:
                        t.acc = -1.2
        # 3. Kinematics updates
        if t.state == 'ACCELERATING':
            t.acc = t.calculate_acceleration()
            t.speed += t.acc * dt
            if t.speed >= speed_limit:
                t.speed = speed_limit
                t.state = 'CRUISING'
                t.acc = 0.0
        elif t.state == 'CRUISING':
            t.acc = 0.0
            if t.speed < speed_limit:
                t.state = 'ACCELERATING'
            else:
                t.speed = speed_limit
        elif t.state == 'BRAKING':
            t.speed += t.acc * dt
            if t.speed < 0.0:
                t.speed = 0.0
        # 4. Progress coordinate update
        t.seg_progress += t.speed * dt
        if t.seg_progress >= current_seg['length']:
            t.seg_progress = t.seg_progress - current_seg['length']
            t.seg_index = (t.seg_index + 1) % len(self.journey)
            t.state = 'ACCELERATING'
        next_seg_active = self.journey[t.seg_index]
        progress_ratio = (t.seg_progress / next_seg_active['length']) if next_seg_active['length'] > 0 else 1.0
        t.x = next_seg_active['x1'] + (next_seg_active['x2'] - next_seg_active['x1']) * progress_ratio
        t.y = next_seg_active['y1'] + (next_seg_active['y2'] - next_seg_active['y1']) * progress_ratio
        
        # Update train telemetry parameters (m, d, s, t mappings)
        t.mode = 'ATO'
        t.direction = next_seg_active['track'].upper()
        t.chainage = round(t.x - 100.0, 1)  # 1 pixel = 1 meter, starting at X=100 (Station 1)
        
        # 5. Run interlocking
        self.evaluate_interlocking(t.x, next_seg_active['track'])
        
        # Log key state transitions and block entries
        if t.state != prev_state:
            self.log_event(f"Train {t.train_id} state changed to {t.state}")
        if t.current_tc != prev_tc and t.current_tc != 'TC-UNKNOWN':
            self.log_event(f"Train {t.train_id} entered track circuit {t.current_tc}")
    def evaluate_interlocking(self, train_x, train_line):
        # Reset occupancy
        for tc in self.track_circuits:
            tc.is_occupied = False
        # Detect active track circuit block
        active_tc = None
        for tc in self.track_circuits:
            if tc.line == train_line:
                min_x = min(tc.start_x, tc.end_x)
                max_x = max(tc.start_x, tc.end_x)
                if min_x <= train_x <= max_x:
                    tc.is_occupied = True
                    active_tc = tc
        
        if active_tc:
            self.train.current_tc = active_tc.tc_id
        else:
            self.train.current_tc = 'TC-UNKNOWN'
        # Lock point switches (Track Locking)
        for pt in self.points:
            prev_locked = pt.is_locked
            if pt.tc_id == (active_tc.tc_id if active_tc else None):
                pt.is_locked = True
            else:
                pt.is_locked = False
            if pt.is_locked != prev_locked:
                status = "LOCKED" if pt.is_locked else "UNLOCKED"
                self.log_event(f"Point Switch {pt.point_id} ({pt.tc_id}) is {status}", type="WARNING" if pt.is_locked else "INFO")
        # Cascade Signal Aspects
        prev_aspects = {sig.signal_id: sig.aspect for sig in self.signals}
        for sig in self.signals:
            sig.aspect = 'GREEN'
        if train_line == 'up':
            up_sigs = sorted([s for s in self.signals if s.line == 'up'], key=lambda s: s.x)
            passed_idx = -1
            for i in range(len(up_sigs)):
                if train_x >= up_sigs[i].x:
                    passed_idx = i
            if passed_idx != -1:
                up_sigs[passed_idx].aspect = 'RED'
                if passed_idx > 0:
                    up_sigs[passed_idx - 1].aspect = 'VIOLET'
            next_idx = passed_idx + 1
            if next_idx < len(up_sigs):
                next_sig = up_sigs[next_idx]
                if next_sig.signal_type == 'crossover':
                    next_sig.aspect = 'VIOLET'
        elif train_line == 'down':
            dn_sigs = sorted([s for s in self.signals if s.line == 'down'], key=lambda s: s.x, reverse=True)
            passed_idx = -1
            for i in range(len(dn_sigs)):
                if train_x <= dn_sigs[i].x:
                    passed_idx = i
            if passed_idx != -1:
                dn_sigs[passed_idx].aspect = 'RED'
                if passed_idx > 0:
                    dn_sigs[passed_idx - 1].aspect = 'VIOLET'
            next_idx = passed_idx + 1
            if next_idx < len(dn_sigs):
                next_sig = dn_sigs[next_idx]
                if next_sig.signal_type == 'crossover':
                    next_sig.aspect = 'VIOLET'
        elif train_line == 'crossover':
            current_seg = self.journey[self.train.seg_index]
            if current_seg and current_seg['index'] is not None:
                co_sig = next((s for s in self.signals if s.signal_type == 'crossover' and s.signal_id.endswith(str(current_seg['index']))), None)
                if co_sig:
                    co_sig.aspect = 'RED'
                    line_sigs = sorted([s for s in self.signals if s.line == co_sig.line], key=lambda s: s.x if co_sig.line == 'up' else -s.x)
                    try:
                        idx = line_sigs.index(co_sig)
                        if idx > 0:
                            line_sigs[idx - 1].aspect = 'VIOLET'
                    except ValueError:
                        pass
        # Log signal changes
        for sig in self.signals:
            old = prev_aspects.get(sig.signal_id)
            if old and sig.aspect != old:
                self.log_event(f"Signal {sig.signal_id} aspect changed to {sig.aspect}")

@login_required(login_url='login')
def simulation_tick(request):
    """
    Simulation tick AJAX endpoint. Updates the physics, occupancy, interlocking,
    and signals on the backend, saving state in the session and returning JSON.
    """
    layout_id = request.session.get('layout_id')
    if not layout_id:
        return HttpResponse('No layout found', status=400)
    try:
        layout = Layout.objects.get(id=layout_id, user=request.user)
    except Layout.DoesNotExist:
        return HttpResponse('Layout not found', status=404)
    
    SVG_WIDTH    = 1200
    SVG_HEIGHT   = 400
    MARGIN_LEFT  = 100
    MARGIN_RIGHT = 100
    SPACING      = 200
    UP_Y         = 120
    DOWN_Y       = 260
    ST_W         = 60
    ST_H         = 24
    
    network = MetroNetwork(layout, SPACING, UP_Y, DOWN_Y, MARGIN_LEFT, MARGIN_RIGHT, SVG_WIDTH, ST_W, ST_H)
    network_data = network.get_serialized_data()
    
    # Reconstruct crossovers to have index
    frontend_crossovers = []
    try:
        layout_data = json.loads(layout.layout_data)
    except Exception:
        layout_data = {}
    crossovers_input = layout_data.get('crossovers', [])
    total_width = SVG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    XOV_WIDTH = 50
    for idx, co in enumerate(crossovers_input, 1):
        pct = co['position']
        x_center = MARGIN_LEFT + (pct / 100.0) * total_width
        x_left = x_center - XOV_WIDTH // 2
        x_right = x_center + XOV_WIDTH // 2
        mid_x = (x_left + x_right) // 2
        mid_y = (UP_Y + DOWN_Y) // 2
        frontend_crossovers.append({
            'index':        idx,
            'x_left':       x_left,
            'x_right':      x_right,
            'mid_x':        mid_x,
            'mid_y':        mid_y,
            'type':         co['type']
        })
        
    journey = build_journey_path(MARGIN_LEFT, MARGIN_RIGHT, SPACING, len(network_data['stations']), UP_Y, DOWN_Y, frontend_crossovers, SVG_WIDTH)
    
    # Load simulation state from session
    sim_data = request.session.get('sim_state')
    if not sim_data:
        engine = TrainSimEngine(network_data, journey)
    else:
        try:
            engine = TrainSimEngine.from_dict(sim_data, network_data, journey)
        except Exception:
            engine = TrainSimEngine(network_data, journey)
            
    # Compute actual delta-time
    last_tick_time = request.session.get('last_tick_time')
    now = time.time()
    if last_tick_time:
        dt = now - last_tick_time
        if dt > 0.1:
            dt = 0.033
    else:
        dt = 0.033
    request.session['last_tick_time'] = now
    
    # Execute simulation tick
    engine.tick(dt)
    
    # Save state back to session
    engine_dict = engine.to_dict()
    request.session['sim_state'] = engine_dict
    
    # Enrich response data with stations, crossovers, and event logs
    response_data = dict(engine_dict)
    response_data['stations'] = network_data['stations']
    
    crossovers_payload = []
    for idx, pt in enumerate(engine.points, 1):
        mid_x = (pt.x_left + pt.x_right) // 2
        mid_y = (pt.y_up + pt.y_down) // 2
        crossovers_payload.append({
            'index':        idx,
            'point_id':     pt.point_id,
            'tc_id':        pt.tc_id,
            'from_station': pt.from_station,
            'to_station':   pt.to_station,
            'position':     pt.position_type,
            'type':         getattr(pt, 'crossover_type', 'up_to_down'),
            'x_left':       pt.x_left,
            'x_right':      pt.x_right,
            'width':        pt.x_right - pt.x_left,
            'mid_x':        mid_x,
            'mid_y':        mid_y,
            'current_state': pt.current_state,
            'is_locked':    pt.is_locked
        })
    response_data['crossovers'] = crossovers_payload
    
    from django.http import JsonResponse
    return JsonResponse(response_data)


@login_required(login_url='login')
def update_track(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
        tc_id = data.get('tc_id')
        command = data.get('command')
        
        sim_state = request.session.get('sim_state')
        if sim_state:
            for tc in sim_state.get('track_circuits', []):
                if tc['tc_id'] == tc_id:
                    import datetime
                    tc['lastStatusChange'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    
                    if command == 'set_tsr':
                        tc['tsr'] = True
                    elif command == 'release_tsr':
                        tc['tsr'] = False
                    elif command == 'no_entry_on':
                        tc['noEntry'] = True
                    elif command == 'no_entry_off':
                        tc['noEntry'] = False
                    elif command == 'maint_block':
                        tc['maintenanceBlock'] = True
                    elif command == 'maint_release':
                        tc['maintenanceBlock'] = False
                    elif command == 'low_adhesion_on':
                        tc['lowAdhesion'] = True
                    elif command == 'low_adhesion_off':
                        tc['lowAdhesion'] = False
                    elif command == 'clear_locking':
                        tc['routeLocked'] = False
                        tc['reservation'] = 'NONE'
                    elif command == 'route_set':
                        tc['routeLocked'] = True
                        tc['reservation'] = 'ROUTE'
                        
                    # Update overall status
                    if tc['maintenanceBlock']:
                        tc['status'] = 'MAINTENANCE'
                    elif tc['is_occupied']:
                        tc['status'] = 'OCCUPIED'
                    elif tc['blocked']:
                        tc['status'] = 'BLOCKED'
                    elif tc['failureStatus']:
                        tc['status'] = 'FAILED'
                    else:
                        tc['status'] = 'CLEAR'
                    break
            request.session['sim_state'] = sim_state
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required(login_url='login')
def update_point(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
        point_id = data.get('point_id')
        position = data.get('position')
        
        sim_state = request.session.get('sim_state')
        if sim_state:
            for p in sim_state.get('points', []):
                if p['point_id'] == point_id:
                    if not p.get('is_locked', False):
                        p['current_state'] = position
                        
                        import datetime
                        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                        sim_state.setdefault('event_logs', []).append({
                            'timestamp': timestamp,
                            'message': f"Point Switch {point_id} set to {position}",
                            'type': 'INFO'
                        })
                    break
            request.session['sim_state'] = sim_state
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)




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


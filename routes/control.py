"""Multi-device dashboard and outbound-polling ESP32 API."""
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from database.db import db
from models.device import Device
from security import csrf

control_bp = Blueprint('control', __name__)
COMMANDS = {'forward', 'reverse', 'left', 'right', 'stop'}
MODES = {'manual', 'auto'}
ACCESSORIES = {'brush', 'rig_up', 'rig_down', 'led', 'spray'}
OFF = {'brush': False, 'rig_up': False, 'rig_down': False, 'led': False, 'spray': False}


def _admin():
    return current_user.is_authenticated and current_user.role == 'admin'


def _device_json(device):
    age = (datetime.utcnow() - device.last_seen).total_seconds() if device.last_seen else None
    connected = age is not None and age < 45
    if not connected:
        # A stale device must never resume a latched output when it reconnects.
        if device.command != 'stop' or (device.accessories or OFF) != OFF:
            device.command = 'stop'
            device.accessories = dict(OFF)
            db.session.commit()
    accessories = dict(device.accessories or OFF) if connected and not device.emergency_stop else dict(OFF)
    t = device.telemetry or {}
    return {
        'id': device.device_id, 'device_id': device.device_id, 'name': device.name,
        'server_url': device.server_url, 'connected': connected,
        'last_seen_seconds': round(age, 1) if age is not None else None,
        'mode': device.mode, 'command': device.command if connected else 'stop',
        'speed': device.speed, 'line_color': device.line_color,
        'emergency_stop': device.emergency_stop, 'accessories': accessories,
        'battery': t.get('battery'), 'distance_cm': t.get('distance_cm'),
        'rssi': t.get('rssi'), 'firmware': t.get('firmware'),
        'line_sensors': t.get('line_sensors', [False] * 4), 'obstacle': t.get('obstacle', False),
    }


def _device_auth(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        token = request.headers.get('X-Device-Token', '')
        device = Device.query.filter_by(token=token).first() if token else None
        if not device:
            return jsonify({'error': 'Device authentication failed. Add this ESP32 in the Devices tab and copy its token.'}), 401
        return fn(device, *args, **kwargs)
    return wrapped


@control_bp.route('/control')
@login_required
def index():
    return render_template('control.html')


@control_bp.route('/devices')
@login_required
def devices_page():
    return render_template('devices.html')


@control_bp.get('/api/robot/devices')
@login_required
def web_devices():
    return jsonify([_device_json(d) for d in Device.query.order_by(Device.created_at.asc()).all()])


@control_bp.get('/api/robot/status')
@login_required
def web_status():
    device_id = request.args.get('device_id', '')
    device = Device.query.filter_by(device_id=device_id).first() if device_id else Device.query.order_by(Device.created_at.asc()).first()
    return jsonify(_device_json(device) if device else {'connected': False, 'device_id': None, 'mode': 'manual', 'command': 'stop', 'accessories': dict(OFF), 'last_seen_seconds': None})


@control_bp.post('/api/robot/command')
@login_required
def web_command():
    if not _admin():
        return jsonify({'error': 'Administrator access required.'}), 403
    body = request.get_json(silent=True) or {}
    device = Device.query.filter_by(device_id=body.get('device_id', '')).first()
    if not device:
        return jsonify({'error': 'Select a registered device first.'}), 404
    mode, command, speed, line_color = body.get('mode'), body.get('command'), body.get('speed'), body.get('line_color')
    if mode is not None:
        if mode not in MODES: return jsonify({'error': 'Mode must be manual or auto.'}), 400
        device.mode, device.command = mode, 'stop'
        if body.get('renewal') is not True:
            device.emergency_stop = False
    if line_color is not None:
        if line_color not in {'white', 'black'}: return jsonify({'error': 'Line colour must be white or black.'}), 400
        device.line_color = line_color
    if command is not None:
        if command not in COMMANDS: return jsonify({'error': 'Invalid movement command.'}), 400
        if device.mode != 'manual' and command != 'stop': return jsonify({'error': 'Movement-pad commands are only allowed in manual mode.'}), 409
        device.command = command
    if speed is not None:
        try: device.speed = max(0, min(255, int(speed)))
        except (TypeError, ValueError): return jsonify({'error': 'Speed must be an integer from 0 to 255.'}), 400
    if 'accessories' in body:
        values = body['accessories']
        if not isinstance(values, dict) or set(values) - ACCESSORIES or any(not isinstance(v, bool) for v in values.values()):
            return jsonify({'error': 'Invalid accessory state.'}), 400
        next_values = dict(device.accessories or OFF); next_values.update(values)
        if next_values.get('rig_up') and next_values.get('rig_down'):
            return jsonify({'error': 'Rig up and rig down cannot run together.'}), 409
        device.accessories = next_values
    if body.get('emergency') is True:
        device.command, device.emergency_stop, device.accessories = 'stop', True, dict(OFF)
    now = datetime.utcnow()
    if body.get('renewal') is not True:
        device.rearm_required = False
        device.command_seq = int(device.command_seq or 0) + 1
        device.command_updated_at = now
    elif device.rearm_required:
        device.command, device.accessories = 'stop', dict(OFF)
    if device.emergency_stop:
        device.command, device.accessories = 'stop', dict(OFF)
    device.command_lease_at = now
    db.session.commit()
    return jsonify({'ok': True, **_device_json(device)})


@control_bp.post('/api/robot/devices')
@login_required
def create_device():
    if not _admin(): return jsonify({'error': 'Administrator access required.'}), 403
    body = request.get_json(silent=True) or {}
    device_id = (body.get('device_id') or '').strip()
    name = (body.get('name') or device_id).strip()
    server_url = (body.get('server_url') or '').strip().rstrip('/')
    if not device_id or len(device_id) > 80 or not name or len(name) > 120:
        return jsonify({'error': 'Provide a device ID (max 80 characters) and name (max 120).'}), 400
    if not server_url.startswith('https://') and not (not os.environ.get('RENDER') and server_url.startswith('http://')):
        return jsonify({'error': 'Use an HTTPS server URL for internet-connected devices.'}), 400
    if Device.query.filter_by(device_id=device_id).first(): return jsonify({'error': 'That device ID already exists.'}), 409
    device = Device(device_id=device_id, name=name, token=secrets.token_urlsafe(32), server_url=server_url, command_updated_at=datetime.utcnow(), command_lease_at=datetime.utcnow(), command_seq=0)
    db.session.add(device); db.session.commit()
    return jsonify({'ok': True, 'device': _device_json(device), 'token': device.token}), 201


@control_bp.patch('/api/robot/devices/<int:row_id>')
@login_required
def update_device(row_id):
    if not _admin(): return jsonify({'error': 'Administrator access required.'}), 403
    device = db.session.get(Device, row_id)
    if not device: return jsonify({'error': 'Device not found.'}), 404
    body = request.get_json(silent=True) or {}
    if 'name' in body:
        name = str(body['name']).strip()
        if not name or len(name) > 120: return jsonify({'error': 'Invalid device name.'}), 400
        device.name = name
    if 'server_url' in body:
        url = str(body['server_url']).strip().rstrip('/')
        if not url.startswith('https://') and not (not __import__('os').environ.get('RENDER') and url.startswith('http://')):
            return jsonify({'error': 'Use an HTTPS server URL for internet-connected devices.'}), 400
        device.server_url = url
    db.session.commit(); return jsonify({'ok': True, 'device': _device_json(device)})


@control_bp.delete('/api/robot/devices/<int:row_id>')
@login_required
def delete_device(row_id):
    if not _admin(): return jsonify({'error': 'Administrator access required.'}), 403
    device = db.session.get(Device, row_id)
    if not device: return jsonify({'error': 'Device not found.'}), 404
    db.session.delete(device); db.session.commit(); return jsonify({'ok': True})


@control_bp.post('/api/robot/devices/<int:row_id>/rotate-token')
@login_required
def rotate_device_token(row_id):
    if not _admin(): return jsonify({'error': 'Administrator access required.'}), 403
    device = db.session.get(Device, row_id)
    if not device: return jsonify({'error': 'Device not found.'}), 404
    device.token = secrets.token_urlsafe(32)
    device.command = 'stop'
    device.accessories = dict(OFF)
    device.command_updated_at = datetime.utcnow()
    device.command_lease_at = datetime.utcnow()
    device.command_seq = 0
    device.rearm_required = True
    db.session.commit()
    return jsonify({'ok': True, 'device_id': device.device_id, 'server_url': device.server_url, 'token': device.token})


@control_bp.get('/api/device/command')
@csrf.exempt
@_device_auth
def device_command(device):
    status = _device_json(device)
    lease_age = (datetime.utcnow() - device.command_lease_at).total_seconds() if device.command_lease_at else 999
    stale = lease_age > 5
    if stale:
        device.command = 'stop'
        device.accessories = dict(OFF)
        db.session.commit()
    return jsonify({'mode': device.mode, 'command': 'stop' if stale or device.rearm_required else status['command'],
                    'command_id': int(device.command_seq or 0),
                    'speed': device.speed, 'line_color': device.line_color,
                    'stop': stale or device.rearm_required or (not status['connected']) or device.emergency_stop,
                    'accessories': dict(OFF) if stale or device.rearm_required else status['accessories']})


@control_bp.post('/api/device/telemetry')
@csrf.exempt
@_device_auth
def device_telemetry(device):
    body = request.get_json(silent=True) or {}
    allowed = {'battery', 'distance_cm', 'rssi', 'firmware', 'device_id', 'obstacle', 'line_sensors', 'line_color'}
    claimed_id = body.get('device_id')
    if claimed_id and claimed_id != device.device_id:
        return jsonify({'error': 'Telemetry device ID does not match the authenticated device.'}), 403
    telemetry = dict(device.telemetry or {})
    telemetry.update({k: body[k] for k in allowed if k in body and k != 'device_id'})
    telemetry['device_id'] = device.device_id
    device.telemetry = telemetry
    device.last_seen = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})

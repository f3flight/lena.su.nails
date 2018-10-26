#!/usr/bin/env python

import json
import os
import yaml

from appointments.appointments import gcal
from googleapiclient.errors import HttpError

from flask import Flask
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session

app = Flask(__name__)
app.config['SECRET_KEY'] = '1pc80m3475475n7wzerifzxnxf87o5ct0w4,mct5wvixamwr6z'
cfg = {}
if os.path.exists('config.yaml'):
    cfg = yaml.load(open('config.yaml', 'r'))


@app.route('/', methods=['GET', 'POST'])
def main():
    session['fail_msg'] = None
    if 'cal' not in g:
        g.cal = gcal.AppointmentManager('credentials.json', cfg)
    if request.method == 'GET':
        return get()
    else:
        return post(request)


@app.route('/free')
def free_json():
    if 'cal' not in g:
        g.cal = gcal.AppointmentManager('credentials.json', cfg)
    return json.dumps(free_slots_stripped())


def get():
    g.cal.refresh()
    return render_template('picker.html', cfg=cfg,
                           free_slots=free_slots_stripped())


def post(request):
    ok = False
    if request.form.get('slot'):
        try:
            ok = g.cal.create_appointment(request.form['slot'], request.form)
        except HttpError as e:
            resp = getattr(e, 'resp', None)
            status = ''
            reason = ''
            details = ''
            if resp:
                status = getattr(resp, 'status', '')
                reason = getattr(resp, 'reason', '')
                if reason:
                    details = e._get_reason()
            return fail_with_msg('Error details: < %s | %s | %s >' %
                                 (status, reason, details))
    else:
        return fail_with_msg('Looks like you forgot to select a time slot?')
    if ok:
        return redirect(request.headers['X-Client-Root'] + 'success', code=302)
    else:
        return fail_with_msg('Sorry, this slot is already booked!'
                             ' Better luck next time!')


@app.route('/success')
def success():
    session['fail_msg'] = None
    return render_template('create_success.html')


@app.route('/fail')
def fail():
    return render_template('create_fail.html')


def free_slots_stripped():
    result = {}
    if g.cal.free_slots:
        for slot in g.cal.free_slots:
            key = slot['start']['dateTime']
            result[key] = {'id': slot['id'], 'end': slot['end']['dateTime']}
    return result


def fail_with_msg(msg):
    session['fail_msg'] = msg
    return redirect(request.headers['X-Client-Root'] + 'fail', code=302)

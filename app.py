import sqlite3
from datetime import date
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)
app.secret_key = 'CHANGE-ME-IN-PRODUCTION'
DB='clinic.db'

CLINICS={
 'DS': {'name':'Darul Sehat Hospital','doctor':'Mon & Wed · 6:30–7:30 PM','fee':2000,'phone':'021-111-300-999','map':''},
 'JH': {'name':'Darul Shifa Orthomedicare — Jauhar','doctor':'Mon–Sat · 7:30–9:00 PM','fee':1700,'phone':'0334-3706234','map':'https://maps.app.goo.gl/j7DCeYppQBEEYyu38'},
 'FB': {'name':'Darul Shifa Orthocare — FB Area','doctor':'Mon–Sat · 9:30–11:00 PM','fee':1300,'phone':'0301-3392979','map':'https://maps.app.goo.gl/FFi5YWraaEJm4sz66'},
}

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY, clinic TEXT, appt_date TEXT, seq INTEGER, token TEXT, name TEXT, age TEXT, phone TEXT, visit_type TEXT, service TEXT DEFAULT 'Orthopedic', status TEXT DEFAULT 'Booked', created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS booking_state(clinic TEXT, appt_date TEXT, is_open INTEGER DEFAULT 1, PRIMARY KEY(clinic,appt_date));
    CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, pin TEXT, role TEXT, clinic TEXT);
    INSERT OR IGNORE INTO users VALUES('admin','2468','admin','ALL');
    INSERT OR IGNORE INTO users VALUES('jauhar','1357','reception','JH');
    INSERT OR IGNORE INTO users VALUES('fbarea','3579','reception','FB');
    INSERT OR IGNORE INTO users VALUES('darulsehat','4680','reception','DS');
    '''); c.commit(); c.close()

STYLE='''<style>body{font-family:Arial,sans-serif;background:#f4f7fb;margin:0;color:#182230}.top{background:#0b3d66;color:white;padding:18px}.wrap{max-width:1100px;margin:auto;padding:18px}.card{background:white;border-radius:14px;padding:16px;margin:12px 0;box-shadow:0 2px 10px #0001}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.btn{display:inline-block;padding:9px 13px;border-radius:9px;background:#0b6efd;color:white;text-decoration:none;border:0;cursor:pointer}.danger{background:#b42318}.ok{background:#067647}.muted{color:#667085}.token{font-size:26px;font-weight:700}.stat{font-size:24px;font-weight:700}input,select{padding:10px;border:1px solid #ccd3dd;border-radius:8px;width:100%;box-sizing:border-box;margin:5px 0 10px}table{width:100%;border-collapse:collapse}th,td{padding:9px;border-bottom:1px solid #eee;text-align:left}@media(max-width:650px){table{font-size:12px}.hide-sm{display:none}}</style>'''

def page(title, body): return f'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>{STYLE}</head><body><div class="top"><b>Prof. Adeel Ahmed Siddiqui · Clinic Queue</b></div><div class="wrap">{body}</div></body></html>'

@app.route('/')
def home():
    cards=''.join([f'''<div class="card"><h3>{v['name']}</h3><div>{v['doctor']}</div><div>Consultation: Rs. {v['fee']:,}</div><p><a class="btn" href="/book/{k}">Book appointment</a></p></div>''' for k,v in CLINICS.items()])
    return page('Clinic Appointment', f'<h2>Orthopedic Appointment & Token System</h2><p class="muted">Choose a clinic. Tokens are issued in first-come, first-served order for each clinic date.</p><div class="grid">{cards}</div><div class="card"><b>Physiotherapy:</b> Jauhar Mon–Sat 6–9 PM · FB Area Mon–Sat 7–11 PM · Rs. 500 · Male & female physiotherapists available.</div><p><a href="/login">Staff login</a></p>')

@app.route('/book/<clinic>', methods=['GET','POST'])
def book(clinic):
    if clinic not in CLINICS: return 'Unknown clinic',404
    if request.method=='POST':
        d=request.form['date']; c=db()
        st=c.execute('SELECT is_open FROM booking_state WHERE clinic=? AND appt_date=?',(clinic,d)).fetchone()
        if st and not st['is_open']: c.close(); return page('Closed','<div class="card"><h2>Booking closed</h2><p>Please contact clinic staff or select another clinic/date.</p></div>')
        seq=c.execute('SELECT COALESCE(MAX(seq),0)+1 n FROM appointments WHERE clinic=? AND appt_date=?',(clinic,d)).fetchone()['n']
        token=f'{clinic}-{seq:03d}'
        c.execute('INSERT INTO appointments(clinic,appt_date,seq,token,name,age,phone,visit_type,service) VALUES(?,?,?,?,?,?,?,?,?)',(clinic,d,seq,token,request.form['name'],request.form['age'],request.form['phone'],request.form['visit_type'],request.form['service']))
        c.commit(); c.close()
        return page('Confirmed',f'''<div class="card"><h2>Appointment confirmed</h2><div class="token">{token}</div><p><b>{request.form['name']}</b><br>{CLINICS[clinic]['name']}<br>{d}<br>{CLINICS[clinic]['doctor']}</p><p>There are <b>{seq-1}</b> booked tokens before yours.</p><p class="muted">Please arrive early. Emergency cases and consultation complexity may affect the actual waiting time.</p></div>''')
    today=date.today().isoformat(); v=CLINICS[clinic]
    return page('Book',f'''<div class="card"><h2>{v['name']}</h2><div>{v['doctor']} · Rs. {v['fee']:,}</div><form method="post"><label>Date</label><input type="date" name="date" min="{today}" required><label>Patient name</label><input name="name" required><label>Age</label><input name="age"><label>Mobile</label><input name="phone" required><label>Visit</label><select name="visit_type"><option>New Patient</option><option>Follow-up</option></select><label>Service</label><select name="service"><option>Orthopedic</option><option>Physiotherapy</option></select><button class="btn">Generate token</button></form></div>''')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        c=db(); u=c.execute('SELECT * FROM users WHERE username=? AND pin=?',(request.form['username'],request.form['pin'])).fetchone(); c.close()
        if u: session.update(user=u['username'],role=u['role'],clinic=u['clinic']); return redirect('/dashboard')
        err='<p class="danger">Invalid login</p>'
    else: err=''
    return page('Staff login',f'''<div class="card" style="max-width:420px"><h2>Staff login</h2>{err}<form method="post"><input name="username" placeholder="Username" required><input name="pin" type="password" placeholder="PIN" required><button class="btn">Login</button></form><p class="muted">Prototype accounts are seeded for testing. Change credentials before real patient use.</p></div>''')

def allowed(clinic): return session.get('role')=='admin' or session.get('clinic')==clinic

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:return redirect('/login')
    d=request.args.get('date',date.today().isoformat()); c=db(); blocks=[]
    for code,v in CLINICS.items():
        if not allowed(code): continue
        rows=c.execute('SELECT * FROM appointments WHERE clinic=? AND appt_date=? ORDER BY seq',(code,d)).fetchall()
        counts={s:sum(1 for r in rows if r['status']==s) for s in ['Booked','Arrived','Waiting','Seen','Cancelled']}
        st=c.execute('SELECT is_open FROM booking_state WHERE clinic=? AND appt_date=?',(code,d)).fetchone(); isopen=1 if st is None else st['is_open']
        trs=''.join([f'''<tr><td><b>{r['token']}</b></td><td>{r['name']}</td><td>{r['age']}</td><td class="hide-sm">{r['phone']}</td><td>{r['visit_type']}</td><td>{r['service']}</td><td>{r['status']}</td><td><a href="/status/{r['id']}/Arrived">Arrived</a> · <a href="/status/{r['id']}/Waiting">Waiting</a> · <a href="/status/{r['id']}/Seen">Seen</a> · <a href="/status/{r['id']}/Cancelled">Cancel</a></td></tr>''' for r in rows]) or '<tr><td colspan="8">No patients yet.</td></tr>'
        blocks.append(f'''<div class="card"><h2>{v['name']}</h2><div class="grid"><div><span class="stat">{len(rows)}</span><br>Total</div><div><span class="stat">{counts['Waiting']}</span><br>Waiting</div><div><span class="stat">{counts['Seen']}</span><br>Seen</div><div><span class="stat">{counts['Cancelled']}</span><br>Cancelled</div></div><p>Booking: <b>{'OPEN' if isopen else 'CLOSED'}</b> · <a class="btn {'danger' if isopen else 'ok'}" href="/toggle/{code}?date={d}">{'Close' if isopen else 'Reopen'} booking</a> <a class="btn" href="/walkin/{code}?date={d}">Add walk-in</a></p><table><tr><th>Token</th><th>Name</th><th>Age</th><th class="hide-sm">Phone</th><th>Visit</th><th>Service</th><th>Status</th><th>Actions</th></tr>{trs}</table></div>''')
    c.close(); return page('Dashboard',f'''<form><label>Clinic date</label><input style="max-width:220px" type="date" name="date" value="{d}" onchange="this.form.submit()"></form>{''.join(blocks)}<p><a href="/logout">Logout</a></p>''')

@app.route('/status/<int:i>/<status>')
def status(i,status):
    if 'user' not in session:return redirect('/login')
    c=db(); r=c.execute('SELECT clinic FROM appointments WHERE id=?',(i,)).fetchone()
    if r and allowed(r['clinic']) and status in ['Booked','Arrived','Waiting','Seen','Cancelled']: c.execute('UPDATE appointments SET status=? WHERE id=?',(status,i)); c.commit()
    c.close(); return redirect(request.referrer or '/dashboard')

@app.route('/toggle/<clinic>')
def toggle(clinic):
    if 'user' not in session or not allowed(clinic): return redirect('/login')
    d=request.args.get('date',date.today().isoformat()); c=db(); r=c.execute('SELECT is_open FROM booking_state WHERE clinic=? AND appt_date=?',(clinic,d)).fetchone(); new=0 if r is None or r['is_open'] else 1
    c.execute('INSERT INTO booking_state(clinic,appt_date,is_open) VALUES(?,?,?) ON CONFLICT(clinic,appt_date) DO UPDATE SET is_open=excluded.is_open',(clinic,d,new)); c.commit(); c.close(); return redirect('/dashboard?date='+d)

@app.route('/walkin/<clinic>',methods=['GET','POST'])
def walkin(clinic):
    if 'user' not in session or not allowed(clinic):return redirect('/login')
    d=request.args.get('date',date.today().isoformat())
    if request.method=='POST':
        c=db(); seq=c.execute('SELECT COALESCE(MAX(seq),0)+1 n FROM appointments WHERE clinic=? AND appt_date=?',(clinic,d)).fetchone()['n']; token=f'{clinic}-{seq:03d}'
        c.execute('INSERT INTO appointments(clinic,appt_date,seq,token,name,age,phone,visit_type,service,status) VALUES(?,?,?,?,?,?,?,?,?,?)',(clinic,d,seq,token,request.form['name'],request.form['age'],request.form['phone'],request.form['visit_type'],request.form['service'],'Arrived')); c.commit(); c.close(); return redirect('/dashboard?date='+d)
    return page('Walk-in',f'''<div class="card"><h2>Add walk-in · {CLINICS[clinic]['name']}</h2><form method="post"><input name="name" placeholder="Patient name" required><input name="age" placeholder="Age"><input name="phone" placeholder="Mobile"><select name="visit_type"><option>New Patient</option><option>Follow-up</option></select><select name="service"><option>Orthopedic</option><option>Physiotherapy</option></select><button class="btn">Add & issue token</button></form></div>''')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__=='__main__':
    init(); app.run(host='0.0.0.0',port=5000,debug=True)

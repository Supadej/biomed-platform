#!/usr/bin/env python3
"""Create the first administrator account in the local SQLite installation."""
import getpass, importlib.util, re, secrets, sys
from pathlib import Path
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('biomed_server',root/'serve.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server);server.initialize()
email=input('Administrator email: ').strip().lower();name=input('Administrator full name: ').strip()
if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):sys.exit('Enter a valid email address.')
if not name:sys.exit('Name is required.')
with server.connect() as c:
 if c.execute('select count(*) from accounts').fetchone()[0]:sys.exit('An account already exists. Use the signed-in System Admin to add staff accounts.')
portal=c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()
if portal:
 import json
 data=json.loads(portal[0]);user=next((u for u in data.get('users',[]) if u.get('role')=='System Admin'),None)
else:user=None
uid=user.get('id') if user else 'u1'
password=getpass.getpass('Create password (minimum 12 characters): ')
if len(password)<12:sys.exit('Use at least 12 characters.')
confirm=getpass.getpass('Confirm password: ')
if password!=confirm:sys.exit('Passwords did not match.')
salt,digest,it=server.password_record(password);aid=secrets.token_hex(16)
with server.connect() as c:c.execute('insert into accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) values(?,?,?,?,?,?,?,?,datetime(\'now\'))',(aid,email,name,'System Admin',uid,digest,salt,it))
print('Administrator account created. Start Biomed and sign in through Staff Portal.')

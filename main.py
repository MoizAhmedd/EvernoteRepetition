import firebase_admin
import datetime
import requests
import json
import os
from firebase_admin import credentials
from firebase_admin import firestore
from creds import SENDGRID_KEY


# Use a service account
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

BAD_NOTEBOOK_IDS = [
	"d79cc7f9-8224-e7f7-17a3-25731973f663",
	"b98c886c-4f43-4f97-aa03-e116e94e69dd",
	49000,
]


email_body = ""

notes_ref = db.collection(u'notes')


def next_date(level):
	levels = {0: 0, 1: 1, 2: 2, 3: 7, 4: 14, 5: 30, 6: 180}
	today = datetime.datetime.today()
	delta = 0
	if level >= 7:
		delta = 365
	else:
		delta = levels[level]
	return (today + datetime.timedelta(days=delta)).strftime('%Y-%m-%d')

def delete_bad_notes():
	count = 0
	bad_notes_ref = notes_ref.where(u'notebook_id',u'in',BAD_NOTEBOOK_IDS)
	bad_docs = bad_notes_ref.stream()

	for bad_doc in bad_docs:
		count += 1
		notes_ref.document(f'{bad_doc.id}').delete()
	
	return f"Deleted {count} bad notes"

def update_new_notes():
	#Update new notes repeat dates, from tomorrow to actual date
	count = 0
	remind_tomorrow_ref = notes_ref.where(u'next_repeat', u'==', u'tomorrow')
	remind_tomorrow_docs = remind_tomorrow_ref.stream()

	for remind_tmr_doc in remind_tomorrow_docs:
		count += 1
		level = remind_tmr_doc.to_dict()["level"]
		updated = notes_ref.document(f"{remind_tmr_doc.id}").set(
			{"next_repeat": next_date(level)}, merge=True
		)
	
	return f"Updated {count} notes"

send_email_ref = notes_ref.where(u'next_repeat',u'==',next_date(0))
send_email_docs = send_email_ref.stream()
	
#Populate email content
for send_email_doc in send_email_docs:
	to_dict = send_email_doc.to_dict()
	new_link = """
		<li><a href = "{}">{} [{} repetitions]</a></li>\n
	""".format(
		to_dict["link"], to_dict["title"], to_dict["level"]
	)
	email_body += new_link
	updated = notes_ref.document(f"{send_email_doc.id}").set(
		{"next_repeat":next_date(to_dict["level"]),"level": to_dict["level"]+1}, merge=True
	)


#Format email content
email_template = """
<!doctype html>

<html lang="en">
<head>
  <title>Spaced Repetition Email</title>
</head>
<body>
	<h4>Here are your notes to review today</h4>
	<hr>
	<ul>
		{}
	</ul>
</body>
</html>
""".format(
	email_body
)

#Send email
if email_body:
	headers = {
	'Authorization': 'Bearer {}'.format(SENDGRID_KEY),
	'Content-Type': 'application/json',
	}
	data = {"personalizations": [{"to": [{"email": "ahmedmoiz854@gmail.com"}]}],"from": {"email": "moiz@subscrybe.app"},"subject": "Daily review","content": [{"type": "text/html", "value": "{}".format(email_template)}]}
	response = requests.post('https://api.sendgrid.com/v3/mail/send', headers=headers, data=json.dumps(data))
	print(response.content)
	print(response.status_code)
else:
	print("No emails")

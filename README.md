# Evernote Repetition System
- Built to help me review notes I take on evernote for different topics

## How it works
- Have a Zapier zap that pushes evernote notes to firebase
- main.py script to run through notes on firebase daily, and give me a list of notes to review
- Based off of how many times I've reviewed the notes, the next date at which I am scheduled to review the notes changes
- Script runs as a cronjob on an ec2 instance


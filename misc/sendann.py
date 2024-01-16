"""
This script sends an email to advertise or remind of a CS seminar.
"""

# Requires dateutil and pyyaml packages 

import smtplib
import subprocess
from email.message import EmailMessage
from dateutil.parser import parse
import argparse
import textwrap
import yaml


# Change the following as needed
EMAIL_SERVER = "smtp.office365.com"
EMAIL_PORT = 587
EMAIL_USERNAME = "Matteo.Sammartino@rhul.ac.uk"
EMAIL_PASSWD_CMD = [
    "python3",
    "mutt_oauth2.py"]
SEMINARS_WEBSITE="https://rhul-cs-seminars.github.io/"

# Email receivers and contents
TECH_RECEIVERS = ["CompSci-Researchstaff@rhul.ac.uk", "InformationSecurity.AcademicStaff@rhul.ac.uk", "Mathematics-AcademicStaff@rhul.ac.uk", "InformationSecurity.VisitingStaff@rhul.ac.uk", "InfoSecu.PhD@rhul.ac.uk", "InformationSecurity.ResearchStaff@rhul.ac.uk", "CompSci-AcademicStaff@rhul.ac.uk", "CompSci-PhD@rhul.ac.uk", "Maths-PhD@rhul.ac.uk", "CompSci-MSc@rhul.ac.uk", "CompSci-UG-4thyears@rhul.ac.uk", "CompSci-UG-3rdyears@rhul.ac.uk"]
DEPT_RECEIVERS = TECH_RECEIVERS

# MOODLE_PAGE = "https://moodle.royalholloway.ac.uk/course/view.php?id=9361"

SUBJECT = "{tag} {topic} ({type}) Seminar {prep}{time} -- {title}"

TECH_ANN = """
Dear all,

There is a technical seminar on {topic} {prep}{time}. Details are given below.


Title:           {title}
Speaker:         {speaker}
Institution:     {institution}
Time:            {time}
Venue:           {venue}
{link}


Abstract:

{abstract}

{bio}

Details of this term's seminars (including links to recordings) are available here:
{seminars_website}


Best wishes,
   Matteo
   
"""


DEPT_ANN = """
Dear all,

There is a Departmental seminar on {topic} {prep}{time}. Details are given below.

Departmental seminars are aimed at a wide audience and will give a good
introduction to a topic in computer science. Your participation is encouraged.

{extra}

Title:         {title}
Speaker:       {speaker}
Institution:   {institution}
Time:          {time}
Venue:         {venue}
{link}

Abstract:

{abstract}

{bio}

Details of this term's seminars (including links to recordings) are available here:
{seminars_website}


Best wishes,
    Matteo
    
"""


def parse_yaml_file(yaml_file):
    with open(yaml_file,'r') as f:
        # Add a dummy section name and then get rid of it
        data = yaml.load_all(f, Loader=yaml.FullLoader)
        # Jekyll yaml files have two --- rows, which are interpreted as
        # two different yaml files. Here we only return the correct one
        return next(data)



def pad_mins(n):

    if n < 10:
        return '%02d' % n
    else:
        return str(n)

def compose_message(data, reminder=None):
    text_wrapper = textwrap.TextWrapper(width=80);

    if data["type"] == "Departmental":
        msg = DEPT_ANN
        receivers = DEPT_RECEIVERS
    else:
        msg = TECH_ANN
        receivers = TECH_RECEIVERS

    if 'extra' not in data:
        data['extra'] = ''

    if data["bio"]:
        bio_list = text_wrapper.wrap(text=data["bio"])
        data["bio"] = "Short Bio:\n\n" + "".join([line + "\n" for line in bio_list])
    else:
        data["bio"] = ""

    data["seminars_website"] = SEMINARS_WEBSITE

    if data["link"]:
        data["link"] = "MS Teams: " + data["link"]
    else:
        data["link"] = ""

    data["prep"]= "on "

    # YAML seminar spec must contain date in ISO format
    date_object = parse(data["date"])

    if reminder:
        data["tag"] = "[CS Sem] REMINDER | "
        
        if reminder == "30":
            data["time"] = "in 30 mins"
        elif reminder == "today":
            data["time"] = "TODAY, " + date_object.strftime("%H:%M")
        else:
            data["time"] = date_object.strftime("%d %b %Y, %H:%M")   

        if reminder != "rem":
            data["prep"] = ""
    else:
        data["time"] = date_object.strftime("%d %b %Y, %H:%M")
        data["tag"] = "[CS Sem]"


    # Wrap abstract at 80 characters
    abs_list = text_wrapper.wrap(text=data["abstract"])
    data["abstract"] = "".join([line + "\n" for line in abs_list])

    email = EmailMessage()
    email['From'] = EMAIL_USERNAME
    email['To'] = receivers
    print(data["time"])
    email['SUBJECT'] = SUBJECT.format(**data)

    # If you want to get a copy too
    email['Bcc'] = EMAIL_USERNAME

    body = msg.format(**data)
    email.set_content(body)        

    return body, email

#Email function
def send_email(email):
    # Make the connection (standard smtplib)
    email_server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
    email_server.connect(EMAIL_SERVER, EMAIL_PORT)
    email_server.ehlo()
    email_server.starttls()
    email_server.ehlo()

    # Authenticate with XOAUTH2
    password = subprocess.check_output(EMAIL_PASSWD_CMD) \
                        .decode("ascii") \
                        .strip()
    sasl_string = f"user={EMAIL_USERNAME}\1auth=Bearer {password}\1\1"
    email_server.auth("XOAUTH2", lambda _=None: sasl_string)


    # Send!
    email_server.send_message(email)

    email_server.quit()




# Main function: 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument("yaml_file", help="the Yaml file containing the seminar description")
    parser.add_argument("--msg", help="print the message to stdout without sending it", action="store_true", default=False)
    parser.add_argument("--token", help="the file containing the authorisation token for connecting to Outlook365", default="./my_token")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--rem", help="the message is a generic reminder",
                        action="store_true", default=False)
    group.add_argument("--30min", help="the message is a 30 mins reminder",
                        action="store_true", default=False)
    group.add_argument("--today", help="the message is a reminder for today",
                        action="store_true", default=False)                        


    args = parser.parse_args();

    sem_desc = parse_yaml_file(args.desc_file)
    
    reminder = None
    if getattr(args,"30min"):
        reminder = "30"
    elif getattr(args, "today"):
        reminder = "today"
    elif getattr(args, "rem"):
        reminder = "rem"

    EMAIL_PASSWD_CMD.append(args.token)
    body, email = compose_message(sem_desc, reminder)

    if args.msg:
        print(email["To"] + "\n\n" + email["SUBJECT"] + "\n\n" + body)
    else:
        send_email(email)

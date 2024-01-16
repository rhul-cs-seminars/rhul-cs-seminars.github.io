
# How To Send Emails Using Python

Here is a quick guide to sending emails using Python. The trickiness is that you cannot use basic username/password authentication since two-factor authentication is used. You instead can use an XOAUTH2 token.

## Step 1: Getting Your Tokens

There are several existing scripts for getting tokens. This method works for me and was adapted from the [Arch Linux ISync Wiki Page][arch-isync].

You may need to install something like [cyrus-sasl-xoauth2][cyrus].

To get a token, use [oauth2token][oauth2token] or [mutt_oauth2.py][muttoauth2] ([README][muttoauth2readme]). I used the latter.

First download mutt_oauth2.py and edit these two variables for your favourite encryption/decryption commands (so you're not storing plaintext tokens on your filesystem):

    ENCRYPTION_PIPE = ['gpg', '--encrypt', '--recipient', 'me@mygpg']
    DECRYPTION_PIPE = ['gpg', '--decrypt']

Then add the `client_id` and `client_secret` for logging into Microsoft. You can "borrow" Thunderbird's ID/secret from the `kIssuers` section [here][thunderbird]. These details are already approved by the college. Using your own app ID would be better, but we are not allowed to create those.

    registrations = {
        'microsoft': {
            ...
            'client_id': '<id>',
            'client_secret': '<secret>',
        }
    }

Then pick a name for your tokens file (`/path/to/my.tokens`) and authenticate with

    $ python mutt_oauth2.py --authorize /path/to/my.tokens

Choose `localhostauthcode` for the authorization flow. The rest should be self explanatory.

## Step 2: Connect With Python

The code below will allow you to connect with Python. Notice that the password command is

    $ python mutt_oauth2.py /path/to/my.tokens

I.e. the password is obtained from the tokens you got in Step 1. The script has some useful constants (e.g. `EMAIL_USERNAME`) at the top. It then makes a standard SMTP connection using `smtplib`. Finally, it does the OAuth authentication.

    import smtplib
    import subprocess

    # Some useful constants
    EMAIL_SERVER = "smtp.office365.com"
    EMAIL_PORT = 587
    EMAIL_USERNAME = "first.last@rhul.ac.uk"
    EMAIL_PASSWD_CMD = [
        "/usr/bin/python",
        "/path/to/mutt_oauth2.py",
        "/path/to/my.tokens"
    ]

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

## Step 3: Send Emails

Now you have a server, your script can send emails as normal for `smtplib`.

    from email.message import EmailMessage

    ...

    email = EmailMessage()
    email['From'] = EMAIL_USERNAME
    email['To'] = "recipient@rhul.ac.uk"
    email['Subject'] = subject

    # If you want to get a copy too
    email['Bcc'] = EMAIL_USERNAME

    email.set_content("Hi, how are you?")

    # Send!
    email_server.send_message(email)


[cyrus]: https://github.com/moriyoshi/cyrus-sasl-xoauth2
[arch-isync]: https://wiki.archlinux.org/title/Isync
[oauth2token]: https://pypi.org/project/oauth2token/
[muttoauth2]: https://gitlab.com/muttmua/mutt/-/blob/master/contrib/mutt_oauth2.py
[muttoauth2readme]: https://gitlab.com/muttmua/mutt/-/blob/master/contrib/mutt_oauth2.py.README
[thunderbird]: https://hg.mozilla.org/comm-central/file/tip/mailnews/base/src/OAuth2Providers.jsm

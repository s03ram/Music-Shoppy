# Music-Shoppy
School projet using DB, Flask and Jinja
Not secured but fun using of Python and SQLite

### Contact section
File config.py not commited because it contains personal info.
If you want to try at home create this file with that code in :


    class Config :
    
        # config for gmail #

        MAIL_SERVER =  "smtp.gmail.com"
        MAIL_PORT =   587
        MAIL_USE_TLS = True  
        MAIL_USE_SSL =  False

        MAIL_USERNAME =  "your email adress"
        MAIL_PASSWORD =  "your application password" #follow the tutorial bellow to get yours
        MAIL_DEFAULT_SENDER =  ("your name", 'your email address (or whatever, it's just display)')

        MAIL_DEBUG = True
        MAIL_SUPPRESS_SEND = False

        MAIL_MAX_EMAILS =  None
        MAIL_ASCII_ATTACHMENTS = False

[Your app password tutorial for gmail.](https://support.google.com/mail/answer/185833?hl=en) (you need a 2-step verification account)

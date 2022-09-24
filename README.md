# playbox
Play music files in your Dropbox

# Setup

- Register your personal application through https://www.dropbox.com/developers/apps
- Create a file `config.ini` in your local directory. The content should look like this:
  - Use your own `dropbox_app_key` and `dropbox_app_secret`

```
[playbox]
path = /Music
dropbox_app_key = kkkkkkkkkkkkkkk
dropbox_app_secret = sssssssssssssss
```

# Running

```
python3 play.py
```

# Credit

This package contains a modified `playsound.py`, see the master version here: https://github.com/TaylorSMarks/playsound

import os
import re
import time


def extract_yt_term(command):
    if not command:
        return None
    command = str(command)
    match = re.search(r'(?:play|search|listen to)\s+(.*?)\s+(?:on|in)\s+youtube', command, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    clean = re.sub(r'\s+(?:on|in)\s+youtube', '', command, flags=re.IGNORECASE).strip()
    clean = re.sub(r'^(?:play|search|listen to)\s+', '', clean, flags=re.IGNORECASE).strip()
    return clean if clean else None


def remove_words(input_string, words_to_remove):
    if not input_string:
        return ""
    words = str(input_string).split()
    words_set = set(w.lower() for w in words_to_remove)
    filtered_words = [word for word in words if word.lower() not in words_set]
    return ' '.join(filtered_words)



# key events like receive call, stop call, go back
def keyEvent(key_code):
    command =  f'adb shell input keyevent {key_code}'
    os.system(command)
    time.sleep(1)

# Tap event used to tap anywhere on screen
def tapEvents(x, y):
    command =  f'adb shell input tap {x} {y}'
    os.system(command)
    time.sleep(1)

# Input Event is used to insert text in mobile
def adbInput(message):
    command =  f'adb shell input text "{message}"'
    os.system(command)
    time.sleep(1)

# to go complete back
def goback(key_code):
    for i in range(6):
        keyEvent(key_code)

# To replace space in string with %s for complete message send
def replace_spaces_with_percent_s(input_string):
    return input_string.replace(' ', '%s')
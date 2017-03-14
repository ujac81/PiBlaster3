# global.coffee -- global DOM definitions for javascript - loaded first in base.pug

window.PiRemote = {}


PiRemote.poll_started = false
PiRemote.polling = 0


PiRemote.playlist_poll_started = false
PiRemote.playlist_polling = false

PiRemote.last_status = ''
PiRemote.current_page = 'index'  # overwritten on load by script in index.pug
PiRemote.safe_page = 'index'  # safe last active page while blurring
PiRemote.last_browse = ''

PiRemote.last_pl_id = '-1'
PiRemote.last_pl_version = '-1'

PiRemote.dragging = false  # true while element is dragged in playlist


# Fade in status bar, set text and start fade out timer.
PiRemote.setStatusText = (text, fade=3000) ->
    $('.footer').fadeTo('fast', 1)
    $('#statusbar').html(text)

    window.setTimeout ( ->
        if text == $('#statusbar').html()
            # text was not changed --> do fade out
            $('.footer').fadeTo 'slow', 0
        return
        ), fade

    return

# Convert seconds to string like 3:02
PiRemote.secToMin = (secs) ->
    res = ''

    minutes = Math.floor(parseInt(secs)/60)
    seconds = parseInt(secs) % 60

    res += minutes + ':'
    if seconds < 10
        res += '0'
    res += seconds

    res

# Calculate font width for string element.
String::width = (font_size) ->
    fsize = font_size or 'medium'
    o = $('<div>' + this + '</div>').css(
        'position': 'absolute'
        'float': 'left'
        'white-space': 'nowrap'
        'visibility': 'hidden'
        'font-size': fsize).appendTo($('body'))
    w = o.width()
    o.remove()
    w

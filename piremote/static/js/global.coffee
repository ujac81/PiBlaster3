# global.coffee -- global DOM definitions for javascript - loaded first in base.pug

window.PiRemote = {}


PiRemote.poll_started = false
PiRemote.polling = false



PiRemote.secToMin = (secs) ->
    res = ''

    minutes = Math.floor(parseInt(secs)/60)
    seconds = parseInt(secs) % 60

    res += minutes + ':'
    if seconds < 10
        res += '0'
    res += seconds

    return res


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

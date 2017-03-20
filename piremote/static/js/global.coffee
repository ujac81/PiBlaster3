# global.coffee -- global DOM definitions for javascript - loaded first in base.pug

window.PiRemote = {}


PiRemote.poll_started = false
PiRemote.polling = 0


PiRemote.playlist_poll_started = false
PiRemote.playlist_polling = false

PiRemote.last_status = ''
PiRemote.current_page = 'index'  # overwritten on load by script in index.pug
PiRemote.current_sub_page = 'home'
PiRemote.safe_page = 'index'  # safe last active page while blurring
PiRemote.last_browse = ''

PiRemote.last_pl_id = '-1'
PiRemote.last_pl_version = '-1'
PiRemote.pl_edit_name = ''  # name of playlist in edit mode (='' if no edit)

PiRemote.last_search = ''
PiRemote.last_search_data = []

PiRemote.dragging = false  # true while element is dragged in playlist


# Fade in status bar, set text and start fade out timer.
PiRemote.setStatus = (text, error, fade) ->
    $('.footer').toggleClass('error', error)
    $('.footer').toggleClass('status', ! error)

    $('#statusbar').html(text)
    $('.footer').fadeTo('fast', 1)

    if 'text' == ''
        $('.footer').fadeTo('fast', 0)
        return

    window.setTimeout ( ->
        if text == $('#statusbar').html()
            # text was not changed --> do fade out
            $('.footer').fadeTo 'slow', 0
        return
        ), fade

    return


# Fade in status bar, set text and start fade out timer.
PiRemote.setStatusText = (text, fade=5000) ->
    PiRemote.setStatus text, false, fade
    return


# Fade in status red bar, set text and start fade out timer.
PiRemote.setErrorText = (text, fade=10000) ->
    PiRemote.setStatus text, true, fade
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

# Clear nav-bar button area.
PiRemote.clear_navbar_buttons = ->
    d3.select('#button-line').html('')
    return


# Add a button to .buttonline and install load_page callbacks.
PiRemote.add_navbar_button = (sub_page, text, glyphicon=false, sub_page_event=true) ->

    btn = d3.select('#button-line').append('button')
        .attr('class', 'btn btn-default navbar-btn')
        .attr('data-subpage', sub_page)
        .attr('id', 'navbutton_'+sub_page)
        .attr('type', 'button')

    if glyphicon
        btn.append('span').attr('class', 'glyphicon glyphicon-'+text)
    else
        btn.html(text)

    if sub_page_event
        # Load corresponding sub page on click.
        $('button#navbutton_'+sub_page).off 'click'
        $('button#navbutton_'+sub_page).on 'click', ->
            PiRemote.load_page PiRemote.current_page, $(this).data('subpage')
            return

    return


# Add a drop down menu to the menu bar.
PiRemote.add_navbar_drop_down = (title, id) ->

    line = d3.select('#button-line').append('button')
    d = line.append('div').attr('class', 'dropdown')
    but = d.append('button').attr('id', id).attr('type', 'button')
            .attr('data-toggle', 'dropdown').attr('aria-haspopup', 'true')
            .attr('aria-expanded', 'false')
    but.html(title)
    but.append('span').attr('class', 'caret')
    ul = d.append('ul').attr('class', 'dropdown-menu').attr('aria-labelledby', id)

    return ul

    line = d3.select('#button-line')
    ul_out = line.append('ul').attr('class', '')
    li_out = ul_out.append('li').attr('class', 'dropdown')
    a = li_out.append('a').attr('class', 'dropdown-toggle')
        .attr('href', '#').attr('data-toggle', 'dropdown')
    a.html(title)
    a.append('span').attr('class', 'caret')
    ul = li_out.append('ul').attr('class', 'dropdown-menu').attr('role', 'menu')
    ul


PiRemote.add_navbar_drop_down_item = (root, title) ->
    li = root.append('li')
    li.append('a').attr('href', '#').html(title)


# Raise a dialog box including confirm button.
# If confirm clicked, perform function.
PiRemote.confirm_dialog = (req) ->

    d3.select('#smallModalLabel').html(req.title)
    cont = d3.select('#smallModalMessage')
    cont.html('')

    need_pw = req.requirepw isnt `undefined` and req.requirepw
    if need_pw
        cont.append('p').attr('class', 'confirmpassword')
            .append('input').attr('type', 'text').attr('id', 'confirmpw').attr('placeholder', 'Confirm Password')


    cont.append('p').attr('id', 'confirminfo')

    cont.append('p').attr('class', 'confirmbutton')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary')
            .attr('id', 'confirmbutton').html('Confirm')

    $('button#confirmbutton').off 'click'
    $('button#confirmbutton').on 'click', ->
        if need_pw
            do_confirm = false
            PiRemote.do_ajax
                url: 'command'
                method: 'POST'
                data:
                    cmd: 'checkpw'
                    payload: [$('input#confirmpw').val()]
                success: (data) ->
                    if data.ok isnt `undefined` and data.ok == 1
                        req.confirmed()
                        $('#modalSmall').modal('hide')
                    else
                        d3.select('p#confirminfo').html('Wrong confirm password!')
                    return
        else
            req.confirmed()
            $('#modalSmall').modal('hide')
        return

    $('#modalSmall').modal('show')
    return

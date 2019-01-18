# global.coffee -- global DOM definitions for javascript - loaded first in base.pug

window.PiRemote = {}

PiRemote.init_variables = ->

    PiRemote.socket = null  # websocket connection

    PiRemote.use_short_polling = true  # True if websocket not working.

    PiRemote.poll_started = false  # true while polling in main view
    PiRemote.polling = 0  # current poll index in main view (>0, do not poll again)

    PiRemote.playlist_poll_started = false  # true while polling in playlist view
    PiRemote.playlist_polling = false  # true if active poll in playlist view
    
    PiRemote.playlist_on_get_status = false  # true while waiting for status
    PiRemote.playlist_on_get_changes = false  # true while waiting for pl changes

    PiRemote.last_index_data = null  # store received data in index view.

    PiRemote.last_status = ''  # store status bar text for fade-out
    # PiRemote.current_page set via index.pug
    PiRemote.current_sub_page = 'home'  # selected sub-view from buttons
    PiRemote.safe_page = 'index'  # safe last active page while blurring
    PiRemote.last_files = ''  # remember path in browse files view
    PiRemote.last_upload = ''  # remember path in upload view

    PiRemote.last_pl_id = '-1'  # id of last played song (move position indicator if changed)
    PiRemote.last_pl_version = '-1'  # version id of last transmitted playlist (req. update if changed)
    PiRemote.pl_edit_name = ''  # name of playlist in edit mode (='' if no edit)

    PiRemote.last_search = ''  # remember last search pattern
    PiRemote.last_search_data = []  # keep data of last search

    
    PiRemote.select_indexes = {'rating': 0, 'date': 1, 'genre': 2, 'artist': 3, 'album': 4, 'song' :5}
    PiRemote.select_classes = $.map(PiRemote.select_indexes, (v, k) -> k)
    PiRemote.select_class_names = ['Rating', 'Year', 'Genre', 'Artist', 'Album', 'Files']
    PiRemote.selected = {}  # per class array of selected items
    PiRemote.browse_current_page_index = 0  # current class index in browse by tag
    PiRemote.last_browse = null  # last received data in browse by tag
    PiRemote.should_browse = null  # set by info dialog if should browse genre/artist/album

    PiRemote.dragging = false  # true while element is dragged in playlist

    PiRemote.poll_interval = 1000  # poll interval in ms
    PiRemote.poll_interval_min = 500  # prevent polling if last poll time smaller than this
    
    PiRemote.update_instance_id = 0  # keep number of calls of update_time() to break recursion.
    PiRemote.pl_update_instance_id = 0  # same for playlist view
    
    PiRemote.action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    return


# Fade in status bar, set text and start fade out timer.
# NOTE: If you are using differing fade times, the fade-out might not work
# if you send differing messages in short time.
PiRemote.setStatus = (text, error, warning, fade) ->
    $('#footer').toggleClass('error', error)
    $('#footer').toggleClass('warning', not error and warning)
    $('#footer').toggleClass('status', not error and not warning)

    if text == ''
        $('#footer').fadeTo('fast', 0)
    else
        $('#statusbar').html(text)
        $('#footer').fadeTo('fast', 1)
        window.setTimeout ( ->
            if text == $('#statusbar').html()
                # text was not changed --> do fade out
                $('#footer').fadeTo 'slow', 0
            return
            ), fade

    return


# Fade in status bar, set text and start fade out timer.
PiRemote.setStatusText = (text, fade=5000) ->
    PiRemote.setStatus text, false, false, fade
    return


# Fade in status red bar, set text and start fade out timer.
PiRemote.setErrorText = (text, fade=5000) ->
    PiRemote.setStatus text, true, false, fade
    return


# Fade in status red bar, set text and start fade out timer.
PiRemote.setWarningText = (text, fade=5000) ->
    PiRemote.setStatus text, false, true, fade
    return


# Convert seconds to string like 3:02
PiRemote.secToMin = (secs) ->
    seconds = parseInt(secs) % 60
    res = '' + Math.floor(parseInt(secs)/60) + ':'
    res += '0' if seconds < 10
    res + seconds


# Convert seconds to string like 1:03:02
PiRemote.secToHMS = (secs) ->

    hours = Math.floor(parseInt(secs)/3600)
    minutes = Math.floor((parseInt(secs)-3600*hours)/60)
    seconds = parseInt(secs) % 60

    res = '' + hours + ":"
    res += "0" if minutes < 10
    res += minutes + ':'
    res += '0' if seconds < 10
    res += seconds
    

# Add thousand separators to number
PiRemote.separators_to_number = (x) ->
    x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")


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
        btn.on 'click', ->
            PiRemote.load_page PiRemote.current_page, $(this).data('subpage')
            return

    btn


# Raise a dialog box including confirm button.
# If confirm clicked, perform function.
PiRemote.confirm_dialog = (req) ->

    d3.select('#smallModalLabel').html(req.title)
    cont = d3.select('#smallModalMessage')
    cont.html('')

    need_pw = req.requirepw isnt `undefined` and req.requirepw and PiRemote.has_user_pw
    if need_pw
        cont.append('p').attr('class', 'confirmpassword')
            .append('input').attr('type', 'text').attr('id', 'confirmpw').attr('placeholder', 'Confirm Password')

    cont.append('p').attr('id', 'confirminfo')

    cont.append('p').attr('class', 'confirmbutton')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary')
            .attr('id', 'confirmbutton').html('Confirm')

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


# Raise a dialog box including confirm button.
# If confirm clicked, perform function.
PiRemote.error_message = (title, message) ->

    d3.select('#smallModalLabel').html(title)
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('p').html(message)
    $('#modalSmall').modal('show')
    return


# Display the search bar on top of the page.
PiRemote.show_search_header = (search_fun) ->
    $('body').addClass 'search'
    $('#searchbardiv').show()
    $('button#gosearch').off 'click'
    $('button#gosearch').on 'click', ->
        search_fun $('input#searchfield').val()
        return
    return
    
    
# Raise a dialog with stacked actions.
PiRemote.raise_selection_dialog = (title, text, items) ->
    d3.select('#smallModalLabel').html(title)
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('p').html(text)

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])
    $(document).off 'click', 'span.browse-action-file'
    $('#modalSmall').modal('show')
    return
    
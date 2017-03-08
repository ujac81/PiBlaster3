# ajax.coffee -- AJAX callbacks for all items.

# Installed via document ready function in application.coffee
# Loaded via base.pug

# Disable caching for AJAX -- required for safari browser
PiRemote.ajax_setup = ->

    $.ajaxSetup
        type: 'POST',
        headers:
            "cache-control": "no-cache"

    $.ajaxSetup
        type: 'GET',
        headers:
            "cache-control": "no-cache"

    return

# Perform AJAX post request
PiRemote.do_ajax = (req) ->
    data = req.data
    data.timeStamp = new Date().getTime()  # avoid caching
    data.csrfmiddlewaretoken = $('input[name=csrfmiddlewaretoken')[0].value
    $.ajax
        url: '/piremote/ajax/' + req.url + '/'
        data: data
        dataType: 'json'
        method: req.method
        success: (data) ->
            if data.status
                PiRemote.setStatusText data.status
            req.success(data)
            return
        error: (jqXHR) ->
            console.log 'AJAX ERROR'
            console.log jqXHR
            return

    return

# Perform insert or add actions on playlists.
# Invoked by dialogs in browse/search/....
PiRemote.pl_action = (cmd, plname, list, type) ->

    return if list.length == 0

    # TODO if type is dir, ask if recursive append/insert is ok

    PiRemote.do_ajax
        url: 'plaction'
        data:
            'cmd': cmd
            'plname': plname
            'list': list
        method: 'POST'
        success: (data) ->
            # setStatusText done by do_ajax
            return
    return
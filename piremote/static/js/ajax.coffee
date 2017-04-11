# ajax.coffee -- AJAX callbacks for all items.

# Installed via document ready function in application.coffee
# Loaded via base.pug

# Disable caching for AJAX -- required for safari browser
# TODO: safari still not working....
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
    data = req.data or {}
    data.timeStamp = new Date().getTime()  # avoid caching
    data.csrfmiddlewaretoken = $('input[name=csrfmiddlewaretoken')[0].value
    $.ajax
        url: '/piremote/ajax/' + req.url + '/'
        data: data
        dataType: 'json'
        method: req.method
        success: (data) ->
            PiRemote.setStatusText data.status_str if data.status_str
            PiRemote.setErrorText data.error_str if data.error_str
            req.success(data) if req.success
            return
        error: (jqXHR) ->
            console.log 'AJAX ERROR'
            console.log jqXHR
            PiRemote.setErrorText 'AJAX communication error! You might want to reload.'
            return

    return


# Perform insert or add actions on playlists.
# Invoked by dialogs in browse/search/....
PiRemote.pl_action = (cmd, plname, list, type='file', req={}) ->
    PiRemote.do_ajax
        url: 'plaction'
        data:
            'cmd': cmd
            'plname': plname
            'list': list
        method: 'POST'
        success: (data) ->
            req.success data if req.success
            return

    return


# Perform save/load actions on playlists.
# Invoked by dialogs in browse/search/....
PiRemote.pls_action = (cmd, plname, req={}) ->
    payload = []
    payload = req.payload if req.payload
    PiRemote.do_ajax
        url: 'plsaction'
        data:
            'cmd': cmd
            'plname': plname
            'payload': payload
        method: 'POST'
        success: (data) ->
            req.success(data) if req.success
            return

    return


# POST ajax/command like 'poweroff', 'update' or 'rescan'
PiRemote.do_command = (cmd, payload=[]) ->
    PiRemote.do_ajax
        url: 'command'
        method: 'POST'
        data:
            cmd: cmd
            payload: payload

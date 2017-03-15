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
            PiRemote.setStatusText data.status if data.status
            PiRemote.setErrorText data.error if data.error
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
PiRemote.pl_action = (cmd, plname, list, type='file') ->

    # TODO if type is dir, ask if recursive append/insert is ok

    PiRemote.do_ajax
        url: 'plaction'
        data:
            'cmd': cmd
            'plname': plname
            'list': list
        method: 'POST'

    return
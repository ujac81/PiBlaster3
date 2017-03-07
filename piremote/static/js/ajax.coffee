# ajax.coffee -- AJAX callbacks for all items.

# Installed via document ready function in application.coffee
# Loaded via base.pug


# Perform AJAX post request
PiRemote.do_ajax = (req) ->
    data = req.data
    data.csrfmiddlewaretoken = $('input[name=csrfmiddlewaretoken')[0].value
    $.ajax
        url: '/piremote/ajax/' + req.url + '/'
        data: data
        dataType: 'json'
        method: req.method
        success: (data) ->
            req.success(data)
            return
        error: (jqXHR) ->
            console.log 'AJAX ERROR'
            console.log jqXHR
            return

    return

# Perform insert or add actions on playlists.
# Invoked by dialogs in browse/search/....
PiRemote.pl_action = (cmd, plname, list) ->
    PiRemote.do_ajax
        url: 'plaction'
        data:
            'cmd': cmd
            'plname': plname
            'list': list
        method: 'POST'
        success: (data) ->
            # TODO post to status line
            # console.log data
            return
    return
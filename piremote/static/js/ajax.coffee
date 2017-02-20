# ajax.coffee -- AJAX callbacks for all items.

# Installed via document ready function in application.coffee
# Loaded via base.pug


# Perform AJAX post request
PiRemote.do_ajax_post = (req) ->
    data = req.data
    data.csrfmiddlewaretoken = $('input[name=csrfmiddlewaretoken')[0].value
    $.ajax
        url: '/piremote/ajax/' + req.url + '/'
        data: data
        dataType: 'json'
        method: 'POST'
        success: (data) ->
            req.success(data)
            return
        error: (jqXHR) ->
            console.log 'AJAX ERROR'
            console.log jqXHR
            return

    return

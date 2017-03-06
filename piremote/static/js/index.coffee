

# Install browse menu actions
PiRemote.install_index_actions = ->

    $(window).resize ->
        PiRemote.resize_index()
        return

    PiRemote.resize_index()
    PiRemote.set_position(0)

    PiRemote.start_status_poll()

    $('.idxbuttons span').off 'click'
    $('.idxbuttons span').on 'click', (event) ->
        PiRemote.do_ajax_post
            url: 'cmd'
            data:
                'cmd': $(this).data('action')
            success: (data) ->
                console.log data
                if data.success
                    PiRemote.update_status data
                return

        return

    return


PiRemote.start_status_poll = ->
    if PiRemote.poll_started
        return
    PiRemote.poll_started = true
    PiRemote.do_status_poll()
    return

PiRemote.do_status_poll = ->
    if PiRemote.polling
        return

    data = {}
    data.csrfmiddlewaretoken = $('input[name=csrfmiddlewaretoken')[0].value
    $.ajax
        url: '/piremote/ajax/status/'
        dataType: 'json'
        data: data
        method: 'GET'
        success: (data) ->
            PiRemote.update_status data
            PiRemote.polling = true
            window.setTimeout ( ->
                PiRemote.polling = false
                PiRemote.do_status_poll()
            ), 1000
            return
        error: (jqXHR) ->
            console.log 'AJAX ERROR'
            console.log jqXHR
            return

    return


PiRemote.resize_index = ->
    $("#idxpos").width($("#idxpos").parent().outerWidth()-40)
    return

PiRemote.set_position = (pct) ->
    pct_set = 100-pct
    pct_set = 0 if pct_set < 0
    pct_set = 100 if pct_set > 100

    $('#idxposfill').css('right', pct_set+'%')


    return


PiRemote.update_status = (data) ->

    if (data.title)
        $('h2#idxtitle').html(data.title)
    if (data.artist)
        $('h3#idxartist').html(data.artist)

    if (data.album)
        album = data.album
        if (data.date) and (data.date != '')
            album += ' ('+data.date+')'
        $('h4#idxalbum').html(album)

    if (data.time) and (data.elapsed)
        pct = 100.0 * parseFloat(data.elapsed) / parseFloat(data.time)
        PiRemote.set_position pct

        $('h5#idxtime').html(PiRemote.secToMin(data.elapsed)+' / '+PiRemote.secToMin(data.time))

    d3.select('span#playpause').classed('glyphicon-play', data.state != 'play')
    d3.select('span#playpause').classed('glyphicon-pause', data.state == 'play')

    d3.select('span#random').classed('enabled', data.random == '1')
    d3.select('span#random').classed('disabled', data.random != '1')

    d3.select('span#repeat').classed('enabled', data.repeat == '1')
    d3.select('span#repeat').classed('disabled', data.repeat != '1')


    return

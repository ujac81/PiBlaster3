

PiRemote.load_index_page = ->

    root = d3.select('.piremote-content')

    idxshow = root.append('div').attr('id', 'idxshow')
    idxshow.append('h2').attr('id', 'idxtitle')
    idxshow.append('h3').attr('id', 'idxartist')
    idxshow.append('h4').attr('id', 'idxalbum')

    idxpos = root.append('div').attr('id', 'idxpos')
    idxpos.append('div').attr('id', 'idxposfill')

    idxtime = root.append('div').attr('id', 'idxtime')
    idxtime.append('h5').attr('id', 'idxtime')

    row1 = root.append('div').attr('class', 'idxbuttons')
    row1.append('span').attr('data-action', 'back')
                       .attr('class', 'glyphicon glyphicon-step-backward')
    row1.append('span').attr('data-action', 'playpause').attr('id', 'playpause')
                       .attr('class', 'glyphicon glyphicon-play')
    row1.append('span').attr('data-action', 'stop')
                       .attr('class', 'glyphicon glyphicon-stop')
    row1.append('span').attr('data-action', 'next')
                       .attr('class', 'glyphicon glyphicon-step-forward')

    row2 = root.append('div').attr('class', 'idxbuttons')
    row2.append('span').attr('data-action', 'decvol')
                       .attr('class', 'glyphicon glyphicon-volume-down')
    row2.append('span').attr('data-action', 'mute')
                       .attr('class', 'glyphicon glyphicon-volume-off')
    row2.append('span').attr('data-action', 'incvol')
                       .attr('class', 'glyphicon glyphicon-volume-up')

    row3 = root.append('div').attr('class', 'idxbuttons')
    row3.append('span').attr('data-action', 'random')
                       .attr('class', 'glyphicon glyphicon-random')
    row3.append('span').attr('data-action', 'repeat')
                       .attr('class', 'glyphicon glyphicon-repeat')

    PiRemote.poll_started = false
    PiRemote.install_index_actions()
    return


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
        PiRemote.do_ajax
            url: 'cmd'
            method: 'POST'
            data:
                'cmd': $(this).data('action')
            success: (data) ->
                if data.success
                    PiRemote.update_status data
                return

        return

    return


PiRemote.start_status_poll = ->
    return if PiRemote.poll_started
    PiRemote.poll_started = true
    PiRemote.do_status_poll()
    return

PiRemote.do_status_poll = ->
    return if PiRemote.polling
    return if PiRemote.current_page != 'index'

    PiRemote.do_ajax
            url: 'status'
            method: 'GET'
            data: {}
            success: (data) ->
                PiRemote.update_status data
                PiRemote.polling = true
                window.setTimeout ( ->
                    PiRemote.polling = false
                    PiRemote.do_status_poll()
                ), 1000
                return
    return


PiRemote.resize_index = ->
    return if PiRemote.current_page != 'index'
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

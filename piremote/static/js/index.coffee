# index.coffee -- build "Play" page and install actions.

# Build main view.
# Loaded via PiRemote.load_page('index') every time 'Play' is selected in menu
# Start status short polling.
# Install actions.
PiRemote.load_index_page = ->

    # Insert buttons
    PiRemote.add_navbar_button 'home', 'home', true
    PiRemote.add_navbar_button 'index_volume', 'volume-up', true
    PiRemote.add_navbar_button 'index_equalizer', 'equalizer', true

    # build main content for current sub page.
    if PiRemote.current_sub_page == 'index_volume'
        PiRemote.index_fetch_mixer 'volume'
    else if PiRemote.current_sub_page == 'index_equalizer'
        PiRemote.index_fetch_mixer 'equalizer'
    else
        PiRemote.index_build_main()

    PiRemote.index_refresh_status()
    return


# index/home page -- show song information and buttons
PiRemote.index_build_main = ->

    root = d3.select('.piremote-content')

    # TITLE, ARTIST, ALBUM
    idxshow = root.append('div').attr('id', 'idxshow')
    idxshow.append('h2').attr('id', 'idxtitle')
    idxshow.append('h3').attr('id', 'idxartist')
    idxshow.append('h4').attr('id', 'idxalbum')

    idxrate = root.append('div').attr('class', 'idxrate')
    idxrate.append('span').attr('class', 'norate')
    for i in [1..5]
        idxrate.append('span')
            .attr('class', 'ratespan glyphicon glyphicon-star-empty')
            .attr('data-idx', i)
    idxrate.append('span').attr('class', 'norate')
    PiRemote.last_rating = 0

    # POSITION INDICATOR
    idxpos = root.append('div').attr('id', 'idxpos')
    idxpos.append('div').attr('id', 'idxposfill')

    # TIME
    idxtime = root.append('div').attr('id', 'idxtime')
    idxtime.append('h5').attr('id', 'idxtime')

    # BUTTON ROW 1
    row1 = root.append('div').attr('class', 'idxbuttons')
    row1.append('span').attr('data-action', 'back')
                       .attr('class', 'glyphicon glyphicon-step-backward')
    row1.append('span').attr('data-action', 'playpause').attr('id', 'playpause')
                       .attr('class', 'glyphicon glyphicon-play')
    row1.append('span').attr('data-action', 'stop')
                       .attr('class', 'glyphicon glyphicon-stop')
    row1.append('span').attr('data-action', 'next')
                       .attr('class', 'glyphicon glyphicon-step-forward')

    # BUTTON ROW 2
    row2 = root.append('div').attr('class', 'idxbuttons')
    row2.append('span').attr('data-action', 'decvol')
                       .attr('class', 'glyphicon glyphicon-volume-down')
    row2.append('span').attr('data-action', 'mute')
                       .attr('class', 'glyphicon glyphicon-volume-off')
    row2.append('span').attr('data-action', 'incvol')
                       .attr('class', 'glyphicon glyphicon-volume-up')

    # BUTTON ROW 3
    row3 = root.append('div').attr('class', 'idxbuttons')
    row3.append('span').attr('data-action', 'random').attr('id', 'random')
                       .attr('class', 'glyphicon glyphicon-random')
    row3.append('span').attr('data-action', 'repeat').attr('id', 'repeat')
                       .attr('class', 'glyphicon glyphicon-repeat')

    
    # Resize position indicator on window resize
    $(window).resize ->
        PiRemote.resize_index()
        return

    # Position action
    $('#idxpos').on 'click', (event) ->
        x_off = $(this).offset().left
        pct = (event.pageX-x_off)/$(this).width()*100.0
        PiRemote.do_ajax
            url: 'cmd'
            method: 'POST'
            data:
                'cmd': 'seekcur '+pct
            success: (data) ->
                if data.success
                    PiRemote.update_status data
                return

    # Button actions
    $('.idxbuttons span').on 'click', ->
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

    # rate song
    $('div.idxrate span').on 'click', ->
        if PiRemote.last_index_data isnt null and PiRemote.last_index_data.file and PiRemote.last_index_data.file isnt ''
            rate = 0
            if $(this).hasClass('ratespan')
                rate = $(this).data('idx')
            PiRemote.do_ajax
                url: 'rate'
                method: 'POST'
                data:
                    filename: PiRemote.last_index_data.file
                    rating: rate
                    success: (data) ->
                        PiRemote.index_refresh_status()
                        return
        return

    # click in title raises info dialog
    $('#idxshow').on 'click', ->
        if PiRemote.last_index_data isnt null and PiRemote.last_index_data.file and PiRemote.last_index_data.file isnt ''
            PiRemote.search_raise_info_dialog PiRemote.last_index_data.file
        return
    
    PiRemote.poll_started = false
    PiRemote.polling = false
    PiRemote.resize_index()
    PiRemote.set_position(0)
    
    if PiRemote.use_short_polling and not PiRemote.poll_started
        PiRemote.poll_started = true
        PiRemote.do_status_poll()
    return


# AJAX GET for mixer status and build sliders from result.
PiRemote.index_fetch_mixer = (slider_class) ->
    PiRemote.do_ajax
        url: 'mixer'
        method: 'GET'
        data:
            'class': slider_class
        success: (data) ->
            if data.ok
                PiRemote.index_build_sliders data.data, slider_class
            return
    return


# Build sliders from AJAX GET mixer.
# Install AJAX POST mixerset callbacks for each slider.
PiRemote.index_build_sliders = (data, slider_class) ->

    names = []
    values = []
    for item in data
        names.push item.name
        values.push(parseInt(item.value))


    root = d3.select('.piremote-content')
    p = root.append('p').attr('class', 'sliders')
    table = p.append('table').attr('class', 'table sliders')

    tr1 = table.append('tr').attr('class', 'trslider1')
    tr2 = table.append('tr').attr('class', 'trslider2')
    tr3 = table.append('tr').attr('class', 'trslider3')

    for name in names
        tr1.append('td').attr('class', 'sliderhead').html(name)

    for val, i in values
        tr2.append('td').attr('class', 'slidermain')
            .append('div').attr('class', 'slider').attr('data-id', i)
            .append('div').attr('class', 'sliderfill').attr('data-id', i)
        tr3.append('td').attr('class', 'slidernum').attr('data-id', i).html(val)
        $('.sliderfill[data-id='+i+']').css('top', (100.0-val)+'%')

    PiRemote.resize_sliders()

    $('.slider').on 'click', (event) ->
        return if PiRemote.on_slider_change
        PiRemote.on_slider_change = true
        y_off = $(this).offset().top
        pct_inv = ((event.pageY-y_off)/$(this).height()*100.0)
        pct = parseInt(100.0-pct_inv)
        id = parseInt($(this).data('id'))

        PiRemote.do_ajax
            url: 'mixerset'
            method: 'POST'
            data:
                class: slider_class
                channel: id
                value: pct
            success: (data) ->
                $('.slidernum[data-id='+data.chan_id+']').html(data.value)
                $('.sliderfill[data-id='+data.chan_id+']').css('top', (100.0-data.value)+'%')
                PiRemote.on_slider_change = false
                return
        return

    # Resize sliders
    $(window).resize ->
        PiRemote.resize_sliders()
        return
    return


# Short polling loop.
# Recursively receive new status.
# Callback on AJAX receive is update_status()
PiRemote.do_status_poll = ->
    # Do not enter loop if not on index page or polling invoked twice (should not happen)
    return unless PiRemote.use_short_polling
    return if PiRemote.polling
    return if PiRemote.current_page != 'index'

    # Remember last poll send time
    PiRemote.last_poll_time = new Date().getTime()

    PiRemote.do_ajax
            url: 'status'
            method: 'GET'
            data: {}
            success: (data) ->
                PiRemote.update_status data  #  <-- poll callback
                PiRemote.polling = true
                window.setTimeout ( ->
                    PiRemote.polling = false
                    now = new Date().getTime()
                    if (now-PiRemote.last_poll_time > PiRemote.poll_interval_min)
                        # Assume two polling loops if time is too short.
                        PiRemote.do_status_poll()
                ), PiRemote.poll_interval  # <-- short polling interval
                return
    return


# Callback for page resize event.
# Resize position slider.
PiRemote.resize_index = ->
    return if PiRemote.current_page != 'index'
    $("#idxpos").width($("#idxpos").parent().outerWidth()-40)
    return


# Callback for page resize event.
# Resize position slider.
PiRemote.resize_sliders = ->
    return if PiRemote.current_sub_page not in ['index_volume', 'index_equalizer']
    w = $('.slidernum').width()
    h = ($(window).height() - $('#footer').height() - $('#navbar').height() - $('.trslider1').height() - $('.trslider3').height()) - 20
    left = (w-20)*0.5+10
    left = 0 if left < 0
    d3.selectAll('td.slidermain').style("padding-left", left+"px")
    d3.selectAll('td.slidermain > .slider').style("height", h+"px")
    return


# Set position fill in position slider (percentage value required).
PiRemote.set_position = (pct) ->
    pct_set = 100-pct
    pct_set = 0 if pct_set < 0
    pct_set = 100 if pct_set > 100

    $('#idxposfill').css('right', pct_set+'%')
    return


# Callback for AJAX status receive.
# Called by short polling and button events.
# Set content (album, artist, ...) of all elements, set position slider and update buttons.
PiRemote.update_status = (data) ->

    PiRemote.last_index_data = data

    # TITLE, ARTIST, ALBUM
    $('h2#idxtitle').html(if (data.title) then data.title else '&nbsp;')
    $('h3#idxartist').html(if (data.artist) then data.artist else 'Unknown Artist')
    album = '&nbsp;'
    if (data.album)
        album = data.album
        if (data.date) and (data.date != '')
            album += ' ('+data.date+')'
    $('h4#idxalbum').html(album)

    unless PiRemote.last_rating == data.rating
        PiRemote.index_set_rating 'div.idxrate', data.rating
        PiRemote.last_rating = data.rating

    # TIME
    PiRemote.index_set_time data.elapsed, data.time

    # BUTTONS
    d3.select('span#playpause').classed('glyphicon-play', data.state != 'play')
    d3.select('span#playpause').classed('glyphicon-pause', data.state == 'play')

    d3.select('span#random').classed('enabled', data.random == '1')
    d3.select('span#random').classed('disabled', data.random != '1')

    d3.select('span#repeat').classed('enabled', data.repeat == '1')
    d3.select('span#repeat').classed('disabled', data.repeat != '1')

    PiRemote.last_index_data['last_update'] = new Date().getTime()
    PiRemote.update_instance_id += 1
    PiRemote.index_update_time()

    return


# Update time information on time bar and time index text.
PiRemote.index_set_time = (elapsed, time) ->
    if (time) and (elapsed)
        pct = 100.0 * parseFloat(elapsed) / parseFloat(time)
        PiRemote.set_position pct
        $('h5#idxtime').html(PiRemote.secToMin(elapsed)+' / '+PiRemote.secToMin(time))
    else
        PiRemote.set_position 0
    return


# Internal infinite time loop to progress time bar in websocket mode.
# In websocket mode status is only updated if song changed or play/pause pressed or else.
PiRemote.index_update_time = ->
    return if PiRemote.use_short_polling
    return if PiRemote.last_index_data['state'] != 'play'
    my_instance_id = PiRemote.update_instance_id
    window.setTimeout ( ->
        return if PiRemote.last_index_data['state'] != 'play'
        t_new = new Date().getTime()
        delta = t_new - PiRemote.last_index_data['last_update']
        PiRemote.last_index_data['last_update'] = t_new
        PiRemote.last_index_data['elapsed'] = parseFloat(PiRemote.last_index_data['elapsed'])+delta/1000
        PiRemote.index_set_time PiRemote.last_index_data['elapsed'], PiRemote.last_index_data['time']
        if my_instance_id == PiRemote.update_instance_id
            PiRemote.index_update_time()
        return
    ), 1000
    return


# Force AJAX GET of current status.
# Required in websocket mode if current data is outdated.
PiRemote.index_refresh_status = ->
    PiRemote.do_ajax
        url: 'status'
        method: 'GET'
        data: {}
        success: (data) ->
            PiRemote.update_status data
            return
    return


# Toggle star/star-empty classes for stars depending on rating.
PiRemote.index_set_rating = (parent, rating) ->
    for i in [1..5]
        star = $(parent+' > span.ratespan[data-idx='+i+']')
        star.toggleClass('glyphicon-star-empty', i > rating)
        star.toggleClass('glyphicon-star', i <= rating)
    return

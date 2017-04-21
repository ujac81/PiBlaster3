# settings.coffee -- build settings page

# AJAX receive settings from SQL and invoke build page callback.
PiRemote.load_settings_page = ->

    PiRemote.do_ajax
        url: 'settings'
        data:
            'payload': ['party_mode', 'party_remain', 'party_low_water', 'party_high_water']
        method: 'GET'
        success: (data) ->
            PiRemote.settings_build_page data
            return

    return


# Callback for AJAX GET /piremote/ajax/settings --> build settings page.
PiRemote.settings_build_page = (settings) ->

    root = d3.select('.piremote-content')

    p = root.append('p').attr('class', 'settingsgroup')
    p.append('h4').attr('class','settingshead').html('Party Mode')

    PiRemote.settings_add_check_box p, 'party_mode', settings.party_mode, 'Party mode'
    PiRemote.settings_add_spin_box p, 'party_remain', settings.party_remain, 'Keep at least this many songs in playlist', 10, 1000
    PiRemote.settings_add_spin_box p, 'party_low_water', settings.party_low_water, 'Append if this many songs left', 10, 1000
    PiRemote.settings_add_spin_box p, 'party_high_water', settings.party_high_water, 'Append this many songs', 10, 1000

    p = root.append('p').attr('class', 'settingsgroup')
    p.append('h4').attr('class','settingshead').html('Power')
    PiRemote.settings_add_button p, 'poweroff', 'Power off', 'Off'

    $('button#button_poweroff').off 'click'
    $('button#button_poweroff').on 'click', ->
        PiRemote.confirm_dialog
            title: 'Power off?'
            requirepw: 1
            confirmed: ->
                PiRemote.do_command 'poweroff'

    p = root.append('p').attr('class', 'settingsgroup')
    p.append('h4').attr('class','settingshead').html('Database')
    PiRemote.settings_add_button p, 'update', 'Update', 'Update'

    $('button#button_update').off 'click'
    $('button#button_update').on 'click', ->
        PiRemote.confirm_dialog
            title: 'Update DB?'
            confirmed: ->
                PiRemote.do_command 'update'

    p = root.append('p').attr('class', 'settingsgroup').attr('id', 'stats')
    p.append('h4').attr('class','settingshead').html('Statistics')

    PiRemote.do_ajax
        url: 'stats'
        method: 'GET'
        success: (data) ->
            p = d3.select('p#stats')
            stats = data.stats
            PiRemote.settings_add_text p, 'Total number of songs', stats.songs
            PiRemote.settings_add_text p, 'Total artists', stats.artists
            PiRemote.settings_add_text p, 'Total albums', stats.albums
            PiRemote.settings_add_text p, 'Total play time', PiRemote.secToHMS(stats.db_playtime)
            if stats.free
                free = Math.round(parseInt(stats.free)/1024/1024)
                PiRemote.settings_add_text p, 'Free space in upload', ''+free+' MB'
            return

    p = root.append('p').attr('class', 'settingsgroup').attr('id', 'ratings')
    p.append('h4').attr('class','settingshead').html('Ratings')
    PiRemote.settings_add_link p, 'Download ratings', '/piremote/download/ratings'

    return


# Add checkbox to settings view.
PiRemote.settings_add_check_box = (root, key, value, text) ->

    d = root.append('div').attr('class', 'setting')

    d.append('div').attr('class', 'slabel').html(text)
    d.append('div').attr('class', 'svalue')
        .append('input').attr('type', 'checkbox').attr('id', 'check_'+key).attr('value', key)

    $('input#check_'+key)[0].checked = if value is '0' then false else true

    $('input#check_'+key).off 'click'
    $('input#check_'+key).on 'click', (event) ->
        val = if this.checked then '1' else '0'
        PiRemote.settings_set key, val
        return

    return


# Add spin box to settings view.
PiRemote.settings_add_spin_box = (root, key, value, text, min, max) ->

    d = root.append('div').attr('class', 'setting')

    d.append('div').attr('class', 'slabel').html(text)
    d.append('div').attr('class', 'svalue')
        .append('input')
        .attr('class', 'spin')
        .attr('type', 'number').attr('min', min).attr('max', max).attr('value', value)
        .attr('id', 'spin_'+key)

    $("input#spin_"+key).bind 'keyup input change', ->
        val = +this.value
        min = +this.min
        max = +this.max
        val = min if val < min
        val = max if val > max
        PiRemote.settings_set key, val
        return
    return


# Add button to settings view.
PiRemote.settings_add_button = (root, key, text, button_text) ->

    d = root.append('div').attr('class', 'setting')

    d.append('div').attr('class', 'slabel').html(text)
    d.append('div').attr('class', 'svalue')
        .append('button')
        .attr('class', 'btn btn-default')
        .attr('id', 'button_'+key)
        .html(button_text)

    return


# Add download link
PiRemote.settings_add_link = (root, text, link) ->

    d = root.append('div').attr('class', 'setting')

    d.append('div').attr('class', 'slabel').html(text)
    d.append('div').attr('class', 'svalue')
        .append('a')
        .attr('href', link)
        .append('button')
        .attr('class', 'btn btn-default')
        .html('Download')

    return


# Add text label to settings view.
PiRemote.settings_add_text = (root, text, value) ->
    d = root.append('div').attr('class', 'setting')
    d.append('div').attr('class', 'slabel').html(text)
    d.append('div').attr('class', 'svalue').html(value)
    return


# Setter callback.
PiRemote.settings_set = (key, value) ->
    PiRemote.do_ajax
        url: 'set'
        data:
            key: key
            value: value
        method: 'POST'

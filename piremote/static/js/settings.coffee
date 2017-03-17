# settings.coffee -- build settings page


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


PiRemote.settings_build_page = (settings) ->

    root = d3.select('.piremote-content')

    p = root.append('p').attr('class', 'settingsgroup')
    p.append('h4').attr('class','settingshead').html('Party Mode')

    PiRemote.settings_add_check_box p, 'party_mode', settings.party_mode, 'Party mode'
    PiRemote.settings_add_spin_box p, 'party_remain', settings.party_remain, 'Keep at least this many songs in playlist', 10, 1000
    PiRemote.settings_add_spin_box p, 'party_low_water', settings.party_low_water, 'Append if this many songs left', 10, 1000
    PiRemote.settings_add_spin_box p, 'party_high_water', settings.party_high_water, 'Append this many songs', 10, 1000

    p = root.append('p').attr('class', 'settingsgroup')

    return


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

PiRemote.settings_set = (key, value) ->
    PiRemote.do_ajax
        url: 'set'
        data:
            key: key
            value: value
        method: 'POST'

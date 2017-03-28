# browse.coffee -- install callbacks for browse view

# Build browse page.
# Loaded via PiRemote.load_page('browse') every time 'Browse' is selected in menu
PiRemote.load_browse_page = ->

    # Insert buttons
    PiRemote.add_navbar_button 'browse_left', 'chevron-left', true, false
    PiRemote.add_navbar_button 'browse_right', 'chevron-right', true, false


    $('button#navbutton_browse_left').off 'click'
    $('button#navbutton_browse_left').on 'click', ->
        if PiRemote.browse_current_page_index > 0
            PiRemote.browse_current_page_index -= 1
        PiRemote.do_browse PiRemote.select_classes[PiRemote.browse_current_page_index]
        return

    $('button#navbutton_browse_right').off 'click'
    $('button#navbutton_browse_right').on 'click', ->
        if PiRemote.browse_current_page_index < 4
            PiRemote.browse_current_page_index += 1
        PiRemote.do_browse PiRemote.select_classes[PiRemote.browse_current_page_index]
        return


    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'browse-list')
    bl.append('h3').attr('id', 'browse-head')
    tb = bl.append('table').attr('id', 'tbbrowse').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'browse')

    $('#addsign').show()
    $('#addsign').off 'click'
    $('#addsign').on 'click', ->
        PiRemote.browse_raise_add_dialog()
        return

    if PiRemote.last_browse isnt null
        PiRemote.build_browse PiRemote.last_browse
    else
        PiRemote.do_browse 'date'
    return

# AJAX GET of mpd.list(....)
PiRemote.do_browse = (what) ->

    selected_lists = {}
    for mode in PiRemote.select_classes
        selected_lists[mode] = []
        for key, val of PiRemote.selected[mode]
            if val
                selected_lists[mode].push key

    # Prevent browsing of all files (too much or browser too slow)
    if what == 'song'
        all_all = 0
        for key, val of selected_lists
            if val.length == 1 and val[0] == 'All' and key != 'song'
                all_all += 1
        if all_all >= 4
            PiRemote.error_message 'Error', "Browsing of all files prevented for performance reasons. Please select at least one category not equal to 'all'."
            # Stay at album view
            PiRemote.browse_current_page_index = 3
            return

    PiRemote.do_ajax
        url: 'list'
        method: 'GET'
        data:
            what: what
            dates: selected_lists['date']
            genres: selected_lists['genre']
            artists: selected_lists['artist']
            albums: selected_lists['album']
        success: (data) ->
            PiRemote.last_browse = data
            PiRemote.build_browse data
            return

    return

# Build table result from
PiRemote.build_browse = (data) ->

    mode = data.what
    title = PiRemote.select_class_names[PiRemote.browse_current_page_index]
    d3.select('h3#browse-head').html('Browse by '+title)

    # clean table
    tbody = d3.select('tbody#browse')
    tbody.selectAll('tr').remove()

    if mode == 'song'
        PiRemote.build_browse_song data
        return


    # ... vertical dots for each element
    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    if mode == 'date'
        browse_data = ['All', '0-1970', '1971-1980', '1981-1990', '1991-2000', '2001-2010', '2010-today'].concat(data.browse)
    else
        browse_data = ['All'].concat(data.browse)

    # Append dirs
    tbody.selectAll('tr')
        .data(browse_data, (d) -> d).enter()
        .append('tr')
        .attr('class', 'selectable')
        .attr('data-index', (d, i) -> i)
        .attr('data-item', (d) -> d)
        .classed('selected', (d)->PiRemote.selected[mode][d])
        .classed('all', (d, i)->i == 0 and d == 'All')
        .selectAll('td')
        .data((d, i) -> [i, d, action_span]).enter()
        .append('td')
            .attr('class', (d, i)-> 'browse-td'+i)
            .classed('browse-selectable', (d, i) -> i != 2)
            .html((d) -> d)

    # Set selection for mode to all if nothing selected
    sel = d3.selectAll('tr.selectable.selected').data()
    if sel.length == 0
        d3.selectAll('tr.selectable[data-index="0"]').classed('selected', 1)
        PiRemote.selected[mode] = {'All': true}

    # single-click on selectable items toggles select
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').off 'click'
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').on 'click', (event) ->
        tr = $(this).parent()
        if tr.data('index') == 0 and tr.data('item') == 'All'
            # deselect all if All clicked
            d3.selectAll('tr.selectable').classed('selected', 0)
            d3.selectAll('tr.selectable[data-index="0"]').classed('selected', 1)
            PiRemote.selected[mode] = {'All': true}
            return


        # any other item clicked -- check if deselect all or select all if selection empty

        tr.toggleClass 'selected'
        PiRemote.selected[mode][tr.data('item')] = tr.hasClass 'selected'

        sel = d3.selectAll('tr.selectable.selected').data()
        if sel.length == 0
            # select all
            d3.selectAll('tr.selectable[data-index="0"]').classed('selected', 1)
            PiRemote.selected[mode] = {'All': true}
        else
            # deselect 'All'
            d3.selectAll('tr.selectable[data-index="0"]').classed('selected', 0)
            PiRemote.selected[mode]['All'] = false
        return
    return


PiRemote.build_browse_song = (data) ->

    # ... vertical dots for each element
    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    # Append dirs
    d3.select('tbody#browse').selectAll('tr')
        .data(data.browse, (d) -> d).enter()
        .append('tr')
        .attr('class', 'selectable')
        .attr('data-index', (d, i) -> i)
        .selectAll('td')
        .data((d, i) -> [i+1, d[1], action_span]).enter()
        .append('td')
            .attr('class', (d, i)-> 'browse-td'+i)
            .classed('browse-selectable', (d, i) -> i != 2)
            .html((d) -> d)

    # single-click on selectable items toggles select
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').off 'click'
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').on 'click', (event) ->
        $(this).parent().toggleClass 'selected'
        return

    if data.truncated > 0
        PiRemote.setErrorText ''+data.truncated+' search results truncated, displaying first '+data.browse.length+' results.'

    return

# Callback for press on '+' sign.
# Raise selection actions dialog.
PiRemote.browse_raise_add_dialog = ->
    d3.select('#smallModalLabel').html('Browse Actions')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['select-all', 'Select all'],
        ['invert', 'Invert Selection'],
        ['seed', 'Random add Songs'],
        ['seed-other', 'Random add Songs to another Playlist'],
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        mode = PiRemote.select_classes[PiRemote.browse_current_page_index]
        PiRemote.do_browse_action mode, $(this).data('action')
        return

    # Raise dialog.
    $('#modalSmall').modal('show')
    return

PiRemote.do_browse_action = (mode, action) ->

    title = PiRemote.select_class_names[PiRemote.browse_current_page_index]

    if action == 'select-all'
        if d3.selectAll('tr.all').size() == 1
            d3.selectAll('tr.selectable').classed('selected', 0)
            d3.selectAll('tr.selectable[data-index="0"]').classed('selected', 1)
            PiRemote.selected[mode] = {'All': true}
        else
            d3.selectAll('tr.selectable').classed('selected', 1)
            sel = d3.selectAll('tr.selectable.selected').data()
            PiRemote.selected[mode] = {}
            for item in sel
                PiRemote.selected[mode][item] = true
        $('#modalSmall').modal('hide')
    else if action == 'invert'
        d3.selectAll('tr.selectable').classed('selected', ()-> ! d3.select(this).classed('selected'))
        sel = d3.selectAll('tr.selectable.selected').data()
        if sel.length == 0
            d3.selectAll('tr.selectable[data-index="0"]').classed('selected', 1)
            PiRemote.selected[mode] = {'All': true}
        else
            PiRemote.selected[mode] = {'All': false}
            for item in sel
                PiRemote.selected[mode][item] = true
        $('#modalSmall').modal('hide')
    else if action == 'seed'
        items = d3.selectAll('tr.selected').data()
        PiRemote.pl_edit_name = ''
        PiRemote.browse_raise_seed_dialog mode, '', 'Seed by '+title, items
    else if action == 'seed-other'
        items = d3.selectAll('tr.selected').data()
        PiRemote.pl_action_on_playlists
            title: 'Random Add to Playlist'
            success: (data) ->
                PiRemote.pl_edit_name = data
                PiRemote.browse_raise_seed_dialog mode, data, 'Seed by '+title, items
                return

    return


PiRemote.browse_raise_seed_dialog = (mode, plname, title, items) ->

    d3.select('#smallModalLabel').html(title)
    cont = d3.select('#smallModalMessage')
    cont.html('')

    cont.append('p').html('Set number of random items to add')

    cont.append('p').append('input')
        .attr('type', 'number').attr('min', '10').attr('max', '1000').attr('value', '20')
        .attr('id', 'seedspin').attr('class', 'spin')

    cont.append('p').attr('class', 'confirmbutton')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary')
            .attr('id', 'confirmbutton').html('Seed')

    $('button#confirmbutton').off 'click'
    $('button#confirmbutton').on 'click', ->
        selected_lists = {}
        for mode in PiRemote.select_classes
            selected_lists[mode] = []
            for key, val of PiRemote.selected[mode]
                if val
                    selected_lists[mode].push key

        PiRemote.do_ajax
            url: 'seedbrowse'
            method: 'POST'
            data:
                what: what
                count: $('input#seedspin').val()
                dates: selected_lists['date']
                genres: selected_lists['genre']
                artists: selected_lists['artist']
                albums: selected_lists['album']
            success: (data) ->
                $('#modalSmall').modal('hide')
                return

        return


    return



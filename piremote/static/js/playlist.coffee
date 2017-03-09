# playlist.coffee -- install callbacks for playlist view

# Build playlist page.
# Loaded via PiRemote.load_page('playlist') every time 'Playlist' is selected in menu
PiRemote.load_playlist_page = ->

    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'play-list')
    tb = bl.append('table').attr('id', 'tbpl').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'pl')


    # Resize position indicator on window resize
    $(window).resize ->
        PiRemote.resize_pl_position_indicator()
        return

    PiRemote.get_playlist()
    return


# Invoke AJAX get of current playlist, callback will rebuild playlist table.
PiRemote.get_playlist = ->

    PiRemote.playlist_poll_started = false
    PiRemote.playlist_polling = false


    PiRemote.do_ajax
        url: 'plinfo'
        method: 'GET'
        data: {}
        success: (data) ->
            PiRemote.rebuild_playlist data   # <-- rebuild table callback
            return
    return


# Callback for get_playlist() -- rebuild full playlist tabke.
# Table design is one outer table (striped) including an inner table:
#
#  Number | Title          | Length | Action
#  -------+----------------+--------|
#         | album / artist |        | (rowspan)
#
PiRemote.rebuild_playlist = (data) ->

    tbody = d3.select('tbody#pl')
    tbody.selectAll('tr').remove()

    PiRemote.last_pl_version = data.pl.version

    # Prepare data for table build:
    # Array of
    # [ ID, [ [number, title, length, action-span], ['', artist, '']]
    tb_data = []
    for elem in data.pl.data
        span_item = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'
        rows = [[parseInt(elem[0])+1, elem[1], elem[4], span_item]]
        art = ''
        if elem[2].length
            art = elem[2]
        if elem[3].length
            if elem[2].length
                art += ' - '
            art += elem[3]
        rows.push(['', art, ''])
        tb_data.push([elem[5], rows])

    # calculate cell widths for number and time.
    # Set fixed cell widths later to avoid misaligned right borders of number column.
    no_text = '' + tb_data.length
    no_width = no_text.width('large')+20
    time_width = '000:00'.width('large')+20

    # Build table
    tbody
        .selectAll('tr')
        .data(tb_data, (d) -> d).enter()   # <-- ENTER outer <tr> loop, full data
        .append('tr')
            .attr('data-id', (d) -> d[0])  # id
            .attr('class', 'selectable')
        .selectAll('td')
        .data((d)->[d[1]]).enter()        # <-- ENTER outer <td> loop, [[row1, row2]]
        .append('td')
            .attr('class', 'pltdmain')
        .selectAll('table')
        .data((d)->[d]).enter()           # <-- ENTER inner <table>, [[row1, row2]]
        .append('table')
            .attr('class', 'pltbsub')
        .selectAll('tr')
        .data((d)->d).enter()           # <-- ENTER inner <tr>, [row1, row2]
        .append('tr')
        .attr('class', (d, i) -> 'pltr-'+i)
        .selectAll('td')
        .data((d)->d).enter()           # <-- ENTER inner <td>, [row1|2_elements]
        .append('td')
            .attr('class', (d, i) -> 'pltd-'+i)
            .attr('style', (d, i) ->
                if i == 0
                    return 'width: '+no_width+'px;'     # number column
                if i == 2
                    return 'width: '+time_width+'px;'   # number time
                if i == 3
                    return 'width: 20px;'               # action column
                return 'max-width: 100%;')
            .attr('rowspan', (d, i) ->
                if i == 3       # NOTE: only row1 has 4 elements, 2nd row has 3.
                    return '2'
                return '1')
            .classed('pl-action', (d, i) -> i ==3)
            .classed('selectable', (d, i) -> i != 3)
            .html((d)->d)

    PiRemote.last_pl_id = '-1'
    PiRemote.update_pl_status data.status
    PiRemote.install_pl_handlers()
    PiRemote.start_pl_poll()
    return


# Install callback functions for action elements in playlist table.
PiRemote.install_pl_handlers = ->

    # single-click on selectable items toggles select
    $('table#tbpl > tbody > tr.selectable > td > table > tr > td.selectable').off 'click'
    $('table#tbpl > tbody > tr.selectable > td > table > tr > td.selectable').on 'click', (event) ->
        $(this).parent().parent().parent().parent().toggleClass 'selected'
        return

    $('td.pl-action').off 'click'
    $('td.pl-action').on 'click', (event) ->
        id = $(this).parent().parent().parent().parent().data('id')
        PiRemote.pl_raise_action_dialog id
        return

    return


# Initiate short polling for current playlist position and song position indicator
PiRemote.start_pl_poll = ->
    return if PiRemote.playlist_poll_started
    PiRemote.playlist_poll_started = true
    PiRemote.do_pl_poll()
    return


# Short polling for play status
PiRemote.do_pl_poll = ->
    return if PiRemote.playlist_polling
    return unless PiRemote.playlist_poll_started
    return if PiRemote.current_page != 'playlist'

    PiRemote.do_ajax
        url: 'status'
        method: 'GET'
        data: {}
        success: (data) ->
            PiRemote.update_pl_status data  # <-- poll callback
            PiRemote.playlist_polling = true
            window.setTimeout ( ->
                PiRemote.playlist_polling = false
                PiRemote.do_pl_poll()
                return
            ),  1000 # <-- short polling interval
            return
    return


# Callback for status polling loop.
# Update currently played song and position indicator
PiRemote.update_pl_status = (data) ->

    # Check if playlist version changed
    if PiRemote.last_pl_version != parseInt(data.playlist)
        d3.select('tbody#pl').selectAll('tr').remove()
        d3.select('tbody#pl').selectAll('tr').append('td').html('refetching....')
        PiRemote.get_playlist()
        return

    # Update position indicator and currently highlighted item only if song id changed.
    if data.id and data.id != PiRemote.last_pl_id
            # turn off running for all but running
            d3.selectAll('table#tbpl tr.selectable').filter((d) -> d[0] != data.id).classed('running', 0)
            # activate running song
            d3.selectAll('table#tbpl tr.selectable[data-id="'+data.id+'"').classed('running', 1)
            PiRemote.last_pl_id = data.id

            # scroll to current item
            window.scrollTo 0, $('table#tbpl tr.selectable.running').offset().top -
                window.innerHeight*0.2

            # remove old position div
            d3.selectAll('#plpos').remove()

            # add position div and adjust width
            d3.select('table#tbpl tr.selectable.running td table tr.pltr-0 td.pltd-1')
                .append('div').attr('id', 'plpos')
                .append('div').attr('id', 'plposfill')
            PiRemote.resize_pl_position_indicator()
    else if not data.id
        # remove old position div
        d3.selectAll('#plpos').remove()
        # turn off all indicators
        d3.selectAll('table#tbpl tr.selectable').classed('running', 0)

    # position indicator
    if (data.time) and (data.elapsed)
        pct = 100.0 * parseFloat(data.elapsed) / parseFloat(data.time)
        PiRemote.pl_set_position_indicator pct
    else
        PiRemote.pl_set_position_indicator 0

    return


# Resize width of the position indicator frame.
# Callback for resize event and also invoked after status update if current song changed.
PiRemote.resize_pl_position_indicator = ->
    $('#plpos').width 1
    w = $('table#tbpl tr.selectable.running td table tr.pltr-0 td.pltd-1').width()
    if w
        $('#plpos').width w - 2
    return

# Set position fill in position slider (percentage value required).
PiRemote.pl_set_position_indicator = (pct) ->
    pct_set = 100-pct
    pct_set = 0 if pct_set < 0
    pct_set = 100 if pct_set > 100

    $('#plposfill').css('right', pct_set+'%')
    return


# Raise modal action dialog after click on vertical action dots.
PiRemote.pl_raise_action_dialog = (id) ->

    title = d3.select('tr[data-id="'+id+'"]').data()[0][1][1][1]
    return unless title

    d3.select('#smallModalLabel').html('Playlist Action')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('h5').html(title)

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['select-all', 'Select All'],
        ['deselect-all', 'Deselect All'],
        ['invert-selection', 'Invert Selection'],
        ['playid', 'Play Item Now'],
        ['playidnext', 'Play Item Next'],
        ['playidsnext', 'Selection After Current'],
        ['moveidend', 'Item to End'],
        ['moveidsend', 'Selection to End'],
        ['item-to-pl', 'Item to Another Playlist'],
        ['selection-to-pl', 'Selection to Another Playlist'],
        ['deleteid', 'Delete Item'],
        ['deleteids', 'Delete Selection'],
        ['clear', 'Clear Playlist'],
        ['save', 'Save Playlist As'],
        ['randomize', 'Randomize Playlist'],
        ['randomize-rest', 'Randomize Playlist After Current'],
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0]).attr('data-id', id)
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.pl_do_action $(this).data('action'), $(this).data('id')
        $('#modalSmall').modal('hide')
        return

    # Raise dialog.
    $('#modalSmall').modal()
    return


# Callback for actions clicked in playlist action dialog
PiRemote.pl_do_action = (action, id) ->

    if action == 'select-all'
        d3.selectAll('tr.selectable').classed('selected', 1)
    else if action == 'deselect-all'
        d3.selectAll('tr.selectable').classed('selected', 0)
    else if action == 'invert-selection'
        d3.selectAll('tr.selectable').classed('selected', ()-> ! d3.select(this).classed('selected'))
    else if action in ['playid', 'playidnext', 'moveidend', 'deleteid']
        PiRemote.pl_action action, '', [id]
    else if action in ['playidsnext', 'moveidsend', 'deleteids']
        items = d3.selectAll('tr.selectable.selected').data().map((d)->d[0])
        PiRemote.pl_action action, '', items
    else if action in ['clear', 'randomize', 'randomize-rest']
        # TODO: ask for clear?
        PiRemote.pl_action action, '', []
    else if action == 'item-to-pl'
        console.log 'TODO '+action
    else if action == 'selection-to-pl'
        console.log 'TODO '+action
    else if action == 'save'
        console.log 'TODO '+action
    else

        console.log 'TODO '+action


    return

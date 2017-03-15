# playlist.coffee -- install callbacks for playlist view

# Build playlist page.
# Loaded via PiRemote.load_page('playlist') every time 'Playlist' is selected in menu
PiRemote.load_playlist_page = ->

    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'play-list')
    tb = bl.append('table').attr('id', 'tbpl').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'pl')


    $('#addsign').show()
    $('#addsign').off 'click'
    $('#addsign').on 'click', ->
        PiRemote.pl_raise_add_dialog()
        return

    # Resize position indicator on window resize
    $(window).resize ->
        PiRemote.resize_pl_position_indicator()
        return

    PiRemote.get_playlist()
    return


# Invoke AJAX get of current playlist, callback will rebuild playlist table.
PiRemote.get_playlist = ->

    PiRemote.playlist_poll_started = false

    PiRemote.do_ajax
        url: 'plinfo'
        method: 'GET'
        data: {}
        success: (data) ->
            PiRemote.rebuild_playlist data   # <-- rebuild table callback
            return
    return


# Invoke AJAX post of changes in playlist.
# Called if playlist version has changed.
PiRemote.get_playlist_changes = (last_version) ->

    PiRemote.playlist_poll_started = false

    PiRemote.do_ajax
        url: 'plchanges'
        method: 'GET'
        data:
            version: last_version
        success: (data) ->
            PiRemote.pl_apply_changes data   # <-- change playlist
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

    d3.select('tbody#pl').selectAll('tr').remove()
    PiRemote.last_pl_version = data.pl.version

    # Prepare data for table build:
    # Array of
    # [pos, id, title, length, arist-album]
    PiRemote.tb_data = []
    for elem in data.pl.data
        art = ''
        if elem[2].length
            art = elem[2]
        if elem[3].length
            if elem[2].length
                art += ' - '
            art += elem[3]
        item = [parseInt(elem[0]), parseInt(elem[5]), elem[1], elem[4], art, false]
        PiRemote.tb_data.push(item)

    PiRemote.pl_update_table()

    PiRemote.last_pl_id = '-1'
    PiRemote.update_pl_status data.status
    PiRemote.install_pl_handlers()
    PiRemote.start_pl_poll()
    return


# Rebuild playlist table with current content from PiRemote.tb_data.
# Called by rebuild_playlist() and pl_apply_changes()
PiRemote.pl_update_table =  ->

    # calculate cell widths for number and time.
    # Set fixed cell widths later to avoid misaligned right borders of number column.
    no_text = '' + PiRemote.tb_data.length
    no_width = no_text.width('large')+20
    time_width = '000:00'.width('large')+20

    # action element in last cell of first row in sub table
    span_item = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    # MAINROW
    tbody = d3.select('tbody#pl')
    mainrows = tbody.selectAll('tr.mainrow').data(PiRemote.tb_data)
    mainrows.attr('data-id', (d) -> d[1])  # id
            .attr('data-pos', (d) -> d[0])  # pos
            .classed('selected', (d) -> d[5])

    # DELETE
    mainrows.exit().remove()

    # UPDATE
    maincellup = mainrows.selectAll('td.pltdmain').data((d)->[d])
    subtableup = maincellup.selectAll('table.pltbsub').data((d)->[d])
    subrowsup = subtableup.selectAll('tr').data((d)->[[d[0]+1, d[2], d[3], span_item], ['', d[4], '']])
    subcellsup = subrowsup.selectAll('td').data((d)->d)
    subcellsup
        .attr('style', (d, i) ->
                if i == 0
                    return 'width: '+no_width+'px;'     # number column
                if i == 2
                    return 'width: '+time_width+'px;'   # number time
                if i == 3
                    return 'width: 20px;'               # action column
                return 'max-width: 100%;')
        .html((d)->d)

    # NEW
    maincells = mainrows.enter().append('tr')
        .attr('data-id', (d) -> d[1])  # id
        .attr('data-pos', (d) -> d[0])  # pos
        .attr('class', 'selectable mainrow')
        .classed('selected', (d) -> d[5])
        .selectAll('td.pltdmain').data((d)->[d])

    subtables = maincells.enter().append('td').attr('class', 'pltdmain')
        .selectAll('table.pltbsub').data((d)->[d])

    subrows = subtables.enter().append('table').attr('class', 'pltbsub')
        .selectAll('tr').data((d)->[[d[0]+1, d[2], d[3], span_item], ['', d[4], '']])

    subcells = subrows.enter().append('tr').attr('class', (d, i) -> 'pltr-'+i)
        .selectAll('td').data((d)->d)

    subcell = subcells.enter().append('td')
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
        .classed('selectable', (d, i) -> i != 3 && i != 0)
        .html((d)->d)

    return


# Apply changes to playlist.
# Callback for POST /piremote/plchanges AJAX call.
PiRemote.pl_apply_changes = (data) ->

    PiRemote.last_pl_version = data.pl.version
    len = data.pl.length
    change_list = data.pl.changes

    selected_ids = []
    selected_ids.push elem[1] for elem in PiRemote.tb_data when elem[5]

    PiRemote.tb_data.length = len

    for elem in change_list
        pos = parseInt(elem[0])
        id = parseInt(elem[5])
        art = ''
        if elem[2].length
            art = elem[2]
        if elem[3].length
            if elem[2].length
                art += ' - '
            art += elem[3]
        selected = id in selected_ids
        item = [pos, id, elem[1], elem[4], art, selected]
        PiRemote.tb_data[pos] = item

    PiRemote.pl_update_table()

    # Reinstall callbacks and set position and current song indicator
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
        pos = $(this).parent().parent().parent().parent().data('pos')
        PiRemote.tb_data[pos][5] = ! PiRemote.tb_data[pos][5]
        return

    # single click on action raises action dialog
    $('td.pl-action').off 'click'
    $('td.pl-action').on 'click', (event) ->
        id = $(this).parent().parent().parent().parent().data('id')
        PiRemote.pl_raise_action_dialog id
        return

    # single click on index column raises info dialog
    $('td.pltd-0').off 'click'
    $('td.pltd-0').on 'click', (event) ->
        # Fetch filename
        id = $(this).parent().parent().parent().parent().data('id')
        PiRemote.do_ajax
            url: 'plinfo/'+id
            method: 'GET'
            success: (data) ->
                if data.result isnt `undefined` and data.result.length > 0 and data.result[0].file isnt `undefined`
                    PiRemote.search_raise_info_dialog data.result[0].file
                return
        return

    # Detect click-and-hold on item
    $('table#tbpl > tbody > tr.selectable > td > table > tr > td.selectable').off 'mousedown'
    $('table#tbpl > tbody > tr.selectable > td > table > tr > td.selectable').on 'mousedown', (event) ->
        $this = $(this).data "mousedown", true
        setTimeout ( ->
            if $this.data('mousedown') == true  # prevent too short hold time
                PiRemote.pl_raise_drag_element event, $this
                # TODO: invert selection state of the element
            return
        ), 1000  # <-- click and hold timeout
        return

    # Set mousedown data to false if mouse no longer down:
    # Prevent mouse-hold event if hold too short.
    $('table#tbpl > tbody > tr.selectable > td > table > tr > td.selectable').off 'mouseup'
    $('table#tbpl > tbody > tr.selectable > td > table > tr > td.selectable').on 'mouseup', ->
        $(this).data "mousedown", false
        return

    # Detect mouse up events while dragging
    $(document).off 'mouseup'
    $(document).on 'mouseup', (event) ->
        PiRemote.pl_drop_drag_element event if PiRemote.dragging
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
    return if PiRemote.playlist_polling > 1
    return unless PiRemote.playlist_poll_started
    return if PiRemote.current_page != 'playlist'

    PiRemote.do_ajax
        url: 'status'
        method: 'GET'
        data: {}
        success: (data) ->
            PiRemote.update_pl_status data  # <-- poll callback
            PiRemote.playlist_polling += 1
            window.setTimeout ( ->
                PiRemote.do_pl_poll()
                PiRemote.playlist_polling -= 1
                return
            ),  1000 # <-- short polling interval
            return
    return


# Callback for status polling loop.
# Update currently played song and position indicator
PiRemote.update_pl_status = (data) ->

    # Check if playlist version changed
    if PiRemote.last_pl_version != parseInt(data.playlist)
        PiRemote.get_playlist_changes PiRemote.last_pl_version
        return

    # Update position indicator and currently highlighted item only if song id changed.
    if data.id and data.id != PiRemote.last_pl_id

            # turn off running for all but running
            d3.selectAll('table#tbpl tr.selectable').filter((d) -> d[1] != data.id).classed('running', 0)
            # activate running song
            d3.selectAll('table#tbpl tr.selectable[data-id="'+data.id+'"').classed('running', 1)
            PiRemote.last_pl_id = data.id

            # scroll to current item
            # TODO BUG tr.selectable.running can be undefined
            running = $('table#tbpl tr.selectable.running')
            if running.length > 0
                window.scrollTo 0, running.offset().top -
                    window.innerHeight*0.2

            # remove old position div
            d3.selectAll('#plpos').remove()

            # add position div and adjust width
            if running.length > 0
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
    running = $('table#tbpl tr.selectable.running')
    if running.length > 0
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

    title = d3.select('tr[data-id="'+id+'"]').data()[0][2]
    return unless title

    d3.select('#smallModalLabel').html('Playlist Action')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('h5').html(title)

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['playid', 'Play Item Now'],
        ['playidnext', 'Play Item Next'],
        ['moveidend', 'Item to End'],
        ['item-to-pl', 'Item to Another Playlist'],
        ['deleteid', 'Delete Item'],
        ['goto', 'Go to Folder'],
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



# Raise modal action dialog after click on vertical action dots.
PiRemote.pl_raise_add_dialog = ->

    d3.select('#smallModalLabel').html('Playlist Action')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')

    items = [
        ['select-all', 'Select All'],
        ['deselect-all', 'Deselect All'],
        ['invert-selection', 'Invert Selection'],
        ['playidsnext', 'Selection After Current'],
        ['moveidsend', 'Selection to End'],
        ['selection-to-pl', 'Selection to Another Playlist'],
        ['deleteids', 'Delete Selection'],
        ['clear', 'Clear Playlist'],
        ['save', 'Save Playlist As'],
        ['randomize', 'Randomize Playlist'],
        ['randomize-rest', 'Randomize Playlist After Current'],
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.pl_do_action $(this).data('action')
        $('#modalSmall').modal('hide')
        return

    # Raise dialog.
    $('#modalSmall').modal()
    return


# Callback for actions clicked in playlist action dialog
PiRemote.pl_do_action = (action, id=-1) ->

    if action == 'select-all'
        d3.selectAll('tr.selectable').classed('selected', 1)
        elem[5] = true for elem in PiRemote.tb_data
    else if action == 'deselect-all'
        d3.selectAll('tr.selectable').classed('selected', 0)
        elem[5] = false for elem in PiRemote.tb_data
    else if action == 'invert-selection'
        d3.selectAll('tr.selectable').classed('selected', ()-> ! d3.select(this).classed('selected'))
        elem[5] = ! elem[5] for elem in PiRemote.tb_data
    else if action in ['playid', 'playidnext', 'moveidend', 'deleteid']
        PiRemote.pl_action action, '', [id]
    else if action in ['playidsnext', 'moveidsend', 'deleteids']
        items = d3.selectAll('tr.selectable.selected').data().map((d)->d[1])
        PiRemote.pl_action action, '', items
        PiRemote.pl_do_action 'deselect-all'
    else if action in ['clear', 'randomize', 'randomize-rest']
        # TODO: ask for clear?
        PiRemote.pl_action action, '', []
    else if action == 'item-to-pl'
        console.log 'TODO '+action
    else if action == 'selection-to-pl'
        console.log 'TODO '+action
    else if action == 'save'
        console.log 'TODO '+action
    else if action == 'goto'
        # Fetch folder for id
        PiRemote.do_ajax
            url: 'plinfo/'+id
            method: 'GET'
            success: (data) ->
                if data.result isnt `undefined` and data.result.length > 0 and data.result[0].file isnt `undefined`
                    PiRemote.last_browse = data.result[0].file.split('/').slice(0,-1).join('/')
                    PiRemote.load_page 'browse'
                return
    else
        console.log 'TODO '+action

    return


# Callback for click-and-hold event.
# Show playlist drag element and move it below cursor.
PiRemote.pl_raise_drag_element = (event, element) ->
    return if PiRemote.dragging

    tr = element.parent().parent().parent().parent()
    pos = tr.data('pos')
    PiRemote.drag_id = tr.data('id')

    $('#dragdiv').text(PiRemote.tb_data[pos][2])
    $('#dragdiv').show()
    $('#dragdiv').css('top', event.pageY-20)


    $(document).on 'mousemove', (event) ->
        event.preventDefault()
        $('#dragdiv').css('top', event.pageY-20)
        return


    PiRemote.dragging = true
    return


# Callback for mouseup.
# Drop dragged element if dragging.
PiRemote.pl_drop_drag_element = (event) ->
    return unless PiRemote.dragging
    PiRemote.dragging = false

    # stop dragging
    $(document).off 'mousemove'
    $('#dragdiv').hide()

    # get position id of element where dragging has stopped
    elem = $(document.elementFromPoint($(window).width()/2, event.pageY))
    find_tr = elem
    while not find_tr.is('html') and not find_tr.is('tr.mainrow')
        find_tr = find_tr.parent()

    pos = PiRemote.tb_data.length  # dropped somewhere else --> put to end
    if find_tr.is('tr.mainrow')
        pos = find_tr.data('pos')  # dropped on item -> use its position

    # perform move
    PiRemote.pl_action 'moveid', '', [PiRemote.drag_id, pos]

    return

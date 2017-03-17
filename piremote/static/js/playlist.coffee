# playlist.coffee -- install callbacks for playlist view

# Build playlist page.
# Loaded via PiRemote.load_page('playlist') every time 'Playlist' is selected in menu
PiRemote.load_playlist_page = ->

    # Insert buttons
    PiRemote.add_navbar_button 'home', 'home', true
    PiRemote.add_navbar_button 'pl_save_playlist', 'save-file', true, false
    PiRemote.add_navbar_button 'pl_playlists', 'open-file', true
    PiRemote.add_navbar_button 'pl_edit_playlists', 'list', true
    PiRemote.add_navbar_button 'pl_clear_playlist', 'remove', true, false
    PiRemote.add_navbar_button 'pl_seed_playlist', 'plus', true, false

    $('button#navbutton_pl_save_playlist').off 'click'
    $('button#navbutton_pl_save_playlist').on 'click', ->
        PiRemote.pl_raise_save_dialog()
        return

    $('button#navbutton_pl_clear_playlist').off 'click'
    $('button#navbutton_pl_clear_playlist').on 'click', ->
        PiRemote.pl_raise_clear_dialog()
        return

    $('button#navbutton_pl_seed_playlist').off 'click'
    $('button#navbutton_pl_seed_playlist').on 'click', ->
        PiRemote.pl_raise_seed_dialog()
        return

    # build main content for current sub page.
    if PiRemote.current_sub_page == 'pl_playlists'
        PiRemote.pl_build_load_playlist()
    else if  PiRemote.current_sub_page == 'pl_edit_playlists'
        PiRemote.pl_build_edit_playlist()
    else
        PiRemote.pl_build_home()

    return


# Build playlist/home page and load current playlist
PiRemote.pl_build_home = ->

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

# Load list of playlists
PiRemote.pl_build_load_playlist = ->

    $('#addsign').hide()

    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'play-list')
    tb = bl.append('table').attr('id', 'tbpls').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'pls')

    PiRemote.pls_action 'list', '',
        success: (data)->
            PiRemote.pl_rebuild_playlist_list data
            return

    return


# Load edit playlist dialog and enter playlist edit mode.
PiRemote.pl_build_edit_playlist = ->

    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'play-list')
    tb = bl.append('table').attr('id', 'tbpledit').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'pledit')

    PiRemote.pl_action_on_playlists
        title: 'Choose Playlist to Edit'
        success: (data) ->
            PiRemote.get_playlist_by_name data
            $('#modalSmall').modal('hide')
            return
    return


# Load edit playlist dialog and enter playlist edit mode.
PiRemote.get_playlist_by_name = (plname) ->
    PiRemote.pl_edit_name = plname
    PiRemote.do_ajax
        url: 'plshortinfo'
        method: 'GET'
        data:
            plname: plname
        success: (data) ->
            PiRemote.rebuild_edit_playlist data   # <-- rebuild table callback
            return

    return


# Invoke AJAX get of current playlist, callback will rebuild playlist table.
PiRemote.get_playlist = ->

    PiRemote.pl_edit_name = ''

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
    # [pos, id, title, length, arist-album, selected, file]
    PiRemote.tb_data = []
    for elem in data.pl.data
        art = ''
        if elem[2].length
            art = elem[2]
        if elem[3].length
            if elem[2].length
                art += ' - '
            art += elem[3]
        item = [parseInt(elem[0]), parseInt(elem[5]), elem[1], elem[4], art, false, elem[6]]
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
        item = [pos, id, elem[1], elem[4], art, selected, elem[6]]
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
    return if PiRemote.current_sub_page != 'home'

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
        return

    # Raise dialog.
    $('#modalSmall').modal('show')
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
        return

    # Raise dialog.
    $('#modalSmall').modal('show')
    return


# Callback for actions clicked in playlist action dialog
PiRemote.pl_do_action = (action, id=-1) ->

    if action == 'select-all'
        d3.selectAll('tr.selectable').classed('selected', 1)
        elem[5] = true for elem in PiRemote.tb_data
        $('#modalSmall').modal('hide')
    else if action == 'deselect-all'
        d3.selectAll('tr.selectable').classed('selected', 0)
        elem[5] = false for elem in PiRemote.tb_data
        $('#modalSmall').modal('hide')
    else if action == 'invert-selection'
        d3.selectAll('tr.selectable').classed('selected', ()-> ! d3.select(this).classed('selected'))
        elem[5] = ! elem[5] for elem in PiRemote.tb_data
        $('#modalSmall').modal('hide')
    else if action in ['playid', 'playidnext', 'moveidend', 'deleteid']
        PiRemote.pl_action action, '', [id]
        $('#modalSmall').modal('hide')
    else if action in ['playidsnext', 'moveidsend', 'deleteids']
        items = d3.selectAll('tr.selectable.selected').data().map((d)->d[1])
        PiRemote.pl_action action, '', items
        PiRemote.pl_do_action 'deselect-all'
        $('#modalSmall').modal('hide')
    else if action in ['randomize', 'randomize-rest']
        PiRemote.pl_action action, '', []
        $('#modalSmall').modal('hide')
    else if action == 'item-to-pl'
        file = d3.select('tr[data-id="'+id+'"]').data()[0][6]
        PiRemote.pl_append_items_to_playlist [file]
    else if action == 'selection-to-pl'
        items = d3.selectAll('tr.selectable.selected').data().map((d)->d[6  ])
        PiRemote.pl_append_items_to_playlist items
    else if action == 'goto'
        file = d3.select('tr[data-id="'+id+'"]').data()[0][6]
        PiRemote.last_browse = file.split('/').slice(0,-1).join('/')
        PiRemote.load_page 'browse'
        $('#modalSmall').modal('hide')
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


# Raise the playlist save dialog and save playlist as name set
PiRemote.pl_raise_save_dialog = (title='Save Current Playlist', action='saveas', plname='', save_button='Save', req={})->

    d3.select('#smallModalLabel').html(title)
    cont = d3.select('#smallModalMessage')
    cont.html('')

    cont.append('p').html('Enter name for playlist')

    trsave = cont
        .append('table').attr('id', 'savebar').attr('class', 'table')
        .append('tr').attr('id', 'savebartr')
    trsave
        .append('td').attr('id', 'savebarinput')
        .append('input').attr('type', 'text').attr('id', 'savefield').attr('placeholder', 'my playlist').attr('pattern', '[a-zA-Z0-9_\\- ]+')
    trsave
        .append('td').attr('id', 'savebarbutton')
        .append('button').attr('type', 'submit').attr('class', 'btn btn-default').attr('id', 'gosave').html(save_button)

    $('button#gosave').off 'click'
    $('button#gosave').on 'click', ->
        if $('input#savefield').val().length > 0
            PiRemote.pls_action action, $('input#savefield').val(),
                payload: [plname]
                success: (data) ->
                    req.success(data) if req.success
                    $('#modalSmall').modal('hide')
                    return
        return

    # Raise dialog.
    $('#modalSmall').modal('show')

    return


# Callback for clear button in button bar.
# Confirm clear and perform clear.
PiRemote.pl_raise_clear_dialog = ->
    if PiRemote.pl_edit_name == ''
        PiRemote.confirm_dialog
            title: 'Clear Playlist?'
            requirepw: 1
            confirmed: ->
                PiRemote.pl_action 'clear', '', []
                return
    else
        PiRemote.confirm_dialog
            title: 'Clear Playlist '+PiRemote.pl_edit_name+'?'
            requirepw: 1
            confirmed: ->
                PiRemote.pls_action 'clear', PiRemote.pl_edit_name,
                    success: (data) ->
                        PiRemote.get_playlist_by_name PiRemote.pl_edit_name
                return
    return

# Callback for plus button.
# Seed playlist with N random songs
PiRemote.pl_raise_seed_dialog = ->

    d3.select('#smallModalLabel').html('Seed Playlist '+PiRemote.pl_edit_name)
    cont = d3.select('#smallModalMessage')
    cont.html('')

    cont.append('p').html('Set number of random items to add')

    cont.append('p').append('input')
        .attr('type', 'number').attr('min', '10').attr('max', '100').attr('value', '20')
        .attr('id', 'seedspin')

    cont.append('p').attr('class', 'confirmbutton')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary')
            .attr('id', 'confirmbutton').html('Seed')

    $('button#confirmbutton').off 'click'
    $('button#confirmbutton').on 'click', ->
        PiRemote.pl_action 'seed', PiRemote.pl_edit_name, [$('input#seedspin').val()], 'file',
            success: (data) ->
                # Reload playlist in edit mode.
                # No reload in playlist mode (polling will auto-update).
                if PiRemote.pl_edit_name != ''
                    PiRemote.get_playlist_by_name PiRemote.pl_edit_name
                $('#modalSmall').modal('hide')
                return
        return

    $('#modalSmall').modal('show')
    return


# Callback for AJAX receive of list of playlists.
# Rebuild list of playlists
PiRemote.pl_rebuild_playlist_list = (data) ->

    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    # clean table
    tbody = d3.select('tbody#pls')
    tbody.selectAll('tr').remove()

    tbody.selectAll('tr').data(data.pls).enter()
        .append('tr')
            .attr('class', 'pls-item')
            .attr('data-plname', (d)->d)
            .selectAll('td')
            .data((d,i)->[i+1, d, action_span])
            .enter()
        .append('td')
            .attr('class', (d,i)-> 'pls-col-'+i)
            .html((d)->d)

    $('td.pls-col-2').off 'click'
    $('td.pls-col-2').on 'click', (event) ->
        pl = $(this).parent().data('plname')
        PiRemote.pl_raise_playlist_list_actions pl
        return

    return

# Callback for action dots pressed on item in playlists list.
PiRemote.pl_raise_playlist_list_actions = (plname) ->

    d3.select('#smallModalLabel').html('Playlist Action')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('p').html('Playlist <strong>'+plname+'</strong> actions:')

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')

    items = [
        ['load', 'Load to Current'],
        ['rename', 'Rename'],
        ['rm', 'Remove'],
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        action = $(this).data('action')
        if action == 'load'
            PiRemote.pls_action 'load', plname,
                success: (data) ->
                    PiRemote.load_page 'playlist', 'home'
                    $('#modalSmall').modal('hide')
                    return
        else if action == 'rm'
            PiRemote.confirm_dialog
                title: 'Remove Playlist '+plname+'?'
                requirepw: 1
                confirmed: ->
                    PiRemote.pls_action 'rm', plname,
                        success: (data) ->
                            PiRemote.load_page 'playlist', 'pl_playlists'
                            return
                    return
        else if action == 'rename'
            PiRemote.pl_raise_save_dialog 'Rename Playlist '+plname, 'rename', plname, 'Rename',
                success: (data) ->
                    PiRemote.load_page 'playlist', 'pl_playlists'
                    $('#modalSmall').modal('hide')
                    return
            return
        return

    # Raise dialog.
    $('#modalSmall').modal('show')
    return


# Perform action on list of playlists.
# req: {title: "TITLE", success: function(plname)}
PiRemote.pl_action_on_playlists = (req) ->

    PiRemote.pls_action 'list', '',
        success: (data)->
            d3.select('#smallModalLabel').html(req.title)
            cont = d3.select('#smallModalMessage')
            cont.html('')
            navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
            navul.append('li').attr('role', 'presentation')
                    .append('span').attr('class', 'browse-action-file browse-action-new')
                    .attr('data-plname', '')
                    .html('Create new playlist')
            for elem in data.pls
                navul.append('li').attr('role', 'presentation')
                    .append('span').attr('class', 'browse-action-file')
                    .attr('data-plname', elem)
                    .html(elem)

            # Callback for click actions on navigation.
            $(document).off 'click', 'span.browse-action-file'
            $(document).on 'click', 'span.browse-action-file', () ->
                plname = $(this).data('plname')
                if plname.length > 0
                    req.success plname if req.success
                else
                    d3.select('#smallModalLabel').html('Create New Playlist')
                    cont = d3.select('#smallModalMessage')
                    cont.html('')
                    cont.append('p').html('Enter name for playlist')
                    trsave = cont
                        .append('table').attr('id', 'savebar').attr('class', 'table')
                        .append('tr').attr('id', 'savebartr')
                    trsave
                        .append('td').attr('id', 'savebarinput')
                        .append('input').attr('type', 'text').attr('id', 'savefield').attr('placeholder', 'my playlist').attr('pattern', '[a-zA-Z0-9_\\- ]+')
                    trsave
                        .append('td').attr('id', 'savebarbutton')
                        .append('button').attr('type', 'submit').attr('class', 'btn btn-default').attr('id', 'gosave').html('Create')

                    $('button#gosave').off 'click'
                    $('button#gosave').on 'click', ->
                        if $('input#savefield').val().length > 0
                            PiRemote.pls_action 'new', $('input#savefield').val(),
                                success: (data) ->
                                    req.success data.plname if req.success and data.plname != ''
                                    return
                        return
                return  # click on playlists list

            $('#modalSmall').modal('show')
            return
    return


# Callback for get_playlist_by_name() for edit playlist mode.
PiRemote.rebuild_edit_playlist = (data) ->

    PiRemote.tb_short_data = data.pl
    PiRemote.pl_edit_name = data.plname

    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    # clean table
    tbody = d3.select('tbody#pledit')
    tbody.selectAll('tr').remove()

    tbody.selectAll('tr').data(data.pl).enter()
        .append('tr')
            .attr('class', 'pledit-item')
            .attr('data-index', (d,i)->i)
            .selectAll('td')
            .data((d,i)->[i+1, d[1], action_span])
            .enter()
        .append('td')
            .attr('class', (d,i)-> 'pledit-col-'+i)
            .html((d)->d)

    $('td.pledit-col-0').off 'click'
    $('td.pledit-col-0').on 'click', (event) ->
        i = $(this).parent().data('index')
        PiRemote.search_raise_info_dialog data.pl[i][0]
        return

    $('td.pledit-col-1').off 'click'
    $('td.pledit-col-1').on 'click', (event) ->
        $(this).parent().toggleClass 'selected'
        return

    $('td.pledit-col-2').off 'click'
    $('td.pledit-col-2').on 'click', (event) ->
        i = $(this).parent().data('index')
        PiRemote.pl_raise_edit_action_dialog data.pl[i][0], data.pl[i][1], i
        return

    $('#addsign').show()
    $('#addsign').off 'click'
    $('#addsign').on 'click', ->
        PiRemote.pl_raise_edit_add_dialog()
        return
    return

# Action dots clicked in playlist edit mode
PiRemote.pl_raise_edit_action_dialog = (file, title, pos) ->

    d3.select('#smallModalLabel').html('Item Action')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    cont.append('h5').html(title)

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')

    items = [
        ['moveend', 'Move to End'],
        ['insert', 'Insert into Current Playlist'],
        ['append', 'Append to Current Playlist'],
        ['selection-to-pl', 'Append to Another Playlist'],
        ['delete', 'Delete'],
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        action = $(this).data('action')
        if action in ['insert', 'append']
            PiRemote.pl_action action, '', [file]
            $('#modalSmall').modal('hide')
        else if action in ['delete', 'moveend']
            PiRemote.pls_action action, PiRemote.pl_edit_name,
                payload: [pos]
                success: (data) ->
                    PiRemote.get_playlist_by_name PiRemote.pl_edit_name
                    return
            $('#modalSmall').modal('hide')
        else if action == 'selection-to-pl'
            PiRemote.pl_append_items_to_playlist [file]
        return

    # Raise dialog.
    $('#modalSmall').modal('show')
    return


    return


# Plus sign pressed in edit mode
PiRemote.pl_raise_edit_add_dialog = ->

    d3.select('#smallModalLabel').html('Playlist Action')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')

    items = [
        ['select-all', 'Select All'],
        ['deselect-all', 'Deselect All'],
        ['invert-selection', 'Invert Selection'],
        ['moveend', 'Move Selection to End'],
        ['insert', 'Insert Selection to Current Playlist'],
        ['append', 'Append Selection to Current Playlist'],
        ['selection-to-pl', 'Append Selection to Another Playlist'],
        ['delete', 'Delete Selection'],
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        action = $(this).data('action')
        items = d3.selectAll('tr.pledit-item.selected').data().map((d)->d[0])
        positions = d3.selectAll('tr.pledit-item.selected').data().map((d)->d[2])

        if action == 'select-all'
            d3.selectAll('tr.pledit-item').classed('selected', 1)
            $('#modalSmall').modal('hide')
        else if action == 'deselect-all'
            d3.selectAll('tr.pledit-item').classed('selected', 0)
            $('#modalSmall').modal('hide')
        else if action == 'invert-selection'
            d3.selectAll('tr.pledit-item').classed('selected', ()-> ! d3.select(this).classed('selected'))
            $('#modalSmall').modal('hide')
        else if action in ['insert', 'append']
            PiRemote.pl_action action, '', items
            d3.selectAll('tr.pledit-item').classed('selected', 0)
            $('#modalSmall').modal('hide')
        else if action in ['delete', 'moveend']
            PiRemote.pls_action action, PiRemote.pl_edit_name,
                payload: positions
                success: (data) ->
                    PiRemote.get_playlist_by_name PiRemote.pl_edit_name
                    return
            $('#modalSmall').modal('hide')
        else if action == 'selection-to-pl'
            PiRemote.pl_append_items_to_playlist items
        return

    # Raise dialog.
    $('#modalSmall').modal('show')
    return


# Append items to playlist -- raise playlist chooser dialog and add.
PiRemote.pl_append_items_to_playlist = (items) ->
    PiRemote.pl_action_on_playlists
        title: 'Choose Playlist to Append'
        success: (data) ->
            PiRemote.pl_action 'append', data, items
            $('#modalSmall').modal('hide')
            return
    return
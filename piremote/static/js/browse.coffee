# browse.coffee -- install callbacks for browse view

# Build browse page
PiRemote.load_browse_page = ->

    root = d3.select('.piremote-content')
    console.log root
    bl = root.append('div').attr('class', 'browse-list')
    tb = bl.append('table').attr('id', 'tbbrowse').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'browse')

    PiRemote.install_browse_actions()
    PiRemote.do_browse PiRemote.last_browse

    return

# Install browse menu actions
PiRemote.install_browse_actions = ->

    # click on menu items
    $(document).off 'click', 'a[data-toggle="browse"]'
    $(document).on 'click', 'a[data-toggle="browse"]', (event) ->
        action = event.target.dataset.action
        event.preventDefault()
        $('#bs-collapse-nav').collapse 'hide'
        if action == 'home'
            PiRemote.do_browse ''
        else if action == 'up'
            uptr = $('#trupdir')
            if uptr.length
                PiRemote.do_browse uptr.data('dirname')
        else if action == 'selectall'
            d3.selectAll('tr.selectable').classed('selected', 1)
        else if action == 'deselectall'
            d3.selectAll('tr.selectable').classed('selected', 0)
        else
            console.log 'Unknown browse action: '+action

        return

    $(document).off 'click', 'span.browse-span'
    $(document).on 'click', 'span.browse-span', () ->
        PiRemote.do_browse $(this).data('dirname')
        $('#modalSmall').modal('hide')
        return

    # Selection span in dir raise dialog pressed.
    $(document).off 'click', 'span.browse-action-dir'
    $(document).on 'click', 'span.browse-action-dir', () ->
        PiRemote.do_browse_action $(this).data('action'), $(this).data('item'), 'dir'
        $('#modalSmall').modal('hide')
        return

    # Selection span in file raise dialog pressed.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.do_browse_action $(this).data('action'), $(this).data('item'), 'file'
        $('#modalSmall').modal('hide')
        return

    return


# (Re)install browse handler on browse items -- needs to be recalled on table rebuild.
PiRemote.install_browse_handlers = ->


    # double-click to enter dir
    #$('div.browse-list > table > tbody > tr.dir-item').on 'dblclick', (event) ->
    #    PiRemote.do_browse $(this).data('dirname')
    #    return

    # single-click on selectable items toggles select
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').off 'click'
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').on 'click', (event) ->
        $(this).parent().toggleClass 'selected'
        return

    # move up by single-click
    $('#trupdir').off
    $('#trupdir').on 'click', (event) ->
        PiRemote.do_browse $(this).data('dirname')
        return

    # single click on folder or folder td enters folder
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-dir').off
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-dir').on 'click', (event) ->
        PiRemote.do_browse $(this).parent().data('dirname')
        return
#    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-dir > img').off
#    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-dir > img').on 'click', (event) ->
#        PiRemote.do_browse $(this).parent().parent().data('dirname')
#        return

    # Single click on file image or file image cell raises file dialog
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-file').off
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-file').on 'click', (event) ->
        PiRemote.raise_file_dialog $(this).parent()
        return
#    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-file > img').off
#    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-file > img').on 'click', (event) ->
#        PiRemote.raise_file_dialog $(this).parent().parent()
#        return

    # action triggered
    $('div.browse-list > table > tbody > tr.selectable > td.browse-action').off
    $('div.browse-list > table > tbody > tr.selectable > td.browse-action').on 'click', (event) ->
        parent = $(this).parent()
        if parent.is('.dir-item')
            PiRemote.raise_dir_dialog parent
        else if parent.is('.file-item')
            PiRemote.raise_file_actions parent
        else
            console.log 'ACTION ERROR'
            console.log parent

        return

    return

# Invoke ajax call to browse directory
PiRemote.do_browse = (dirname) ->
    PiRemote.last_browse = dirname
    PiRemote.do_ajax
        url: 'browse'
        method: 'POST'
        data:
            'dirname': dirname
        success: (data) ->
            PiRemote.rebuild_browse data
            return
    return

# Rebuild browse table using AJAX JSON result.
# Called by success in do_browse()
PiRemote.rebuild_browse = (data) ->

    # clean table
    tbody = d3.select('tbody#browse')
    tbody.selectAll('tr').remove()

    # First entry is folder up
    if data.dirname != ''
        up_span = '<span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span>'
        updir = data.dirname.split('/').slice(0, -1).join('/')
        uptr = tbody.append('tr').classed('dir-item', 1).attr('data-dirname', updir).attr('id', 'trupdir')
        uptr.append('td').classed('browse-head', 1).html(up_span)
        dirname = '/'+data.dirname+'/../'
        uptr.append('td').classed('browse-file', 1).html(dirname.replace(/\//g, ' / '))
        uptr.append('td').classed('browse-action', 1)

    dirs = data.browse.filter (d) -> d[0] == '1'

    # ... vertical dots for each element
    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    # Append dirs
    tbody.selectAll('tr')
        .data(dirs, (d) -> d).enter()
        .append('tr')
            .attr('class', 'dir-item selectable')
            .attr('data-dirname', (d) -> d[5])
        .selectAll('td')
        .data((d, i) -> ['<img src="/piremote/static/img/folder-blue.png"/>', d[1], action_span]).enter()
        .append('td')
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-head-dir', (d, i) -> i == 0)
            .classed('browse-dir', (d, i) -> i == 1)
            .classed('browse-selectable', (d, i) -> i == 1)
            .classed('browse-action', (d, i) -> i == 2)
            .html((d) -> d)

    # Append files
    files = data.browse.filter (d) -> d[0] == '2'
    tbody.selectAll('tr')
        .data(files, (d) -> d).enter()
        .append('tr')
            .attr('class', 'file-item selectable')
            .attr('data-title', (d) -> d[1])
            .attr('data-artist', (d) -> d[2])
            .attr('data-album', (d) -> d[3])
            .attr('data-length', (d) -> d[4])
            .attr('data-filename', (d) -> d[5])
            .attr('data-date', (d) -> d[7])
        .selectAll('td')
        .data((d, i) -> ['<img src="/piremote/static/img/'+d[6]+'.png"/>', d[1], action_span]).enter()
        .append('td')
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-head-file', (d, i) -> i == 0)
            .classed('browse-action', (d, i) -> i == 0)
            .classed('browse-file', (d, i) -> i == 1)
            .classed('browse-selectable', (d, i) -> i == 1)
            .classed('browse-action', (d, i) -> i == 2)
            .html((d) -> d)

    PiRemote.install_browse_handlers()
    window.scrollTo 0, 0
    return


# Image pressed on pressed on file item.
PiRemote.raise_file_dialog = (element) ->
    d3.select('#smallModalLabel').html('Audio File')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('h5').html(element.data('title'))

    artist = element.data('artist')
    album = element.data('album')
    length = element.data('length')
    year = element.data('date')

    p = cont.append('p')
    for item in ['Artist', 'Album', 'Length', 'Date']
        data = element.data(item.toLowerCase())
        if data.length > 0
            p.append('strong').html(item+': ')
            p.append('span').html(data)
            p.append('br')


    $('#modalSmall').modal()
    PiRemote.install_browse_actions()
    return

# Action glyph pressed on file item.
PiRemote.raise_file_actions = (element) ->
    d3.select('#smallModalLabel').html('File Actions')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('h5').html(element.data('title'))

    filename = element.data('filename')

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['select-all', 'Select all'],
        ['deselect-all', 'Deselect all'],
        ['append-item', 'Append Item'],
        ['insert-item', 'Insert Item'],
        ['append', 'Append Selection'],
        ['insert', 'Insert Selection'],
        ['append-other', 'Append Item to Playlist']
        ['append-other', 'Append Selection to Playlist']
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0]).attr('data-item', filename)
            .html(elem[1])

    $('#modalSmall').modal()
    PiRemote.install_browse_actions()
    return


# Action glyph pressed on dir item.
PiRemote.raise_dir_dialog = (element) ->
    d3.select('#smallModalLabel').html('Directory')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    dirname = element.data('dirname')
    dirs = dirname.split('/')
    p = cont.append('p')
    full_path = ''
    p.append('span').attr('class', 'browse-span').attr('data-dirname', '').html('Root')
    for dir in dirs
        p.append('span').attr('class', 'browse-arrow glyphicon glyphicon-arrow-right')
        p.append('span')
            .attr('class', 'browse-span')
            .attr('data-dirname', full_path+dir)
            .html(dir)
        full_path += dir + '/'

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['select-all', 'Select all'],
        ['deselect-all', 'Deselect all'],
        ['append-item', 'Append Item'],
        ['append', 'Append Selection'],
        ['append-other', 'Append Item to Playlist']
        ['append-other', 'Append Selection to Playlist']
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-dir')
            .attr('data-action', elem[0]).attr('data-item', dirname)
            .html(elem[1])

    $('#modalSmall').modal()
    PiRemote.install_browse_actions()
    return

# Callback if span pressed in dir or file dialog
PiRemote.do_browse_action = (action, item, type) ->

    if action == 'select-all'
        d3.selectAll('tr.selectable').classed('selected', 1)
    else if action == 'deselect-all'
        d3.selectAll('tr.selectable').classed('selected', 0)
    else if action == 'append-item'
        PiRemote.pl_action 'append', '', [item], type
    else if action == 'insert-item'
        PiRemote.pl_action 'insert', '', [item], type
    else if action == 'append'
        sel = d3.selectAll('tr.'+type+'-item.selected')
        items = sel.data().map((d) -> d[5])
        PiRemote.pl_action action, '', items, type
        sel.classed('selected', 0)
    else if action == 'insert'
        sel = d3.selectAll('tr.'+type+'-item.selected')
        items = sel.data().map((d) -> d[5])
        PiRemote.pl_action action, '', items, type
        sel.classed('selected', 0)

    return



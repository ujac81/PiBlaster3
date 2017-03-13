# browse.coffee -- install callbacks for browse view

# Build browse page.
# Loaded via PiRemote.load_page('browse') every time 'Browse' is selected in menu
PiRemote.load_browse_page = ->

    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'browse-list')
    tb = bl.append('table').attr('id', 'tbbrowse').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'browse')

    $('#addsign').show()
    $('#addsign').off 'click'
    $('#addsign').on 'click', ->
        PiRemote.browse_raise_add_dialog()
        return

    PiRemote.do_browse PiRemote.last_browse

    return


# Invoke ajax call to browse directory.
PiRemote.do_browse = (dirname) ->
    PiRemote.last_browse = dirname
    PiRemote.do_ajax
        url: 'browse'
        method: 'POST'
        data:
            'dirname': dirname
        success: (data) ->
            PiRemote.rebuild_browse data  # <-- rebuild table callback
            return
    return


# Rebuild browse table using AJAX JSON result.
# Called by success in do_browse().
# Installs on click events after end.
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
            .attr('class', 'dir-item')
            .attr('data-dirname', (d) -> d[5])
        .selectAll('td')
        .data((d, i) -> ['<img src="/piremote/static/img/folder-blue.png"/>', d[1], action_span]).enter()
        .append('td')
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-head-dir', (d, i) -> i == 0)
            .classed('browse-dir', (d, i) -> i == 1)
            #.classed('browse-selectable', (d, i) -> i == 1)
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


# on click events for browse list -- called after table rebuild.
PiRemote.install_browse_handlers = ->

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
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-head-dir').off
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-head-dir').on 'click', (event) ->
        PiRemote.do_browse $(this).parent().data('dirname')
        return

    # single click on dir name enters folder
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-dir').off
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-dir').on 'click', (event) ->
        PiRemote.do_browse $(this).parent().data('dirname')
        return

    # Single click on file image or file image cell raises file dialog
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-file').off
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-file').on 'click', (event) ->
        PiRemote.raise_file_dialog $(this).parent()
        return

    # dir action triggered
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-action').off
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-action').on 'click', (event) ->
        PiRemote.raise_dir_dialog $(this).parent()
        return

    # file action triggered
    $('div.browse-list > table > tbody > tr.selectable > td.browse-action').off
    $('div.browse-list > table > tbody > tr.selectable > td.browse-action').on 'click', (event) ->
        PiRemote.raise_file_actions $(this).parent()
        return
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
        ['append-item', 'Append Item'],
        ['insert-item', 'Insert Item'],
        ['append-other', 'Append Item to Playlist']
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0]).attr('data-item', filename)
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.do_browse_action $(this).data('action'), $(this).data('item'), 'file'
        $('#modalSmall').modal('hide')
        return

    # Raise dialog.
    $('#modalSmall').modal()
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

    # Callback function for clicks on dir items in header.
    $(document).off 'click', 'span.browse-span'
    $(document).on 'click', 'span.browse-span', () ->
        PiRemote.do_browse $(this).data('dirname')
        $('#modalSmall').modal('hide')
        return

    # Raise dialog.
    $('#modalSmall').modal()
    return


# Callback for press on '+' sign.
# Raise selection actions dialog.
PiRemote.browse_raise_add_dialog = ->
    d3.select('#smallModalLabel').html('File Actions')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['select-all', 'Select all'],
        ['deselect-all', 'Deselect all'],
        ['invert', 'Invert Selection'],
        ['append', 'Append Selection'],
        ['insert', 'Insert Selection'],
        ['append-other', 'Append Selection to another Playlist']
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.do_browse_action $(this).data('action')
        $('#modalSmall').modal('hide')
        return

    # Raise dialog.
    $('#modalSmall').modal()
    return


# Callback if span pressed in dir or file dialog.
# Invoke playlist actions via PiRemote.pl_action().
PiRemote.do_browse_action = (action, item=null, type='file') ->

    if action == 'select-all'
        d3.selectAll('tr.selectable').classed('selected', 1)
    else if action == 'deselect-all'
        d3.selectAll('tr.selectable').classed('selected', 0)
    else if action == 'invert'
        d3.selectAll('tr.selectable').classed('selected', ()-> ! d3.select(this).classed('selected'))
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



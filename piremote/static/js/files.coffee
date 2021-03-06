# files.coffee -- install callbacks for files view

# Build files page.
# Loaded via PiRemote.load_page('files') every time 'Files' is selected in menu
PiRemote.load_files_page = (no_refresh=false) ->

    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'browse-list')
    tb = bl.append('table').attr('id', 'tbbrowse').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'browse')
    
    $('h3#heading').html('Browse Files').show()
    $('#addsign').show()
    $('#addsign').off 'click'
    $('#addsign').on 'click', ->
        PiRemote.files_raise_add_dialog()
        return

    PiRemote.do_files PiRemote.last_files
    return


# Invoke ajax call to files directory.
PiRemote.do_files = (dirname) ->
    PiRemote.last_files = dirname
    PiRemote.do_ajax
        url: 'browse'
        method: 'POST'
        data:
            'dirname': dirname
        success: (data) ->
            PiRemote.rebuild_files data  # <-- rebuild table callback
            return
    return


# Rebuild files table using AJAX JSON result.
# Called by success in do_files().
# Installs on click events after end.
PiRemote.rebuild_files = (data) ->

    # clean table
    tbody = d3.select('tbody#browse')
    tbody.selectAll('tr').remove()

    # First entry is folder up
    if data.dirname != ''
        up_span = '<span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span>'
        updir = data.dirname.split('/').slice(0, -1).join('/')
        uptr = tbody.append('tr').attr('class', 'dir-item file-view').attr('data-dirname', updir).attr('id', 'trupdir')
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
            .attr('class', 'dir-item file-view')
            .attr('data-dirname', (d) -> d[5])
        .selectAll('td')
        .data((d) -> ['<img src="/piremote/static/img/folder-blue.png"/>', d[1], action_span]).enter()
        .append('td')
            .attr('class', (d, i)-> 'browse-td'+i)
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-head-dir', (d, i) -> i == 0)
            .classed('browse-dir', (d, i) -> i == 1)
            .classed('browse-action', (d, i) -> i == 2)
            .html((d) -> d)

    # Append files
    files = data.browse.filter (d) -> d[0] == '2'
    tbody.selectAll('tr')
        .data(files, (d) -> d).enter()
        .append('tr')
            .attr('class', 'file-item selectable file-view')
            .attr('data-title', (d) -> d[1])
            .attr('data-artist', (d) -> d[2])
            .attr('data-album', (d) -> d[3])
            .attr('data-length', (d) -> d[4])
            .attr('data-filename', (d) -> d[5])
            .attr('data-date', (d) -> d[7])
        .selectAll('td')
        .data((d, i) -> ['<img src="/piremote/static/img/'+d[6]+'.png"/>', PiRemote.make_float_rating(d[1], d[8]), action_span]).enter()
        .append('td')
            .attr('class', (d, i)-> 'browse-td'+i)
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-head-file', (d, i) -> i == 0)
            .classed('browse-action', (d, i) -> i == 0)
            .classed('browse-file', (d, i) -> i == 1)
            .classed('browse-selectable', (d, i) -> i == 1)
            .classed('browse-action', (d, i) -> i == 2)
            .html((d) -> d)

    # single-click on selectable items toggles select
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').on 'click', ->
        $(this).parent().toggleClass 'selected'
        return

    # move up by single-click
    $('#trupdir').on 'click', ->
        PiRemote.do_files $(this).data('dirname')
        return

    # single click on folder td enters folder
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-head-dir').on 'click', ->
        PiRemote.do_files $(this).parent().data('dirname')
        return

    # single click on dir name enters folder
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-dir').on 'click', ->
        PiRemote.do_files $(this).parent().data('dirname')
        return

    # Single click on file image or file image cell raises file dialog
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-file').on 'click', ->
        PiRemote.search_raise_info_dialog $(this).parent().data('filename')
        return

    # dir action triggered
    $('div.browse-list > table > tbody > tr.dir-item > td.browse-action').on 'click', ->
        PiRemote.raise_dir_dialog $(this).parent()
        return

    # file action triggered
    $('div.browse-list > table > tbody > tr.selectable > td.browse-action').on 'click', ->
        PiRemote.raise_file_actions $(this).parent().data('title'), $(this).parent().data('filename')
        return
        
    window.scrollTo 0, 0
    return


# Action glyph pressed on file item.
PiRemote.raise_file_actions = (title, filename) ->
    d3.select('#smallModalLabel').html('File Actions')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('h5').html(title)

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['append-item', 'Append Item'],
        ['insert-item', 'Insert Item'],
        ['append-other', 'Append Item to another Playlist']
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0]).attr('data-item', filename)
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.do_files_action $(this).data('action'), $(this).data('item'), 'file'
        return

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
        PiRemote.do_files $(this).data('dirname')
        $('#modalSmall').modal('hide')
        return

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    items = [
        ['append-item', 'Append Directory'],
        ['append-other', 'Append Directory to another Playlist']
        ['seed', 'Random add Songs'],
        ['seed-other', 'Random add Songs to another Playlist'],
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-dir')
            .attr('data-action', elem[0]).attr('data-item', dirname)
            .html(elem[1])

    # Callback function for clicks on navigation actions.
    $(document).off 'click', 'span.browse-action-dir'
    $(document).on 'click', 'span.browse-action-dir', () ->
        PiRemote.do_files_action $(this).data('action'), $(this).data('item'), 'dir'
        return

    $('#modalSmall').modal()
    return


# Callback for press on '+' sign.
# Raise selection actions dialog.
PiRemote.files_raise_add_dialog = ->
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
        ['append-items-other', 'Append Selection to another Playlist']
        ]
    for elem in items
        navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', elem[0])
            .html(elem[1])

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.do_files_action $(this).data('action')
        return

    $('#modalSmall').modal('show')
    return


# Callback if span pressed in dir or file dialog.
# Invoke playlist actions via PiRemote.pl_action().
PiRemote.do_files_action = (action, item=null, type='file') ->
    
    if action == 'select-all'
        d3.selectAll('tr.selectable').classed('selected', 1)
        $('#modalSmall').modal('hide')
    else if action == 'deselect-all'
        d3.selectAll('tr.selectable').classed('selected', 0)
        $('#modalSmall').modal('hide')
    else if action == 'invert'
        d3.selectAll('tr.selectable').classed('selected', ()-> ! d3.select(this).classed('selected'))
        $('#modalSmall').modal('hide')
    else if action == 'append-item'
        PiRemote.pl_action 'append', '', [item], type
        $('#modalSmall').modal('hide')
    else if action == 'insert-item'
        PiRemote.pl_action 'insert', '', [item], type
        $('#modalSmall').modal('hide')
    else if action == 'append'
        sel = d3.selectAll('tr.'+type+'-item.selected')
        items = sel.data().map((d) -> d[5])
        PiRemote.pl_action action, '', items, type
        sel.classed('selected', 0)
        $('#modalSmall').modal('hide')
    else if action == 'insert'
        sel = d3.selectAll('tr.'+type+'-item.selected')
        items = sel.data().map((d) -> d[5])
        PiRemote.pl_action action, '', items, type
        sel.classed('selected', 0)
        $('#modalSmall').modal('hide')
    else if action == 'append-other'
        PiRemote.pl_append_items_to_playlist [item]
        d3.selectAll('tr.selectable').classed('selected', 0)
    else if action == 'append-items-other'
        sel = d3.selectAll('tr.'+type+'-item.selected')
        items = sel.data().map((d) -> d[5])
        PiRemote.pl_append_items_to_playlist items
        sel.classed('selected', 0)
    else if action == 'seed'
        PiRemote.pl_edit_name = ''
        PiRemote.pl_raise_seed_dialog item
    else if action == 'seed-other'
        PiRemote.pl_action_on_playlists
            title: 'Random Add to Playlist'
            success: (data) ->
                PiRemote.pl_edit_name = data
                PiRemote.pl_raise_seed_dialog item
                return
    return


# put title and rating stars into a div container, float title left, rating right
PiRemote.make_float_rating = (title, rating) ->
    text = '<div class="tfloat"><div class="flleft">'+title+'</div><div class="flright">'
    text += PiRemote.pl_make_ratings(rating)
    text += '</div><div>'
    text
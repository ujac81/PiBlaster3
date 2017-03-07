# browse.coffee -- install callbacks for browse view

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

    return


# (Re)install browse handler on browse items -- needs to be recalled on table rebuild.
PiRemote.install_browse_handlers = ->

    # remove any old handlers
    $('div.browse-list > table > tbody > tr.dir-item').off 'dblclick'
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').off 'click'
    $('div.browse-list > table > tbody > tr.selectable > td.browse-action').off 'click'
    $('div.browse-list > table > tbody > tr.selectable > td > img').off 'click'
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-dir').off 'click'
    $('#trupdir').off 'click'

    # double-click to enter dir
    $('div.browse-list > table > tbody > tr.dir-item').on 'dblclick', (event) ->
        PiRemote.do_browse $(this).data('dirname')
        return

    # single-click on selectable items toggles select
    $('div.browse-list > table > tbody > tr.selectable > td.browse-selectable').on 'click', (event) ->
        $(this).parent().toggleClass 'selected'
        return

    # move up by single-click
    $('#trupdir').on 'click', (event) ->
        PiRemote.do_browse $(this).data('dirname')
        return

    # single click on folder enters folder
    $('div.browse-list > table > tbody > tr.selectable > td.browse-head-dir').on 'click', (event) ->
        PiRemote.do_browse $(this).parent().data('dirname')
        return

    # action triggered
    $('div.browse-list > table > tbody > tr.selectable > td.browse-action').on 'click', (event) ->
        parent = $(this).parent()
        if parent.is('.dir-item')
            PiRemote.raise_dir_dialog parent
        else if parent.is('.file-item')
            PiRemote.raise_file_dialog parent
        else
            console.log 'ACTION ERROR'
            console.log parent

        return

    $('div.browse-list > table > tbody > tr.selectable > td > img').on 'click', (event) ->
        PiRemote.raise_file_dialog $(this).parent().parent()
        return

    return


PiRemote.do_browse = (dirname) ->
    PiRemote.do_ajax_post
        url: 'browse'
        data:
            'dirname': dirname
        success: (data) ->
            PiRemote.rebuild_browse data
            return
    return


PiRemote.rebuild_browse = (data) ->
    tbody = d3.select('tbody#browse')
    tbody.selectAll('tr').remove()

    up_span = '<span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span>'
    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    if data.dirname != ''
        updir = data.dirname.split('/').slice(0, -1).join('/')
        uptr = tbody.append('tr').classed('dir-item', 1).attr('data-dirname', updir).attr('id', 'trupdir')
        uptr.append('td').classed('browse-head', 1).html(up_span)
        dirname = '/'+data.dirname+'/../'
        uptr.append('td').classed('browse-file', 1).html(dirname.replace(/\//g, ' / '))
        uptr.append('td').classed('browse-action', 1)

    dirs = data.browse.filter (d) -> d[0] == '1'

    tbody.selectAll('tr')
        .data(dirs, (d) -> d).enter()
        .append('tr')
            .attr('class', 'dir-item selectable')
            .attr('data-dirname', (d) -> d[5])
        .selectAll('td')
        .data((d, i) -> ['<img src="/static/img/folder-blue.png"/>', d[1], action_span]).enter()
        .append('td')
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-head-dir', (d, i) -> i == 0)
            .classed('browse-dir', (d, i) -> i == 1)
            .classed('browse-selectable', (d, i) -> i == 1)
            .classed('browse-action', (d, i) -> i == 2)
            .html((d) -> d)

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
        .data((d, i) -> ['<img src="/static/img/'+d[6]+'.png"/>', d[1], action_span]).enter()
        .append('td')
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-action', (d, i) -> i == 0)
            .classed('browse-file', (d, i) -> i == 1)
            .classed('browse-selectable', (d, i) -> i == 1)
            .classed('browse-action', (d, i) -> i == 2)
            .html((d) -> d)




    PiRemote.install_browse_handlers()
    window.scrollTo 0, 0

    return


# Action glyph pressed on file item.
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


# Action glyph pressed on dir item.
PiRemote.raise_dir_dialog = (element) ->
    d3.select('#smallModalLabel').html('Directory')
    cont = d3.select('#smallModalMessage')
    cont.html('')
    dirs = element.data('dirname').split('/')
    p = cont.append('p')
    full_path = ''
    for dir in dirs
        p.append('span').attr('class', 'browse-arrow glyphicon glyphicon-arrow-right')
        p.append('span')
            .attr('class', 'browse-span')
            .attr('data-dirname', full_path+dir)
            .html(dir)
        full_path += dir + '/'


    $('#modalSmall').modal()
    return

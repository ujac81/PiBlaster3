# browse.coffee -- install callbacks for browse view


# (Re)install browse handler on browse items -- needs to be recalled on table rebuild.
PiRemote.install_browse_handlers = ->

    # remove any old handlers
    $('div.browse-list > table > tbody > tr.dir-item').off 'dblclick'

    # double-click to enter dir
    $('div.browse-list > table > tbody > tr.dir-item').on 'dblclick', (event) ->
        event.preventDefault()
        dirname = $(this).data('dirname')
        PiRemote.do_browse dirname
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

    if data.dirname != ''
        updir = data.dirname.split('/').slice(0, -1).join('/')
        uptr = tbody.append('tr').classed('dir-item', 1).attr('data-dirname', updir)
        uptr.append('td')
        uptr.append('td').html('..')

    dirs = data.browse.filter (d) -> d[0] == '1'

    tbody.selectAll('tr')
        .data(dirs, (d) -> d).enter()
        .append('tr').classed('dir-item', 1).attr('data-dirname', (d) -> d[5])
        .selectAll('td')
        .data((d, i) -> ['<img src="/static/img/folder-blue.png"/>', d[1]]).enter()
        .append('td')
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-dir', (d, i) -> i == 1)
            .html((d) -> d)

    files = data.browse.filter (d) -> d[0] == '2'
    tbody.selectAll('tr')
        .data(files, (d) -> d).enter()
        .append('tr').classed('file-item', 1).attr('data-filename', (d) -> d[5])
        .selectAll('td')
        .data((d, i) -> ['<img src="/static/img/'+d[6]+'.png"/>', d[1]]).enter()
        .append('td')
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-file', (d, i) -> i == 1)
            .html((d) -> d)




    PiRemote.install_browse_handlers()
    window.scrollTo 0, 0

    return
# browse.coffee -- install callbacks for browse view


# (Re)install browse handler on browse items -- needs to be recalled on table rebuild.
PiRemote.install_browse_handlers = ->

    # remove any old handlers
    $('div.browse-list > table > tbody > tr.dir-item').off 'dblclick'

    # double-click to enter dir
    $('div.browse-list > table > tbody > tr.dir-item').on 'dblclick', (event) ->
        PiRemote.browse_dir $(this), event
        return

    return


# On double click on tr.dir-item
PiRemote.browse_dir = (element, event) ->
    event.preventDefault()
    PiRemote.do_ajax_post
        url: 'browse'
        data: 'dirname': element.data().dirname
        success: (data) ->
            PiRemote.rebuild_browse data
            return



    return


PiRemote.rebuild_browse = (data) ->
    tbody = d3.select('tbody#browse')

    dirs = data.browse.filter (d) -> d[0] == '1'

    tbody.selectAll('tr')
        .remove()
        .data(dirs, (d) -> d).enter()
        .append('tr').classed('dir-item', 1).attr('data-dirname', (d) -> d[5])
        .selectAll('td')
        .data((d, i) -> ['<img src="/static/img/folder-blue.png" />', d[1]]).enter()
        .append('td').classed('browse-head', (d, i) -> i == 0).html((d) -> d)





    PiRemote.install_browse_handlers()

    return
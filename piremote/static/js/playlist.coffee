# playlist.coffee -- install callbacks for playlist view

# Build browse page
PiRemote.load_playlist_page = ->

    root = d3.select('.piremote-content')
    console.log root
    bl = root.append('div').attr('class', 'play-list')
    tb = bl.append('table').attr('id', 'tbpl').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'pl')

    PiRemote.install_pl_actions()
    PiRemote.get_playlist()
    return


PiRemote.install_pl_actions = ->

    PiRemote.install_pl_handlers()

    return


PiRemote.install_pl_handlers = ->

    return



PiRemote.get_playlist = ->
    PiRemote.do_ajax
        url: 'plinfo'
        method: 'GET'
        data: {}
        success: (data) ->
            PiRemote.rebuild_playlist data
            return
    return


PiRemote.rebuild_playlist = (data) ->

    tbody = d3.select('tbody#pl')
    tbody.selectAll('tr').remove()

    tb_data = []
    for elem in data.pl
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

    no_text = '' + tb_data.length
    no_width = no_text.width('large')+20
    time_width = '000:00'.width('large')+20


    tbody
        .selectAll('tr')
        .data(tb_data, (d) -> d).enter()
        .append('tr')
            .attr('data-id', (d) -> d[0])
            .attr('class', 'selectable')
        .selectAll('td')
        .data((d)->[d[1]]).enter()
        .append('td')
            .attr('class', 'pltdmain')
        .selectAll('table')
        .data((d)->[d]).enter()
        .append('table')
            .attr('class', 'pltbsub')
        .selectAll('tr')
        .data((d)->d).enter()
        .append('tr')
        .attr('class', (d, i) -> 'pltr-'+i)
        .selectAll('td')
        .data((d)->d).enter()
        .append('td')
            .attr('class', (d, i) -> 'pltd-'+i)
            .attr('style', (d, i) ->
                if i == 0
                    return 'width: '+no_width+'px;'
                if i == 2
                    return 'width: '+time_width+'px;'
                if i == 3
                    return 'width: 20px;'
                return 'max-width: 100%;')
            .attr('rowspan', (d, i) ->
                if i == 3
                    return '2'
                return '1')
            .html((d)->d)


    return
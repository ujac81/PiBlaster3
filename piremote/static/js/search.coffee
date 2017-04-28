# search.coffee -- provide search view functions

# Build search page.
# Loaded via PiRemote.load_page('search') every time 'Search' is selected in menu
PiRemote.load_search_page = ->
    PiRemote.show_search_header (pattern) ->
        PiRemote.last_search = pattern
        PiRemote.do_ajax
            url: 'search'
            method: 'POST'
            data:
                pattern: pattern
            success: (data) ->
                PiRemote.search_rebuild data  # <-- rebuild table callback
                return
        return
        
    root = d3.select('.piremote-content')
    bl = root.append('div').attr('id', 'search-list')
    tb = bl.append('table').attr('id', 'tbsearch').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'search')

    PiRemote.search_rebuild PiRemote.last_search_data
    return

    
# Callback for AJAX POST on /piremote/ajax/search.
# Rebuild results table
PiRemote.search_rebuild = (data) ->

    $('#addsign').hide()

    PiRemote.last_search_data = data

    # no search result so far
    return if data.status_str is `undefined` and data.error_str is `undefined`

    tbody = d3.select('tbody#search')
    tbody.selectAll('tr').remove()

    if data.error_str
        tbody.append('tr').append('td').html(data.error_str)
        return

    if data.search isnt `undefined` and data.search.length == 0
        tbody.append('tr').append('td').html(data.status_str)
        return

    # Rebuild results table

    # calculate cell widths for number and time.
    # Set fixed cell widths later to avoid misaligned right borders of number column.
    no_text = '' + data.search.length
    no_width = no_text.width('large')+20
    time_width = '000:00'.width('large')+20

    # action element in last cell of first row in sub table
    span_item = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    # items: [title, artist, album, length, filename]
    mainrows = tbody.selectAll('tr.mainrow').data(data.search)
    maincells = mainrows.enter().append('tr')
        .attr('data-filename', (d)->d[5])
        .attr('data-title', (d)->d[0])
        .attr('class', 'mainrow selectable file-item')
        .selectAll('td.searchtdmain').data((d) -> [d])

    subtables = maincells.enter().append('td').attr('class', 'searchtdmain')
        .selectAll('table.searchtbsub').data((d) -> [d])

    subrows = subtables.enter().append('table').attr('class', 'searchtbsub')
        .selectAll('tr').data((d, i) -> [[i+1, d[0], d[3], span_item], ['', d[1]+' - '+d[2], PiRemote.pl_make_ratings(d[6])]])

    subcells = subrows.enter().append('tr').attr('class', (d, i) -> 'searchtr-'+i)
        .selectAll('td').data((d)->d)

    subcell = subcells.enter().append('td')
        .attr('class', (d, i) -> 'searchtd-'+i)
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
        .classed('search-action', (d, i) -> i ==3)
        .classed('selectable', (d, i) -> i != 3 and i != 0)
        .html((d)->d)

    $('#addsign').show()
    $('#addsign').off 'click'
    $('#addsign').on 'click', ->
        # browse actions are identical
        PiRemote.files_raise_add_dialog()
        return

    # single-click on selectable items toggles select
    $('table#tbsearch > tbody > tr.selectable > td > table > tr > td.selectable').on 'click', (event) ->
        $(this).parent().parent().parent().parent().toggleClass 'selected'
        return

    # single click on action raises action dialog
    $('td.search-action').on 'click', (event) ->
        e =  $(this).parent().parent().parent().parent()
        PiRemote.raise_file_actions e.data('title'), e.data('filename')
        return

    # single click on index column raises info dialog
    $('td.searchtd-0').on 'click', (event) ->
        file = $(this).parent().parent().parent().parent().data('filename')
        PiRemote.search_raise_info_dialog file
        return

    return


# Callback for click in index column.
# AJAX GET of file info and display of song information.
# Also used by playlist and browse.
PiRemote.search_raise_info_dialog = (file) ->
    PiRemote.do_ajax
        url: 'fileinfo'
        method: 'GET'
        data:
            file: file
        success: (data) ->
            if data.info isnt `undefined` and data.info.length > 0 and data.info[0].file isnt `undefined`
                info = data.info[0]

                d3.select('#smallModalLabel').html('File Info')
                cont = d3.select('#smallModalMessage')
                cont.html('')
                p = cont.append('p')

                for item in ['Title', 'Artist', 'Album', 'Track', 'Time', 'Date', 'Genre']
                    res = info[item.toLowerCase()]
                    if res isnt `undefined` and res.length > 0
                        if item == 'Time'
                            res = PiRemote.secToMin res
                        p.append('strong').html(item+': ')
                        p.append('span').html(res)
                        p.append('br')

                # show rating
                p.append('strong').html('Rating: ')
                idxrate = p.append('span').attr('class', 'idxrate')
                idxrate.append('span').attr('class', 'norate')
                for i in [1..5]
                    idxrate.append('span')
                        .attr('class', 'ratespan glyphicon')
                        .attr('data-idx', i)
                        .classed('glyphicon-star-empty', i > info.rating)
                        .classed('glyphicon-star', i <= info.rating)
                idxrate.append('span').attr('class', 'norate')
                p.append('br')

                # rate song
                $('span.idxrate span').on 'click', (event) ->
                    rate = 0
                    if $(this).hasClass('ratespan')
                        rate = $(this).data('idx')
                    PiRemote.do_ajax
                        url: 'rate'
                        method: 'POST'
                        data:
                            filename: info.file
                            rating: rate
                            success: (data) ->
                                PiRemote.index_set_rating 'span.idxrate', rate
                                return
                    return

                # show filename and parent dirs
                filename = info.file.split('/').slice(-1)[0]
                dirs = info.file.split('/').slice(0, -1)

                p.append('strong').html('Filename: ')
                p.append('span').html(filename)
                p.append('br')
                p.append('strong').html('Folder: ')
                p.append('br')

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
                $(document).on 'click', 'span.browse-span', () ->
                    $('#modalSmall').modal('hide')
                    PiRemote.last_files = $(this).data('dirname')
                    PiRemote.load_page 'files'
                    return

                p = cont.append('p')
                audio = p.append('audio').attr('controls', 'controls')
                audio.append('source').attr('src', '/music/'+file)

                $('#modalSmall').modal()
                PiRemote.index_set_rating 'span.idxrate', info.rating
            else
                PiRemote.error_message 'File not found', 'File info for this file cannot be found. Maybe the file was removed. Full path was: '+file
            return
    return
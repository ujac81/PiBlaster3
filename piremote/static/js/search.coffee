# search.coffee -- provide search view functions

# Build search page.
# Loaded via PiRemote.load_page('search') every time 'Search' is selected in menu
PiRemote.load_search_page = ->

    $('body').addClass 'search'

    root = d3.select('.piremote-content')

    dsearch = root.append('div').attr('id', 'searchbardiv')

    trsearch = dsearch
        .append('table').attr('id', 'searchbar').attr('class', 'table')
        .append('tr').attr('id', 'searchbartr')
    trsearch
        .append('td').attr('id', 'searchbarlabel').html('Search:')
    trsearch
        .append('td').attr('id', 'searchbarinput')
        .append('input').attr('type', 'text').attr('id', 'searchfield').attr('placeholder', PiRemote.last_search)
    trsearch
        .append('td').attr('id', 'searchbarbutton')
        .append('button').attr('type', 'submit').attr('class', 'btn btn-default').attr('id', 'gosearch').html('Go')


    bl = root.append('div').attr('id', 'search-list')
    tb = bl.append('table').attr('id', 'tbsearch').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'search')

    $('button#gosearch').off 'click'
    $('button#gosearch').on 'click', ->
        PiRemote.do_search $('input#searchfield').val()
        return


    PiRemote.search_rebuild PiRemote.last_search_data

    return


# Perform search via AJAX POST
PiRemote.do_search = (pattern) ->

    PiRemote.last_search = pattern

    PiRemote.do_ajax
        url: 'search'
        method: 'POST'
        data:
            'pattern': pattern
        success: (data) ->
            PiRemote.search_rebuild data  # <-- rebuild table callback
            return
    return

# Callback for AJAX POST on /piremote/ajax/search.
# Rebuild results table
PiRemote.search_rebuild = (data) ->

    $('#addsign').hide()

    PiRemote.last_search_data = data

    # no search result so far
    return if data.status is `undefined` and data.error is `undefined`

    tbody = d3.select('tbody#search')
    tbody.selectAll('tr').remove()

    if data.error
        tbody.append('tr').append('td').html(data.error)
        return

    if data.search isnt `undefined` and data.search.length == 0
        tbody.append('tr').append('td').html(data.status)
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
        .selectAll('td.searchtdmain').data((d)->[d])

    subtables = maincells.enter().append('td').attr('class', 'searchtdmain')
        .selectAll('table.searchtbsub').data((d)->[d])

    subrows = subtables.enter().append('table').attr('class', 'searchtbsub')
        .selectAll('tr').data((d, i)->[[i+1, d[0], d[3], span_item], ['', d[1]+' - '+d[2], '']])

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
        PiRemote.search_raise_add_dialog()
        return

    PiRemote.install_search_handlers()

    return

# (Re)install event handlers for items in search list
PiRemote.install_search_handlers = ->

    # single-click on selectable items toggles select
    $('table#tbsearch > tbody > tr.selectable > td > table > tr > td.selectable').off 'click'
    $('table#tbsearch > tbody > tr.selectable > td > table > tr > td.selectable').on 'click', (event) ->
        $(this).parent().parent().parent().parent().toggleClass 'selected'
        return

    # single click on action raises action dialog
    $('td.search-action').off 'click'
    $('td.search-action').on 'click', (event) ->
        PiRemote.search_raise_action_dialog $(this).parent().parent().parent().parent()
        return


    # single click on index column raises info dialog
    $('td.searchtd-0').off 'click'
    $('td.searchtd-0').on 'click', (event) ->
        file = $(this).parent().parent().parent().parent().data('filename')
        PiRemote.search_raise_info_dialog file
        return


    return


# Callback for add sign.
PiRemote.search_raise_add_dialog = ->
    # browse actions are identical
    PiRemote.browse_raise_add_dialog()
    return


# Callback for action dots clicked.
PiRemote.search_raise_action_dialog = (element) ->
    # browse actions are identical
    PiRemote.raise_file_actions element
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
                $(document).off 'click', 'span.browse-span'
                $(document).on 'click', 'span.browse-span', () ->
                    $('#modalSmall').modal('hide')
                    PiRemote.last_browse = $(this).data('dirname')
                    PiRemote.load_page 'browse'
                    return

                $('#modalSmall').modal()
            return
    return
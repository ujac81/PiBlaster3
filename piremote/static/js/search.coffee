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
        .attr('data-filename', (d)->d[4])
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
        .classed('selectable', (d, i) -> i != 3)
        .html((d)->d)



    return


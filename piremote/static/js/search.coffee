# search.coffee -- provide search view functions

# Build search page.
# Loaded via PiRemote.load_page('search') every time 'Search' is selected in menu
PiRemote.load_search_page = ->

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

    console.log data

    return


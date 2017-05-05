# history.coffee -- browse history table

# build page for history browsing
PiRemote.load_history_page = ->

    # Back button should always return to browse dates mode.
    PiRemote.add_navbar_button 'home', 'chevron-left', true
    PiRemote.add_navbar_button 'history_search', 'search', true
    
    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'hist-list')
    tb = bl.append('table').attr('id', 'tbhist').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'hist')

    if PiRemote.current_sub_page == 'history_search'
        PiRemote.show_search_header (pattern) ->
            PiRemote.do_history 'search', pattern
            return
    else
        # Start with browsing dates.
        PiRemote.do_history 'dates'
    return


# Invoke AJAX GET of history data.
PiRemote.do_history = (mode, pattern='') ->
    PiRemote.do_ajax
        url: 'history'
        method: 'GET'
        data:
            mode: mode
            pattern: pattern
        success: (data) ->
            PiRemote.hist_update_table data
            return
    return


# Callback for retrieved history data.
PiRemote.hist_update_table = (data) ->

    $('h3#heading').html(data.title).show()
    # clean table
    tbody = d3.select('tbody#hist')
    tbody.selectAll('tr').remove()
    
    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    if data.mode == 'dates'
        # List plain dates and retrieve per date information if any date clicked.
        d3.select('tbody#hist').selectAll('tr')
            .data(data.history, (d) -> d).enter()
            .append('tr')
            .attr('class', 'file-item histitem histdate')
            .attr('data-mode', (d) -> d[0])
            .selectAll('td')
            .data((d, i) -> [i+1, d[1], action_span]).enter()
            .append('td')
                .attr('class', (d, i) -> 'hist-td'+i)
                .html((d) -> d)

        $('div.hist-list > table > tbody > tr.histdate > td.hist-td1').on 'click', (event) ->
            PiRemote.hist_raise_date_actions $(this).parent().data('mode')
            return
            
        $('div.hist-list > table > tbody > tr.histdate > td.hist-td2').on 'click', (event) ->
            PiRemote.hist_raise_date_actions $(this).parent().data('mode')
            return

        $('#addsign').hide()
    else
        # Build history data for specific date.

        d3.select('tbody#hist').selectAll('tr')
            .data(data.history, (d) -> d).enter()
            .append('tr')
            .attr('class', 'file-item selectable histitem')
            .attr('data-title', (d) -> d[1])
            .attr('data-file', (d) -> d[5])
            .selectAll('td')
            .data((d) -> [d[0], d[1], action_span]).enter()
            .append('td')
                .attr('class', (d, i) -> 'hist-td'+i)
                .html((d) -> d)

        # click on first to columns should raise file info
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td0').on 'click', (event) ->
            PiRemote.search_raise_info_dialog $(this).parent().data('file')
            return

        # click on title should select
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td1').on 'click', (event) ->
            $(this).parent().toggleClass 'selected'
            return

        # click on action column should raise add/insert dialog
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td2').on 'click', (event) ->
            PiRemote.raise_file_actions $(this).parent().data('title'), $(this).parent().data('file')
            return

        $('#addsign').show()
        $('#addsign').off 'click'
        $('#addsign').on 'click', ->
            # browse actions are identical
            PiRemote.files_raise_add_dialog()
            return

    return

    
# Action dots clicked on history date
PiRemote.hist_raise_date_actions = (date) ->
    
    d3.select('#smallModalLabel').html('History actions for '+date)
    cont = d3.select('#smallModalMessage')
    cont.html('')
    
    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    navul.append('li').attr('role', 'presentation')
        .append('span').attr('class', 'browse-action-file')
        .attr('data-action', 'download').html('Download as playlist')
    navul.append('li').attr('role', 'presentation')
        .append('span').attr('class', 'browse-action-file')
        .attr('data-action', 'saveas').html('Save as playlist')
    
    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        action = $(this).data('action')
        if action == 'download'
            PiRemote.do_download_as_text
                url: 'download/playlist'
                data:
                    source: 'history'
                    name: date
                filename: date+'.m3u'
            $('#modalSmall').modal('hide')
        else if action == 'saveas'
            PiRemote.do_ajax
                url: 'download/playlist'
                method: 'GET'
                data:
                    source: 'history'
                    name: date
                success: (data) ->
                    if data.data.length == 0
                        PiRemote.setErrorText 'Not saving empty playlist!'
                    else
                        items = [i.replace(data.prefix+'/', '') for i in data.data]
                        PiRemote.pl_append_items_to_playlist items[0]
                    return
        return
        
    $('#modalSmall').modal('show')
    return
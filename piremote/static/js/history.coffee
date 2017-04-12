# history.coffee -- browse history table

# build page for history browsing
PiRemote.load_history_page = ->

    # Back button should always return to browse dates mode.
    PiRemote.add_navbar_button 'browse_left', 'chevron-left', true, false
    $('button#navbutton_browse_left').off 'click'
    $('button#navbutton_browse_left').on 'click', ->
        PiRemote.do_history 'dates'
        return

    root = d3.select('.piremote-content')
    bl = root.append('div').attr('class', 'hist-list')
    bl.append('h3').attr('id', 'hist-head')
    tb = bl.append('table').attr('id', 'tbhist').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'hist')

    # Start with browsing dates.
    PiRemote.do_history 'dates'
    return


# Invoke AJAX GET of history data.
PiRemote.do_history = (mode) ->
    PiRemote.do_ajax
            url: 'history'
            method: 'GET'
            data:
                mode: mode
            success: (data) ->
                PiRemote.hist_update_table data
                return
    return


# Callback for retrieved history data.
PiRemote.hist_update_table = (data) ->

    d3.select('h3#hist-head').html(data.title)
    # clean table
    tbody = d3.select('tbody#hist')
    tbody.selectAll('tr').remove()

    if data.mode == 'dates'
        # List plain dates and retrieve per date information if any date clicked.
        d3.select('tbody#hist').selectAll('tr')
            .data(data.history, (d) -> d).enter()
            .append('tr')
            .attr('class', 'histdate')
            .attr('data-mode', (d) -> d[0])
            .selectAll('td')
            .data((d) -> [d[1]]).enter()
            .append('td')
                .attr('class', 'hist-td1')
                .html((d) -> d)

        $('div.hist-list > table > tbody > tr.histdate').off 'click'
        $('div.hist-list > table > tbody > tr.histdate').on 'click', (event) ->
            PiRemote.do_history $(this).data('mode')
            return

        $('#addsign').hide()
    else
        # Build history data for specific date.

        action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

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
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td0').off 'click'
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td0').on 'click', (event) ->
            PiRemote.search_raise_info_dialog $(this).parent().data('file')
            return

        # click on title should select
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td1').off 'click'
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td1').on 'click', (event) ->
            $(this).parent().toggleClass 'selected'
            return

        # click on action column should raise add/insert dialog
        $('div.hist-list > table > tbody > tr.histitem > td.hist-td2').off 'click'
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


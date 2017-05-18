# smart.coffee -- build "Smart Playlists" page and install actions.


# Load list of smart playlists and build it.
PiRemote.load_smart_playlist_page = ->
    
    PiRemote.add_navbar_button 'home', 'home', true
    btn_new = PiRemote.add_navbar_button 'new_file', 'file', true, false
    btn_up = PiRemote.add_navbar_button 'up_upload_file', 'upload', true, false
    btn_new.on 'click', ->
        PiRemote.smart_pl_new()
        return
    btn_up.on 'click', ->
        PiRemote.smart_upload_filter()
        return
        
    if PiRemote.upload_message
        if PiRemote.upload_message.error_str
            d3.select('#smallModalLabel').html('Upload Error')
            cont = d3.select('#smallModalMessage').html('').append('p').attr('class', 'error').html(PiRemote.upload_message.error_str)
        if PiRemote.upload_message.status_str
            d3.select('#smallModalLabel').html('File Uploaded')
            cont = d3.select('#smallModalMessage').html('').append('p').html(PiRemote.upload_message.status_str)

        $('#modalSmall').modal('show')
        PiRemote.upload_message = `undefined`
    
    PiRemote.smart_pl_rebuild_list()
    return
    
    
# Receive list of smart playlists and redraw table.
PiRemote.smart_pl_rebuild_list = ->
    PiRemote.do_ajax
        method: 'GET'
        url: 'list/smart_playlists'
        success: (data) ->
            # list of smart playlists gets available choices/genres/artists/etc
            PiRemote.smart_pl_list_data = data
            if data.data
                PiRemote.smart_pl_build_list data.data
    return
    
    
# Display list of smart playlists and connect actions.
PiRemote.smart_pl_build_list = (data) ->
    $('h3#heading').html('List of smart playlists').show()
    
    root = d3.select('.piremote-content')
    root.html('')
    bl = root.append('div').attr('class', 'play-list')
    tb = bl.append('table').attr('id', 'tbpls').attr('class', 'table table-striped')
    tbody = tb.append('tbody').attr('id', 'pls')
    
    tbody.selectAll('tr').data(data).enter()
        .append('tr')
            .attr('class', 'pls-item')
            .attr('data-id', (d)->d[0])
            .attr('data-plname', (d)->d[1])
            .selectAll('td')
            .data((d,i) -> [i+1, d[1], PiRemote.action_span])
            .enter()
        .append('td')
            .attr('class', (d,i)-> 'pls-col-'+i)
            .html((d)->d)
    
    $('td.pls-col-1').on 'click', ->
        pl = $(this).parent().data('plname')
        id = $(this).parent().data('id')
        PiRemote.smart_pl_load_smart_pl pl, id
        return
    
    $('td.pls-col-2').on 'click', ->
        pl = $(this).parent().data('plname')
        id = $(this).parent().data('id')
        PiRemote.smart_pl_raise_smart_pl_actions pl, id
        return
       
    return
    

# Raise the playlist save dialog and save playlist as name set
PiRemote.smart_pl_new = (title='New smart playlist', text='Enter name for playlist', action='create', id=0)->

    d3.select('#smallModalLabel').html(title)
    cont = d3.select('#smallModalMessage')
    cont.html('')
    cont.append('p').html(text)

    trsave = cont
        .append('table').attr('id', 'savebar').attr('class', 'table')
        .append('tr').attr('id', 'savebartr')
    trsave
        .append('td').attr('id', 'savebarinput')
        .append('input').attr('type', 'text').attr('id', 'savefield').attr('placeholder', 'my playlist').attr('pattern', '[a-zA-Z0-9_\\- ]+')
    trsave
        .append('td').attr('id', 'savebarbutton')
        .append('button').attr('type', 'submit').attr('class', 'btn btn-default').attr('id', 'gosave').html('Create')

    $('button#gosave').on 'click', ->
        if $('input#savefield').val().length > 0
            PiRemote.do_ajax
                method: 'POST'
                url: 'smartpl/'+action
                data:
                    id: id
                    name: $('input#savefield').val()
                success: (data) ->
                    if data.name
                        PiRemote.smart_pl_load_smart_pl data.name
                    else
                        PiRemote.smart_pl_rebuild_list()
                    $('#modalSmall').modal('hide')
                    return
        return

    $('#modalSmall').modal('show')
    return
  

# Load smart playlist filters for name/id of smart playlist.
PiRemote.smart_pl_load_smart_pl = (name, id) ->
    PiRemote.do_ajax
        method: 'GET'
        url: 'list/smart_playlist'
        data:
            id: id
        success: (data) ->
            if data.data
                PiRemote.smart_pl_build name, id, data
            return
    return
    
    
# Build list with filters from smart playlist filter listing.
PiRemote.smart_pl_build = (name, id, data) ->
    $('h3#heading').html(name).show()
    root = d3.select('.piremote-content')
    root.html('')
    
    PiRemote.last_smart_pl_name = name
    PiRemote.last_smart_pl_id = id
    PiRemote.last_smart_pl_data = data
    
    # list of filters
    divseed = root.append('div').attr('id', 'smartseed')
    
    divfilt = root.append('div').attr('id', 'smartfilt')
    divfilt.selectAll('p').data(data.data).enter()
        .append('p')
        .attr('class', 'smartp')
        .attr('data-pos', (d)->d[4])
        .attr('data-idx', (d, i)->i)
        .each((d, i) -> PiRemote.pl_smart_update_filter(d, i))
        
    divadd = root.append('div').attr('id', 'smartadd')
    padd = divadd.append('p')
    upspan = padd.append('span').attr('class', 'glyphicon glyphicon-circle-arrow-up')
    downspan = padd.append('span').attr('class', 'glyphicon glyphicon-circle-arrow-down')
    minusspan = padd.append('span').attr('class', 'glyphicon glyphicon-minus-sign')
    plusspan = padd.append('span').attr('class', 'glyphicon glyphicon-plus-sign')
    divempty = root.append('div').attr('id', 'smartempty')
    divempty.append('p').attr('id', 'empty')
    
    pseed = divseed.append('p')
    input = pseed.append('span').append('input')
        .attr('type', 'number').attr('min', '10').attr('max', '1000').attr('value', '50')
        .attr('id', 'seedspin').attr('class', 'spin')
    seedcur = pseed.append('span')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary').html('Add')
    seedother = pseed.append('span')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary').html('Add to other')
    
    # move up
    upspan.on 'click', ->
        data = d3.select('p.smartp.selected').data()
        if data.length > 0
            PiRemote.smart_pl_do_action
                id: data[0][5]
                action: 'upitem'
        return
        
    # move down
    downspan.on 'click', ->
        data = d3.select('p.smartp.selected').data()
        if data.length > 0
            PiRemote.smart_pl_do_action
                id: data[0][5]
                action: 'downitem'
        return
    
    # remove filter item on '-' click
    minusspan.on 'click', ->
        data = d3.select('p.smartp.selected').data()
        if data.length > 0
            PiRemote.smart_pl_do_action
                id: data[0][5]
                action: 'rmitem'
        return
    
    # add new filter on '+' click and reload
    plusspan.on 'click', ->
        PiRemote.smart_pl_do_action
            id: id
            action: 'new'
        return
        
    # click on p item (de)selects
    $('p.smartp').on 'click', ->
        is_selected = $(this).hasClass('selected')
        d3.selectAll('p.smartp').classed('selected', false)
        $(this).toggleClass('selected', ! is_selected)
        return
        
    # Seed to current
    seedcur.on 'click', ->
        PiRemote.smart_pl_do_action
            action: 'apply'
            id: id
            data:
                count: $('input#seedspin')[0].value
                playlist: ''
        return
        
    # Seed to other playlist
    seedother.on 'click', ->
        PiRemote.pl_action_on_playlists
            title: 'Choose Playlist for Seeding'
            success: (data) ->
                PiRemote.smart_pl_do_action
                    action: 'apply'
                    id: id
                    data:
                        count: $('input#seedspin')[0].value
                        playlist: data
                $('#modalSmall').modal('hide')
                return
        return
    return
        
    
# Action dots pressed on smart playlist in list of smart playlists
PiRemote.smart_pl_raise_smart_pl_actions = (name, id) ->
    
    title = 'Smart Playlist Action'
    text = 'Smart Playlist <strong>'+name+'</strong> actions:'
    items = [
        ['rename', 'Rename'],
        ['rm', 'Remove'],
        ['clone', 'Duplicate'],
        ['download', 'Download']
        ]
    PiRemote.raise_selection_dialog title, text, items
    
    $(document).on 'click', 'span.browse-action-file', () ->
        action = $(this).data('action')
        if action == 'rename'
            PiRemote.smart_pl_new 'Rename Smart Playlist', 'Enter new name', 'rename', id
        else if action == 'rm'
            PiRemote.confirm_dialog
                title: 'Remove Smart Playlist '+name+'?'
                requirepw: 1
                confirmed: ->
                    PiRemote.do_ajax
                        method: 'POST'
                        url: 'smartpl/rm'
                        data:
                            name: name
                            id: id
                        success: (data) ->
                            PiRemote.smart_pl_rebuild_list()
                            return
                    $('#modalSmall').modal('hide')
                    return
        else if action == 'clone'
            PiRemote.do_ajax
                method: 'POST'
                url: 'smartpl/clone'
                data:
                    id: id
                success: (data) ->
                    PiRemote.smart_pl_rebuild_list()
                    return
            $('#modalSmall').modal('hide')
        else if action == 'download'
            PiRemote.do_download_as_text
                url: 'download/smartpl/'+id
                filename: name+'.json'
        return
    return
    

# AJAX POST to smartplaction/FILTER_ID/ACTION.
# Will reload whole filter set if reload flag set in result.
PiRemote.smart_pl_do_action = (req) ->
    PiRemote.do_ajax
        method: 'POST'
        url: 'smartplaction/'+req.id+'/'+req.action
        data: req.data
        success: (data) ->
            if data.success and req.success
                req.success data
            if data.reload
                PiRemote.smart_pl_load_smart_pl PiRemote.last_smart_pl_name, PiRemote.last_smart_pl_id
            return
    return
    

# Called after creation of filter <p> element to fill in filter contents.
# :param data: data from SmartPlaylistItem.get_by_id
# :param index: index in p-list and data array -- NOT item index in database !!!
PiRemote.pl_smart_update_filter = (data, index) ->
    p = d3.select('p[data-idx="'+index+'"]')
    p.html('')
    
    payload = data[2]
    payloads = data[6]
    filter_id = data[5]  # id in smart playlist item table <-- use this for filter modification!
    is_negate = data[3]
    weight = data[1] * 100  # [0..1] --> need percentage
    
    sel = p.append('select').attr('data-idx', index)
    sel.selectAll('option').data(PiRemote.smart_pl_list_data.choices).enter()
        .append('option')
        .attr('value', (d)->d[0])
        .html((d)->d[1])
    
    sel.selectAll('option').attr('selected', null)
    sel.selectAll('option[value="'+data[0]+'"]').attr('selected', 'true')
    sel.on 'change', (d) ->
        d3.event.stopPropagation()
        PiRemote.smart_pl_do_action
            id: d[5]
            action: 'itemtype'
            data:
                type: $(this)[0].value
        return
    sel.on 'click', ->
        d3.event.stopPropagation()
        return
    sel.on 'mousedown', ->
        d3.event.stopPropagation()
        return
    
    # Show negate switch for filters where it makes sense
    if data[0] in [1, 2, 3, 4, 5]
        p.append('label').attr('for', 'checkbox-'+filter_id).html('Negate')
        check = p.append('input').attr('type', 'checkbox').attr('name', 'checkbox-'+filter_id).attr('class', 'checkbox')
        check.attr('checked', 'true') if is_negate
        check.on 'click', ->
            d3.event.stopPropagation()
            PiRemote.smart_pl_do_action
                id: filter_id
                action: 'negate'
                data:
                    negate: if $(this).is(':checked') then '1' else '0'
            return
    p.append('br')
    
    # RATING FIELD
    if data[0] == 1 or data[0] == 2
        cur_rating = 0
        if payload != ''
            cur_rating = parseInt(payload)
        s = p.append('span').attr('class', 'ratings')
        for i in [1..5]
            r = s.append('span').attr('class', 'glyphicon')
                .classed('glyphicon-star', i <= cur_rating)
                .classed('glyphicon-star-empty', i > cur_rating)
                .attr('data-idx', i)
                .attr('data-filtid', filter_id)
            r.on 'click', ->
                d3.event.stopPropagation()
                for j in [1..5]
                    elem = $('span[data-idx="'+j+'"][data-filtid="'+filter_id+'"]')
                    elem.toggleClass('glyphicon-star-empty', j > $(this).data('idx'))
                    elem.toggleClass('glyphicon-star', j <= $(this).data('idx'))
                    
                PiRemote.smart_pl_do_action
                    id: filter_id
                    action: 'setpayload'
                    data:
                        payload: $(this).data('idx')
                return
                
    # multi selection field (table with -/+ signs)
    if data[0] in [3, 4, 5]
        minus_item = '<span class="glyphicon glyphicon-minus-sign"></span>'
        t = p.append('table').attr('class', 'smartfilt table table-striped')
        t.append('tbody').selectAll('tr').data(payloads).enter()
            .append('tr')
            .attr('class', 'smartrow')
            .attr('data-item', (d)->d)
            .selectAll('td').data((d, i)-> [i+1, d, minus_item]).enter()
            .append('td')
            .html((d) -> d)
            .on 'click', (d, i)->
                d3.event.stopPropagation()
                # click on '-' sign removes payload item
                if i == 2
                    item = $(this).parent().data('item')
                    PiRemote.smart_pl_do_action
                        id: filter_id
                        action: 'rmpayload'
                        data:
                            payload: item
                return
        
        # Add append row with + sign -> click on whole row adds
        addrow = t.select('tbody').append('tr').attr('class', 'smartaddrow')
        addrow.append('td').attr('colspan', 2).html('Add selector')
        addrow.append('td').append('span').attr('class', 'glyphicon glyphicon-plus-sign')
        
        addrow.on 'click', ->
            d3.event.stopPropagation()
            if data[0] == 3  # Directory selector
                PiRemote.raise_dir_selector_dialog
                    startdir: ''
                    title: 'Select Directory'
                    button: 'Add'
                    success: (data) ->
                        PiRemote.smart_pl_do_action
                            id: filter_id
                            action: 'addpayload'
                            data:
                                payload: data
                        return
            if data[0] == 4  # Genre selector
                PiRemote.raise_selector_dialog
                    choices: PiRemote.smart_pl_list_data.genres
                    chosen: payloads
                    title: 'Select Genres'
                    button: 'Select'
                    multi: true
                    success: (data) ->
                        PiRemote.smart_pl_do_action
                            id: filter_id
                            action: 'setpayloads'
                            data:
                                payloads: data
                        return
            if data[0] == 5  # Artist selector
                PiRemote.raise_selector_dialog
                    choices: PiRemote.smart_pl_list_data.artists
                    chosen: payloads
                    title: 'Select Artists'
                    button: 'Select'
                    multi: true
                    success: (data) ->
                        PiRemote.smart_pl_do_action
                            id: filter_id
                            action: 'setpayloads'
                            data:
                                payloads: data
                        return
            return
            
    # DATE FIELD
    if data[0] == 6 or data[0] == 7
        cur_date = 'Choose Year'
        if payload != ''
            cur_date = payload
        s = p.append('span').attr('class', 'ratings')
        ss = s.append('span').html(cur_date)
        ss.on 'click', ->
            d3.event.stopPropagation()
            PiRemote.raise_selector_dialog
                    choices: PiRemote.smart_pl_list_data.dates
                    chosen: cur_date
                    title: 'Select Year'
                    button: 'Select'
                    multi: false
                    success: (data) ->
                        if data.length > 0
                            PiRemote.smart_pl_do_action
                                id: filter_id
                                action: 'setpayload'
                                data:
                                    payload: data[0]
                                success: (d) ->
                                    ss.html(data[0])
                                    return
                        return
            return
                
    # WEIGHT
    if data[0] in [1..7]
        p.append('br')
        s = p.append('span').attr('class', 'weightspan')
        s.append('div').attr('class', 'wlabel').html('weight')
        wpos = s.append('div').attr('class', 'weight')
        wfill = wpos.append('div').attr('class', 'weightfill').style('right', (100-weight)+'%')
        wpos.on 'click', ->
            d3.event.stopPropagation()
            pct = (d3.mouse(this)[0])/$(this).width()*100.0
            pct = 0 if pct < 5
            pct = 100 if pct > 95
            pct_set = 100-pct
            pct_set = 0 if pct_set < 0
            pct_set = 100 if pct_set > 100
            wfill.style('right', pct_set+'%')
            PiRemote.smart_pl_do_action
                id: filter_id
                action: 'setweight'
                data:
                    weight: pct/100.0
            return
        
    return
    
    
# Open dialog with directory selector
PiRemote.raise_dir_selector_dialog = (req) ->
    
    d3.select('#smallModalLabel').html(req.title)
    cont = d3.select('#smallModalMessage')
    cont.html('')
    p = cont.append('p')
    t = cont.append('table').attr('class', 'table table-striped').attr('id', 'tbbrowse')
    t.append('tbody').attr('id', 'tbodydirsel')
    
    PiRemote.dir_selector_do_browse req.startdir
    $('#modalSmall').modal('show')
    
    btn = cont.append('p').attr('class', 'confirmbutton')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary')
        .attr('id', 'confirmbutton').html(req.button)
    
    btn.on 'click', ->
        dir = $('tbody#tbodydirsel > tr.selected').data('dirname')
        if dir
            req.success dir
            $('#modalSmall').modal('hide')
        return
    
    return
    

# AJAX get of browse directories -> fill table in directory selector dialog
PiRemote.dir_selector_do_browse = (dir) ->
    PiRemote.do_ajax
        url: 'browse'
        method: 'POST'
        data:
            'dirname': dir
        success: (data) ->
            PiRemote.dir_selector_rebuild data
            return
    return

    
# Build directory table from AJAX result
PiRemote.dir_selector_rebuild = (data) ->
    tbody = d3.select('tbody#tbodydirsel')
    tbody.selectAll('tr').remove()

    # First entry is folder up
    if data.dirname != ''
        up_span = '<span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span>'
        updir = data.dirname.split('/').slice(0, -1).join('/')
        uptr = tbody.append('tr').attr('class', 'dir-item file-view').attr('data-dirname', updir).attr('id', 'trupdir')
        uptr.append('td').classed('browse-head', 1).html(up_span)
        dirname = '/'+data.dirname+'/../'
        uptr.append('td').classed('browse-file', 1).html(dirname.replace(/\//g, ' / '))
        uptr.append('td').classed('browse-action', 1)

    action_span = '<span class="glyphicon glyphicon-chevron-right"></span>'
    dirs = data.browse.filter (d) -> d[0] == '1'
    # Append dirs
    tbody.selectAll('tr')
        .data(dirs, (d) -> d).enter()
        .append('tr')
            .attr('class', 'dir-item file-view')
            .attr('data-dirname', (d) -> d[5])
        .selectAll('td')
        .data((d) -> ['<img src="/piremote/static/img/folder-blue.png"/>', d[1], action_span]).enter()
        .append('td')
            .attr('class', (d, i)-> 'browse-td'+i)
            .classed('browse-head', (d, i) -> i == 0)
            .classed('browse-head-dir', (d, i) -> i == 0)
            .classed('browse-dir', (d, i) -> i == 1)
            .classed('browse-action', (d, i) -> i == 2)
            .html((d) -> d)
    
    # single-click on selectable items toggles select
    $('tbody#tbodydirsel > tr.dir-item > td.browse-dir').on 'click', ->
        d3.select('tbody#tbodydirsel').selectAll('tr').classed('selected', false)
        $(this).parent().toggleClass 'selected', true
        return
        
    # move up by single-click
    $('#trupdir').on 'click', ->
        PiRemote.dir_selector_do_browse $(this).data('dirname')
        return
        
    # single click on folder td enters folder
    $('tbody#tbodydirsel > tr.dir-item > td.browse-head-dir').on 'click', ->
        PiRemote.dir_selector_do_browse $(this).parent().data('dirname')
        return
        
    # single click on chevron td enters folder
    $('tbody#tbodydirsel > tr.dir-item > td.browse-action').on 'click', ->
        PiRemote.dir_selector_do_browse $(this).parent().data('dirname')
        return

        
        
# Open dialog with directory selector
PiRemote.raise_selector_dialog = (req) ->
    
    d3.select('#smallModalLabel').html(req.title)
    cont = d3.select('#smallModalMessage')
    cont.html('')
    p = cont.append('p')
    t = cont.append('table').attr('class', 'table table-striped').attr('id', 'tbchoose')
    tbody = t.append('tbody').attr('id', 'tbodychoose')
    
    tbody.selectAll('tr').data(req.choices).enter()
        .append('tr')
        .attr('class', 'choices')
        .classed('choosen', (d) -> d in req.chosen)
        .selectAll('td').data((d) -> [d]).enter()
        .append('td')
        .html((d)->d)
        .on 'click', (d, i)->
            if not req.multi
                d3.selectAll('tr.choices').classed('choosen', false)
            $(this).parent().toggleClass 'choosen'
            return
    
    btn = cont.append('p').attr('class', 'confirmbutton')
        .append('button').attr('type', 'button').attr('class', 'btn btn-primary')
        .attr('id', 'confirmbutton').html(req.button)
    
    btn.on 'click', ->
        item = d3.selectAll('tr.choices.choosen').data()
        if item
            req.success item
            $('#modalSmall').modal('hide')
        return
        
    $('#modalSmall').modal('show')
    return
    
    
# Upload json file from downloaded filter
PiRemote.smart_upload_filter = ->
    
    d3.select('#smallModalLabel').html('Upload Smart Playlist')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    f = cont.append('form')
        .attr('action', '/piremote/upload/smartpl/')
        .attr('method', 'POST')
        .attr('enctype', 'multipart/form-data')

    f.append('input').attr('type', 'hidden').attr('name', 'csrfmiddlewaretoken').attr('value',$('input[name=csrfmiddlewaretoken')[0].value)
    
    t = f.append('table').attr('class', 'table uptable')
    tr = t.append('tr')
    tr.append('td').attr('class', 'uptext').html('File')
    tr.append('td').attr('colspan', '2').append('p')
        .append('input')
            .attr('type', 'file').attr('name', 'mediafile').attr('accept', 'application/json')

    tr = t.append('tr')
    tr.append('td').attr('class', 'uptext').html('Playlist Name')
    tr.append('td').attr('colspan', '2')
        .append('input')
            .attr('type', 'text').attr('name', 'playlist').attr('placeholder', 'Playlist Name').attr('required', '')

    tr = t.append('tr')
    tr.append('td').attr('class', 'upsubmit').attr('colspan', '3').attr('align', 'center')
        .append('input')
            .attr('type', 'submit').attr('name', 'submit').attr('value', 'Upload')

    $('#modalSmall').modal('show')
    
    return
    
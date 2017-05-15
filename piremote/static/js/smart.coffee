# smart.coffee -- build "Smart Playlists" page and install actions.


# Load list of smart playlists and build it.
PiRemote.load_smart_playlist_page = ->
    
    PiRemote.add_navbar_button 'home', 'home', true
    btn_new = PiRemote.add_navbar_button 'new_file', 'file', true, false
    btn_new.on 'click', ->
        PiRemote.smart_pl_new()
        return
        
    PiRemote.smart_pl_rebuild_list()
    return
    
    
# Receive list of smart playlists and redraw table.
PiRemote.smart_pl_rebuild_list = ->
    PiRemote.do_ajax
        method: 'GET'
        url: 'list/smart_playlists'
        success: (data) ->
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
    
    console.log data
    
    return
    
    
# Action dots pressed on smart playlist in list of smart playlists
PiRemote.smart_pl_raise_smart_pl_actions = (name, id) ->
    
    title = 'Smart Playlist Action'
    text = 'Smart Playlist <strong>'+name+'</strong> actions:'
    items = [
        ['rename', 'Rename'],
        ['rm', 'Remove'],
        ['clone', 'Duplicate'],
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
                    return
            $('#modalSmall').modal('hide')
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
        return

    return
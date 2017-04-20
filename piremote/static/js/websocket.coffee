# websocket.coffee -- Access web sockets for status changes on player.

# Try to connect to websocket.
PiRemote.install_websocket = ->

    addr = 'ws://'+(''+window.location).split('/').slice(2,3)+'/piremote/ws/piremote?subscribe-broadcast'
    PiRemote.socket = new WebSocket(addr)

    # On successful open, disable short polling and invoke client status loop for time bar.
    PiRemote.socket.onopen = ->
        PiRemote.setStatusText 'Websocket opened.'
        PiRemote.use_short_polling = false
        if PiRemote.current_page == 'index' and PiRemote.current_sub_page == 'home'
            PiRemote.index_refresh_status()
        else if PiRemote.current_page == 'playlist' and PiRemote.current_sub_page == 'home'
            PiRemote.pl_refresh_status()
        return

    # Send data to index or playlist page -- ignore otherwise.
    PiRemote.socket.onmessage = (e) ->
        if e.data == 'playlist'
            # Not full status data about current song transmitted, but tag that playlist has changed.
            if PiRemote.current_page == 'playlist' and PiRemote.current_sub_page == 'home'
                PiRemote.pl_refresh_status()
            return

        if PiRemote.current_page == 'index' and PiRemote.current_sub_page == 'home'
            PiRemote.index_refresh_status()
        else if PiRemote.current_page == 'playlist' and PiRemote.current_sub_page == 'home'
            PiRemote.pl_refresh_status()
        return

    # On any websocket error switch back to short polling.
    PiRemote.socket.onerror = (e) ->
        PiRemote.setWarningText 'No websocket support -- switching to short polling!'
        PiRemote.use_short_polling = true
        PiRemote.load_page PiRemote.current_page, PiRemote.current_sub_page
        return

    # Should never happen (maybe on page reload or leave)
    PiRemote.socket.onclose = (e) ->
        # PiRemote.setStatusText 'Websocket closed.'
        PiRemote.use_short_polling = true
        return

    return

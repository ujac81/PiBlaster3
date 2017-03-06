# playlist.coffee -- install callbacks for playlist view


PiRemote.install_pl_actions = ->

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

    console.log data

    return
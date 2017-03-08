# application.coffee -- document ready function - loaded last in base.pug


# Run on document.ready event.
# Install callbacks and init web socket.
$ ->
    # disable caching for AJAX
    PiRemote.ajax_setup()

    PiRemote.setStatusText 'PiRemote v3.0 loaded.'

    $(document).off 'click', 'a[data-toggle="menu"]'
    $(document).on 'click', 'a[data-toggle="menu"]', (event) ->
        action = event.target.dataset.action
        event.preventDefault()
        $('#bs-collapse-nav').collapse 'hide'
        PiRemote.load_page action

    PiRemote.load_page 'index'
#
#    # invoke AJAX POST to /ajax/browse for dir '' to build table for root dir
#    if $('tbody#browse')[0]
#        PiRemote.install_browse_actions()
#        # PiRemote.install_browse_handlers()
#        PiRemote.do_browse ''
#
#    if $('tbody#pl')[0]
#        PiRemote.install_pl_actions()
#        PiRemote.install_pl_handlers()
#        PiRemote.get_playlist()
#
#    if $('#idxshow')[0]
#        PiRemote.install_index_actions()


    return


PiRemote.load_page = (page) ->
    return if page == PiRemote.current_page
    PiRemote.current_page = page

    d3.select('.piremote-content').html('')

    console.log 'LOAD '+page

    if page == 'index'
        PiRemote.load_index_page()
    else if page == 'browse'
        PiRemote.load_browse_page()
    else if page == 'playlist'
        PiRemote.load_playlist_page()
    else
        d3.select('.piremote-content').append('p').html('No such page '+page)


    return
# application.coffee -- document ready function - loaded last in base.pug


# Run on document.ready event.
# Install callbacks and init web socket.
$ ->
    # disable caching for AJAX
    PiRemote.ajax_setup()

    $('.footer').fadeTo 0, 0


    # invoke AJAX POST to /ajax/browse for dir '' to build table for root dir
    if $('tbody#browse')[0]
        PiRemote.install_browse_actions()
        # PiRemote.install_browse_handlers()
        PiRemote.do_browse ''

    if $('tbody#pl')[0]
        PiRemote.install_pl_actions()
        PiRemote.install_pl_handlers()
        PiRemote.get_playlist()

    if $('#idxshow')[0]
        PiRemote.install_index_actions()


    return

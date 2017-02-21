# application.coffee -- document ready function - loaded last in base.pug


# Run on document.ready event.
# Install callbacks and init web socket.
$ ->

    PiRemote.install_browse_handlers()

    # invoke AJAX POST to /ajax/browse for dir '' to build table for root dir
    if $('tbody#browse')[0]
        PiRemote.do_browse ''


    return

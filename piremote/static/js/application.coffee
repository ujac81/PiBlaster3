# application.coffee -- document ready function - loaded last in base.pug

# Run on document.ready event.
$ ->
    # disable caching for AJAX
    PiRemote.ajax_setup()

    # Top menu action -- invoke load_page() on data-action value.
    $(document).off 'click', 'a[data-toggle="menu"]'
    $(document).on 'click', 'a[data-toggle="menu"]', (event) ->
        action = event.target.dataset.action
        event.preventDefault()
        $('#bs-collapse-nav').collapse 'hide'
        PiRemote.load_page action

    # Initial load of main page.
    PiRemote.load_page PiRemote.current_page, true

    # Disable polling while focus is lost.
    # Load blur page on focus loss and reload page on focus return.
# TODO renable for release
#    $(window).blur ->
#        PiRemote.safe_page = PiRemote.current_page
#        PiRemote.load_page 'blur'
#        return
#    $(window).focus ->
#        PiRemote.load_page PiRemote.safe_page
#        return

    PiRemote.setStatusText 'PiRemote v3.0 loaded.'
    return


# Dynamic page loader -- pages built via d3.js.
# For loader functions see browse.coffee, playlist.coffee, ....
PiRemote.load_page = (page, force=false) ->
    # return if page == PiRemote.current_page && ! force
    PiRemote.current_page = page

    # clean main page node
    d3.select('.piremote-content').html('')
    $('#addsign').hide()

    if page == 'index'
        PiRemote.load_index_page()
    else if page == 'browse'
        PiRemote.load_browse_page()
    else if page == 'playlist'
        PiRemote.load_playlist_page()
    else if page == 'search'
        PiRemote.load_search_page()
    else if page == 'blur'
        d3.select('.piremote-content').append('p').html('No focus on page')
    else
        d3.select('.piremote-content').append('p').html('No such page '+page)

    return
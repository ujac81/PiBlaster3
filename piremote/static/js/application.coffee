# application.coffee -- document ready function - loaded last in base.pug

# Run on document.ready event.
$ ->
    PiRemote.init_variables()

    # Build selection classes
    for item in PiRemote.select_classes
        PiRemote.selected[item] = {'All': true, 'Unknown': false}

    # disable caching for AJAX
    PiRemote.ajax_setup()

    # Send current system time to backend.
    # Raspberry PI might need a time signal to set its internal clock.
    PiRemote.do_ajax
        url: 'command'
        method: 'POST'
        data:
            cmd: 'settime'
            payload: [new Date().getTime()]

    # Top menu action -- invoke load_page() on data-action value.
    $(document).off 'click', 'a[data-toggle="menu"]'
    $(document).on 'click', 'a[data-toggle="menu"]', (event) ->
        action = event.target.dataset.action
        event.preventDefault()
        $('#bs-collapse-nav').collapse 'hide'
        PiRemote.load_page action

    # Initial load of main page.
    PiRemote.load_page PiRemote.current_page, 'home', true

    # Disable polling while focus is lost.
    # Load blur page on focus loss and reload page on focus return.
    unless PiRemote.debug
        $(window).blur ->
            PiRemote.safe_page = PiRemote.current_page
            PiRemote.safe_sub_page = PiRemote.current_sub_page
            PiRemote.load_page 'blur'
            return
        $(window).focus ->
            PiRemote.load_page PiRemote.safe_page, PiRemote.safe_sub_page
            return

    # Clear modal dialog after hide.
    # This ensures that embedded audio player is stopped.
    $('#modalSmall').on 'hidden.bs.modal', ->
        d3.select('#smallModalLabel').html('')
        d3.select('#smallModalMessage').html('')
        return

    PiRemote.setStatusText 'PiRemote v3.0 loaded.'

    # Open websocket for updates from MPD idle worker via redis.
    PiRemote.install_websocket()
    return


# Dynamic page loader -- pages built via d3.js.
# For loader functions see browse.coffee, playlist.coffee, ....
PiRemote.load_page = (page, sub_page='home', force=false) ->
    # return if page == PiRemote.current_page && ! force
    PiRemote.current_page = page
    PiRemote.current_sub_page = sub_page

    # Reset max poll counter for enforced page reloads.
    PiRemote.tot_poll_count = 0

    # remove page specific classes from body
    $('body').removeClass()
    $('#searchbardiv').hide()

    # clean main page node
    PiRemote.clear_navbar_buttons()
    d3.select('.piremote-content').html('')
    $('#addsign').hide()

    if page == 'index'
        PiRemote.load_index_page()
    else if page == 'browse'
        PiRemote.load_browse_page()
    else if page == 'files'
        PiRemote.load_files_page()
    else if page == 'playlist'
        PiRemote.load_playlist_page()
    else if page == 'search'
        PiRemote.load_search_page()
    else if page == 'history'
        PiRemote.load_history_page()
    else if page == 'settings'
        PiRemote.load_settings_page()
    else if page == 'upload'
        PiRemote.load_upload_page()
    else if page == 'blur'
        d3.select('.piremote-content').append('p').html('No focus on page')
    else
        d3.select('.piremote-content').append('p').html('No such page '+page)

    return
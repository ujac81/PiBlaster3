# upload.coffee -- install callbacks for upload view

# Build upload page
PiRemote.load_upload_page = ->

    # Insert buttons
    PiRemote.add_navbar_button 'up_upload_file', 'upload', true, false
    $('button#navbutton_up_upload_file').on 'click', ->
        PiRemote.up_upload_file()
        return

    if PiRemote.upload_message
        if PiRemote.upload_message.error
            d3.select('#smallModalLabel').html('Upload Error')
            cont = d3.select('#smallModalMessage').html('').append('p').attr('class', 'error').html(PiRemote.upload_message.error)
        if PiRemote.upload_message.status
            d3.select('#smallModalLabel').html('File Uploaded')
            cont = d3.select('#smallModalMessage').html('').append('p').html(PiRemote.upload_message.status)
            cont.append('p').html('Database update running -- it might take a few moments for your uploaded file to appear in database.')

        $('#modalSmall').modal('show')
        PiRemote.upload_message = `undefined`

    root = d3.select('.piremote-content')
    root.append('div').attr('id', 'upload-message')
    bl = root.append('div').attr('class', 'upload-list')
    tb = bl.append('table').attr('id', 'tbupload').attr('class', 'table table-striped')
    tb.append('tbody').attr('id', 'upload')
    $('h3#heading').html('Browse Uploadable Files').show()

    $('#addsign').show()
    $('#addsign').off 'click'
    $('#addsign').on 'click', ->
        PiRemote.upload_raise_add_dialog()
        return

    PiRemote.upload_browse PiRemote.last_upload

    return


# Callback for upload file button on top.
PiRemote.up_upload_file = ->

    d3.select('#smallModalLabel').html('Upload File')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    f = cont.append('form')
        .attr('action', '/piremote/upload/')
        .attr('method', 'POST')
        .attr('enctype', 'multipart/form-data')

    f.append('input').attr('type', 'hidden').attr('name', 'csrfmiddlewaretoken').attr('value',$('input[name=csrfmiddlewaretoken')[0].value)

    t = f.append('table').attr('class', 'table uptable')
    tr = t.append('tr')
    tr.append('td').attr('class', 'uptext').html('File')
    tr.append('td').attr('colspan', '2').append('p')
        .append('input')
            .attr('type', 'file').attr('name', 'mediafile').attr('accept', 'audio/*')

    tr = t.append('tr')
    tr.append('td').attr('class', 'uptext').html('Uploader')
    tr.append('td').attr('colspan', '2')
        .append('input')
            .attr('type', 'text').attr('name', 'uploader').attr('placeholder', 'Uploader Name').attr('required', '')

    tr = t.append('tr')
    tr.append('td').attr('class', 'upsubmit').attr('colspan', '3').attr('align', 'center')
        .append('input')
            .attr('type', 'submit').attr('name', 'submit').attr('value', 'Upload')

    $('#modalSmall').modal('show')
    return


# AJAX get of browse list.
PiRemote.upload_browse = (dir) ->
    d3.select('#upload-message').html('')
    PiRemote.do_ajax
        url: 'upload'
        method: 'POST'
        data:
            'dirname': dir
        success: (data) ->
            if data.uploads
                PiRemote.pending_uploads data
            else
                PiRemote.rebuild_upload data  # <-- rebuild table callback
            return
    return


# Build dir listing on upload
PiRemote.rebuild_upload = (data) ->

    # clean table
    tbody = d3.select('tbody#upload')
    tbody.selectAll('tr').remove()

    if data.dirname != ''
        # First entry is folder up
        dirname = data.dirname+'/../'
        up_span = '<span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span>'
        updir = data.dirname.split('/').slice(0, -1).join('/').replace(/\/\//g, '/')
        uptr = tbody.append('tr').classed('dir-item', 1).attr('data-path', updir).attr('id', 'trupdir')
        uptr.append('td').classed('tdup-0', 1).html(up_span)
        uptr.append('td').classed('tdup-1', 1).html(dirname.replace(/\//g, ' / '))
        uptr.append('td').classed('tdup-2', 1)


    dirs = data.browse.filter (d) -> d[0] == 'dir'
    # ... vertical dots for each element
    action_span = '<span class="glyphicon glyphicon-option-vertical" aria-hidden="true"></span>'

    # Append dirs
    tbody.selectAll('tr')
        .data(dirs, (d) -> d).enter()
        .append('tr')
            .attr('class', 'dir-item')
            .attr('data-path', (d) -> d[2]+'/'+d[1])
        .selectAll('td')
        .data((d, i) -> ['<img src="/piremote/static/img/folder-blue.png"/>', d[1], action_span]).enter()
        .append('td')
            .attr('class', (d, i)-> 'tdup-'+i)
            .html((d) -> d)

    # Append files
    files = data.browse.filter (d) -> d[0] == 'file'
    tbody.selectAll('tr')
        .data(files, (d) -> d).enter()
        .append('tr')
            .attr('class', 'file-item selectable')
            .attr('data-path', (d) -> d[2]+'/'+d[1])
        .selectAll('td')
        .data((d, i) -> ['<img src="/piremote/static/img/'+d[3]+'.png"/>', d[1], action_span]).enter()
        .append('td')
            .attr('class', (d, i)-> 'tdup-'+i)
            .classed('selectable', (d,i) -> i == 1)
            .html((d) -> d)

    # single-click on selectable items toggles select
    $('div.upload-list > table > tbody > tr.selectable > td.selectable').on 'click', ->
        $(this).parent().toggleClass 'selected'
        return

    # move up by single-click
    $('#trupdir').on 'click', ->
        PiRemote.upload_browse $(this).data('path')
        return

    # single click on folder or folder td enters folder
    $('div.upload-list > table > tbody > tr.dir-item > td.tdup-0').on 'click', ->
        PiRemote.upload_browse $(this).parent().data('path')
        return

    # single click on dir name enters folder
    $('div.upload-list > table > tbody > tr.dir-item > td.tdup-1').on 'click', ->
        PiRemote.upload_browse $(this).parent().data('path')
        return

    # dir action triggered
    $('div.upload-list > table > tbody > tr.dir-item > td.tdup-2').on 'click', ->
        PiRemote.up_dir_dialog $(this).parent()
        return

    # file action triggered
    $('div.upload-list > table > tbody > tr.selectable > td.tdup-2').on 'click', ->
        PiRemote.up_file_dialog $(this).parent()
        return

    window.scrollTo 0, 0
    return


# Raise modal dialog by click add sign.
PiRemote.upload_raise_add_dialog = ->

    d3.select('#smallModalLabel').html('File Actions')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', 'upload-selection')
            .html('Upload Selection')

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.up_do_action $(this).data('action')
        return

    $('#modalSmall').modal()
    return


# Raise modal dialog by click on dir item actions.
PiRemote.up_dir_dialog = (item) ->

    d3.select('#smallModalLabel').html('Directory Actions')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    path = item.data('path')

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', 'upload-item')
            .html('Upload Directory')

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.up_do_action $(this).data('action'), path
        return

    $('#modalSmall').modal()
    return


# Raise modal dialog by click on file item actions.
PiRemote.up_file_dialog = (item) ->

    d3.select('#smallModalLabel').html('Directory Actions')
    cont = d3.select('#smallModalMessage')
    cont.html('')

    path = item.data('path')

    navul = cont.append('ul').attr('class', 'nav nav-pills nav-stacked')
    navul.append('li').attr('role', 'presentation')
            .append('span').attr('class', 'browse-action-file')
            .attr('data-action', 'upload-item')
            .html('Upload File')

    # Callback for click actions on navigation.
    $(document).off 'click', 'span.browse-action-file'
    $(document).on 'click', 'span.browse-action-file', () ->
        PiRemote.up_do_action $(this).data('action'), path
        return

    $('#modalSmall').modal()
    return


# Callback for any action in upload view (dots clicked or else).
PiRemote.up_do_action = (action, item=null) ->

    items = []
    if action == 'upload-selection'
        sel = d3.selectAll('tr.file-item.selected')
        items = sel.data().map((d) -> d[2]+'/'+d[1])
    else
        items = [item]

    PiRemote.do_ajax
        url: 'doupload'
        method: 'POST'
        data:
            paths: items

    $('#modalSmall').modal('hide')
    return


# Display pending uploads if found in database.
# No interaction, user has to wait until uploads finished.
# Uploads performed by uploader thread.
PiRemote.pending_uploads = (data) ->
    d3.select('#upload-message').append('p').html('There are pending uploads. Please wait until uploads are finished. Reload this page to see if uploads are finished.')
    d3.select('#upload-message').append('p').append('strong').html('List of pending uploads:')
    ol = d3.select('#upload-message').append('ol')
    ol.selectAll('li').data(data.uploads).enter().append('li').html((d)->d)
    return
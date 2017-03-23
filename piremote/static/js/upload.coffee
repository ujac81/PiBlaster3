# upload.coffee -- install callbacks for upload view

# Build upload page
PiRemote.load_upload_page = ->

    # Insert buttons
    PiRemote.add_navbar_button 'up_upload_file', 'upload', true, false

    $('button#navbutton_up_upload_file').off 'click'
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

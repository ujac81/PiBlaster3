# upload.coffee -- install callbacks for upload view

# Build upload page
PiRemote.load_upload_page = ->

    # Insert buttons
    PiRemote.add_navbar_button 'up_upload_file', 'upload', true, false


    $('button#navbutton_up_upload_file').off 'click'
    $('button#navbutton_up_upload_file').on 'click', ->
        PiRemote.up_upload_file()
        return

    console.log PiRemote.upload_message

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
    f.append('input').attr('type', 'file').attr('name', 'mediafile')
    f.append('input').attr('type', 'text').attr('name', 'uploader').attr('placeholder', 'Uploader Name')
    f.append('input').attr('type', 'submit').attr('name', 'submit').attr('value', 'Upload')
    f.append('input').attr('type', 'hidden').attr('name', 'csrfmiddlewaretoken').attr('value',$('input[name=csrfmiddlewaretoken')[0].value)




    $('#modalSmall').modal('show')
    return
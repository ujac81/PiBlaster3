
PiRemote = {}


$ ->

    console.log 'hello world.'

    $('div.browse-list > table > tbody > tr.dir-item').off 'click'
    $('div.browse-list > table > tbody > tr.dir-item').on 'click', ->
        console.log $(this).data().dirname
        return



PiRemote.browse_dir = (event) ->
    console.log event
    return
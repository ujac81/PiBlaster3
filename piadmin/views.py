from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.template import loader


# GET /
def index(request):
    template = loader.get_template('piadmin/index.pug')
    return HttpResponse(template.render({}, request))


def wifi(request):
    template = loader.get_template('piadmin/wifi.pug')
    return HttpResponse(template.render({}, request))


def delete(request):
    template = loader.get_template('piadmin/delete.pug')
    return HttpResponse(template.render({}, request))


def deleteup(request):
    template = loader.get_template('piadmin/deleteup.pug')
    return HttpResponse(template.render({}, request))


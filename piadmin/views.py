from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.template import loader


# GET /
# We only have one get for the main page.
# Sub pages are dynamical loaded via AJAX and inner page content is rebuilt by d3.js.
def index(request):
    template = loader.get_template('piadmin/index.pug')
    return HttpResponse(template.render({}, request))

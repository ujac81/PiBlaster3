#-*- coding: utf-8 -*-
from django import forms


class UploadForm(forms.Form):
    uploader = forms.CharField(max_length=100)
    mediafile = forms.FileField()


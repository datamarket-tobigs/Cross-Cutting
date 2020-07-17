from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'index.html'


class VideoView(TemplateView):
    template_name = 'video.html'


class AboutView(TemplateView):
    template_name = 'about.html'

class ClipsView(TemplateView):
    template_name = 'clip.html'
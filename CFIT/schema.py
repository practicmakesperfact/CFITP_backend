
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class CustomSchemaView(SpectacularAPIView):
    renderer_classes = [OpenApiJsonRenderer, OpenApiYamlRenderer, JSONRenderer]

    def get(self, request, *args, **kwargs):
        generator = self._get_schema_generator()
        schema = generator.get_schema(request=request, public=True)

        # Force JSON if requested
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return Response(schema, content_type='application/json')

        # Let renderer pick
        return Response(schema)
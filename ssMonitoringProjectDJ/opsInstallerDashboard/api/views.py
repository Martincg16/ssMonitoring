from rest_framework.decorators import api_view, permission_classes
from .permissions import HasApiKey
from rest_framework.response import Response
from rest_framework import status

from solarData.models import Proyecto
from ops.models import TipoHito, HitoProyecto
from .serializers import SyncSerializer

# Maps milestone prefix to HitoProyecto date field
PREFIX_MAP = [
    ('cg_repo_', 'fecha_reportada'),
    ('cg_real_', 'fecha_real'),
    ('cg_',      'fecha_programada'),
]


def parse_milestone(milestone):
    """
    Parses a Bubble milestone name into (date_field, codigo).
    e.g. 'cg_real_inicio_de_instalacion' -> ('fecha_real', 'inicio_de_instalacion')
    """
    for prefix, date_field in PREFIX_MAP:
        if milestone.startswith(prefix):
            return date_field, milestone[len(prefix):]
    return None, None


@api_view(['POST'])
@permission_classes([HasApiKey])
def sync(request):
    """
    Called by n8n when a milestone date changes in Bubble.
    Upserts the HitoProyecto row for the given project and milestone.
    """
    serializer = SyncSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # Parse milestone name
    date_field, codigo = parse_milestone(data['milestone'])
    if not date_field:
        return Response(
            {'error': f'Prefijo de milestone no reconocido: {data["milestone"]}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Find project
    try:
        proyecto = Proyecto.objects.get(pid=data['pid'])
    except Proyecto.DoesNotExist:
        return Response(
            {'error': f'Proyecto con pid {data["pid"]} no encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Find milestone type
    try:
        tipo_hito = TipoHito.objects.get(codigo=codigo)
    except TipoHito.DoesNotExist:
        return Response(
            {'error': f'Código de hito "{codigo}" no encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Upsert the hito and set the date
    hito, _ = HitoProyecto.objects.get_or_create(
        pid=proyecto,
        id_tipo_hito=tipo_hito,
    )
    setattr(hito, date_field, data['date'])
    hito.save()

    return Response({'status': 'ok'}, status=status.HTTP_200_OK)
